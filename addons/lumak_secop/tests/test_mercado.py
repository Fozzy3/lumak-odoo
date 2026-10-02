from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase

from odoo.addons.lumak_secop.models.licitaciones import LumakSecopImport

from .test_secop import ROW


def fila(**cambios):
    """Un proceso como lo manda el monitor diario desde la base estadística."""
    return {
        "secop_id": ROW["id_del_proceso"], "referencia": "MIN-067", "nombre": "Sistema de PQRSD", "entidad": "Municipio de Fortul",
        "departamento": "Arauca", "ciudad": "Fortul", "modalidad": "Mínima cuantía", "estado": "Publicado",
        "fecha_publicacion": "2026-09-25", "fecha_cierre": "2026-10-01", "presupuesto": 49_000_000, "url": "https://secop",
        "nicho": True, "n_ofertas": 2, "ganador": False, "precio_ganador": False, "descuento_ganador": False,
        "ofertas": [
            {"proveedor": "Rival 1", "nit": "900000001", "valor": 40_000_000, "puesto": 1, "descuento": 18.4, "gano": 0},
            {"proveedor": "Rival 2", "nit": "900000002", "valor": 45_000_000, "puesto": 2, "descuento": 8.2, "gano": 0}],
        **cambios}


class TestMercado(TransactionCase):
    """Mercado SECOP: los procesos publicados y sus ofertas, para buscarlos a mano y ver estadísticas."""

    def setUp(self):
        super().setUp()
        self.Proceso = self.env["lumak.secop.proceso"]

    def _proceso(self):
        return self.Proceso.search([("secop_id", "=", ROW["id_del_proceso"])])

    def test_the_daily_sync_updates_a_process_instead_of_duplicating_it(self):
        self.Proceso.sincronizar([fila()])
        ganada = {"proveedor": "Rival 1", "nit": "900000001", "valor": 40_000_000, "puesto": 1, "descuento": 18.4, "gano": 1}
        self.Proceso.sincronizar([fila(estado="Adjudicado", ganador="Rival 1", descuento_ganador=18.4, ofertas=[ganada])])
        p = self._proceso()
        self.assertEqual(len(p), 1)
        self.assertEqual((p.estado, p.ganador), ("Adjudicado", "Rival 1"))
        self.assertEqual(p.oferta_ids.mapped("gano"), [1], "las ofertas se reemplazan, no se acumulan")

    def test_bringing_a_process_to_the_pipeline_creates_the_lead_once(self):
        self.Proceso.sincronizar([fila()])
        p = self._proceso()
        with patch.object(LumakSecopImport, "_fetch", return_value=[ROW]):
            accion = p.action_traer_al_flujo()
        self.assertEqual(p.lead_id.secop_id, ROW["id_del_proceso"])
        self.assertEqual(accion["res_id"], p.lead_id.id)
        self.assertEqual(accion["views"], [(self.env.ref("lumak_secop.crm_lead_form_secop").id, "form")], "abre la ficha de SECOP")
        with patch.object(LumakSecopImport, "_fetch", return_value=[]):  # si volviera a consultar SECOP, fallaría
            self.assertEqual(p.action_traer_al_flujo()["res_id"], p.lead_id.id)
        self.Proceso.sincronizar([fila()])
        self.assertTrue(p.lead_id, "la sincronización siguiente conserva el enlace")

    def test_a_process_already_in_the_pipeline_is_linked_by_its_secop_id(self):
        lead = self.env["crm.lead"].create({"name": "Ya en el flujo", "type": "opportunity", "secop_id": ROW["id_del_proceso"]})
        self.Proceso.sincronizar([fila()])
        self.assertEqual(self._proceso().lead_id, lead)

    def test_dashboard_shows_this_week_publications(self):
        hoy = fields.Date.context_today(self.Proceso)
        antes = self.env["crm.lead"].get_secop_dashboard()["mercado"]
        self.Proceso.sincronizar([
            fila(fecha_publicacion=str(hoy), fecha_cierre=str(hoy + timedelta(days=3))),
            fila(secop_id="CO1.REQ.2", nicho=False, fecha_publicacion=str(hoy - timedelta(days=1))),
            fila(secop_id="CO1.REQ.3", fecha_publicacion=str(hoy - timedelta(days=40)), fecha_cierre=str(hoy - timedelta(days=30)))])
        m = self.env["crm.lead"].get_secop_dashboard()["mercado"]
        self.assertEqual(m["semana"] - antes["semana"], 2)
        self.assertEqual(m["semana_nicho"] - antes["semana_nicho"], 1)
        self.assertEqual(m["abiertos_nicho"] - antes["abiertos_nicho"], 1)

    def test_the_strategy_page_starts_with_the_competition_analysis_and_is_editable(self):
        empresa = self.env.company
        self.assertIn("Por qué ganan", empresa.lumak_estrategia, "arranca con el análisis de la competencia")
        accion = self.env["res.company"].action_lumak_estrategia()
        self.assertEqual((accion["res_model"], accion["res_id"]), ("res.company", empresa.id))
        empresa.lumak_estrategia = "<p>Nueva regla</p>"
        self.assertIn("Nueva regla", empresa.lumak_estrategia)
