"""Base DuckDB con el histórico: tablas que se actualizan (upsert) y vistas estadísticas que se recalculan al consultar."""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import duckdb

from .normalizar import nit_base

COLUMNAS = {
    "procesos": ["id_proceso", "id_portafolio", "referencia", "entidad", "nit_entidad", "orden_entidad", "departamento", "ciudad",
                 "modalidad", "tipo_contrato", "unspsc", "segmento", "nombre", "descripcion", "fase", "estado",
                 "fecha_publicacion", "fecha_cierre", "fecha_adjudicacion", "precio_base", "respuestas", "n_lotes", "duracion",
                 "adjudicado", "url", "nicho", "etiquetas", "tipo_entidad", "crudo", "actualizado"],
    "adjudicaciones": ["id_adjudicacion", "id_proceso", "nit", "nombre", "valor"],
    "ofertas": ["id_oferta", "id_portafolio", "nit", "nombre", "valor", "fecha", "invitacion_directa", "filas"],
    "contratos": ["id_contrato", "id_portafolio", "nit", "nombre", "valor", "estado", "fecha_firma", "es_pyme"],
}

ESQUEMA = """
create table if not exists procesos (
    id_proceso varchar primary key, id_portafolio varchar, referencia varchar, entidad varchar, nit_entidad varchar,
    orden_entidad varchar, departamento varchar, ciudad varchar, modalidad varchar, tipo_contrato varchar, unspsc varchar,
    segmento varchar, nombre varchar, descripcion varchar, fase varchar, estado varchar, fecha_publicacion date,
    fecha_cierre date, fecha_adjudicacion date, precio_base double, respuestas integer, n_lotes integer, duracion varchar,
    adjudicado boolean, url varchar, nicho boolean, etiquetas varchar[], tipo_entidad varchar, crudo json, actualizado timestamp);
create table if not exists adjudicaciones (
    id_adjudicacion varchar primary key, id_proceso varchar, nit varchar, nombre varchar, valor double);
create table if not exists ofertas (
    id_oferta varchar primary key, id_portafolio varchar, nit varchar, nombre varchar, valor double, fecha date,
    invitacion_directa boolean, filas integer);
create table if not exists contratos (
    id_contrato varchar primary key, id_portafolio varchar, nit varchar, nombre varchar, valor double, estado varchar,
    fecha_firma date, es_pyme boolean);
create table if not exists cargas (
    inicio timestamp, fin timestamp, desde date, procesos integer, ofertas integer, contratos integer, nota varchar);
"""

VISTAS = """
-- Cada oferta con su puesto por precio, su descuento frente al presupuesto y si ganó
create or replace view v_ofertas as
with ganadores as (select distinct id_proceso, nit from adjudicaciones where nit is not null),
o as (
    select o.*, p.id_proceso, p.precio_base, p.entidad, p.nit_entidad, p.departamento, p.fecha_publicacion, p.nicho,
           p.modalidad, p.etiquetas,
           abs(o.valor - p.precio_base) < 1 as valor_igual_base,
           exists (select 1 from ganadores g where g.id_proceso = p.id_proceso and g.nit = o.nit) as es_ganador
    from ofertas o join procesos p on p.id_portafolio = o.id_portafolio)
select *, rank() over (partition by id_portafolio order by valor) as puesto,
       count(*) over (partition by id_portafolio) as n_ofertas,
       1 - valor / nullif(precio_base, 0) as descuento,
       -- Menos del 10 % o más del 150 % del presupuesto: casi siempre un error al digitar el valor en SECOP
       coalesce(valor < precio_base * 0.1 or valor > precio_base * 1.5, false) as valor_atipico
from o;

-- Un proceso por fila: cuántos ofertaron, quién ganó, en qué puesto, por cuánto, y el segundo
create or replace view v_procesos as
with r as (
    select id_portafolio, count(*) as n_ofertas,
           min(puesto) filter (where es_ganador) as puesto_ganador,
           min(valor) filter (where es_ganador) as precio_ganador,
           max(nombre) filter (where es_ganador) as ganador_nombre,
           max(nit) filter (where es_ganador) as ganador_nit,
           max(nombre) filter (where puesto = 1) as primero_nombre, min(valor) filter (where puesto = 1) as primero_valor,
           max(nombre) filter (where puesto = 2) as segundo_nombre, min(valor) filter (where puesto = 2) as segundo_valor,
           avg(valor_igual_base::int) as parte_igual_base,
           coalesce(bool_or(valor_atipico) filter (where es_ganador), false) as ganador_atipico
    from v_ofertas group by id_portafolio)
select p.* exclude (crudo), coalesce(r.n_ofertas, 0) as n_ofertas, r.ganador_nit, r.ganador_nombre, r.puesto_ganador,
       r.puesto_ganador = 1 as gano_el_mas_barato, r.precio_ganador,
       1 - r.precio_ganador / nullif(p.precio_base, 0) as descuento_ganador,
       r.primero_nombre, r.primero_valor, r.segundo_nombre, r.segundo_valor,
       (r.segundo_valor - r.primero_valor) / nullif(r.primero_valor, 0) as distancia_1_2,
       case when coalesce(r.n_ofertas, 0) = 0 then 'sin_ofertas'
            when (r.n_ofertas > 1 and r.parte_igual_base >= 0.5) or r.ganador_atipico then 'valores_dudosos'
            when p.respuestas is not null and r.n_ofertas <> p.respuestas then 'incompleto'
            else 'buena' end as calidad
from procesos p left join r on r.id_portafolio = p.id_portafolio;

-- Cada competidor: cuánto oferta, cuánto gana y con qué descuento
create or replace view v_competidores as
select nit, mode(nombre) as nombre, count(*) as ofertas, count(*) filter (where es_ganador) as ganadas,
       count(*) filter (where es_ganador) / count(*) as tasa_exito,
       median(descuento) filter (where not valor_igual_base and not valor_atipico) as descuento_mediano,
       median(descuento) filter (where es_ganador and not valor_igual_base and not valor_atipico) as descuento_mediano_ganando,
       count(*) filter (where nicho) as ofertas_nicho, count(distinct nit_entidad) as entidades,
       count(distinct departamento) as departamentos, min(fecha_publicacion) as primera, max(fecha_publicacion) as ultima
from v_ofertas where nit is not null group by nit;

-- Quién le oferta a cada entidad: la base para predecir quién se presentará al próximo proceso
create or replace view v_rivales_por_entidad as
select nit_entidad, mode(entidad) as entidad, nit, mode(nombre) as nombre, count(*) as ofertas,
       count(*) filter (where es_ganador) as ganadas, max(fecha_publicacion) as ultima
from v_ofertas where nit is not null group by nit_entidad, nit;
"""


class Base:
    def __init__(self, con):
        self.con = con
        con.execute(ESQUEMA)
        con.execute(VISTAS)

    @classmethod
    def abrir(cls, ruta):
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        return cls(duckdb.connect(str(ruta)))

    def _guardar(self, tabla, filas):
        """Carga masiva: la página va a un JSON temporal y DuckDB la lee de una vez (executemany tarda 14 ms por fila)."""
        if not filas:
            return 0
        tipos = dict(self.con.execute(f"select column_name, data_type from information_schema.columns "
                                      f"where table_name = '{tabla}'").fetchall())
        cols = COLUMNAS[tabla]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            for fila in filas:
                registro = {c: json.loads(fila[c]) if tipos[c] == "JSON" and isinstance(fila.get(c), str) else fila.get(c)
                            for c in cols}
                tmp.write(json.dumps(registro, default=str, ensure_ascii=False) + "\n")
        columnas = "{" + ", ".join(f"'{c}': '{tipos[c]}'" for c in cols) + "}"
        try:
            self.con.execute(f"insert or replace into {tabla} ({', '.join(cols)}) select {', '.join(cols)} "
                             f"from read_json('{tmp.name}', format = 'newline_delimited', columns = {columnas})")
        finally:
            os.unlink(tmp.name)
        return len(filas)

    def guardar_procesos(self, filas):
        ahora = datetime.now()
        return self._guardar("procesos", [{**f, "actualizado": ahora} for f in filas])

    # El NIT se normaliza al guardar: el mismo proveedor llega con y sin dígito de verificación
    def guardar_adjudicaciones(self, filas):
        return self._guardar("adjudicaciones", [{**f, "nit": nit_base(f.get("nit"))} for f in filas])

    def guardar_ofertas(self, filas):
        return self._guardar("ofertas", [{**f, "nit": nit_base(f.get("nit"))} for f in filas])

    def guardar_contratos(self, filas):
        return self._guardar("contratos", [{**f, "nit": nit_base(f.get("nit"))} for f in filas])

    def registrar_carga(self, inicio, desde, procesos, ofertas, contratos, nota=""):
        self.con.execute("insert into cargas values (?, ?, ?, ?, ?, ?, ?)",
                         [inicio, datetime.now(), desde, procesos, ofertas, contratos, nota])
