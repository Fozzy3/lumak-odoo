"""Carga del histórico desde datos.gov.co. Idempotente: se puede repetir la misma ventana sin duplicar."""
import json
import os
import tempfile
from datetime import date, datetime

from .normalizar import clasificar, contrato, oferta, proceso, tipo_entidad
from .socrata import http, paginas

PROCESOS = "p6dx-8zbt"            # SECOP II - Procesos de Contratación
OFERTAS = "wi7w-2nvm"             # SECOPII - Ofertas Por Proceso (una fila por renglón de la lista de precios)
OFERTAS_HISTORICO = "b28v-edj8"   # SECOPII - Ofertas Por Proceso Histórico
CONTRATOS = "jbjy-vk9h"           # SECOP II - Contratos Electrónicos

MODALIDADES = ("Mínima cuantía",)
# Segmentos UNSPSC de tecnología (43 equipos y software, 81 servicios de ingeniería y TI) y, en servicios
# profesionales, educativos o de gestión (80, 82, 84), los que nombran software en el título
PALABRAS = ("SOFTWARE", "SISTEMA DE INFORMACI", "APLICATIVO", "PLATAFORMA", "PAGINA WEB", "PÁGINA WEB", "PORTAL",
            "CHATBOT", "INTELIGENCIA ARTIFICIAL")
CAMPOS_OFERTA = ("identificador_de_la_oferta, id_del_proceso_de_compra, nit_del_proveedor, nombre_proveedor, "
                 "valor_de_la_oferta, fecha_de_registro, invitacion_directa")


def filtro_procesos(desde):
    modalidades = ", ".join(f"'{m}'" for m in MODALIDADES)
    palabras = " or ".join(f"upper(nombre_del_procedimiento) like '%{p}%'" for p in PALABRAS)
    return (f"modalidad_de_contratacion in ({modalidades}) and fecha_de_publicacion_del >= '{desde}' and ("
            "codigo_principal_de_categoria like 'V1.43%' or codigo_principal_de_categoria like 'V1.81%' or "
            "((codigo_principal_de_categoria like 'V1.80%' or codigo_principal_de_categoria like 'V1.82%' or "
            f"codigo_principal_de_categoria like 'V1.84%') and ({palabras})))")


def cargar_procesos(base, desde, fetch=http):
    portafolios, total = set(), 0
    for pagina in paginas(PROCESOS, {"$where": filtro_procesos(desde), "$order": "id_del_proceso"}, fetch=fetch):
        procesos, adjudicaciones = [], []
        for fila in pagina:
            p, adj = proceso(fila)
            procesos.append(p)
            if adj:
                adjudicaciones.append(adj)
            if p["id_portafolio"]:
                portafolios.add(p["id_portafolio"])
        total += base.guardar_procesos(procesos)
        base.guardar_adjudicaciones(adjudicaciones)
    return total, sorted(portafolios)


def _pedir_ofertas(grupo, fetch):
    lista = ", ".join(f"'{p}'" for p in grupo)
    filas = []
    for dataset in (OFERTAS, OFERTAS_HISTORICO):
        params = {"$select": f"{CAMPOS_OFERTA}, count(*) as filas", "$group": CAMPOS_OFERTA,
                  "$where": f"id_del_proceso_de_compra in ({lista})", "$order": "identificador_de_la_oferta"}
        filas += [f for pagina in paginas(dataset, params, fetch=fetch) for f in pagina]
    return filas


def cargar_ofertas(base, portafolios, fetch=http, lote=150):
    """Agrupa en el servidor: cada oferta viene repetida una vez por renglón de la lista de precios.
    Si SECOP no responde un lote, lo parte en dos hasta aislar el proceso que falla; ese se salta y se informa."""
    total, fallidos = 0, []
    pendientes = [portafolios[i:i + lote] for i in range(0, len(portafolios), lote)][::-1]
    while pendientes:
        grupo = pendientes.pop()
        try:
            filas = _pedir_ofertas(grupo, fetch)
        except OSError:  # incluye TimeoutError y los errores de red de urllib
            if len(grupo) == 1:
                fallidos.append(grupo[0])
            else:
                mitad = len(grupo) // 2
                pendientes += [grupo[mitad:], grupo[:mitad]]
            continue
        total += base.guardar_ofertas([oferta(f) for f in filas])
    return total, fallidos


def sin_ofertas(base):
    """Portafolios con respuestas en SECOP pero sin ofertas en la base: lo que falta tras una carga interrumpida."""
    return [fila[0] for fila in base.con.execute("""
        select distinct p.id_portafolio from procesos p
        where p.respuestas > 0 and p.id_portafolio is not null
          and not exists (select 1 from ofertas o where o.id_portafolio = p.id_portafolio)
        order by 1""").fetchall()]


def cargar_contratos(base, desde, fetch=http, hoy=None):
    """Año por año: una sola consulta por todo el histórico es demasiado pesada para SECOP."""
    hoy = hoy or date.today()
    modalidades = ", ".join(f"'{m}'" for m in MODALIDADES)
    categorias = " or ".join(f"codigo_de_categoria_principal like 'V1.{s}%'" for s in ("43", "81", "80", "82", "84"))
    total = 0
    for anio in range(int(desde[:4]), hoy.year + 1):
        inicio = max(desde, f"{anio}-01-01")
        where = (f"modalidad_de_contratacion in ({modalidades}) and fecha_de_firma between '{inicio}' and "
                 f"'{anio}-12-31' and ({categorias})")
        for pagina in paginas(CONTRATOS, {"$where": where, "$order": "id_contrato"}, fetch=fetch):
            total += base.guardar_contratos([contrato(f) for f in pagina])
    return total


def actualizar(base, desde, fetch=http, contratos=True):
    """Trae procesos publicados desde `desde`, sus ofertas y los contratos firmados en la misma ventana."""
    inicio = datetime.now()
    n_procesos, portafolios = cargar_procesos(base, desde, fetch)
    n_ofertas, fallidos = cargar_ofertas(base, portafolios, fetch)
    n_contratos = cargar_contratos(base, desde, fetch) if contratos else 0
    nota = f"sin respuesta de SECOP: {', '.join(fallidos)}" if fallidos else ""
    base.registrar_carga(inicio, desde, n_procesos, n_ofertas, n_contratos, nota)
    return n_procesos, n_ofertas, n_contratos


def reclasificar(base):
    """Vuelve a clasificar el nicho desde la fila original guardada, sin descargar nada. Devuelve cuántos cambiaron."""
    filas = base.con.execute("select id_proceso, nicho, crudo from procesos").fetchall()
    nuevos, cambios = [], 0
    for id_proceso, nicho_antes, crudo in filas:
        fila = json.loads(crudo)
        texto = f"{fila.get('nombre_del_procedimiento', '')} {fila.get('descripci_n_del_procedimiento', '')}"
        nicho, etiquetas = clasificar(texto, fila.get("codigo_principal_de_categoria"), fila.get("tipo_de_contrato"))
        cambios += nicho != nicho_antes
        nuevos.append({"id_proceso": id_proceso, "nicho": nicho, "etiquetas": etiquetas,
                       "tipo_entidad": tipo_entidad(fila.get("entidad"))})
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        tmp.write("\n".join(json.dumps(n, ensure_ascii=False) for n in nuevos))
    try:
        base.con.execute(f"""
            update procesos set nicho = t.nicho, etiquetas = t.etiquetas, tipo_entidad = t.tipo_entidad
            from read_json('{tmp.name}', format = 'newline_delimited',
                           columns = {{'id_proceso': 'VARCHAR', 'nicho': 'BOOLEAN', 'etiquetas': 'VARCHAR[]', 'tipo_entidad': 'VARCHAR'}}) t
            where procesos.id_proceso = t.id_proceso""")
    finally:
        os.unlink(tmp.name)
    return cambios
