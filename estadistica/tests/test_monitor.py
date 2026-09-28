"""Monitor diario contra un SECOP y un Odoo falsos."""
from datetime import date

from secop_estadistica.monitor import MODALIDADES, sincronizar
from tests.test_normalizar import FILA_PROCESO
from tests.test_precio import base  # noqa: F401  (histórico de 20 procesos del nicho)

SOFTWARE = {**FILA_PROCESO, "id_del_proceso": "CO1.REQ.900", "id_del_portafolio": "CO1.BDOS.900", "adjudicado": "No",
            "id_adjudicacion": "No Adjudicado", "fecha_de_recepcion_de": "2026-10-02T00:00:00.000",
            "nombre_del_procedimiento": "Desarrollo de un sistema de información para PQRSD"}
EQUIPOS = {**SOFTWARE, "id_del_proceso": "CO1.REQ.901", "id_del_portafolio": "CO1.BDOS.901",
           "nombre_del_procedimiento": "Suministro de computadores portátiles", "codigo_principal_de_categoria": "V1.43211500",
           "tipo_de_contrato": "Compraventa"}


def secop(procesos):
    pedidos = []

    def fetch(dataset, params):
        pedidos.append(params["$where"])
        return [] if params["$offset"] else procesos
    fetch.pedidos = pedidos
    return fetch


class OdooFalso:
    def __init__(self, leads=(), no_encontrados=()):
        self.leads, self.no_encontrados = list(leads), set(no_encontrados)
        self.importados, self.llamadas = [], []

    def call(self, model, method, *args, **kwargs):
        self.llamadas.append((model, method, args, kwargs))
        if (model, method) == ("crm.lead", "search_read"):
            dominio = args[0]
            if dominio and dominio[0][0] == "secop_id":
                return [{"secop_id": i} for i in self.importados if i in dominio[0][2]]
            return self.leads
        if (model, method) == ("lumak.secop.import", "create"):
            self.pendiente = args[0]["referencia"]
            return 1
        if (model, method) == ("lumak.secop.import", "action_import"):
            if self.pendiente in self.no_encontrados:
                raise RuntimeError("No encontré ese proceso en los datos abiertos de SECOP II.")
            self.importados.append(self.pendiente)
            return {"res_id": 100 + len(self.importados)}
        if (model, method) == ("crm.team", "search"):
            return [7]
        return True

    def escritos(self):
        return [(args[0], args[1]) for model, method, args, _ in self.llamadas if (model, method) == ("crm.lead", "write")]


def test_it_brings_only_new_open_niche_processes_once(base):  # noqa: F811
    odoo, datos = OdooFalso(), secop([SOFTWARE, EQUIPOS])
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=datos)
    assert (r["abiertos"], r["creados"]) == (1, 1) and odoo.importados == ["CO1.REQ.900"]
    assert all(m in datos.pedidos[0] for m in MODALIDADES) and "fecha_de_recepcion_de >= '2026-09-28'" in datos.pedidos[0]
    sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([SOFTWARE, EQUIPOS]))
    assert odoo.importados == ["CO1.REQ.900"], "el segundo día no lo duplica"


def test_a_process_not_yet_in_open_data_does_not_stop_the_rest(base):  # noqa: F811
    otro = {**SOFTWARE, "id_del_proceso": "CO1.REQ.902", "id_del_portafolio": "CO1.BDOS.902"}
    odoo = OdooFalso(no_encontrados={"CO1.REQ.900"})
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([SOFTWARE, otro]))
    assert r["creados"] == 1 and [e[0] for e in r["errores"]] == ["CO1.REQ.900"]


def test_it_writes_the_price_analysis_on_open_leads(base):  # noqa: F811
    lead = {"id": 55, "secop_id": False, "expected_revenue": 50_000_000, "secop_costo_estimado": 25_000_000,
            "secop_estampillas": 4.1}
    sin_presupuesto = {"id": 56, "secop_id": False, "expected_revenue": 0, "secop_costo_estimado": 0, "secop_estampillas": 0}
    odoo = OdooFalso(leads=[lead, sin_presupuesto])
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([]))
    escritos = dict((ids[0], vals) for ids, vals in odoo.escritos())
    assert r["analizados"] == 1 and set(escritos) == {55}, "sin presupuesto no hay nada que analizar"
    assert escritos[55]["secop_precio_sugerido"] > 0 and 0 < escritos[55]["secop_prob_ganar"] < 1
    assert "Precio sugerido" in escritos[55]["secop_analisis_precio"]


def test_new_processes_without_category_are_found_by_their_words(base):  # noqa: F811
    # SECOP publica 3 de cada 4 procesos nuevos con categoría UNSPECIFIED y la llena después
    sin_categoria = {**SOFTWARE, "id_del_proceso": "CO1.REQ.903", "id_del_portafolio": "CO1.BDOS.903",
                     "codigo_principal_de_categoria": "UNSPECIFIED"}
    odoo, datos = OdooFalso(), secop([sin_categoria])
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=datos)
    assert "codigo_principal_de_categoria = 'UNSPECIFIED'" in datos.pedidos[0]
    assert "descripci_n_del_procedimiento" in datos.pedidos[0]
    assert r["creados"] == 1
