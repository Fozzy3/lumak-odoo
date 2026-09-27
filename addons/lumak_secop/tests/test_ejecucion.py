from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEjecucion(TransactionCase):
    """Del contrato ganado a los documentos de cada pago y a la experiencia que sirve para la siguiente oferta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.write({"lumak_representante": "Carlos Stiven Mora Hoyos", "lumak_representante_cc": "1.000.000.000",
                               "lumak_fecha_constitucion": date(2026, 9, 26), "street": "Calle 1", "city": "Bogotá",
                               "email": "contacto@lumak.co", "phone": "3000000000"})
        cls.entidad = cls.env["res.partner"].create({"name": "Municipio de Prueba", "is_company": True})
        lead = cls.env["crm.lead"].create({
            "name": "Sistema de información de PQRSD", "type": "opportunity", "partner_id": cls.entidad.id,
            "team_id": cls.env.ref("lumak_secop.team_secop").id, "expected_revenue": 11_900_000,
            "stage_id": cls.env.ref("lumak_secop.stage_preparando").id, "secop_numero": "MC-001-2026",
            "secop_unspsc": "81111500", "date_deadline": date(2026, 10, 2)})
        lead.stage_id = cls.env.ref("lumak_secop.stage_adjudicado")
        cls.lead, cls.proyecto = lead, lead.secop_proyecto_id
        cls.proyecto.write({"contrato_numero": "CT-045-2026", "supervisor": "Ana Pérez, Secretaría TIC",
                            "date_start": date(2026, 10, 5), "date": date(2026, 12, 31)})

    def _html(self, reporte, record):
        return " ".join(self.env["ir.actions.report"]._render_qweb_html(reporte, record.ids)[0].decode().split())

    def test_contract_data_comes_from_the_award(self):
        self.assertEqual(self.proyecto.contrato_objeto, "Sistema de información de PQRSD")
        self.assertAlmostEqual(self.proyecto.contrato_valor, 11_900_000, delta=1)

    def test_activity_report_for_each_payment(self):
        html = self._html("lumak_secop.report_informe_actividades", self.proyecto)
        for texto in ("CT-045-2026", "Municipio de Prueba", "Sistema de información de PQRSD", "Ana Pérez",
                      "Entrega y recibo a satisfacción del supervisor"):
            self.assertIn(texto, html)

    def test_payment_contributions_certificate(self):
        html = self._html("lumak_secop.report_aportes_pago", self.proyecto)
        self.assertIn("CT-045-2026", html)
        self.assertIn("no ha tenido trabajadores", html)

    def test_experience_request_and_register(self):
        html = self._html("lumak_secop.report_derecho_peticion", self.proyecto)
        self.assertIn("Ley 1755 de 2015", html)
        self.assertIn("CT-045-2026", html)
        self.proyecto.action_registrar_experiencia()
        experiencia = self.env["lumak.experiencia"].search([("proyecto_id", "=", self.proyecto.id)])
        self.assertEqual(len(experiencia), 1)
        self.assertEqual((experiencia.contratante_id, experiencia.contrato_numero, experiencia.unspsc),
                         (self.entidad, "CT-045-2026", "81111500"))
        self.assertAlmostEqual(experiencia.valor, 11_900_000, delta=1)
        self.proyecto.action_registrar_experiencia()
        self.assertEqual(self.env["lumak.experiencia"].search_count([("proyecto_id", "=", self.proyecto.id)]), 1)

    def test_offer_package_lists_the_experience(self):
        self.env["lumak.experiencia"].create({
            "contratante_id": self.env["res.partner"].create({"name": "Universidad Distrital", "is_company": True}).id,
            "publico": True, "de_socio": True,
            "objeto": "Experto profesional en inteligencia artificial y agentes", "valor": 15_000_000,
            "fecha_inicio": date(2026, 6, 1), "fecha_fin": date(2026, 8, 31)})
        otro = self.env["crm.lead"].create({
            "name": "Chatbot", "type": "opportunity", "partner_id": self.entidad.id, "expected_revenue": 5_000_000,
            "team_id": self.env.ref("lumak_secop.team_secop").id, "secop_numero": "MC-002-2026",
            "stage_id": self.env.ref("lumak_secop.stage_preparando").id})
        otro.action_secop_preparar_oferta()
        experiencia = otro.message_ids[0].attachment_ids.filtered(lambda a: "Formato de experiencia" in a.name)
        self.assertTrue(experiencia)
        self.assertIn("Universidad Distrital", experiencia.raw.decode())

    def test_certification_request_for_registered_experience(self):
        acc = self.env["res.partner"].create({"name": "Agencia Catastral de Cundinamarca", "is_company": True})
        socio = self.env["lumak.experiencia"].create({
            "contratante_id": acc.id, "de_socio": True, "contrato_numero": "CD-ACC-CPS-057-2023",
            "objeto": "Desarrollo frontend", "valor": 9_285_000, "correccion": "el número de cédula del contratista"})
        html = self._html("lumak_secop.report_solicitud_certificacion", socio)
        self.assertIn("Ley 1755 de 2015", html)
        self.assertIn("CD-ACC-CPS-057-2023", html)
        self.assertIn("el número de cédula del contratista", html)
        self.assertIn("en calidad de contratista", html, "la experiencia del socio la pide él, no la empresa")
        self.assertNotIn("representante legal de", html)
        empresa = self.env["lumak.experiencia"].create({"contratante_id": acc.id, "objeto": "Soporte", "contrato_numero": "CT-9"})
        self.assertIn("representante legal de", self._html("lumak_secop.report_solicitud_certificacion", empresa))
