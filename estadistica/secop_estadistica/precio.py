"""Cuánto ofertar en una mínima cuantía, según el histórico del nicho.

Probabilidad de ganar con un descuento d = parte de los procesos comparables en que el ganador ofertó un descuento
menor o igual a d, es decir, en que esa oferta le habría ganado. Supone que Lumak cumple los requisitos (en mínima
cuantía gana la oferta más barata que cumpla) y que la competencia se comporta como en los últimos 3 años.
Utilidad = precio sin IVA menos SIMPLE y estampillas, menos el costo. El sugerido maximiza probabilidad × utilidad.
"""
from datetime import date, timedelta

from .reporte import millones, pct

SIMPLE = 0.059   # tarifa del SIMPLE hasta 6.000 UVT de ingresos al año (misma que el módulo de Odoo)
IVA = 0.19
METAS = (0.5, 0.7, 0.85)
REJILLA = [i / 200 for i in range(0, 161)]  # descuentos de 0 % a 80 %, de a 0,5 %


def descuentos_ganadores(con, hoy, meses=36):
    """Descuento del ganador en los procesos del nicho con datos confiables de los últimos `meses`."""
    return [fila[0] for fila in con.execute("""
        select descuento_ganador from v_procesos
        where nicho and calidad = 'buena' and precio_ganador is not null and descuento_ganador between 0 and 0.9
          and fecha_publicacion >= ?""", [hoy - timedelta(days=30 * meses)]).fetchall()]


def probabilidad(descuentos, d):
    return sum(x <= d + 1e-9 for x in descuentos) / len(descuentos) if descuentos else 0.0


def _punto(presupuesto, d, p, costo, estampillas, iva, simple):
    precio = presupuesto * (1 - d)  # el presupuesto oficial ya trae el IVA
    neto = precio / (1 + iva) * (1 - simple - estampillas / 100)
    utilidad = neto - costo if costo else None
    return {"descuento": d, "precio": precio, "probabilidad": p, "utilidad": utilidad,
            "utilidad_esperada": p * utilidad if utilidad is not None else None}


def competidores(con, nit_entidad, departamento, hoy, limite=5):
    """Quién le ha ofertado a la entidad en el nicho; si hay pocos, los activos del nicho en el departamento."""
    filas = []
    if nit_entidad:
        filas = [(n, o, g, "en esta entidad") for n, o, g in con.execute("""
            select mode(nombre), count(*), count(*) filter (where es_ganador) from v_ofertas
            where nicho and nit_entidad = ? and nit is not null
            group by nit order by 3 desc, 2 desc limit ?""", [nit_entidad, limite]).fetchall()]
    if len(filas) < 3 and departamento:
        vistos = {f[0] for f in filas}
        extra = con.execute("""
            select mode(nombre), count(*), count(*) filter (where es_ganador) from v_ofertas
            where nicho and departamento = ? and nit is not null and fecha_publicacion >= ?
            group by nit order by 3 desc, 2 desc limit ?""", [departamento, hoy - timedelta(days=730), limite]).fetchall()
        filas += [(n, o, g, "en el departamento") for n, o, g in extra if n not in vistos][:limite - len(filas)]
    return [{"nombre": n, "ofertas": o, "ganadas": g, "donde": d} for n, o, g, d in filas]


def resumen_entidad(con, nit_entidad):
    if not nit_entidad:
        return None
    n, ofertas, descuento = con.execute("""
        select count(*), median(n_ofertas) filter (where n_ofertas > 0),
               median(descuento_ganador) filter (where calidad = 'buena' and descuento_ganador between 0 and 0.9)
        from v_procesos where nicho and nit_entidad = ?""", [nit_entidad]).fetchone()
    return {"procesos": n, "ofertas": ofertas, "descuento": descuento} if n else None


def analizar(con, presupuesto, costo=None, estampillas=0.0, nit_entidad=None, departamento=None, hoy=None,
             iva=IVA, simple=SIMPLE):
    hoy = hoy or date.today()
    ds = descuentos_ganadores(con, hoy)
    curva = [_punto(presupuesto, d, probabilidad(ds, d), costo, estampillas, iva, simple) for d in REJILLA] if ds else []
    opciones = [{**p, "meta": meta} for meta in METAS
                if (p := next((c for c in curva if c["probabilidad"] >= meta), None))]
    sugerido = None
    if costo and curva:
        rentables = [c for c in curva if c["utilidad"] > 0]
        # a igual utilidad esperada, el precio más alto
        sugerido = max(rentables, key=lambda c: (c["utilidad_esperada"], -c["descuento"])) if rentables else None
    return {"comparables": len(ds), "opciones": opciones, "sugerido": sugerido, "costo": costo,
            "competidores": competidores(con, nit_entidad, departamento, hoy), "entidad": resumen_entidad(con, nit_entidad)}


def texto(a):
    """Resumen en español para la pestaña SECOP de Odoo."""
    if not a["comparables"]:
        return "Sin histórico comparable en los últimos 3 años: decide el precio con el costo y la invitación."
    lineas = [f"Basado en {a['comparables']} procesos comparables del nicho (últimos 3 años)."]
    s = a["sugerido"]
    if s:
        lineas.append(f"Precio sugerido: {millones(s['precio'])} ({pct(s['descuento'])} bajo el presupuesto). "
                      f"Probabilidad de ganar: {pct(s['probabilidad'])}. Utilidad si gana: {millones(s['utilidad'])}.")
    elif a["costo"]:
        lineas.append("Con este costo ningún precio deja utilidad: revisa el costo o no ofertes.")
    else:
        lineas.append("Pon el costo estimado en la pestaña SECOP para calcular la utilidad y el precio sugerido.")
    lineas.append("Opciones:")
    for o in a["opciones"]:
        utilidad = f", utilidad si gana {millones(o['utilidad'])}" if o["utilidad"] is not None else ""
        lineas.append(f"- {pct(o['meta'])} de probabilidad: ofertar {millones(o['precio'])} "
                      f"({pct(o['descuento'])} bajo el presupuesto){utilidad}")
    e = a["entidad"]
    if e:
        linea = f"Esta entidad: {e['procesos']} procesos del nicho"
        if e["ofertas"]:
            linea += f"; ofertas por proceso (mediana) {e['ofertas']:g}"
        if e["descuento"] is not None:
            linea += f"; el ganador ofertó {pct(e['descuento'])} bajo el presupuesto (mediana)"
        lineas.append(linea + ".")
    if a["competidores"]:
        lineas.append("Competidores probables: " + "; ".join(
            f"{c['nombre']} (ganó {c['ganadas']} de {c['ofertas']} {c['donde']})" for c in a["competidores"]) + ".")
    return "\n".join(lineas)
