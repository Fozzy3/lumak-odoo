from datetime import date, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.lumak_secop.models.licitaciones import (
    LumakSecopImport, cierre_info, lead_vals_from_row, monto_corto, secop_query, secop_title,
)

# Fila real del dataset p6dx-8zbt (recortada), publicada el 25 sep 2026.
ROW = {
    "entidad": "MUNICIPIO DE FORTUL",
    "nit_entidad": "800136069",
    "ciudad_entidad": "Fortul",
    "ordenentidad": "Territorial",
    "id_del_proceso": "CO1.REQ.11103103",
    "referencia_del_proceso": "MIN - FRL - SGDS - 067 - 2026",
    "nombre_del_procedimiento": "APOYO LOGÍSTICO PARA LA REALIZACIÓN DEL FESTIVAL DE JUVENTUDES  - ARAUCA.",
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


class TestHelpers(TransactionCase):
    def test_title_turns_shouting_into_readable_title(self):
        self.assertEqual(secop_title(ROW["nombre_del_procedimiento"]),
                         "Apoyo Logístico para la Realización del Festival de Juventudes - Arauca")
        self.assertEqual(secop_title("MUNICIPIO DE FORTUL"), "Municipio de Fortul")
        self.assertEqual(secop_title("SOPORTE DEL SOFTWARE PQRS DE LA ESE Y LA IPS 2026"),
                         "Soporte del Software PQRS de la ESE y la IPS 2026")
        self.assertEqual(secop_title("Software académico"), "Software académico")  # si ya viene bien, no se toca
        self.assertEqual(secop_title(""), "")

    def test_cierre_info_countdown_and_urgency(self):
        hoy = date(2026, 10, 1)
        self.assertEqual(cierre_info(None, 0, hoy), ("sin_fecha", "Sin fecha de cierre"))
        self.assertEqual(cierre_info(hoy, 15.0, hoy), ("critica", "Cierra hoy · 3:00 p. m."))
        self.assertEqual(cierre_info(hoy, 9.5, hoy), ("critica", "Cierra hoy · 9:30 a. m."))
        self.assertEqual(cierre_info(hoy + timedelta(days=1), 0, hoy), ("critica", "Cierra mañana"))
        self.assertEqual(cierre_info(hoy + timedelta(days=3), 0, hoy), ("pronto", "Cierra en 3 días"))
        self.assertEqual(cierre_info(hoy + timedelta(days=10), 0, hoy), ("tiempo", "Cierra en 10 días"))
        self.assertEqual(cierre_info(hoy - timedelta(days=2), 0, hoy), ("vencido", "Cerró hace 2 días"))

    def test_monto_corto(self):
        self.assertEqual(monto_corto(49_000_000), "$49 M")
        self.assertEqual(monto_corto(28_500_000), "$28,5 M")
        self.assertEqual(monto_corto(150_000_000), "$150 M")
        self.assertEqual(monto_corto(4_998_000), "$5,0 M")
        self.assertEqual(monto_corto(1_250_000_000), "$1.250 M")
        self.assertEqual(monto_corto(850_000), "$850 mil")
        self.assertEqual(monto_corto(0), "")


@tagged("post_install", "-at_install")
class TestSecop(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        ref = lambda name: env.ref(f"lumak_secop.{name}")
        cls.team = ref("team_secop")
        cls.detectado, cls.evaluando = ref("stage_detectado"), ref("stage_evaluando")
        cls.preparando, cls.presentada = ref("stage_preparando"), ref("stage_presentada")
        cls.adjudicado = ref("stage_adjudicado")
        cls.plan_oferta, cls.plan_post = ref("plan_oferta_mc"), ref("plan_post_cierre")
        cls.tag_territorial = ref("tag_territorial")
        cls.today = fields.Date.context_today(env["crm.lead"])

    def _lead(self, **vals):
        return self.env["crm.lead"].create({"name": "Proceso de prueba", "type": "opportunity",
                                            "team_id": self.team.id, "stage_id": self.detectado.id, **vals})

    # --- Configuración que instala el módulo ------------------------------------------------
    def test_module_installs_the_bidding_setup(self):
        self.assertTrue(self.team.es_licitaciones)
        etapas = self.env["crm.stage"].search([("team_ids", "in", self.team.ids)])
        self.assertEqual(etapas.mapped("name"), ["Detectado", "Evaluando", "Preparando oferta", "Oferta presentada",
                                                 "En evaluación", "Adjudicado"])
        self.assertEqual(etapas.filtered("is_won"), self.adjudicado)
        self.assertTrue(all(e.requirements for e in etapas))
        self.assertFalse(self.env["crm.stage"].search([("team_ids", "=", False)]), "no quedan etapas globales")
        self.assertEqual(self.env.ref("crm.stage_lead1").team_ids, self.env.ref("sales_team.team_sales_department"))
        self.assertTrue(self.plan_oferta.template_ids and self.plan_post.template_ids)
        self.assertEqual(set(self.plan_oferta.template_ids.mapped("delay_from")), {"before_plan_date"})
        self.assertEqual(set(self.plan_post.template_ids.mapped("delay_from")), {"after_plan_date"})
        self.assertTrue(self.env.ref("lumak_secop.lost_mipyme"))
        plantilla = self.env.ref("lumak_secop.project_contrato_secop")
        self.assertTrue(plantilla.is_template)
        self.assertEqual(plantilla.type_ids.mapped("name"), ["Legalización", "Ejecución", "Facturación y pago",
                                                             "Liquidación y cierre"])
        self.assertTrue(plantilla.task_ids)
        self.assertTrue(plantilla.task_ids.filtered(lambda t: "Ley 2013" in t.name), "registro de bienes y rentas al contratar")

    # --- Importar desde SECOP ---------------------------------------------------------------
    def test_query_from_link_id_or_reference(self):
        self.assertEqual(secop_query(ROW["urlproceso"]["url"]), {"$where": "urlproceso.url like '%CO1.NTC.10958661%'"})
        self.assertEqual(secop_query(" CO1.REQ.11103103 "), {"id_del_proceso": "CO1.REQ.11103103"})
        self.assertEqual(secop_query(" MIN - FRL - SGDS - 067 - 2026 "), {"referencia_del_proceso": "MIN - FRL - SGDS - 067 - 2026"})

    def test_vals_from_row(self):
        vals = lead_vals_from_row(self.env, ROW)
        self.assertEqual(vals["name"], "Apoyo Logístico para la Realización del Festival de Juventudes - Arauca")
        self.assertEqual(vals["secop_id"], "CO1.REQ.11103103")
        self.assertEqual(vals["secop_numero"], "MIN - FRL - SGDS - 067 - 2026")
        self.assertEqual(vals["secop_url"], ROW["urlproceso"]["url"])
        self.assertEqual(vals["secop_modalidad"], "minima")
        self.assertNotIn("secop_unspsc", vals)  # UNSPECIFIED no se guarda
        self.assertEqual(vals["team_id"], self.team.id)
        self.assertEqual(vals["stage_id"], self.detectado.id)
        self.assertEqual(vals["expected_revenue"], 49_000_000.0)
        self.assertEqual(vals["date_deadline"], "2026-10-01")
        self.assertEqual(vals["tag_ids"], [(6, 0, self.tag_territorial.ids)])
        self.assertEqual(vals["secop_plazo"], "1 mes(es)")

    def _import(self, text):
        with patch.object(LumakSecopImport, "_fetch", return_value=[ROW]):
            action = self.env["lumak.secop.import"].create({"referencia": text}).action_import()
        return self.env["crm.lead"].browse(action["res_id"])

    def test_import_creates_lead_with_entity_and_does_not_duplicate(self):
        lead = self._import(ROW["urlproceso"]["url"])
        self.assertEqual(lead.stage_id, self.detectado)
        self.assertEqual(lead.partner_id.name, "Municipio de Fortul")
        self.assertTrue(lead.partner_id.is_company)
        self.assertTrue(lead.partner_id.vat.startswith("800136069"))
        self.assertEqual(self._import("CO1.REQ.11103103"), lead)
        self.assertEqual(self.env["crm.lead"].search_count([("secop_id", "=", "CO1.REQ.11103103")]), 1)
        self.assertEqual(self.env["res.partner"].search_count([("vat", "=like", "800136069%")]), 1)

    def test_import_not_found(self):
        with patch.object(LumakSecopImport, "_fetch", return_value=[]), self.assertRaises(UserError):
            self.env["lumak.secop.import"].create({"referencia": "CO1.REQ.1"}).action_import()

    # --- Campos que ven las vistas -----------------------------------------------------------
    def test_computed_display_fields(self):
        lead = self._lead(date_deadline=self.today + timedelta(days=2), secop_hora_cierre=15.0, expected_revenue=4_998_000)
        self.assertEqual(lead.secop_urgencia, "pronto")
        self.assertEqual(lead.secop_cierre_label, "Cierra en 2 días")
        self.assertEqual(lead.secop_presupuesto_corto, "$5,0 M")
        self.assertTrue(lead.secop_es_licitacion)
        lead.stage_id = self.adjudicado
        self.assertEqual((lead.secop_urgencia, lead.secop_cierre_label), ("cerrado", "Adjudicado"))

    # --- Menús y botones ---------------------------------------------------------------------
    def test_pipeline_action_uses_secop_views_and_team(self):
        action = self.env["crm.lead"].action_secop_pipeline()
        self.assertEqual(action["res_model"], "crm.lead")
        self.assertIn(("team_id", "=", self.team.id), action["domain"])
        self.assertEqual(action["context"]["default_team_id"], self.team.id)
        self.assertNotIn("search_default_assigned_to_me", action["context"])
        # copia la acción genérica del CRM: sin esto hereda su título («Clientes privados») y su ruta /odoo/crm al recargar
        self.assertEqual(action.get("display_name", action["name"]), "Licitaciones SECOP")
        self.assertNotIn("path", action)
        self.assertNotIn("id", action)
        views = dict((mode, view) for view, mode in action["views"])
        self.assertEqual(views["kanban"], self.env.ref("lumak_secop.crm_lead_kanban_secop").id)
        self.assertEqual(views["list"], self.env.ref("lumak_secop.crm_lead_list_secop").id)
        self.assertEqual(views["calendar"], self.env.ref("lumak_secop.crm_lead_calendar_secop").id)

    def test_pipeline_action_filters(self):
        semana = self.env["crm.lead"].action_secop_pipeline(filtro="semana")
        self.assertIn(("date_deadline", "<=", fields.Date.to_string(self.today + timedelta(days=7))), semana["domain"])

    def test_private_pipeline_leaves_secop_out_by_any_path(self):
        ventas = self.env.ref("sales_team.team_sales_department")
        secop = self._lead(user_id=self.env.uid)
        privado = self.env["crm.lead"].create({"name": "Cliente privado", "type": "opportunity",
                                               "team_id": ventas.id, "user_id": self.env.uid})
        sin_equipo = self.env["crm.lead"].create({"name": "Sin equipo", "type": "opportunity", "team_id": False})
        # desde el menú (acción de servidor) y al recargar la página (la acción directa, ruta /odoo/crm)
        for action in (self.env["crm.team"].action_your_pipeline(),
                       self.env["ir.actions.act_window"]._for_xml_id("crm.crm_lead_action_pipeline")):
            domain = action["domain"]
            found = self.env["crm.lead"].search(safe_eval(domain) if isinstance(domain, str) else domain)
            self.assertIn(privado, found)
            self.assertIn(sin_equipo, found)
            self.assertNotIn(secop, found)
            context = action["context"]
            self.assertNotIn("search_default_assigned_to_me", safe_eval(context) if isinstance(context, str) else context)

    def test_private_pipeline_name_in_spanish(self):
        # crm trae su traducción («Mi flujo», «Flujo»); el nombre en inglés del XML no la reemplaza
        self.env["res.lang"]._activate_lang("es_CO")
        records = (self.env.ref("crm.crm_lead_action_pipeline"), self.env.ref("crm.menu_crm_opportunities"))
        for record in records:
            record.update_field_translations("name", {"es_CO": "Mi flujo"})
        self.env["crm.team"]._secop_rename_private_pipeline()
        for record in records:
            self.assertEqual(record.with_context(lang="es_CO").name, "Clientes privados")
            self.assertEqual(record.with_context(lang="en_US").name, "Clientes privados")

    def test_crm_app_opens_on_licitaciones(self):
        self.assertLess(self.env.ref("lumak_secop.menu_secop_root").sequence,
                        self.env.ref("crm.crm_menu_sales").sequence)

    def test_open_in_secop(self):
        lead = self._lead(secop_url=ROW["urlproceso"]["url"])
        self.assertEqual(lead.action_open_secop(), {"type": "ir.actions.act_url", "url": ROW["urlproceso"]["url"], "target": "new"})

    # --- Tablero ---------------------------------------------------------------------------
    def test_dashboard_numbers(self):
        Lead = self.env["crm.lead"]
        base = Lead.get_secop_dashboard()
        self._lead(date_deadline=self.today + timedelta(days=2), expected_revenue=10_000_000)
        self._lead(date_deadline=self.today + timedelta(days=20), expected_revenue=30_000_000)
        self._lead(stage_id=self.adjudicado.id, expected_revenue=5_000_000)
        perdido = self._lead(expected_revenue=50_000_000, secop_precio_ganador=40_000_000)
        perdido.action_set_lost()
        data = Lead.get_secop_dashboard()
        self.assertEqual(data["activos"] - base["activos"], 2)
        self.assertEqual(data["cierran_semana"] - base["cierran_semana"], 1)
        self.assertEqual(data["ganados"] - base["ganados"], 1)
        self.assertEqual(data["perdidos"] - base["perdidos"], 1)
        if not base["descuento_n"]:
            self.assertEqual((data["descuento_ganador"], data["descuento_n"]), (20, 1))
        self.assertTrue(data["proximos"][0]["cierre_label"])

    # --- Planes automáticos por etapa --------------------------------------------------------
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
        self.assertTrue(any("fecha de cierre" in m.body for m in lead.message_ids))

    def test_created_directly_in_stage_schedules_plan(self):
        lead = self._lead(stage_id=self.preparando.id, date_deadline=date(2026, 10, 2))
        self.assertEqual(len(lead.activity_ids), len(self.plan_oferta.template_ids))
