"""Monitor diario: trae de SECOP los procesos abiertos del nicho, los crea en Odoo (etapa «Detectado») y escribe en
cada proceso abierto el precio para ganar según el histórico. Odoo tiene que estar corriendo (docker compose up -d)."""
import json
import os
import urllib.request
from datetime import date, datetime, timezone
from http.cookiejar import CookieJar

from .cargar import PROCESOS, filtro_procesos
from .normalizar import proceso
from .precio import analizar, texto
from .socrata import http, paginas

# Las modalidades en que Lumak puede competir hoy (menor cuantía pide RUP: desde 2027)
MODALIDADES = ("Mínima cuantía", "Contratación régimen especial (con ofertas)")


class Odoo:
    """Cliente JSON-RPC mínimo con la sesión del usuario (Odoo local; credenciales por variables de entorno)."""

    def __init__(self, url, db, usuario, clave):
        self.url = url.rstrip("/")
        self.abridor = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        self._post("/web/session/authenticate", {"db": db, "login": usuario, "password": clave})

    @classmethod
    def desde_entorno(cls):
        e = os.environ.get
        return cls(e("LUMAK_ODOO_URL", "http://127.0.0.1:8069"), e("LUMAK_ODOO_DB", "lumak"),
                   e("LUMAK_ODOO_USUARIO", "admin"), e("LUMAK_ODOO_CLAVE", "admin"))

    def _post(self, ruta, params):
        cuerpo = json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode()
        pedido = urllib.request.Request(self.url + ruta, cuerpo, {"Content-Type": "application/json"})
        with self.abridor.open(pedido, timeout=300) as respuesta:
            datos = json.load(respuesta)
        if "error" in datos:
            raise RuntimeError(datos["error"]["data"]["message"])
        return datos["result"]

    def call(self, model, method, *args, **kwargs):
        return self._post("/web/dataset/call_kw", {"model": model, "method": method, "args": list(args), "kwargs": kwargs})


def abiertos(base, desde, hoy, fetch=http):
    """Procesos publicados desde `desde` que aún reciben ofertas. Todos se guardan en la base; se devuelven los del nicho."""
    where = f"{filtro_procesos(desde, MODALIDADES)} and fecha_de_recepcion_de >= '{hoy}'"
    nicho = []
    for pagina in paginas(PROCESOS, {"$where": where, "$order": "id_del_proceso"}, fetch=fetch):
        filas = [proceso(f) for f in pagina]
        base.guardar_procesos([p for p, _ in filas])
        base.guardar_adjudicaciones([a for _, a in filas if a])
        nicho += [p for p, _ in filas if p["nicho"]]
    return nicho


def sincronizar(base, odoo, desde, hoy=None, fetch=http):
    hoy = hoy or date.today()
    nuevos = abiertos(base, desde, hoy, fetch)
    ids = [p["id_proceso"] for p in nuevos]
    ya = {l["secop_id"] for l in odoo.call("crm.lead", "search_read", [["secop_id", "in", ids]], fields=["secop_id"],
                                             context={"active_test": False})} if ids else set()
    creados, errores = [], []
    for p in nuevos:
        if p["id_proceso"] in ya:
            continue
        try:
            asistente = odoo.call("lumak.secop.import", "create", {"referencia": p["id_proceso"]})
            accion = odoo.call("lumak.secop.import", "action_import", [asistente])
            odoo.call("crm.lead", "message_post", [accion["res_id"]], body="Detectado por el monitor diario de SECOP.")
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
    return {"abiertos": len(nuevos), "creados": len(creados), "analizados": analizados, "errores": errores}
