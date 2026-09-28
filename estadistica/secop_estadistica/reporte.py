"""Informe semanal en Markdown: estado de la base, mercado del nicho, competidores y novedades."""
from datetime import date, timedelta
from pathlib import Path


def millones(valor):
    if valor is None:
        return "—"
    return "$" + f"{valor / 1e6:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".") + " M"


def pct(valor):
    return "—" if valor is None else f"{round(100 * valor)} %"


def tabla(encabezado, filas):
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    lineas += ["| " + " | ".join("—" if v is None else str(v) for v in fila) + " |" for fila in filas]
    return "\n".join(lineas) if filas else "_Sin datos._"


def informe(base, hoy=None):
    hoy = hoy or date.today()
    q = lambda sql, *params: base.con.execute(sql, list(params)).fetchall()  # noqa: E731
    hace_12m, hace_24m, hace_7d = hoy - timedelta(days=365), hoy - timedelta(days=730), hoy - timedelta(days=7)

    total, nicho, desde, hasta = q("select count(*), count(*) filter (where nicho), min(fecha_publicacion), "
                                   "max(fecha_publicacion) from procesos")[0]
    ofertas, contratos = q("select (select count(*) from ofertas), (select count(*) from contratos)")[0]
    ultima = q("select max(fin) from cargas")[0][0]
    calidad = q("select calidad, count(*) from v_procesos where nicho group by 1 order by 2 desc")

    # Solo procesos con datos confiables y competencia real (2 o más ofertas)
    mercado = q("""
        select count(*), median(precio_base), median(n_ofertas) filter (where n_ofertas > 0),
               avg((not adjudicado)::int),
               avg(gano_el_mas_barato::int) filter (where calidad = 'buena' and n_ofertas >= 2),
               median(descuento_ganador) filter (where calidad = 'buena' and n_ofertas >= 2)
        from v_procesos where nicho and fecha_publicacion >= ?""", hace_12m)[0]
    por_anio = q("""
        select year(fecha_publicacion), count(*), median(n_ofertas) filter (where n_ofertas > 0),
               median(descuento_ganador) filter (where calidad = 'buena' and n_ofertas >= 2),
               avg(gano_el_mas_barato::int) filter (where calidad = 'buena' and n_ofertas >= 2)
        from v_procesos where nicho group by 1 order by 1""")
    competidores = q("""
        select mode(nombre), count(*), count(*) filter (where es_ganador),
               count(*) filter (where es_ganador) / count(*),
               median(descuento) filter (where es_ganador and not valor_igual_base and not valor_atipico), count(distinct departamento)
        from v_ofertas where nicho and nit is not null and fecha_publicacion >= ?
        group by nit order by 3 desc, 2 desc limit 15""", hace_24m)
    publicados = q("""
        select fecha_publicacion, entidad, nombre, precio_base, estado from v_procesos
        where nicho and fecha_publicacion >= ? order by fecha_publicacion desc""", hace_7d)
    adjudicados = q("""
        select fecha_adjudicacion, entidad, ganador_nombre, precio_ganador, descuento_ganador, n_ofertas from v_procesos
        where nicho and fecha_adjudicacion >= ? order by fecha_adjudicacion desc""", hace_7d)
    entidades = q("""
        select mode(entidad), count(*), sum(precio_base), median(n_ofertas) filter (where n_ofertas > 0)
        from v_procesos where nicho and fecha_publicacion >= ? group by nit_entidad order by 2 desc limit 15""", hace_24m)

    partes = [
        f"# Mínima cuantía de software y TIC — informe del {hoy}",
        "Fuente: datos abiertos de SECOP II (procesos, ofertas y contratos). «Nicho» = software a la medida, soporte de "
        "software, web, analítica, IA y automatización. Los datos confiables excluyen procesos donde la mayoría de ofertas "
        "trae el presupuesto como valor.",
        "## La base",
        f"- Procesos de mínima cuantía en TIC: {total:,} ({nicho:,} del nicho), publicados entre {desde} y {hasta}.".replace(",", "."),
        f"- Ofertas: {ofertas:,}. Contratos: {contratos:,}. Última carga: {ultima:%Y-%m-%d %H:%M}.".replace(",", ".") if ultima
        else f"- Ofertas: {ofertas}. Contratos: {contratos}.",
        "- Calidad de los procesos del nicho: " + ", ".join(f"{c} {n}" for c, n in calidad) + ".",
        "## El mercado del nicho (últimos 12 meses)",
        f"- Procesos: {mercado[0]}. Presupuesto mediano: {millones(mercado[1])}. Ofertas por proceso (mediana): {mercado[2] or '—'}.",
        f"- Sin adjudicar: {pct(mercado[3])}. Gana el más barato: {pct(mercado[4])}. "
        f"Descuento mediano del ganador frente al presupuesto: {pct(mercado[5])}.",
        tabla(["Año", "Procesos", "Ofertas (mediana)", "Descuento del ganador", "Gana el más barato"],
              [(a, n, o, pct(d), pct(g)) for a, n, o, d, g in por_anio]),
        "## Competidores del nicho (últimos 24 meses)",
        tabla(["Proveedor", "Ofertas", "Ganadas", "Tasa", "Descuento al ganar", "Departamentos"],
              [(n, o, g, pct(t), pct(d), dep) for n, o, g, t, d, dep in competidores]),
        "## Novedades de los últimos 7 días",
        "**Publicados**",
        tabla(["Fecha", "Entidad", "Proceso", "Presupuesto", "Estado"],
              [(f, e, n, millones(p), s) for f, e, n, p, s in publicados]),
        "**Adjudicados**",
        tabla(["Fecha", "Entidad", "Ganador", "Precio", "Descuento", "Ofertas"],
              [(f, e, g, millones(p), pct(d), o) for f, e, g, p, d, o in adjudicados]),
        "## Entidades que más compran en el nicho (últimos 24 meses)",
        tabla(["Entidad", "Procesos", "Presupuesto total", "Ofertas (mediana)"],
              [(e, n, millones(t), o) for e, n, t, o in entidades]),
    ]
    return "\n\n".join(partes) + "\n"


def escribir(base, carpeta, hoy=None):
    hoy = hoy or date.today()
    ruta = Path(carpeta) / f"{hoy}.md"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(informe(base, hoy))
    return ruta
