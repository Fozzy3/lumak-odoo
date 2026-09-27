from datetime import date, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.lumak_secop.models import LumakSecopImport, lead_vals_from_row, secop_query

# Fila real del dataset p6dx-8zbt (recortada), publicada el 25 sep 2026.
ROW = {
    "entidad": "MUNICIPIO DE FORTUL",
    "nit_entidad": "800136069",
    "departamento_entidad": "Arauca",
    "ciudad_entidad": "Fortul",
    "ordenentidad": "Territorial",
    "id_del_proceso": "CO1.REQ.11103103",
    "referencia_del_proceso": "MIN - FRL - SGDS - 067 - 2026",
    "nombre_del_procedimiento": "APOYO LOGÍSTICO PARA LA REALIZACIÓN DEL FESTIVAL DE JUVENTUDES",
    "descripci_n_del_procedimiento": "APOYO LOGÍSTICO PARA EL FESTIVAL DE JUVENTUDES EN FORTUL",
    "fase": "Fase de ofertas",
    "precio_base": "49000000",
    "modalidad_de_contratacion": "Mínima cuantía",
    "duracion": "1",
    "unidad_de_duracion": "Mes(es)",
    "fecha_de_recepcion_de": "2026-10-01T00:00:00.000",
    "codigo_principal_de_categoria": "UNSPECIFIED",
    "urlproceso": {"url": "https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.10958661"},
}


def ensure_xmlid(env, name, model, vals):
    """Usa la configuración real (scripts/crm_secop.py) si existe; si no, crea un mínimo para la prueba."""
    record = env.ref(f"lumak.{name}", raise_if_not_found=False)
    if not record:
        record = env[model].create(vals)
        env["ir.model.data"].create({"module": "lumak", "name": name, "model": model, "res_id": record.id})
    return record


@tagged("post_install", "-at_install")
class TestSecop(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.team = ensure_xmlid(env, "team_secop", "crm.team", {
            "name": "Licitaciones SECOP", "use_opportunities": True, "lead_properties_definition": [
                {"name": n, "string": n, "type": t} for n, t in [
                    ("numero_proceso", "char"), ("enlace_secop", "char"), ("unspsc", "char"), ("presupuesto", "float")]
            ] + [{"name": "modalidad", "string": "modalidad", "type": "selection",
                  "selection": [["minima", "Mínima"], ["directa", "Directa"], ["especial", "Especial"]]}],
        })
        stage = lambda name, seq: ensure_xmlid(env, name, "crm.stage", {"name": name, "sequence": seq, "team_ids": [(6, 0, cls.team.ids)]})
        cls.detectado, cls.evaluando = stage("stage_detectado", 101), stage("stage_evaluando", 102)
        cls.preparando, cls.presentada = stage("stage_preparando", 103), stage("stage_presentada", 104)
        todo = env.ref("mail.mail_activity_data_todo")
        plan = lambda name, desde, delays: ensure_xmlid(env, name, "mail.activity.plan", {
            "name": name, "res_model": "crm.lead", "template_ids": [(0, 0, {
                "activity_type_id": todo.id, "summary": f"paso {d}", "delay_count": d, "delay_unit": "days",
                "delay_from": desde, "responsible_type": "on_demand"}) for d in delays]})
        cls.plan_oferta = plan("plan_oferta_mc", "before_plan_date", [2, 1, 0])
        cls.plan_post = plan("plan_post_cierre", "after_plan_date", [1, 2])
        cls.tag_territorial = ensure_xmlid(env, "tag_territorial", "crm.tag", {"name": "Territorial"})

    # --- Importar desde SECOP ---------------------------------------------------------------
    def test_query_from_link_id_or_reference(self):
        self.assertEqual(secop_query(ROW["urlproceso"]["url"]), {"$where": "urlproceso.url like '%CO1.NTC.10958661%'"})
        self.assertEqual(secop_query(" CO1.REQ.11103103 "), {"id_del_proceso": "CO1.REQ.11103103"})
        self.assertEqual(secop_query(" MIN - FRL - SGDS - 067 - 2026 "), {"referencia_del_proceso": "MIN - FRL - SGDS - 067 - 2026"})

    def test_vals_from_row(self):
        vals = lead_vals_from_row(self.env, ROW)
        self.assertEqual(vals["secop_id"], "CO1.REQ.11103103")
        self.assertEqual(vals["team_id"], self.team.id)
        self.assertEqual(vals["stage_id"], self.detectado.id)
        self.assertEqual(vals["expected_revenue"], 49_000_000.0)
        self.assertEqual(vals["date_deadline"], "2026-10-01")
        self.assertEqual(vals["tag_ids"], [(6, 0, self.tag_territorial.ids)])
        self.assertEqual(vals["lead_properties"], {
            "numero_proceso": "MIN - FRL - SGDS - 067 - 2026", "enlace_secop": ROW["urlproceso"]["url"],
            "presupuesto": 49_000_000.0, "modalidad": "minima"})  # UNSPECIFIED no se guarda

    def _import(self, text):
        with patch.object(LumakSecopImport, "_fetch", return_value=[ROW]):
            action = self.env["lumak.secop.import"].create({"referencia": text}).action_import()
        return self.env["crm.lead"].browse(action["res_id"])

    def test_import_creates_lead_with_entity_and_does_not_duplicate(self):
        lead = self._import(ROW["urlproceso"]["url"])
        self.assertEqual(lead.stage_id, self.detectado)
        self.assertEqual(lead.partner_id.name, "MUNICIPIO DE FORTUL")
        self.assertTrue(lead.partner_id.is_company)
        self.assertTrue(lead.partner_id.vat.startswith("800136069"))
        self.assertEqual(self._import("CO1.REQ.11103103"), lead)
        self.assertEqual(self.env["crm.lead"].search_count([("secop_id", "=", "CO1.REQ.11103103")]), 1)
        self.assertEqual(self.env["res.partner"].search_count([("vat", "=like", "800136069%")]), 1)

    def test_import_not_found(self):
        with patch.object(LumakSecopImport, "_fetch", return_value=[]), self.assertRaises(UserError):
            self.env["lumak.secop.import"].create({"referencia": "CO1.REQ.1"}).action_import()

    def test_pipeline_action_shows_only_the_secop_team(self):
        action = self.env["crm.lead"].action_secop_pipeline()
        self.assertEqual(action["res_model"], "crm.lead")
        self.assertIn(("team_id", "=", self.team.id), action["domain"])
        self.assertEqual(action["context"]["default_team_id"], self.team.id)
        self.assertNotIn("search_default_assigned_to_me", action["context"])  # se ven todos los procesos

    # --- Planes automáticos por etapa --------------------------------------------------------
    def _lead(self, **vals):
        return self.env["crm.lead"].create({"name": "Proceso de prueba", "type": "opportunity",
                                            "team_id": self.team.id, "stage_id": self.detectado.id, **vals})

    def _dates(self, lead):
        return sorted(lead.activity_ids.mapped("date_deadline"))

    def test_preparando_schedules_offer_plan_from_deadline_once(self):
        cierre = date(2026, 10, 2)
        lead = self._lead(date_deadline=cierre)
        lead.stage_id = self.preparando
        expected = sorted(cierre - timedelta(days=t.delay_count) for t in self.plan_oferta.template_ids)
        self.assertEqual(self._dates(lead), expected)
        lead.stage_id = self.evaluando
        lead.stage_id = self.preparando  # volver a la etapa no duplica el plan
        self.assertEqual(len(lead.activity_ids), len(self.plan_oferta.template_ids))

    def test_presentada_schedules_post_closing_plan(self):
        cierre = date(2026, 10, 2)
        lead = self._lead(date_deadline=cierre)
        lead.stage_id = self.presentada
        expected = sorted(cierre + timedelta(days=t.delay_count) for t in self.plan_post.template_ids)
        self.assertEqual(self._dates(lead), expected)

    def test_without_deadline_asks_for_it_and_schedules_nothing(self):
        lead = self._lead()
        lead.stage_id = self.preparando
        self.assertFalse(lead.activity_ids)
        self.assertIn("fecha de cierre", lead.message_ids[0].body)

    def test_created_directly_in_stage_schedules_plan(self):
        lead = self._lead(stage_id=self.preparando.id, date_deadline=date(2026, 10, 2))
        self.assertEqual(len(lead.activity_ids), len(self.plan_oferta.template_ids))
