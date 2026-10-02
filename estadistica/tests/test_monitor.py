"""Monitor diario contra un SECOP y un Odoo falsos."""
from datetime import date

import pytest

from secop_estadistica.monitor import DOCUMENTOS, MODALIDADES, Odoo, documentos, publicar, sincronizar
from tests.test_normalizar import FILA_PROCESO
from tests.test_precio import base  # noqa: F401  (histórico de 20 procesos del nicho)

# Una entidad sin ventajas (ni alcaldía ni hospital): así cada prueba ve solo lo que mide
SOFTWARE = {**FILA_PROCESO, "id_del_proceso": "CO1.REQ.900", "id_del_portafolio": "CO1.BDOS.900", "adjudicado": "No",
            "id_adjudicacion": "No Adjudicado", "fecha_de_recepcion_de": "2026-10-02T00:00:00.000",
            "entidad": "EMPRESA DE SERVICIOS DE PRUEBA",
            "nombre_del_procedimiento": "Desarrollo de un sistema de información para PQRSD"}
EQUIPOS = {**SOFTWARE, "id_del_proceso": "CO1.REQ.901", "id_del_portafolio": "CO1.BDOS.901",
           "nombre_del_procedimiento": "Suministro de computadores portátiles", "codigo_principal_de_categoria": "V1.43211500",
           "tipo_de_contrato": "Compraventa"}


def secop(procesos, documentos=()):
    pedidos = []

    def fetch(dataset, params):
        pedidos.append(params["$where"])
        if dataset == DOCUMENTOS:
            return list(documentos)
        return [] if params["$offset"] else procesos
    fetch.pedidos = pedidos
    return fetch


class OdooFalso:
    def __init__(self, leads=(), no_encontrados=(), experiencia=()):
        self.leads, self.no_encontrados, self.experiencia = list(leads), set(no_encontrados), list(experiencia)
        self.importados, self.llamadas, self.publicados, self.etiquetas = [], [], [], {}

    def call(self, model, method, *args, **kwargs):
        self.llamadas.append((model, method, args, kwargs))
        if (model, method) == ("crm.lead", "search_read"):
            dominio = args[0]
            if dominio and dominio[0][0] == "secop_id":
                return [{"secop_id": i} for i in self.importados if i in dominio[0][2]]
            return self.leads
        if (model, method) == ("lumak.experiencia", "search_read"):
            return [{"valor": v} for v in self.experiencia]
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
        if (model, method) == ("crm.tag", "search"):
            return [self.etiquetas[args[0][0][2]]] if args[0][0][2] in self.etiquetas else []
        if (model, method) == ("crm.tag", "create"):
            self.etiquetas[args[0]["name"]] = 200 + len(self.etiquetas)
            return self.etiquetas[args[0]["name"]]
        if (model, method) == ("lumak.secop.proceso", "sincronizar"):
            self.publicados.append(args[0])
            return {"creados": len(args[0]), "actualizados": 0}
        return True

    def escritos(self):
        return [(args[0], args[1]) for model, method, args, _ in self.llamadas if (model, method) == ("crm.lead", "write")]


def test_it_brings_only_new_open_niche_processes_once(base):  # noqa: F811
    odoo, datos = OdooFalso(), secop([SOFTWARE, EQUIPOS])
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=datos)
    assert (r["abiertos"], r["creados"]) == (1, 1) and odoo.importados == ["CO1.REQ.900"]
    assert all(m in datos.pedidos[0] for m in MODALIDADES) and "fecha_de_recepcion_de >= '2026-09-28'" in datos.pedidos[0]
    assert r["publicados"] == sum(map(len, odoo.publicados)) > 0, "y lleva el mercado a Odoo"
    sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([SOFTWARE, EQUIPOS]))
    assert odoo.importados == ["CO1.REQ.900"], "el segundo día no lo duplica"


def test_by_default_it_looks_back_far_enough_to_catch_special_regime_processes(base):  # noqa: F811
    # Régimen especial recibe ofertas hasta unas 3 semanas: el 29 sep 2026 había abiertos publicados hace 22 días
    datos = secop([])
    sincronizar(base, OdooFalso(), hoy=date(2026, 9, 28), fetch=datos)
    assert "fecha_de_publicacion_del >= '2026-08-29'" in datos.pedidos[0]


def test_likely_dead_ends_still_arrive_but_tagged_with_the_reason(base):  # noqa: F811
    periodico = {**SOFTWARE, "id_del_proceso": "CO1.REQ.904", "id_del_portafolio": "CO1.BDOS.904",
                 "nombre_del_procedimiento": "Publicación en periódico regional, portal web y redes sociales del mismo medio"}
    aranda = {**SOFTWARE, "id_del_proceso": "CO1.REQ.905", "id_del_portafolio": "CO1.BDOS.905",
              "nombre_del_procedimiento": "Soporte y actualización de la plataforma ARANDA"}
    odoo = OdooFalso()
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([periodico, aranda, SOFTWARE]))
    assert r["creados"] == 3, "no se pierde ninguno"
    assert odoo.etiquetas == {"⚠ Medios": 200, "⚠ Marca": 201}
    etiquetados = {ids[0]: vals["tag_ids"] for ids, vals in odoo.escritos() if "tag_ids" in vals}
    assert etiquetados == {101: [(4, 200)], 102: [(4, 201)]}, "el de software limpio no lleva marca"
    mensajes = [kw["body"] for model, method, _, kw in odoo.llamadas if method == "message_post"]
    assert "periódico" in mensajes[0] and "distribuidor" in mensajes[1] and "⚠" not in mensajes[2]


def test_it_reads_the_documents_to_tell_whether_they_require_rup(base):  # noqa: F811
    pide = {**SOFTWARE, "id_del_proceso": "CO1.REQ.906", "id_del_portafolio": "CO1.BDOS.906"}
    escaneado = {**SOFTWARE, "id_del_proceso": "CO1.REQ.907", "id_del_portafolio": "CO1.BDOS.907"}
    textos = {"CO1.BDOS.906": "Sin embargo, si será obligatorio que esté registrado en el Registro Único de Proponentes. " * 20,
              "CO1.BDOS.907": ""}
    odoo = OdooFalso()
    sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([pide, escaneado]), leer=textos.get)
    assert odoo.etiquetas == {"⚠ RUP": 200}
    assert {ids[0]: vals["tag_ids"] for ids, vals in odoo.escritos() if "tag_ids" in vals} == {101: [(4, 200)]}
    mensajes = [kw["body"] for model, method, _, kw in odoo.llamadas if method == "message_post"]
    assert "RUP" in mensajes[0] and "No pude leer" in mensajes[1], "si no se pudo leer, lo dice en vez de callar"


def test_documents_skip_budget_and_market_files_and_survive_unreadable_ones():
    filas = [{"nombre_archivo": n, "url_descarga_documento": {"url": f"https://secop/{n}"}}
             for n in ("1. ESTUDIO PREVIO.PDF", "3. CDP.PDF", "2. ANALISIS DEL SECTOR.pdf", "PAA.pdf", "mc0182026.zip",
                       "2.2. ANALISIS DE PRECIOS.xlsx", "PROPUESTA 1 PERIODICO.pdf")]
    pedidos = []
    texto = documentos("CO1.BDOS.1", fetch=secop([], filas), bajar=lambda url: pedidos.append(url) or b"no es un pdf")
    assert pedidos == ["https://secop/1. ESTUDIO PREVIO.PDF", "https://secop/mc0182026.zip"]
    assert texto.strip() == "", "un PDF escaneado o dañado da texto vacío, no un error"


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


def test_every_open_process_reaches_the_classifier_not_only_those_with_keywords(base):  # noqa: F811
    # Envigado, 30 sep 2026: $113 M, sin categoría y sin «software» en el texto; el filtro por palabras lo botaba
    envigado = {**SOFTWARE, "id_del_proceso": "CO1.REQ.903", "id_del_portafolio": "CO1.BDOS.903",
                "codigo_principal_de_categoria": "UNSPECIFIED",
                "nombre_del_procedimiento": "Implementar el sistema municipal de gestión del conocimiento en bienestar animal",
                "descripci_n_del_procedimiento": "Integrando la gestión de información, la analítica y la investigación aplicada"}
    aire = {**EQUIPOS, "id_del_proceso": "CO1.REQ.908", "id_del_portafolio": "CO1.BDOS.908",
            "codigo_principal_de_categoria": "V1.72101500", "tipo_de_contrato": "Prestación de servicios",
            "nombre_del_procedimiento": "Mantenimiento del aire acondicionado"}
    odoo, datos = OdooFalso(), secop([envigado, aire])
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=datos)
    assert "codigo_principal_de_categoria" not in datos.pedidos[0], "SECOP devuelve todo lo abierto; decide el clasificador"
    assert odoo.importados == ["CO1.REQ.903"] and r["creados"] == 1
    guardado = {i for (i,) in base.con.execute("select id_proceso from procesos where id_proceso in ('CO1.REQ.903', 'CO1.REQ.908')").fetchall()}
    assert guardado == {"CO1.REQ.903"}, "lo que no tiene que ver con tecnología no llena Mercado SECOP"


def test_a_process_repeated_by_secop_is_brought_once(base):  # noqa: F811
    # 30 sep 2026: datos.gov.co, a mitad de una actualización, devolvía el mismo proceso en dos filas
    odoo = OdooFalso()
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([SOFTWARE, SOFTWARE]))
    assert r["abiertos"] == 1 and r["creados"] == 1
    assert len([1 for _, method, _, _ in odoo.llamadas if method == "message_post"]) == 1, "un solo aviso"


def test_licence_resale_arrives_tagged(base):  # noqa: F811
    sena = {**SOFTWARE, "id_del_proceso": "CO1.REQ.910", "id_del_portafolio": "CO1.BDOS.910",
            "codigo_principal_de_categoria": "UNSPECIFIED", "nombre_del_procedimiento": "Suscripción inteligencia artificial",
            "descripci_n_del_procedimiento": "Adquisición de suscripciones de inteligencia artificial en la nube"}
    odoo = OdooFalso()
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([sena]))
    assert r["creados"] == 1 and odoo.etiquetas == {"⚠ Reventa": 200}
    mensaje = next(kw["body"] for _, method, _, kw in odoo.llamadas if method == "message_post")
    assert "experiencia" in mensaje


def test_digital_skills_training_arrives_tagged(base):  # noqa: F811
    diplomado = {**SOFTWARE, "id_del_proceso": "CO1.REQ.909", "id_del_portafolio": "CO1.BDOS.909",
                 "codigo_principal_de_categoria": "V1.86101700", "nombre_del_procedimiento": "Diplomado en inteligencia artificial"}
    odoo = OdooFalso()
    r = sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([diplomado]))
    assert r["creados"] == 1 and odoo.etiquetas == {"⚠ Capacitación": 200}


def test_odoo_logs_in_with_an_api_key_that_survives_two_factor(monkeypatch):
    enviados = []

    def rpc(self, servicio, metodo, *args):
        enviados.append((servicio, metodo, args))
        return 7
    monkeypatch.setattr(Odoo, "_rpc", rpc)
    Odoo("http://odoo", "lumak", "carlos", "clave").call("crm.lead", "search_read", [], fields=["id"])
    assert enviados == [("common", "authenticate", ("lumak", "carlos", "clave", {})),
                        ("object", "execute_kw", ("lumak", 7, "clave", "crm.lead", "search_read", [[]], {"fields": ["id"]}))]


def test_odoo_says_clearly_when_the_key_is_wrong_or_missing(monkeypatch):
    monkeypatch.setattr(Odoo, "_rpc", lambda self, *a: False)
    with pytest.raises(RuntimeError, match="rechazó"):
        Odoo("http://odoo", "lumak", "carlos", "vieja")
    monkeypatch.delenv("LUMAK_ODOO_CLAVE", raising=False)
    with pytest.raises(SystemExit, match="LUMAK_ODOO_CLAVE"):
        Odoo.desde_entorno(archivo="/no/existe")


def test_credentials_come_from_the_private_file_when_the_environment_has_none(monkeypatch, tmp_path):
    for v in ("LUMAK_ODOO_USUARIO", "LUMAK_ODOO_CLAVE"):
        monkeypatch.delenv(v, raising=False)
    archivo = tmp_path / "odoo.env"
    archivo.write_text("# comentario\nLUMAK_ODOO_USUARIO=carlos\nLUMAK_ODOO_CLAVE=secreta\n")
    enviados = []
    monkeypatch.setattr(Odoo, "_rpc", lambda self, *a: enviados.append(a) or 7)
    odoo = Odoo.desde_entorno(archivo=archivo)
    assert enviados[0] == ("common", "authenticate", "lumak", "carlos", "secreta", {})
    odoo.avisar("respaldo", "5,5 MB")
    assert enviados[1][5:] == ("crm.lead", "secop_registrar_automatizacion", ["respaldo", "5,5 MB"], {})


def _copia(base, origen, **cambios):
    cols = [c[0] for c in base.con.sql("select * exclude (actualizado) from procesos limit 0").description]
    fila = base.con.execute("select * exclude (actualizado) from procesos where id_proceso = ?", [origen]).fetchone()
    return {**dict(zip(cols, fila)), "crudo": "{}", **cambios}


def test_it_publishes_the_niche_history_and_every_recent_process_with_its_bids(base):  # noqa: F811
    base.guardar_procesos([
        _copia(base, "REQ.1", id_proceso="REQ.VIEJO", id_portafolio="BDOS.VIEJO", nicho=False),
        _copia(base, "REQ.1", id_proceso="REQ.NUEVO", id_portafolio="BDOS.NUEVO", nicho=False,
               fecha_publicacion=date(2026, 9, 20), fecha_cierre=date(2026, 10, 2))])
    odoo = OdooFalso()
    assert publicar(base, odoo, hoy=date(2026, 9, 28), lote=8) == 21
    assert len(odoo.publicados) == 3, "en lotes"
    procesos = {p["secop_id"]: p for lote in odoo.publicados for p in lote}
    assert "REQ.NUEVO" in procesos and "REQ.VIEJO" not in procesos, "del nicho todo; fuera del nicho, solo lo reciente"
    assert procesos["REQ.NUEVO"]["fecha_cierre"] == "2026-10-02" and procesos["REQ.NUEVO"]["ofertas"] == []
    p = procesos["REQ.4"]  # el ganador ofertó 10 % bajo el presupuesto; el segundo, 5 %
    assert p["fecha_publicacion"] == "2025-01-05" and p["descuento_ganador"] == pytest.approx(10)
    assert [(o["puesto"], o["gano"], round(o["descuento"])) for o in p["ofertas"]] == [(1, 1, 10), (2, 0, 5)]


def test_advantages_arrive_as_tags_and_stars_that_sort_the_board(base):  # noqa: F811
    # Una alcaldía (0 o 1 ofertas en el 69 % de sus procesos del nicho), $30 M y una invitación que acepta la experiencia del socio
    alcaldia = {**SOFTWARE, "id_del_proceso": "CO1.REQ.911", "id_del_portafolio": "CO1.BDOS.911",
                "entidad": "ALCALDIA MUNICIPAL DE PRUEBA", "precio_base": "30000000"}
    socios = "La entidad tendrá en cuenta la experiencia individual de los socios de sociedades con menos de tres años. " * 20
    odoo = OdooFalso(experiencia=[35_524_267, 28_285_000])
    sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([alcaldia]), leer=lambda _: socios)
    assert set(odoo.etiquetas) == {"✓ Poca competencia", "✓ Tu experiencia alcanza", "✓ Acepta experiencia de socios"}
    (_, vals), = odoo.escritos()
    assert vals["priority"] == "3", "tres ventajas, tres estrellas: el tablero ordena por estrellas"
    mensaje = next(kw["body"] for _, method, _, kw in odoo.llamadas if method == "message_post")
    assert "un solo contrato" in mensaje


def test_entity_history_beats_its_type_and_experience_must_cover_the_budget(base):  # noqa: F811
    # Una alcaldía que en su historia recibe 4 ofertas por proceso no es «poca competencia», aunque sea alcaldía
    base.guardar_procesos([_copia(base, "REQ.5", id_proceso=f"REQ.H{i}", id_portafolio=f"BDOS.H{i}", nit_entidad="900200200",
                                  respuestas=4, fecha_cierre=date(2026, 3, 1)) for i in range(3)])
    competida = {**SOFTWARE, "id_del_proceso": "CO1.REQ.912", "id_del_portafolio": "CO1.BDOS.912",
                 "entidad": "ALCALDIA DE COMPETIDA", "nit_entidad": "900200200", "precio_base": "100000000"}
    odoo = OdooFalso(experiencia=[35_524_267, 28_285_000])
    sincronizar(base, odoo, "2026-09-25", hoy=date(2026, 9, 28), fetch=secop([competida]))
    assert odoo.etiquetas == {} and odoo.escritos() == [], "$100 M no se cubre con $63,8 M de experiencia"
