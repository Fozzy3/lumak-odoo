import re
import unicodedata

import requests
from stdnum.co import nit

from odoo import _, api, fields, models
from odoo.exceptions import UserError

SECOP_URL = "https://www.datos.gov.co/resource/p6dx-8zbt.json"  # SECOP II - Procesos de contratación

# Prefijo de «modalidad_de_contratacion» (sin tildes, minúsculas) -> opción de la propiedad «modalidad»
MODALIDADES = [
    ("minima cuantia", "minima"),
    ("seleccion abreviada de menor cuantia", "samc"),
    ("seleccion abreviada menor cuantia", "samc"),
    ("licitacion publica", "licitacion"),
    ("concurso de meritos", "concurso"),
    ("contratacion directa", "directa"),
    ("contratacion regimen especial", "especial"),
]
ETIQUETAS = {"Territorial": "lumak.tag_territorial", "Nacional": "lumak.tag_nacional"}
# Al entrar a la etapa se agenda el plan una sola vez, contando desde la fecha de cierre.
PLANES_POR_ETAPA = {"lumak.stage_preparando": "lumak.plan_oferta_mc", "lumak.stage_presentada": "lumak.plan_post_cierre"}


def _plain(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(c)).lower()


def secop_query(text):
    """Filtro del dataset según lo que pegue el usuario: enlace, ID (CO1.REQ…) o referencia."""
    text = (text or "").strip()
    notice = re.search(r"CO1\.NTC\.\d+", text)
    if notice:
        return {"$where": f"urlproceso.url like '%{notice.group()}%'"}
    if re.fullmatch(r"CO1\.REQ\.\d+", text):
        return {"id_del_proceso": text}
    return {"referencia_del_proceso": text}


def lead_vals_from_row(env, row):
    presupuesto = float(row.get("precio_base") or 0)
    props = {
        "numero_proceso": row.get("referencia_del_proceso"),
        "enlace_secop": (row.get("urlproceso") or {}).get("url"),
        "presupuesto": presupuesto,
    }
    modalidad = next((key for prefix, key in MODALIDADES if _plain(row.get("modalidad_de_contratacion")).startswith(prefix)), None)
    if modalidad:
        props["modalidad"] = modalidad
    if row.get("codigo_principal_de_categoria", "UNSPECIFIED") != "UNSPECIFIED":
        props["unspsc"] = row["codigo_principal_de_categoria"]
    etiqueta = env.ref(ETIQUETAS.get(row.get("ordenentidad"), "lumak.none"), raise_if_not_found=False)
    detalle = [row.get("descripci_n_del_procedimiento"),
               f"Duración: {row.get('duracion')} {row.get('unidad_de_duracion')}" if row.get("duracion") else None,
               f"Fase en SECOP: {row.get('fase')}" if row.get("fase") else None]
    return {
        "name": row.get("nombre_del_procedimiento") or row["id_del_proceso"],
        "type": "opportunity",
        "team_id": env.ref("lumak.team_secop").id,
        "stage_id": env.ref("lumak.stage_detectado").id,
        "secop_id": row["id_del_proceso"],
        "expected_revenue": presupuesto,
        "date_deadline": (row.get("fecha_de_recepcion_de") or "")[:10] or False,
        "description": "".join(f"<p>{line}</p>" for line in detalle if line),
        "tag_ids": [(6, 0, etiqueta.ids)] if etiqueta else [],
        "lead_properties": props,
    }


def secop_partner(env, row):
    """La entidad compradora como contacto, buscada por NIT (sin importar el dígito de verificación)."""
    numero = row.get("nit_entidad") or ""
    partner = env["res.partner"].search([("vat", "=like", f"{numero}%"), ("is_company", "=", True)], limit=1) if numero else None
    if partner:
        return partner
    vat = f"{numero}-{nit.calc_check_digit(numero)}" if numero.isdigit() else False
    return env["res.partner"].create({
        "name": row.get("entidad") or numero, "is_company": True, "vat": vat,
        "city": row.get("ciudad_entidad"), "country_id": env.ref("base.co").id,
    })


class CrmLead(models.Model):
    _inherit = "crm.lead"

    secop_id = fields.Char("ID del proceso SECOP", index=True, copy=False)
    secop_planes = fields.Char("Planes SECOP agendados", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._secop_schedule_stage_plans()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if "stage_id" in vals:
            self._secop_schedule_stage_plans()
        return res

    @api.model
    def action_secop_pipeline(self):
        """Tablero del CRM solo con el equipo «Licitaciones SECOP» (sus etapas, sin las de ventas)."""
        team = self.env.ref("lumak.team_secop")
        action = self.env["ir.actions.act_window"]._for_xml_id("crm.crm_lead_action_pipeline")
        action.update({
            "name": _("Licitaciones SECOP"),
            "domain": [("type", "=", "opportunity"), ("team_id", "=", team.id)],
            "context": {"default_type": "opportunity", "default_team_id": team.id},
        })
        return action

    def _secop_schedule_stage_plans(self):
        for stage_xmlid, plan_xmlid in PLANES_POR_ETAPA.items():
            stage = self.env.ref(stage_xmlid, raise_if_not_found=False)
            plan = self.env.ref(plan_xmlid, raise_if_not_found=False)
            if not stage or not plan:
                continue
            for lead in self.filtered(lambda l: l.stage_id == stage and plan_xmlid not in (l.secop_planes or "")):
                if not lead.date_deadline:
                    lead.message_post(body=_("Pon la fecha de cierre para agendar el plan «%s».", plan.name))
                    continue
                self.env["mail.activity.schedule"].with_context(active_model="crm.lead", active_ids=lead.ids).create({
                    "res_model": "crm.lead", "res_ids": str(lead.ids), "plan_id": plan.id,
                    "plan_date": lead.date_deadline, "plan_on_demand_user_id": (lead.user_id or self.env.user).id,
                }).action_schedule_plan()
                lead.secop_planes = ",".join(filter(None, [lead.secop_planes, plan_xmlid]))


class LumakSecopImport(models.TransientModel):
    _name = "lumak.secop.import"
    _description = "Importar proceso desde SECOP II"

    referencia = fields.Char("Enlace, ID o referencia del proceso", required=True)

    def _fetch(self, params):
        try:
            response = requests.get(SECOP_URL, params={**params, "$limit": 1}, timeout=30)
            response.raise_for_status()
        except requests.RequestException as error:
            raise UserError(_("No pude consultar SECOP II (%s). Intenta de nuevo en un momento.", error)) from error
        return response.json()

    def action_import(self):
        rows = self._fetch(secop_query(self.referencia))
        if not rows:
            raise UserError(_("No encontré ese proceso en los datos abiertos de SECOP II. "
                              "Si se publicó hoy, puede aparecer mañana."))
        row = rows[0]
        lead = self.env["crm.lead"].search([("secop_id", "=", row["id_del_proceso"])], limit=1)
        if not lead:
            lead = self.env["crm.lead"].create({**lead_vals_from_row(self.env, row), "partner_id": secop_partner(self.env, row).id})
        return {"type": "ir.actions.act_window", "res_model": "crm.lead", "res_id": lead.id,
                "view_mode": "form", "target": "current"}
