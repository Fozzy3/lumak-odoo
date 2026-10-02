import re
import unicodedata
from datetime import timedelta

import requests
from stdnum.co import nit

from odoo import _, api, fields, models
from odoo.exceptions import UserError

SECOP_URL = "https://www.datos.gov.co/resource/p6dx-8zbt.json"  # SECOP II - Procesos de contratación

MODALIDADES = [
    ("minima", "Mínima cuantía"),
    ("samc", "Selección abreviada de menor cuantía"),
    ("licitacion", "Licitación pública"),
    ("concurso", "Concurso de méritos"),
    ("directa", "Contratación directa"),
    ("especial", "Régimen especial"),
]
# Prefijo de «modalidad_de_contratacion» (sin tildes, minúsculas) -> modalidad
MODALIDAD_SECOP = [
    ("minima cuantia", "minima"),
    ("seleccion abreviada de menor cuantia", "samc"),
    ("seleccion abreviada menor cuantia", "samc"),
    ("licitacion publica", "licitacion"),
    ("concurso de meritos", "concurso"),
    ("contratacion directa", "directa"),
    ("contratacion regimen especial", "especial"),
]
ETIQUETAS = {"Territorial": "lumak_secop.tag_territorial", "Nacional": "lumak_secop.tag_nacional"}
# Al entrar a la etapa se agenda el plan una sola vez, contando desde la fecha de cierre.
PLANES_POR_ETAPA = {"lumak_secop.stage_preparando": "lumak_secop.plan_oferta_mc", "lumak_secop.stage_presentada": "lumak_secop.plan_post_cierre"}
# Lo que toca hacer en cada etapa; se muestra arriba en la ficha del proceso
SIGUIENTE_PASO = {
    "lumak_secop.stage_detectado": "Lee la invitación (botón «Abrir en SECOP»). Si vas: pásalo a «Preparando oferta». "
                                   "Si no: «Perdido» con el motivo.",
    "lumak_secop.stage_preparando": "Pon el costo estimado en la pestaña SECOP, fija el precio en la cotización y pulsa "
                                    "«Preparar documentos de la oferta». Presenta en SECOP II y pásalo a «Presentada».",
    "lumak_secop.stage_presentada": "Espera el informe de evaluación y subsana si te lo piden. Si ganas: «Ganado». "
                                    "Si no: «Perdido» y anota el precio ganador.",
    "lumak_secop.stage_adjudicado": "Aprueba el contrato electrónico en SECOP II. Lo demás sigue en el proyecto del contrato "
                                    "(botón de arriba).",
}
PARTICULAS = {"de", "del", "la", "las", "el", "los", "y", "e", "o", "u", "para", "por", "en", "a", "al",
              "con", "sin", "sobre", "entre", "su", "sus", "que"}
SIGLAS = {"ESE", "IPS", "EPS", "TIC", "TICS", "IA", "SECOP", "SENA", "ICBF", "DANE", "NIT", "RUT", "SAS", "S.A.S",
          "ERP", "CRM", "API", "PAE", "PETI", "MSPI", "MIPG", "SST", "SGSST", "IE", "I.E", "ESP", "PGIRS", "POT",
          "SISBEN", "SIMAT", "SIGEP", "SGC", "ISO", "UD", "UNAL", "SAMC"}
# «Preguntar a la IA»: el perfil de arranque (el usuario lo ajusta en Datos de la empresa) y lo que se le pide a la IA.
# Todo esto sale a otra IA: nada de datos personales.
PERFIL_IA = """LUMAK SOLUTIONS S.A.S., Bogotá, en el régimen SIMPLE.
Qué hacemos: sistemas de información a la medida (aplicaciones web, integraciones, automatización, analítica), con soporte y mantenimiento mensual, SaaS y nube. La capacitación es una línea secundaria.
Clientes: entidades públicas pequeñas por SECOP II y privados (cajas de compensación, universidades, cooperativas, clínicas).
Cuántos somos: una persona, el representante legal, que desarrolla el software. Sin empleados; si un proyecto lo pide, sumamos un contratista.
Objetivo: ganar contratos pequeños de software que podamos ejecutar y que nos dejen experiencia certificable.
Dónde competimos hoy: mínima cuantía y régimen especial con ofertas. Aún no tenemos RUP y llevamos menos de un año constituidos, así que tampoco aplican los procesos limitados a MiPyME.
No es lo nuestro: hardware y equipos, venta o renovación de licencias de marca, medios y publicidad, obras e interventoría."""
PREGUNTA_IA = """## Qué necesito
Lee la invitación, los estudios previos y los anexos del proceso, y respóndeme en español sencillo:
1. Qué quieren contratar y qué hay que entregar, en pocas líneas.
2. ¿Encaja con lo que hacemos y con nuestro objetivo? Sí, no o dudoso, y por qué.
3. Requisitos habilitantes que no cumplimos: experiencia, RUP, MiPyME, personal, garantías, visitas u otros.
4. Riesgos: marca o producto específico, hardware, plazo corto o alcance que no se ve en el título.
5. Tu recomendación en una línea: ofertar o no.
No inventes: si no pudiste abrir un documento, dilo y pídemelo."""


def _plain(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(c)).lower()


def _capitalizar(palabra):
    minus = palabra.lower()
    for i, c in enumerate(minus):
        if c.isalpha():
            return minus[:i] + c.upper() + minus[i + 1:]
    return palabra


def secop_title(text):
    """Convierte los títulos en MAYÚSCULAS de SECOP en títulos legibles; lo que ya viene bien no se toca."""
    text = re.sub(r"\s+", " ", text or "").strip().rstrip(".")
    letras = [c for c in text if c.isalpha()]
    if not letras or sum(c.isupper() for c in letras) / len(letras) < 0.8:
        return text
    palabras = []
    for i, palabra in enumerate(text.split(" ")):
        nucleo = palabra.strip("()[]{},.;:\"'")
        if i and palabra.lower() in PARTICULAS:
            palabras.append(palabra.lower())
        elif nucleo in SIGLAS or not re.search(r"[AEIOUÁÉÍÓÚaeiouáéíóú]", palabra) or re.search(r"\d", palabra):
            palabras.append(palabra)
        else:
            palabras.append(_capitalizar(palabra))
    return " ".join(palabras)


def _hora_texto(hora):
    h, m = int(hora), round((hora % 1) * 60)
    return f"{(h % 12) or 12}:{m:02d} {'a. m.' if h < 12 else 'p. m.'}"


def cierre_info(deadline, hora, today):
    """(urgencia, texto) de la cuenta regresiva. La urgencia decide el color en las vistas."""
    if not deadline:
        return "sin_fecha", "Sin fecha de cierre"
    dias = (deadline - today).days
    if dias < 0:
        return "vencido", f"Cerró hace {-dias} día{'s' if dias < -1 else ''}"
    if dias <= 1:
        texto = "Cierra hoy" if dias == 0 else "Cierra mañana"
        return "critica", f"{texto} · {_hora_texto(hora)}" if hora else texto
    return ("pronto" if dias <= 3 else "tiempo"), f"Cierra en {dias} días"


def monto_corto(valor):
    """$49 M, $5,0 M, $1.250 M, $850 mil (separadores colombianos)."""
    if not valor:
        return ""
    if valor >= 1_000_000:
        millones = valor / 1_000_000
        con_decimal = millones < 10 or (millones < 100 and abs(millones - round(millones)) >= 0.05)
        texto = f"{millones:,.1f}" if con_decimal else f"{millones:,.0f}"
        return "$" + texto.replace(",", "_").replace(".", ",").replace("_", ".") + " M"
    return f"${valor / 1000:,.0f}".replace(",", ".") + " mil"


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
    modalidad = next((key for prefix, key in MODALIDAD_SECOP if _plain(row.get("modalidad_de_contratacion")).startswith(prefix)), False)
    etiqueta = env.ref(ETIQUETAS[row["ordenentidad"]], raise_if_not_found=False) if row.get("ordenentidad") in ETIQUETAS else None
    detalle = [secop_title(row.get("descripci_n_del_procedimiento")),
               f"Duración: {row.get('duracion')} {row.get('unidad_de_duracion')}" if row.get("duracion") else None,
               f"Fase en SECOP: {row.get('fase')}" if row.get("fase") else None]
    vals = {
        "name": secop_title(row.get("nombre_del_procedimiento")) or row["id_del_proceso"],
        "type": "opportunity",
        "team_id": env.ref("lumak_secop.team_secop").id,
        "stage_id": env.ref("lumak_secop.stage_detectado").id,
        "secop_id": row["id_del_proceso"],
        "secop_numero": row.get("referencia_del_proceso"),
        "secop_url": (row.get("urlproceso") or {}).get("url"),
        "secop_modalidad": modalidad,
        "expected_revenue": presupuesto,
        "date_deadline": (row.get("fecha_de_recepcion_de") or "")[:10] or False,
        "secop_plazo": f"{row['duracion']} {row.get('unidad_de_duracion', '').lower()}".strip() if row.get("duracion") else False,
        "description": "".join(f"<p>{line}</p>" for line in detalle if line),
        "tag_ids": [(6, 0, etiqueta.ids)] if etiqueta else [],
    }
    if row.get("codigo_principal_de_categoria", "UNSPECIFIED") != "UNSPECIFIED":
        vals["secop_unspsc"] = row["codigo_principal_de_categoria"]
    return vals


def secop_partner(env, row):
    """La entidad compradora como contacto, buscada por NIT (sin importar el dígito de verificación)."""
    numero = row.get("nit_entidad") or ""
    partner = env["res.partner"].search([("vat", "=like", f"{numero}%"), ("is_company", "=", True)], limit=1) if numero else None
    if partner:
        return partner
    vat = f"{numero}-{nit.calc_check_digit(numero)}" if numero.isdigit() else False
    return env["res.partner"].create({
        "name": secop_title(row.get("entidad")) or numero, "is_company": True, "vat": vat,
        "city": row.get("ciudad_entidad"), "country_id": env.ref("base.co").id,
    })


class CrmLead(models.Model):
    _inherit = "crm.lead"

    secop_id = fields.Char("ID del proceso SECOP", index=True, copy=False)
    secop_planes = fields.Char("Planes SECOP agendados", copy=False)
    secop_numero = fields.Char("N.º de proceso", copy=False)
    secop_url = fields.Char("Enlace SECOP II", copy=False)
    secop_modalidad = fields.Selection(MODALIDADES, "Modalidad")
    secop_unspsc = fields.Char("Código UNSPSC")
    secop_hora_cierre = fields.Float("Hora de cierre")
    secop_limite_observaciones = fields.Date("Límite de observaciones")
    secop_estampillas = fields.Float("Estampillas (%)")
    secop_mipyme = fields.Boolean("Limitado a MiPyME")
    secop_pago_contra_entrega = fields.Boolean("Pago contra entrega")
    secop_exige_garantias = fields.Boolean("Exige garantías")
    secop_oferentes = fields.Integer("N.º de oferentes")
    secop_precio_ganador = fields.Monetary("Precio ganador", currency_field="company_currency")
    secop_urgencia = fields.Selection([
        ("sin_fecha", "Sin fecha"), ("vencido", "Vencido"), ("critica", "Hoy o mañana"),
        ("pronto", "En 3 días o menos"), ("tiempo", "Con tiempo"), ("cerrado", "Cerrado"),
    ], "Urgencia", compute="_compute_secop_cierre")
    secop_cierre_label = fields.Char("Cierre", compute="_compute_secop_cierre")
    secop_presupuesto_corto = fields.Char("Presupuesto", compute="_compute_secop_presupuesto_corto")
    secop_es_licitacion = fields.Boolean(compute="_compute_secop_es_licitacion")
    secop_siguiente_paso = fields.Char("Siguiente paso", compute="_compute_secop_siguiente_paso")
    secop_prompt_ia = fields.Text("Pregunta para la IA", compute="_compute_secop_prompt_ia")

    @api.depends("stage_id", "won_status")
    def _compute_secop_siguiente_paso(self):
        pasos = {self.env.ref(xmlid).id: texto for xmlid, texto in SIGUIENTE_PASO.items()}
        for lead in self:
            lead.secop_siguiente_paso = pasos.get(lead.stage_id.id, "") if lead.won_status != "lost" else ""

    @api.depends("date_deadline", "secop_hora_cierre", "won_status")
    def _compute_secop_cierre(self):
        today = fields.Date.context_today(self)
        for lead in self:
            if lead.won_status in ("won", "lost"):
                lead.secop_urgencia = "cerrado"
                lead.secop_cierre_label = _("Adjudicado") if lead.won_status == "won" else _("Perdido")
            else:
                lead.secop_urgencia, lead.secop_cierre_label = cierre_info(lead.date_deadline, lead.secop_hora_cierre, today)

    @api.depends("expected_revenue")
    def _compute_secop_presupuesto_corto(self):
        for lead in self:
            lead.secop_presupuesto_corto = monto_corto(lead.expected_revenue)

    @api.depends("team_id")
    def _compute_secop_es_licitacion(self):
        team = self.env.ref("lumak_secop.team_secop", raise_if_not_found=False)
        for lead in self:
            lead.secop_es_licitacion = bool(team) and lead.team_id == team

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._secop_al_cambiar_etapa()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if "stage_id" in vals:
            self._secop_al_cambiar_etapa()
        return res

    def _secop_al_cambiar_etapa(self):
        """Lo que pasa solo al entrar a una etapa. Otros archivos lo extienden (contratos.py)."""
        self._secop_schedule_stage_plans()

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

    def action_open_secop(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url", "url": self.secop_url, "target": "new"}

    @api.depends("name", "partner_id", "secop_id", "secop_url", "secop_modalidad", "expected_revenue", "date_deadline",
                 "secop_hora_cierre")
    @api.depends_context("company")
    def _compute_secop_prompt_ia(self):
        """La pregunta que «Preguntar a la IA» copia: la empresa, el proceso y qué revisar, para pegarla en cualquier IA."""
        empresa = self.env.company
        experiencia = "\n".join(
            f"- {e.objeto} · {e.contratante_id.name}" + (f" · {monto_corto(e.valor)}" if e.valor else "")
            + (f" · terminó el {e.fecha_fin:%d/%m/%Y}" if e.fecha_fin else "") + (" (del socio)" if e.de_socio else "")
            for e in self.env["lumak.experiencia"].search([])) or "- Ninguna registrada todavía."
        constituida = f"Constituida el {empresa.lumak_fecha_constitucion:%d/%m/%Y}.\n" if empresa.lumak_fecha_constitucion else ""
        modalidades = dict(MODALIDADES)
        for lead in self:
            cierre = lead.date_deadline and f"{lead.date_deadline:%d/%m/%Y}" + (
                f" {_hora_texto(lead.secop_hora_cierre)}" if lead.secop_hora_cierre else "")
            datos = [("Objeto", lead.name), ("Entidad", lead.partner_id.name), ("ID", lead.secop_id),
                     ("Modalidad", modalidades.get(lead.secop_modalidad)),
                     ("Presupuesto oficial", monto_corto(lead.expected_revenue)), ("Cierre", cierre),
                     ("Enlace en SECOP II", lead.secop_url)]
            captcha = (f"\n- Si SECOP pide captcha, usa los datos abiertos: {SECOP_URL}?id_del_proceso={lead.secop_id} "
                       "trae el id_del_portafolio, y con él los documentos salen en "
                       "https://www.datos.gov.co/resource/dmgg-8hin.json?proceso=<id_del_portafolio>.") if lead.secop_id else ""
            lead.secop_prompt_ia = (
                "Actúa como asesor de contratación pública en Colombia. Quiero saber si este proceso de SECOP II encaja "
                "con mi empresa y si vale la pena presentar oferta.\n\n"
                f"## Mi empresa\n{empresa.lumak_perfil_ia or ''}\n{constituida}Experiencia que podemos acreditar:\n{experiencia}\n\n"
                "## El proceso\n" + "\n".join(f"- {k}: {v}" for k, v in datos if v) + captcha + f"\n\n{PREGUNTA_IA}")

    @api.model
    def action_secop_pipeline(self, filtro=None):
        """Tablero del CRM solo con el equipo «Licitaciones SECOP», con sus vistas propias."""
        team = self.env.ref("lumak_secop.team_secop")
        hoy = fields.Date.context_today(self)
        extra = {"semana": [("date_deadline", ">=", fields.Date.to_string(hoy)),
                            ("date_deadline", "<=", fields.Date.to_string(hoy + timedelta(days=7)))]}.get(filtro, [])
        action = self.env["ir.actions.act_window"]._for_xml_id("crm.crm_lead_action_pipeline")
        # Sin esto hereda el título («Clientes privados») y la ruta /odoo/crm, que al recargar abre el flujo privado
        for key in ("id", "xml_id", "path", "display_name", "view_id"):
            action.pop(key, None)
        action.update({
            "name": _("Cierran esta semana") if filtro == "semana" else _("Mis procesos"),
            "domain": [("type", "=", "opportunity"), ("team_id", "=", team.id)] + extra,
            "context": {"default_type": "opportunity", "default_team_id": team.id},
            "view_mode": "kanban,list,calendar,form,activity",
            "views": [(self.env.ref("lumak_secop.crm_lead_kanban_secop").id, "kanban"),
                      (self.env.ref("lumak_secop.crm_lead_list_secop").id, "list"),
                      (self.env.ref("lumak_secop.crm_lead_calendar_secop").id, "calendar"),
                      (self.env.ref("lumak_secop.crm_lead_form_secop").id, "form"), (False, "activity")],
        })
        return action

    def _secop_accion_ficha(self):
        """Abrir un proceso con la ficha de SECOP (sin los campos genéricos del CRM)."""
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "crm.lead", "res_id": self.id, "view_mode": "form",
                "views": [(self.env.ref("lumak_secop.crm_lead_form_secop").id, "form")], "target": "current"}

    @api.model
    def get_secop_dashboard(self):
        """Cifras del tablero de Licitaciones (ya formateadas para mostrar)."""
        team = self.env.ref("lumak_secop.team_secop")
        hoy = fields.Date.context_today(self)
        base = [("team_id", "=", team.id), ("type", "=", "opportunity")]
        activos = self.search(base + [("won_status", "=", "pending")])
        semana = activos.filtered(lambda l: l.date_deadline and hoy <= l.date_deadline <= hoy + timedelta(days=7))
        todos = self.with_context(active_test=False)
        ganados = todos.search_count(base + [("won_status", "=", "won")])
        # Perdido cuenta solo si ofertamos: se marca perdido desde «Presentada». Lo descartado al revisar no es derrota
        perdido = base + [("won_status", "=", "lost"), ("stage_id", "=", self.env.ref("lumak_secop.stage_presentada").id)]
        perdidos = todos.search_count(perdido)
        con_precio = todos.search(perdido + [("secop_precio_ganador", ">", 0), ("expected_revenue", ">", 0)])
        descuentos = [1 - l.secop_precio_ganador / l.expected_revenue for l in con_precio]
        conteo = {stage.id: total for stage, total in self._read_group(base + [("won_status", "=", "pending")], ["stage_id"], ["__count"])}
        etapas = self.env["crm.stage"].search([("team_ids", "in", team.ids), ("is_won", "=", False)])
        return {
            "activos": len(activos),
            "cierran_semana": len(semana),
            "valor_en_juego": monto_corto(sum(activos.mapped("expected_revenue"))) or "$0",
            "ganados": ganados,
            "perdidos": perdidos,
            "tasa": round(100 * ganados / (ganados + perdidos)) if ganados + perdidos else None,
            "descuento_ganador": round(100 * sum(descuentos) / len(descuentos)) if descuentos else None,
            "descuento_n": len(descuentos),
            "etapas": [{"id": s.id, "nombre": s.name, "total": conteo.get(s.id, 0)} for s in etapas],
            "proximos": [{
                "id": l.id, "nombre": l.name, "entidad": l.partner_id.name or "", "presupuesto": l.secop_presupuesto_corto,
                "cierre_label": l.secop_cierre_label, "urgencia": l.secop_urgencia,
                "modalidad": dict(MODALIDADES).get(l.secop_modalidad, ""),
            } for l in activos.filtered("date_deadline").sorted("date_deadline")[:6]],
        }


class ResCompany(models.Model):
    _inherit = "res.company"

    # Al crear la columna, Odoo llena la empresa existente con el perfil de arranque; de ahí en adelante lo edita el usuario
    lumak_perfil_ia = fields.Text("Perfil para preguntar a la IA", default=PERFIL_IA,
                                  help="Lo que hace la empresa, cuántos son y qué buscan. «Preguntar a la IA» lo copia en "
                                       "cada proceso: sin datos personales.")


class CrmTeam(models.Model):
    _inherit = "crm.team"

    # El flujo genérico del CRM («Clientes privados», views.xml) deja fuera los equipos marcados.
    es_licitaciones = fields.Boolean("Equipo de licitaciones SECOP")

    @api.model
    def _secop_rename_private_pipeline(self):
        # Un nombre en el XML solo cambia el inglés; la traducción de crm («Mi flujo») seguiría viéndose en español.
        nombres = {code: "Clientes privados" for code, _ in self.env["res.lang"].get_installed()}
        for xmlid in ("crm.crm_lead_action_pipeline", "crm.menu_crm_opportunities"):
            self.env.ref(xmlid).update_field_translations("name", nombres)


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
        return lead._secop_accion_ficha()
