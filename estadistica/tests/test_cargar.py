"""La carga contra un datos.gov.co falso: pagina, agrupa las ofertas repetidas y actualiza sin duplicar."""
import duckdb

from secop_estadistica.base import Base
from secop_estadistica.cargar import CONTRATOS, OFERTAS, OFERTAS_HISTORICO, PROCESOS, actualizar
from secop_estadistica.socrata import paginas
from tests.test_normalizar import FILA_PROCESO


def test_pages_until_a_short_page():
    llamadas = []

    def fetch(dataset, params):
        llamadas.append(params["$offset"])
        return [{"n": i} for i in range(3 if params["$offset"] < 6 else 1)]

    filas = [f for pagina in paginas("x", {"$order": "n"}, tam=3, fetch=fetch) for f in pagina]
    assert llamadas == [0, 3, 6] and len(filas) == 7


class DatosFalsos:
    """Responde como Socrata según el dataset; guarda qué se pidió."""

    def __init__(self):
        self.pedidos = []

    def __call__(self, dataset, params):
        self.pedidos.append((dataset, params))
        if params["$offset"]:
            return []
        if dataset == PROCESOS:
            return [FILA_PROCESO]
        if dataset == OFERTAS:
            return [{"identificador_de_la_oferta": "CO1.RPL.1", "id_del_proceso_de_compra": "CO1.BDOS.7857804",
                     "nit_del_proveedor": "901178261", "nombre_proveedor": "HDC", "valor_de_la_oferta": "42292000",
                     "fecha_de_registro": "2025-03-20T00:00:00.000", "invitacion_directa": "No", "filas": "92"},
                    {"identificador_de_la_oferta": "CO1.RPL.2", "id_del_proceso_de_compra": "CO1.BDOS.7857804",
                     "nit_del_proveedor": "901323318", "nombre_proveedor": "MYH", "valor_de_la_oferta": "38062800",
                     "fecha_de_registro": "2025-03-20T00:00:00.000", "invitacion_directa": "No", "filas": "92"}]
        if dataset == CONTRATOS and "'2025-12-31'" in params["$where"]:  # firmado en 2025: solo sale en esa ventana
            return [{"id_contrato": "CO1.PCCNTR.1", "proceso_de_compra": "CO1.BDOS.7857804", "documento_proveedor": "901178261",
                     "proveedor_adjudicado": "HDC", "valor_del_contrato": "42292000.0", "estado_contrato": "En ejecución",
                     "fecha_de_firma": "2025-04-30T00:00:00.000", "es_pyme": "Si"}]
        return []


def test_update_loads_processes_grouped_offers_and_contracts():
    base = Base(duckdb.connect(":memory:"))
    datos = DatosFalsos()
    assert actualizar(base, "2025-01-01", fetch=datos) == (1, 2, 1)
    # las ofertas se piden agrupadas (sin las 92 copias) y a los dos datasets de ofertas
    pedidos_ofertas = [p for d, p in datos.pedidos if d in (OFERTAS, OFERTAS_HISTORICO)]
    assert {d for d, _ in datos.pedidos if d in (OFERTAS, OFERTAS_HISTORICO)} == {OFERTAS, OFERTAS_HISTORICO}
    assert all("count(*)" in p["$select"] and "$group" in p and "CO1.BDOS.7857804" in p["$where"] for p in pedidos_ofertas)
    fila = base.con.sql("select n_ofertas, ganador_nombre, puesto_ganador, gano_el_mas_barato from v_procesos").fetchone()
    assert fila == (2, "HDC", 2, False)
    assert base.con.sql("select procesos, ofertas, contratos from cargas").fetchone() == (1, 2, 1)
    actualizar(base, "2025-01-01", fetch=DatosFalsos())  # la carga semanal repite ventanas: no duplica
    assert base.con.sql("select count(*) from ofertas").fetchone() == (2,)


def test_a_batch_that_times_out_is_split_and_only_the_bad_process_is_skipped():
    from secop_estadistica.cargar import cargar_ofertas

    def fetch(dataset, params):
        if "BDOS.MALO" in params["$where"]:
            raise TimeoutError("SECOP no responde")
        if params["$offset"] or dataset != OFERTAS:
            return []
        ids = [p.strip(" '") for p in params["$where"].split("(")[1].rstrip(")").split(",")]
        return [{"identificador_de_la_oferta": f"RPL.{i}", "id_del_proceso_de_compra": i, "nit_del_proveedor": "900000001",
                 "nombre_proveedor": "X", "valor_de_la_oferta": "1", "fecha_de_registro": "2025-01-01T00:00:00.000",
                 "invitacion_directa": "No", "filas": "1"} for i in ids]

    base = Base(duckdb.connect(":memory:"))
    portafolios = ["BDOS.1", "BDOS.2", "BDOS.MALO", "BDOS.3", "BDOS.4"]
    total, fallidos = cargar_ofertas(base, portafolios, fetch=fetch, lote=5)
    assert (total, fallidos) == (4, ["BDOS.MALO"])


def test_resume_only_asks_for_processes_with_responses_but_no_bids():
    from secop_estadistica.cargar import sin_ofertas
    from secop_estadistica.normalizar import proceso

    base = Base(duckdb.connect(":memory:"))
    con_ofertas, _ = proceso(FILA_PROCESO)
    sin_nada, _ = proceso({**FILA_PROCESO, "id_del_proceso": "REQ.2", "id_del_portafolio": "BDOS.2"})
    sin_respuestas, _ = proceso({**FILA_PROCESO, "id_del_proceso": "REQ.3", "id_del_portafolio": "BDOS.3",
                                 "respuestas_al_procedimiento": "0"})
    base.guardar_procesos([con_ofertas, sin_nada, sin_respuestas])
    base.guardar_ofertas([{"id_oferta": "RPL.1", "id_portafolio": FILA_PROCESO["id_del_portafolio"], "nit": "1",
                           "nombre": "X", "valor": 1, "fecha": None, "invitacion_directa": False, "filas": 1}])
    assert sin_ofertas(base) == ["BDOS.2"]


def test_contracts_are_downloaded_year_by_year():
    from datetime import date

    from secop_estadistica.cargar import cargar_contratos

    pedidos = []

    def fetch(dataset, params):
        pedidos.append(params["$where"])
        return []

    cargar_contratos(Base(duckdb.connect(":memory:")), "2024-06-01", fetch=fetch, hoy=date(2026, 3, 1))
    assert len(pedidos) == 3
    assert "'2024-06-01'" in pedidos[0] and "'2024-12-31'" in pedidos[0] and "'2026-12-31'" in pedidos[2]


def test_reclassify_updates_the_niche_of_stored_processes():
    from secop_estadistica.cargar import reclasificar
    from secop_estadistica.normalizar import proceso

    base = Base(duckdb.connect(":memory:"))
    certificados, _ = proceso({**FILA_PROCESO, "nombre_del_procedimiento": "Certificados de firma digital y soporte de la plataforma",
                               "descripci_n_del_procedimiento": ""})
    base.guardar_procesos([{**certificados, "nicho": True}])  # como quedó con el clasificador anterior
    assert reclasificar(base) == 1
    assert base.con.sql("select nicho from procesos").fetchone() == (False,)
