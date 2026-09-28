"""Las vistas estadísticas sobre casos armados como los reales: el más barato no siempre gana y hay valores dudosos."""
from datetime import date

import duckdb
import pytest

from secop_estadistica.base import Base


@pytest.fixture
def base():
    b = Base(duckdb.connect(":memory:"))
    proc = dict(orden_entidad="Territorial", departamento="Cundinamarca", ciudad="Chía", modalidad="Mínima cuantía",
                tipo_contrato="Prestación de servicios", unspsc="V1.81111500", segmento="81", descripcion="", fase="",
                estado="Seleccionado", fecha_cierre=None, fecha_adjudicacion=None, n_lotes=0, duracion=None,
                adjudicado=True, url=None, nicho=True, etiquetas=["soporte_sw"], tipo_entidad="alcaldia", crudo="{}")
    b.guardar_procesos([
        # A: 3 ofertas, el más barato fue descalificado y ganó el segundo
        dict(proc, id_proceso="REQ.A", id_portafolio="BDOS.A", referencia="A", entidad="Alcaldía A", nit_entidad="1",
             nombre="Soporte A", fecha_publicacion=date(2025, 3, 1), precio_base=50_000_000, respuestas=3),
        # B: 2 ofertas, ganó el más barato
        dict(proc, id_proceso="REQ.B", id_portafolio="BDOS.B", referencia="B", entidad="Alcaldía A", nit_entidad="1",
             nombre="Soporte B", fecha_publicacion=date(2025, 5, 1), precio_base=20_000_000, respuestas=2),
        # D: el ganador aparece con un valor imposible (0,5 % del presupuesto): error de digitación en SECOP
        dict(proc, id_proceso="REQ.D", id_portafolio="BDOS.D", referencia="D", entidad="Alcaldía C", nit_entidad="3",
             nombre="Soporte D", fecha_publicacion=date(2025, 6, 2), precio_base=20_000_000, respuestas=2),
        # C: casi todas las ofertas iguales al presupuesto (dato dudoso de SECOP)
        dict(proc, id_proceso="REQ.C", id_portafolio="BDOS.C", referencia="C", entidad="Alcaldía C", nit_entidad="3",
             nombre="Soporte C", fecha_publicacion=date(2025, 6, 1), precio_base=10_000_000, respuestas=3),
    ])
    b.guardar_adjudicaciones([
        dict(id_adjudicacion="AWD.A", id_proceso="REQ.A", nit="900000002", nombre="Rival Dos SAS", valor=45_000_000),
        dict(id_adjudicacion="AWD.B", id_proceso="REQ.B", nit="900000002", nombre="Rival Dos SAS", valor=15_000_000),
        dict(id_adjudicacion="AWD.C", id_proceso="REQ.C", nit="900000003", nombre="Rival Tres SAS", valor=10_000_000),
        dict(id_adjudicacion="AWD.D", id_proceso="REQ.D", nit="900000003", nombre="Rival Tres SAS", valor=18_000_000),
    ])
    of = lambda i, port, nit, nombre, valor: dict(id_oferta=i, id_portafolio=port, nit=nit, nombre=nombre, valor=valor,
                                                  fecha=date(2025, 3, 5), invitacion_directa=False, filas=1)
    b.guardar_ofertas([
        of("A1", "BDOS.A", "900000001", "Rival Uno SAS", 33_915_000),
        of("A2", "BDOS.A", "9000000026", "Rival Dos SAS", 45_000_000),  # mismo NIT con dígito de verificación
        of("A3", "BDOS.A", "900000003", "Rival Tres SAS", 49_000_000),
        of("B1", "BDOS.B", "900000002", "Rival Dos SAS", 15_000_000),
        of("B2", "BDOS.B", "900000001", "Rival Uno SAS", 18_000_000),
        of("C1", "BDOS.C", "900000003", "Rival Tres SAS", 10_000_000),
        of("C2", "BDOS.C", "900000001", "Rival Uno SAS", 10_000_000),
        of("C3", "BDOS.C", "900000002", "Rival Dos SAS", 9_000_000),
        of("D1", "BDOS.D", "900000003", "Rival Tres SAS", 100_000),
        of("D2", "BDOS.D", "900000001", "Rival Uno SAS", 19_000_000),
    ])
    return b


def test_bid_rank_discount_and_winner(base):
    filas = base.con.sql("select id_oferta, puesto, round(descuento, 4), es_ganador from v_ofertas where id_portafolio='BDOS.A' order by puesto").fetchall()
    assert filas == [("A1", 1, 0.3217, False), ("A2", 2, 0.1, True), ("A3", 3, 0.02, False)]


def test_process_summary(base):
    a = base.con.sql("select n_ofertas, puesto_ganador, gano_el_mas_barato, precio_ganador, round(descuento_ganador, 2), "
                     "segundo_nombre, calidad from v_procesos where id_proceso='REQ.A'").fetchone()
    assert a == (3, 2, False, 45_000_000, 0.1, "Rival Dos SAS", "buena")
    b = base.con.sql("select gano_el_mas_barato, calidad from v_procesos where id_proceso='REQ.B'").fetchone()
    assert b == (True, "buena")
    c = base.con.sql("select calidad from v_procesos where id_proceso='REQ.C'").fetchone()
    assert c == ("valores_dudosos",)
    d = base.con.sql("select calidad from v_procesos where id_proceso='REQ.D'").fetchone()
    assert d == ("valores_dudosos",)
    assert base.con.sql("select valor_atipico from v_ofertas where id_oferta='D1'").fetchone() == (True,)


def test_competitors_and_who_bids_where(base):
    dos = base.con.sql("select ofertas, ganadas, round(tasa_exito, 2) from v_competidores where nit='900000002'").fetchone()
    assert dos == (3, 2, 0.67)
    # el valor imposible no entra al descuento típico
    # sus dos victorias traen el presupuesto o un valor imposible: no hay descuento típico confiable
    assert base.con.sql("select descuento_mediano_ganando from v_competidores where nit='900000003'").fetchone() == (None,)
    rivales_a = base.con.sql("select nit, ofertas from v_rivales_por_entidad where nit_entidad='1' order by nit").fetchall()
    assert rivales_a == [("900000001", 2), ("900000002", 2), ("900000003", 1)]


def test_saving_twice_updates_instead_of_duplicating(base):
    base.guardar_ofertas([dict(id_oferta="B1", id_portafolio="BDOS.B", nit="900000002", nombre="Rival Dos SAS",
                               valor=14_000_000, fecha=date(2025, 5, 5), invitacion_directa=False, filas=2)])
    assert base.con.sql("select count(*), max(valor) from ofertas where id_oferta='B1'").fetchone() == (1, 14_000_000)
