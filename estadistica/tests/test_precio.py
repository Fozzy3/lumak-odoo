"""Cuánto ofertar: probabilidad de ganar según el histórico y utilidad esperada con el costo propio."""
from datetime import date

import duckdb
import pytest

from secop_estadistica.base import Base
from secop_estadistica.precio import analizar, probabilidad, texto

# Descuento del ganador frente al presupuesto en 20 procesos comparables (4 con un solo oferente, sin descuento)
GANADORES = [0, 0, 0, 0, .10, .15, .20, .25, .30, .30, .35, .40, .40, .45, .50, .55, .60, .65, .70, .80]


@pytest.fixture
def base():
    b = Base(duckdb.connect(":memory:"))
    proc = dict(orden_entidad="Territorial", departamento="Cundinamarca", ciudad="Chía", modalidad="Mínima cuantía",
                tipo_contrato="Prestación de servicios", unspsc="V1.81111500", segmento="81", descripcion="", fase="",
                estado="Seleccionado", fecha_cierre=None, fecha_adjudicacion=None, n_lotes=0, duracion=None, adjudicado=True,
                url=None, nicho=True, etiquetas=["app_dev"], tipo_entidad="alcaldia", crudo="{}", precio_base=10_000_000)
    procesos, adjudicaciones, ofertas = [], [], []
    for i, d in enumerate(GANADORES):
        entidad = ("900100100", "Alcaldía de Chía") if i < 5 else (f"8000000{i:02d}", f"Entidad {i}")
        un_solo = d == 0
        procesos.append(dict(proc, id_proceso=f"REQ.{i}", id_portafolio=f"BDOS.{i}", referencia=str(i), entidad=entidad[1],
                             nit_entidad=entidad[0], nombre=f"Sistema {i}", fecha_publicacion=date(2025, 1, 1 + i),
                             respuestas=1 if un_solo else 2))
        ganador = "900000001" if i % 2 else "900000002"
        adjudicaciones.append(dict(id_adjudicacion=f"AWD.{i}", id_proceso=f"REQ.{i}", nit=ganador, nombre=f"Rival {ganador[-1]}",
                                   valor=10_000_000 * (1 - d)))
        ofertas.append(dict(id_oferta=f"W.{i}", id_portafolio=f"BDOS.{i}", nit=ganador, nombre=f"Rival {ganador[-1]}",
                            valor=10_000_000 * (1 - d), fecha=date(2025, 1, 1), invitacion_directa=False, filas=1))
        if not un_solo:
            ofertas.append(dict(id_oferta=f"L.{i}", id_portafolio=f"BDOS.{i}", nit="900000003", nombre="Rival 3",
                                valor=10_000_000 * (1 - d) + 500_000, fecha=date(2025, 1, 1), invitacion_directa=False, filas=1))
    b.guardar_procesos(procesos)
    b.guardar_adjudicaciones(adjudicaciones)
    b.guardar_ofertas(ofertas)
    return b


def test_probability_of_beating_the_historical_winner():
    assert probabilidad(GANADORES, 0) == 0.2          # sin descuento solo se gana donde nadie más se presentó
    assert probabilidad(GANADORES, 0.30) == 0.5
    assert probabilidad(GANADORES, 0.90) == 1.0


def test_with_cost_it_suggests_the_price_with_best_expected_profit(base):
    a = analizar(base.con, presupuesto=50_000_000, costo=25_000_000, estampillas=4.1, hoy=date(2026, 9, 28))
    assert a["comparables"] == 20
    s = a["sugerido"]
    assert s and s["utilidad"] > 0
    # ninguna de las opciones por probabilidad deja más utilidad esperada que la sugerida
    assert all(s["utilidad_esperada"] >= o["utilidad_esperada"] for o in a["opciones"] if o["utilidad_esperada"] is not None)
    assert [o["probabilidad"] >= meta for o, meta in zip(a["opciones"], (0.5, 0.7, 0.85))] == [True, True, True]
    assert "Precio sugerido" in texto(a)


def test_without_cost_it_only_gives_win_chances_and_asks_for_the_cost(base):
    a = analizar(base.con, presupuesto=50_000_000, hoy=date(2026, 9, 28))
    assert a["sugerido"] is None
    assert a["opciones"][0]["precio"] == pytest.approx(50_000_000 * (1 - 0.30), rel=0.01)  # 50 % de probabilidad
    assert "costo estimado" in texto(a)


def test_likely_competitors_come_from_the_entity_history(base):
    a = analizar(base.con, presupuesto=50_000_000, nit_entidad="900100100", hoy=date(2026, 9, 28))
    nombres = [c["nombre"] for c in a["competidores"]]
    assert "Rival 3" in nombres and len(nombres) >= 2
    assert a["entidad"]["procesos"] == 5


def test_no_history_says_so(base):
    a = analizar(base.con, presupuesto=50_000_000, hoy=date(2035, 1, 1))  # nada en los últimos 36 meses
    assert a["comparables"] == 0 and "histórico" in texto(a)


def test_entity_summary_ignores_winners_above_budget_and_competitors_are_from_the_niche(base):
    proc = base.con.sql("select * exclude (actualizado) from procesos where id_proceso = 'REQ.1'").fetchone()
    cols = [c[0] for c in base.con.sql("select * exclude (actualizado) from procesos limit 0").description]
    fuera = dict(zip(cols, proc), id_proceso="REQ.X", id_portafolio="BDOS.X", referencia="X", nicho=False, crudo="{}")
    arriba = dict(zip(cols, proc), id_proceso="REQ.Y", id_portafolio="BDOS.Y", referencia="Y", crudo="{}")
    base.guardar_procesos([fuera, arriba])
    base.guardar_adjudicaciones([dict(id_adjudicacion="AWD.Y", id_proceso="REQ.Y", nit="900000009", nombre="Caro", valor=12_000_000)])
    base.guardar_ofertas([
        dict(id_oferta="X.1", id_portafolio="BDOS.X", nit="900000008", nombre="Telecom SA", valor=9_000_000,
             fecha=date(2025, 1, 1), invitacion_directa=False, filas=1),
        dict(id_oferta="Y.1", id_portafolio="BDOS.Y", nit="900000009", nombre="Caro", valor=12_000_000,
             fecha=date(2025, 1, 1), invitacion_directa=False, filas=1)])
    a = analizar(base.con, presupuesto=50_000_000, nit_entidad="900100100", hoy=date(2026, 9, 28))
    assert a["entidad"]["descuento"] >= 0
    assert "Telecom SA" not in [c["nombre"] for c in a["competidores"]]


def test_negative_money_reads_naturally():
    from secop_estadistica.reporte import millones
    assert millones(-4_200_000) == "-$4,2 M"


def test_entity_line_skips_the_discount_when_there_is_no_reliable_data():
    a = {"comparables": 30, "sugerido": None, "costo": None, "opciones": [], "competidores": [],
         "entidad": {"procesos": 2, "ofertas": 1.0, "descuento": None}}
    assert "—" not in texto(a) and "Esta entidad: 2 procesos del nicho" in texto(a)
