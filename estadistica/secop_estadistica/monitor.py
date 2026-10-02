"""Monitor diario: trae de SECOP los procesos abiertos del nicho, de capacitación y de reventa de licencias, los crea
en Odoo (etapa «Detectado») y escribe en cada proceso abierto el precio para ganar según el histórico. Odoo tiene que
estar corriendo (docker compose up -d)."""
import io
import json
import os
import re
import subprocess
import tempfile
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .cargar import PROCESOS
from .normalizar import acepta_experiencia_socios, alertas, exige_rup, norm, proceso
from .precio import analizar, texto
from .socrata import http, paginas

CREDENCIALES = Path.home() / ".config" / "lumak" / "odoo.env"  # fuera del repo; ver docs/salida-a-produccion.md
# Las modalidades en que Lumak puede competir hoy (menor cuantía pide RUP: desde 2027)
MODALIDADES = ("Mínima cuantía", "Contratación régimen especial (con ofertas)")
# Régimen especial recibe ofertas hasta unas 3 semanas; SECOP solo devuelve los que siguen abiertos, así que mirar
# atrás 30 días no cuesta y cubre también el equipo apagado varios días
DIAS_ATRAS = 30
DOCUMENTOS = "dmgg-8hin"  # SECOP II - Archivos Descarga Desde 2025: se bajan sin el captcha del portal
NO_LEER = r"cdp|disponibilidad|paa|plan anual|sector|cotizaci|propuesta"
# En el nicho (12 meses al 30 sep 2026) cierran con 0 o 1 ofertas el 56-69 % de sus procesos; las gobernaciones, el 10 %
POCA_COMPETENCIA = ("alcaldia", "hospital_ese", "nacional", "universidad")


class Odoo:
    """Cliente JSON-RPC mínimo con una clave de API: sirve aunque el usuario tenga doble factor y se revoca sin tocar
    la contraseña. Credenciales en ~/.config/lumak/odoo.env (docs/salida-a-produccion.md)."""
    # ponytail: /jsonrpc sigue en Odoo 19 aunque está obsoleto; pasar a /json/2 cuando una versión lo quite

    def __init__(self, url, db, usuario, clave):
        self.url, self.db, self.clave = url.rstrip("/"), db, clave
        self.uid = self._rpc("common", "authenticate", db, usuario, clave, {})
        if not self.uid:
            raise RuntimeError(f"Odoo rechazó el usuario {usuario} o su clave de API")

    @classmethod
    def desde_entorno(cls, archivo=CREDENCIALES):
        """Credenciales de las variables de entorno o, si no están, del archivo privado (así sirve igual a mano y en systemd)."""
        e = dict(os.environ)
        if Path(archivo).is_file():
            for linea in Path(archivo).read_text().splitlines():
                clave, igual, valor = linea.strip().partition("=")
                if igual and not clave.startswith("#"):
                    e.setdefault(clave.strip(), valor.strip())
        if faltan := [v for v in ("LUMAK_ODOO_USUARIO", "LUMAK_ODOO_CLAVE") if not e.get(v)]:
            raise SystemExit(f"Faltan {', '.join(faltan)} (van en {CREDENCIALES})")
        return cls(e.get("LUMAK_ODOO_URL", "http://127.0.0.1:8069"), e.get("LUMAK_ODOO_DB", "lumak"),
                   e["LUMAK_ODOO_USUARIO"], e["LUMAK_ODOO_CLAVE"])

    def avisar(self, clave, detalle):
        """Deja en el tablero de Odoo que esta automatización corrió (monitor, historico o respaldo)."""
        return self.call("crm.lead", "secop_registrar_automatizacion", clave, detalle)

    def _rpc(self, servicio, metodo, *args):
        cuerpo = json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"service": servicio, "method": metodo, "args": list(args)}}).encode()
        pedido = urllib.request.Request(self.url + "/jsonrpc", cuerpo, {"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=300) as respuesta:
            datos = json.load(respuesta)
        if "error" in datos:
            raise RuntimeError(datos["error"]["data"]["message"])
        return datos["result"]

    def call(self, model, method, *args, **kwargs):
        return self._rpc("object", "execute_kw", self.db, self.uid, self.clave, model, method, list(args), kwargs)


def abiertos(base, desde, hoy, fetch=http):
    """Procesos publicados desde `desde` que aún reciben ofertas. Se piden todos (unos 450) y decide el clasificador: el
    filtro por palabras de la carga semanal botaba procesos del nicho. Devuelve los del nicho, capacitación y reventa.
    Guarda los que tienen algo de tecnología, para que Mercado SECOP no se llene de sillas y aires acondicionados."""
    modalidades = ", ".join(f"'{m}'" for m in MODALIDADES)
    where = (f"modalidad_de_contratacion in ({modalidades}) and fecha_de_publicacion_del >= '{desde}' "
             f"and fecha_de_recepcion_de >= '{hoy}'")
    elegidos = []
    for pagina in paginas(PROCESOS, {"$where": where, "$order": "id_del_proceso"}, fetch=fetch):
        filas = [(p, a) for p, a in map(proceso, pagina) if p["nicho"] or p["etiquetas"] or p["segmento"] in ("43", "81")]
        base.guardar_procesos([p for p, _ in filas])
        base.guardar_adjudicaciones([a for _, a in filas if a])
        elegidos += [p for p, _ in filas if p["nicho"] or {"capacitacion", "reventa"} & set(p["etiquetas"])]
    return list({p["id_proceso"]: p for p in elegidos}.values())  # SECOP a veces repite un proceso en dos filas


def bajar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(pedido, timeout=120) as respuesta:
        return respuesta.read()


def texto_pdf(datos):
    """Texto de un PDF, o de los PDF de un ZIP. Vacío si está escaneado o dañado (pdftotext viene con poppler)."""
    if datos[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            return " ".join(texto_pdf(z.read(n)) for n in z.namelist() if n.lower().endswith(".pdf"))
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(datos)
        f.flush()
        return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True).stdout


def documentos(id_portafolio, fetch=http, bajar=bajar):
    """Texto de la invitación y los estudios previos publicados en SECOP. Se salta CDP, PAA, análisis del sector y
    cotizaciones: nombran el RUP sin que sea requisito."""
    filas = fetch(DOCUMENTOS, {"$where": f"proceso = '{id_portafolio}'", "$limit": 100})
    return " ".join(texto_pdf(bajar(f["url_descarga_documento"]["url"])) for f in filas
                    if re.search(r"\.(pdf|zip)$", f["nombre_archivo"].lower()) and not re.search(NO_LEER, norm(f["nombre_archivo"])))


def poca_competencia(base, p, hoy):
    """¿Suele llegar 0 o 1 oferta? Por la historia de la entidad si tiene 3 procesos cerrados o más; si no, por su tipo."""
    n, mediana = base.con.execute("select count(respuestas), median(respuestas) from procesos where nit_entidad = ? "
                                  "and fecha_cierre < ?", [p["nit_entidad"], hoy]).fetchone()
    return mediana <= 1 if n >= 3 else p["tipo_entidad"] in POCA_COMPETENCIA


def ventajas(base, p, pliego, experiencia, hoy):
    """[(etiqueta, motivo)] de lo que juega a favor de Lumak. Cada ventaja es una estrella y el tablero ordena por estrellas."""
    v = []
    if poca_competencia(base, p, hoy):
        v.append(("Poca competencia", "Esta entidad suele recibir 0 o 1 ofertas: quien se presenta casi siempre gana, y sin "
                                      "bajar el precio."))
    presupuesto = p["precio_base"] or 0
    if p["nicho"] and experiencia and 0 < presupuesto <= sum(experiencia):
        cuanto = "un solo contrato" if presupuesto <= max(experiencia) else "sumando contratos"
        v.append(("Tu experiencia alcanza", f"El presupuesto se cubre con {cuanto} de la experiencia registrada en Empresa."))
    if acepta_experiencia_socios(pliego):
        v.append(("Acepta experiencia de socios", "La invitación deja acreditar la experiencia de los socios: vale la tuya."))
    return v


def etiqueta(odoo, nombre):
    """Id de la etiqueta del CRM con ese nombre; la crea la primera vez."""
    return (odoo.call("crm.tag", "search", [["name", "=", nombre]], limit=1) or [odoo.call("crm.tag", "create", {"name": nombre})])[0]


def sincronizar(base, odoo, desde=None, hoy=None, fetch=http, leer=None):
    hoy = hoy or date.today()
    desde = desde or hoy - timedelta(days=DIAS_ATRAS)
    leer = leer or (lambda id_portafolio: documentos(id_portafolio, fetch))
    nuevos = abiertos(base, desde, hoy, fetch)
    ids = [p["id_proceso"] for p in nuevos]
    ya = {l["secop_id"] for l in odoo.call("crm.lead", "search_read", [["secop_id", "in", ids]], fields=["secop_id"],
                                             context={"active_test": False})} if ids else set()
    creados, errores = [], []
    experiencia = [e["valor"] for e in odoo.call("lumak.experiencia", "search_read", [["en_oferta", "=", True],
                                                                                     ["valor", ">", 0]], fields=["valor"])]
    for p in nuevos:
        if p["id_proceso"] in ya:
            continue
        try:
            asistente = odoo.call("lumak.secop.import", "create", {"referencia": p["id_proceso"]})
            accion = odoo.call("lumak.secop.import", "action_import", [asistente])
            avisos = alertas(f"{p['nombre'] or ''} {p['descripcion'] or ''}")
            if "reventa" in p["etiquetas"]:
                avisos.append(("Reventa", "Es reventa de licencias o suscripciones: suelen pedir experiencia vendiendo lo mismo."))
            pliego = leer(p["id_portafolio"]) or ""
            if exige_rup(pliego):
                avisos.append(("RUP", "Los documentos piden RUP y Lumak aún no lo tiene."))
            ganan = ventajas(base, p, pliego, experiencia, hoy)
            odoo.call("crm.lead", "message_post", [accion["res_id"]], body=" ".join(
                ["Detectado por el monitor diario de SECOP."] + [f"✓ {motivo}" for _, motivo in ganan] +
                [f"⚠ {motivo}" for _, motivo in avisos] +
                (["No pude leer los documentos (escaneados o aún sin publicar): revisa a mano si piden RUP."]
                 if len(pliego.split()) < 100 else [])))
            if avisos or ganan:
                valores = {"tag_ids": [(4, etiqueta(odoo, f"✓ {nombre}")) for nombre, _ in ganan] +
                                      [(4, etiqueta(odoo, f"⚠ {nombre}")) for nombre, _ in avisos]}
                if ganan:
                    valores["priority"] = str(len(ganan))
                odoo.call("crm.lead", "write", [accion["res_id"]], valores)
            creados.append(accion["res_id"])
        except RuntimeError as error:  # p. ej. aún no está en los datos abiertos: se intenta mañana
            errores.append((p["id_proceso"], str(error)))

    equipo = odoo.call("crm.team", "search", [["es_licitaciones", "=", True]], limit=1)
    leads = odoo.call("crm.lead", "search_read", [["team_id", "in", equipo], ["won_status", "=", "pending"],
                                                   ["type", "=", "opportunity"]],
                      fields=["id", "secop_id", "expected_revenue", "secop_costo_estimado", "secop_estampillas"])
    analizados = 0
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for lead in leads:
        if not lead["expected_revenue"]:
            continue
        fila = base.con.execute("select nit_entidad, departamento from procesos where id_proceso = ?",
                                [lead["secop_id"]]).fetchone() if lead["secop_id"] else None
        a = analizar(base.con, presupuesto=lead["expected_revenue"], costo=lead["secop_costo_estimado"] or None,
                     estampillas=lead["secop_estampillas"] or 0, nit_entidad=fila[0] if fila else None,
                     departamento=fila[1] if fila else None, hoy=hoy)
        s = a["sugerido"]
        odoo.call("crm.lead", "write", [lead["id"]], {
            "secop_precio_sugerido": s["precio"] if s else 0, "secop_prob_ganar": s["probabilidad"] if s else 0,
            "secop_analisis_precio": texto(a), "secop_analisis_fecha": ahora})
        analizados += 1
    return {"abiertos": len(nuevos), "creados": len(creados), "analizados": analizados, "errores": errores,
            "publicados": publicar(base, odoo, hoy)}


def _dia(fecha):
    return fecha.isoformat() if fecha else False


def _pct(fraccion):
    return round(100 * fraccion, 1) if fraccion is not None else False


def publicar(base, odoo, hoy, dias=60, lote=200):
    """Lleva a Odoo (Lumak → Mercado SECOP) todo el nicho y lo publicado en los últimos `dias`, con sus ofertas.
    Los descuentos van en %, y vacíos cuando SECOP trae valores dudosos (así no dañan los promedios)."""
    desde = hoy - timedelta(days=dias)
    ofertas = defaultdict(list)
    for id_proceso, nombre, nit, valor, puesto, descuento, gano in base.con.execute("""
            select id_proceso, nombre, nit, valor, puesto,
                   case when not valor_igual_base and not valor_atipico then descuento end, es_ganador
            from v_ofertas where nicho or fecha_publicacion >= ? order by id_proceso, puesto""", [desde]).fetchall():
        ofertas[id_proceso].append({"proveedor": nombre, "nit": nit or False, "valor": valor, "puesto": puesto,
                                    "descuento": _pct(descuento), "gano": int(bool(gano))})
    procesos = [{
        "secop_id": f[0], "referencia": f[1], "nombre": f[2] or f[0], "entidad": f[3], "departamento": f[4], "ciudad": f[5],
        "modalidad": f[6], "estado": f[7], "fecha_publicacion": _dia(f[8]), "fecha_cierre": _dia(f[9]),
        "presupuesto": f[10] or 0, "url": f[11] or False, "nicho": bool(f[12]), "n_ofertas": f[13] or 0,
        "ganador": f[14] or False, "precio_ganador": f[15] or False, "descuento_ganador": _pct(f[16]),
        "ofertas": ofertas[f[0]],
    } for f in base.con.execute("""
            select id_proceso, referencia, nombre, entidad, departamento, ciudad, modalidad, estado, fecha_publicacion,
                   fecha_cierre, precio_base, url, nicho, n_ofertas, ganador_nombre, precio_ganador,
                   case when calidad = 'buena' and descuento_ganador between 0 and 0.9 then descuento_ganador end
            from v_procesos where nicho or fecha_publicacion >= ? order by id_proceso""", [desde]).fetchall()]
    for i in range(0, len(procesos), lote):
        odoo.call("lumak.secop.proceso", "sincronizar", procesos[i:i + lote])
    return len(procesos)
