from datetime import date

from odoo.tests import TransactionCase, tagged

from odoo.addons.lumak_secop.models.contratos import TARIFA_SIMPLE, precio_minimo


class TestPrecio(TransactionCase):
    def test_precio_minimo_covers_cost_simple_and_stamps(self):
        # base sin IVA ≥ costo ÷ (1 − SIMPLE − estampillas)
        self.assertAlmostEqual(precio_minimo(10_000_000, 4.1), 10_000_000 / (1 - TARIFA_SIMPLE - 0.041))
        self.assertEqual(precio_minimo(0, 4.1), 0)


@tagged("post_install", "-at_install")
class TestContratos(TransactionCase):
    """Del proceso a la cotización (oferta económica) y de lo adjudicado al proyecto del contrato."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = lambda name: cls.env.ref(f"lumak_secop.{name}")
        cls.team, cls.detectado = ref("team_secop"), ref("stage_detectado")
        cls.preparando, cls.adjudicado = ref("stage_preparando"), ref("stage_adjudicado")
        cls.producto = ref("product_contrato_secop")
        cls.entidad = cls.env["res.partner"].create({"name": "Municipio de Prueba", "is_company": True})

    def _lead(self, **vals):
        return self.env["crm.lead"].create({
            "name": "Sistema de información de PQRSD", "type": "opportunity", "team_id": self.team.id,
            "stage_id": self.detectado.id, "partner_id": self.entidad.id, "expected_revenue": 11_900_000,
            "secop_numero": "MC-001-2026", "date_deadline": date(2026, 10, 2), **vals})

    def test_preparing_the_offer_creates_its_quotation_once(self):
        lead = self._lead()
        lead.stage_id = self.preparando
        order = lead.order_ids
        self.assertEqual(len(order), 1)
        self.assertEqual((order.state, order.partner_id, order.client_order_ref), ("draft", self.entidad, "MC-001-2026"))
        self.assertEqual(order.order_line.product_id, self.producto)
        self.assertEqual(order.order_line.name, lead.name)
        # el presupuesto oficial ya trae los impuestos: la cotización arranca en ese tope
        self.assertAlmostEqual(order.amount_total, 11_900_000, delta=1)
        self.assertEqual(lead.secop_valor_ofertado, order.amount_total)
        lead.stage_id = self.detectado
        lead.stage_id = self.preparando
        self.assertEqual(len(lead.order_ids), 1)

    def test_without_entity_it_asks_for_it(self):
        lead = self._lead(partner_id=False)
        lead.stage_id = self.preparando
        self.assertFalse(lead.order_ids)
        self.assertIn("entidad", lead.message_ids[0].body)

    def test_offer_value_follows_the_quotation(self):
        lead = self._lead(stage_id=self.preparando.id)
        lead.order_ids.order_line.price_unit = 9_000_000
        self.assertAlmostEqual(lead.secop_valor_ofertado, lead.order_ids.amount_total)
        lead.secop_costo_estimado = 8_500_000
        self.assertTrue(lead.secop_precio_bajo, "9 M no cubre 8,5 M de costo más SIMPLE")
        lead.secop_costo_estimado = 7_000_000
        self.assertFalse(lead.secop_precio_bajo)

    def test_award_confirms_quotation_and_opens_contract_project(self):
        lead = self._lead(stage_id=self.preparando.id)
        lead.stage_id = self.adjudicado
        order = lead.order_ids
        self.assertEqual(order.state, "sale")
        proyecto = lead.secop_proyecto_id
        self.assertTrue(proyecto)
        self.assertEqual(proyecto.partner_id, self.entidad)
        self.assertFalse(proyecto.is_template)
        plantilla = self.env.ref("lumak_secop.project_contrato_secop")
        self.assertEqual(len(proyecto.task_ids), len(plantilla.task_ids))
        self.assertEqual(proyecto.milestone_ids.sale_line_id, order.order_line, "el hito de pago factura la línea")
        self.assertEqual(proyecto.secop_lead_id, lead)
        self.assertEqual(proyecto.name, "Sistema de información de PQRSD (MC-001-2026)", "el objeto, no el nombre de la plantilla")

    def test_award_without_quotation_says_so(self):
        lead = self._lead()
        lead.stage_id = self.adjudicado
        self.assertFalse(lead.order_ids)
        self.assertIn("cotización", lead.message_ids[0].body)

    def test_price_analysis_from_the_history_shows_in_the_secop_tab(self):
        # la base estadística (estadistica/) calcula el análisis y lo escribe por la API; aquí solo se guarda y se ve
        lead = self._lead()
        lead.write({"secop_precio_sugerido": 41_600_000, "secop_prob_ganar": 0.36,
                    "secop_analisis_precio": "Basado en 188 procesos comparables del nicho."})
        self.assertEqual(lead.secop_prob_ganar, 0.36)
        arch = self.env["crm.lead"].get_view(view_type="form")["arch"]
        for campo in ("secop_precio_sugerido", "secop_prob_ganar", "secop_analisis_precio", "secop_analisis_fecha"):
            self.assertIn(campo, arch)
