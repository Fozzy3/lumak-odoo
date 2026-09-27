import base64
from datetime import date, datetime, timedelta

import pytz

from odoo import fields
from odoo.tests import TransactionCase, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestTableroEmpresa(TransactionCase):
    """El tablero junta licitaciones, contratos, kit y fechas legales en una sola pantalla."""

    def test_company_panels(self):
        Lead = self.env["crm.lead"]
        hoy = fields.Date.context_today(Lead)
        antes = Lead.get_secop_dashboard()
        self.env.ref("lumak_secop.doc_camara").write({
            "archivo": base64.b64encode(b"%PDF"), "archivo_nombre": "camara.pdf", "fecha_expedicion": hoy})
        entidad = self.env["res.partner"].create({"name": "Municipio de Prueba", "is_company": True})
        lead = Lead.create({"name": "Mesa de ayuda", "type": "opportunity", "partner_id": entidad.id,
                            "team_id": self.env.ref("lumak_secop.team_secop").id, "expected_revenue": 10_000_000,
                            "stage_id": self.env.ref("lumak_secop.stage_preparando").id, "date_deadline": hoy})
        lead.stage_id = self.env.ref("lumak_secop.stage_adjudicado")
        self.env["calendar.event"].create({"name": "Anticipo SIMPLE de prueba", "secop_tipo": "obligacion", "allday": True,
                                           "start": datetime.combine(hoy + timedelta(days=3), datetime.min.time()),
                                           "stop": datetime.combine(hoy + timedelta(days=3), datetime.min.time())})
        data = Lead.get_secop_dashboard()
        self.assertEqual(data["kit_ok"], antes["kit_ok"] + 1)
        self.assertEqual(data["kit_total"], antes["kit_total"])
        self.assertNotIn("Certificado de existencia y representación legal", [p["nombre"] for p in data["kit_pendientes"]])
        contrato = next(c for c in data["contratos"] if c["id"] == lead.secop_proyecto_id.id)
        self.assertEqual((contrato["entidad"], contrato["hito"]), ("Municipio de Prueba", "Entrega y recibo a satisfacción del supervisor"))
        self.assertIn("Anticipo SIMPLE de prueba", [o["nombre"] for o in data["obligaciones"]])

    def test_legal_calendar_comes_loaded(self):
        obligaciones = self.env["calendar.event"].search([("secop_tipo", "=", "obligacion")])
        self.assertGreaterEqual(len(obligaciones), 15)
        self.assertIn(date(2026, 11, 24), obligaciones.mapped("start_date"), "primer anticipo del SIMPLE")
        bogota = pytz.timezone("America/Bogota")
        for evento in obligaciones:
            self.assertEqual(pytz.utc.localize(evento.start).astimezone(bogota).date(), evento.start_date, evento.name)


@tagged("post_install", "-at_install")
class TestPorCobrar(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_salesman_all_leads")

    def test_unpaid_and_overdue_invoices(self):
        antes = self.env["crm.lead"].get_secop_dashboard()
        factura = self.init_invoice("out_invoice", amounts=[1_000_000], post=True,
                                    invoice_date=fields.Date.today() - timedelta(days=40))
        factura.invoice_date_due = fields.Date.today() - timedelta(days=10)
        data = self.env["crm.lead"].get_secop_dashboard()
        self.assertEqual(data["facturas_pendientes"] - antes["facturas_pendientes"], 1)
        self.assertEqual(data["facturas_vencidas"] - antes["facturas_vencidas"], 1)
        self.assertTrue(data["por_cobrar"])


@tagged("post_install", "-at_install")
class TestInicio(TransactionCase):
    def test_lumak_app_opens_the_dashboard_and_is_home(self):
        tablero = self.env.ref("lumak_secop.action_secop_dashboard")
        app = self.env.ref("lumak_secop.menu_lumak_root")
        self.assertFalse(app.parent_id)
        self.assertEqual(app.action, tablero)
        primera = self.env["ir.ui.menu"].search([("parent_id", "=", False)], order="sequence, id", limit=1)
        self.assertEqual(primera, app, "al entrar, Odoo abre la primera app")

    def test_company_assets_live_in_the_lumak_app(self):
        app = self.env.ref("lumak_secop.menu_lumak_root")
        for xmlid in ("menu_secop_kit", "menu_secop_experiencia", "menu_lumak_fechas", "menu_lumak_empresa"):
            self.assertEqual(self.env.ref(f"lumak_secop.{xmlid}").parent_id, app)
        fechas = self.env.ref("lumak_secop.action_lumak_fechas")
        self.assertIn("obligacion", fechas.domain)
        empresa = self.env["res.company"].action_lumak_datos_empresa()
        self.assertEqual((empresa["res_model"], empresa["res_id"]), ("res.company", self.env.company.id))
