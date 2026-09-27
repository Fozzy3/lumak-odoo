import base64
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.lumak_secop.models.documentos import periodo_aportes, valor_en_letras

PDF = base64.b64encode(b"%PDF-1.4 prueba")


class TestAyudas(TransactionCase):
    def test_valor_en_letras(self):
        self.assertEqual(valor_en_letras(11_900_000), "ONCE MILLONES NOVECIENTOS MIL PESOS M/CTE")
        self.assertEqual(valor_en_letras(1_000_000.4), "UN MILLÓN PESOS M/CTE")

    def test_aportes_cover_six_months_or_since_constitution(self):
        constitucion = date(2026, 9, 26)
        self.assertEqual(periodo_aportes(constitucion, date(2026, 10, 2)), (constitucion, date(2026, 10, 2)))
        self.assertEqual(periodo_aportes(constitucion, date(2027, 6, 15)), (date(2026, 12, 15), date(2027, 6, 15)))


@tagged("post_install", "-at_install")
class TestKit(TransactionCase):
    def test_document_status_follows_issue_date_and_validity(self):
        hoy = fields.Date.context_today(self.env.user)
        Doc = self.env["lumak.documento"]
        doc = lambda dias, vigencia=30, **v: Doc.create({"name": "Cámara", "vigencia_dias": vigencia, "archivo": PDF,
                                                         "archivo_nombre": "c.pdf", "fecha_expedicion": hoy - timedelta(days=dias), **v})
        self.assertEqual(Doc.create({"name": "RUT"}).estado, "falta")
        vigente = doc(10)
        self.assertEqual((vigente.estado, vigente.vence), ("vigente", hoy + timedelta(days=20)))
        self.assertTrue(vigente.vigente_al(hoy + timedelta(days=20)))
        self.assertFalse(vigente.vigente_al(hoy + timedelta(days=21)))
        self.assertEqual(doc(25).estado, "por_vencer")
        self.assertEqual(doc(31).estado, "vencido")
        permanente = doc(400, vigencia=0)
        self.assertEqual((permanente.estado, permanente.vence), ("vigente", False))

    def test_kit_comes_loaded_with_where_to_get_each_document(self):
        camara = self.env.ref("lumak_secop.doc_camara")
        self.assertEqual(camara.vigencia_dias, 30)
        self.assertTrue(camara.url and camara.emisor)
        self.assertGreaterEqual(self.env["lumak.documento"].search_count([("en_oferta", "=", True)]), 10)


@tagged("post_install", "-at_install")
class TestPaqueteOferta(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            "lumak_representante": "Carlos Stiven Mora Hoyos", "lumak_representante_cc": "1.000.000.000",
            "lumak_representante_cc_expedida": "Bogotá", "lumak_fecha_constitucion": date(2026, 9, 26),
            "street": "Calle 1 # 2-3", "city": "Bogotá", "email": "contacto@lumak.co", "phone": "3000000000",
        })
        entidad = cls.env["res.partner"].create({"name": "Municipio de Prueba", "is_company": True, "city": "Chía"})
        cls.lead = cls.env["crm.lead"].create({
            "name": "Sistema de información de PQRSD", "type": "opportunity",
            "team_id": cls.env.ref("lumak_secop.team_secop").id, "stage_id": cls.env.ref("lumak_secop.stage_preparando").id,
            "partner_id": entidad.id, "expected_revenue": 11_900_000, "secop_numero": "MC-001-2026",
            "secop_modalidad": "minima", "secop_plazo": "3 meses", "date_deadline": date.today() + timedelta(days=3)})
        cls.env.ref("lumak_secop.doc_camara").write({"archivo": PDF, "archivo_nombre": "camara.pdf",
                                                     "fecha_expedicion": date.today()})

    def test_it_says_what_is_missing_before_generating(self):
        self.company.lumak_representante_cc = False
        with self.assertRaisesRegex(UserError, "cédula"):
            self.lead.action_secop_preparar_oferta()

    def test_one_click_builds_the_offer_package(self):
        self.lead.action_secop_preparar_oferta()
        mensaje = self.lead.message_ids[0]
        nombres = mensaje.attachment_ids.mapped("name")
        for nombre in ("01 Carta de presentación - MC-001-2026.pdf", "02 Oferta económica - MC-001-2026.pdf",
                       "03 Certificación de aportes (art. 50) - MC-001-2026.pdf",
                       "04 Compromiso anticorrupción - MC-001-2026.pdf",
                       "05 Declaración de inhabilidades y conflicto de intereses - MC-001-2026.pdf"):
            self.assertIn(nombre, nombres)
        self.assertTrue(any("camara" in n.lower() or "cámara" in n.lower() for n in nombres), "va la Cámara vigente")
        self.assertIn("RUT", mensaje.body, "avisa lo que falta del kit")
        carta = mensaje.attachment_ids.filtered(lambda a: a.name.startswith("01")).raw.decode()
        for texto in ("MC-001-2026", "Municipio de Prueba", "Sistema de información de PQRSD", "Carlos Stiven Mora Hoyos",
                      "1.000.000.000", "ONCE MILLONES NOVECIENTOS MIL PESOS M/CTE", "3 meses"):
            self.assertIn(texto, carta)

    def test_warns_when_offer_is_over_budget(self):
        self.lead.order_ids.order_line.price_unit = 20_000_000
        self.lead.action_secop_preparar_oferta()
        self.assertIn("supera el presupuesto", self.lead.message_ids[0].body)
