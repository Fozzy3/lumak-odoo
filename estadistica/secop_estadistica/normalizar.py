"""De filas de datos.gov.co (todo texto) a registros limpios. El clasificador de nicho viene del estudio de mercado
de septiembre de 2026 (repo secop, analysis/classify2.py)."""
import json
import re
import unicodedata
from datetime import date


def norm(texto):
    texto = (texto or "").lower()
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def nit_base(valor):
    """NIT sin puntos ni dígito de verificación, para cruzar el mismo proveedor escrito de varias formas."""
    digitos = re.sub(r"\D", "", valor or "")
    if not digitos:
        return None
    # Los NIT de empresa tienen 9 dígitos y empiezan por 8 o 9; con 10, el último es el dígito de verificación
    if len(digitos) == 10 and digitos[0] in "89":
        return digitos[:9]
    return digitos


def a_numero(valor):
    try:
        return float(valor) if valor not in (None, "") else None
    except ValueError:
        return None


def a_entero(valor):
    n = a_numero(valor)
    return int(n) if n is not None else None


def a_fecha(valor):
    return date.fromisoformat(valor[:10]) if valor else None


TIPOS_ENTIDAD = [
    ("alcaldia", r"alcald|municipio de|distrito"), ("gobernacion", r"gobernaci|departamento de(?! policia)"),
    ("personeria", r"personer"), ("contraloria", r"contralor"), ("concejo", r"concejo|asamblea"),
    ("hospital_ese", r"hospital|\bese\b|e\.s\.e|salud|clinica|red de salud"),
    ("universidad", r"universidad|institucion universitaria|tecnologico|politecnico|colegio mayor|escuela superior"),
    ("servicios_publicos", r"servicios publicos|acueducto|aseo|energia|empresa de|aguas"),
    ("instituto_desc", r"instituto|fondo|agencia|corporacion|caja de|loteria|terminal|beneficencia"),
    ("nacional", r"ministerio|superintendencia|departamento administrativo|unidad administrativa|policia|ejercito|armada|"
                 r"fiscalia|procuraduria|registraduria|icbf|sena|invias"),
]
ETIQUETAS = [
    ("ia_chatbot", r"chatbot|chat bot|asistente virtual|inteligencia artificial|machine learning|aprendizaje autom|"
                   r"procesamiento de lenguaje|agente virtual|bot de whatsapp|\bia\b|generativa"),
    ("analitica", r"analitica|ciencia de datos|tablero de control|dashboard|power bi|big data|mineria de datos|visualizacion de datos"),
    ("automatizacion", r"automatizaci(?!on industrial)|\brpa\b|transcripci"),
    ("web", r"pagina web|sitio web|portal web|portal institucional|sede electronica|1519"),
    ("app_dev", r"desarrollo de software|desarrollo del software|desarrollo de un software|desarrollo e implementaci|"
                r"desarrollo de aplic|desarrollo de una aplic|desarrollo de un aplicativo|desarrollo del aplicativo|"
                r"desarrollo de sistema|desarrollo de un sistema|desarrollo del sistema|aplicativo|aplicacion web|"
                r"aplicacion movil|app movil|implementacion de un sistema de informacion|implementacion del sistema de informacion|"
                r"software a la medida|desarrollo de modulo|implementacion de software|adquisicion e implementacion de (un )?software"),
    ("soporte_sw", r"(soporte|mantenimiento|actualizacion|parametrizaci)[^.]{0,60}(software|sistema de informacion|aplicativo|"
                   r"plataforma|pagina web|sitio web|portal)|(software|sistema de informacion|aplicativo|plataforma|pagina web|"
                   r"sitio web|portal)[^.]{0,60}(soporte|mantenimiento|actualizacion)"),
]
NUCLEO = {"ia_chatbot", "analitica", "automatizacion", "web", "app_dev", "soporte_sw"}
HARDWARE = (r"materiales|elementos|equipos de|kit\b|suministro de|\bepp\b|ferreter|herramientas|insumos|repuestos|impresora|"
            r"computador|portatil|tablet|camara|ups\b|aire acondicionado|cableado|papeleria|dotacion|vehiculo|mobiliario|"
            r"alimentos|muebles|tinta|toner|scanner|escaner|licencia|antivirus|office 365|microsoft|adobe|autocad|arcgis|"
            r"renovacion de|suscripcion|hosting|dominio|firma digital|certificado digital|correo electronico|nube|cloud|"
            r"infraestructura tecnol|redes|conectividad|internet|telefon|publicidad|pauta|redes sociales|community|fotograf|"
            r"video|impresion|litogr")


# Reventa de licencias, certificados y suscripciones: no es software a la medida aunque diga «soporte de la plataforma»
REVENTA = (r"licencia|antivirus|firma digital|firma electronica|certificado digital|certificados digitales|\bssl\b|"
           r"\btokens?\b|criptografic|office 365|microsoft|google workspace|adobe|autocad|arcgis|suscripci|renovacion de")
# Solo el desarrollo explícito rescata un proceso de reventa («para uso en el aplicativo SIIF» no es desarrollo)
DESARROLLO = r"desarroll|a la medida|construccion de (un |una |el |la )?(software|sistema|aplicativo|plataforma)"


def segmento(codigo):
    m = re.search(r"(\d{8})", codigo or "")
    return m.group(1)[:2] if m else ""


def tipo_entidad(nombre):
    n = norm(nombre)
    return next((tipo for tipo, rx in TIPOS_ENTIDAD if re.search(rx, n)), "otro")


def clasificar(texto, codigo, tipo_contrato):
    """(es del nicho de Lumak, etiquetas): software a la medida, soporte de software, web, analítica, IA, automatización."""
    t = norm(texto)
    etiquetas = [e for e, rx in ETIQUETAS if re.search(rx, t)]
    nicho = bool(NUCLEO & set(etiquetas))
    if re.search(HARDWARE, t) and not {"ia_chatbot", "app_dev", "web", "soporte_sw"} & set(etiquetas):
        nicho = False
    if re.search(REVENTA, t) and not re.search(DESARROLLO, t):
        nicho = False
    if segmento(codigo) not in ("43", "80", "81", "82", "84", ""):
        nicho = False
    if tipo_contrato in ("Suministros", "Obra", "Interventoría", "Arrendamiento de muebles", "Servicios financieros"):
        nicho = False
    return nicho, etiquetas


def proceso(fila):
    """Fila de p6dx-8zbt -> (proceso, adjudicación o None)."""
    texto = f"{fila.get('nombre_del_procedimiento', '')} {fila.get('descripci_n_del_procedimiento', '')}"
    nicho, etiquetas = clasificar(texto, fila.get("codigo_principal_de_categoria"), fila.get("tipo_de_contrato"))
    p = {
        "id_proceso": fila["id_del_proceso"], "id_portafolio": fila.get("id_del_portafolio"),
        "referencia": fila.get("referencia_del_proceso"), "entidad": fila.get("entidad"), "nit_entidad": nit_base(fila.get("nit_entidad")),
        "orden_entidad": fila.get("ordenentidad"), "departamento": fila.get("departamento_entidad"), "ciudad": fila.get("ciudad_entidad"),
        "modalidad": fila.get("modalidad_de_contratacion"), "tipo_contrato": fila.get("tipo_de_contrato"),
        "unspsc": fila.get("codigo_principal_de_categoria"), "segmento": segmento(fila.get("codigo_principal_de_categoria")),
        "nombre": fila.get("nombre_del_procedimiento"), "descripcion": fila.get("descripci_n_del_procedimiento"),
        "fase": fila.get("fase"), "estado": fila.get("estado_del_procedimiento"),
        "fecha_publicacion": a_fecha(fila.get("fecha_de_publicacion_del")), "fecha_cierre": a_fecha(fila.get("fecha_de_recepcion_de")),
        "fecha_adjudicacion": a_fecha(fila.get("fecha_adjudicacion")), "precio_base": a_numero(fila.get("precio_base")),
        "respuestas": a_entero(fila.get("respuestas_al_procedimiento")), "n_lotes": a_entero(fila.get("numero_de_lotes")),
        "duracion": f"{fila.get('duracion', '')} {fila.get('unidad_de_duracion', '')}".strip() or None,
        "adjudicado": fila.get("adjudicado") == "Si", "url": (fila.get("urlproceso") or {}).get("url"),
        "nicho": nicho, "etiquetas": etiquetas, "tipo_entidad": tipo_entidad(fila.get("entidad")),
        "crudo": json.dumps(fila, ensure_ascii=False),
    }
    adj = None
    if fila.get("id_adjudicacion") and fila.get("id_adjudicacion") != "No Adjudicado":
        adj = {"id_adjudicacion": fila["id_adjudicacion"], "id_proceso": fila["id_del_proceso"],
               "nit": nit_base(fila.get("nit_del_proveedor_adjudicado")), "nombre": fila.get("nombre_del_proveedor"),
               "valor": a_numero(fila.get("valor_total_adjudicacion"))}
    return p, adj


def oferta(fila):
    """Fila agrupada de wi7w-2nvm (una por oferta; `filas` es cuántas veces venía repetida)."""
    return {"id_oferta": fila["identificador_de_la_oferta"], "id_portafolio": fila.get("id_del_proceso_de_compra"),
            "nit": nit_base(fila.get("nit_del_proveedor")), "nombre": fila.get("nombre_proveedor"),
            "valor": a_numero(fila.get("valor_de_la_oferta")), "fecha": a_fecha(fila.get("fecha_de_registro")),
            "invitacion_directa": fila.get("invitacion_directa") == "Si", "filas": a_entero(fila.get("filas")) or 1}


def contrato(fila):
    """Fila de jbjy-vk9h: el valor firmado y el estado del contrato que salió del proceso."""
    return {"id_contrato": fila["id_contrato"], "id_portafolio": fila.get("proceso_de_compra"),
            "nit": nit_base(fila.get("documento_proveedor")), "nombre": fila.get("proveedor_adjudicado"),
            "valor": a_numero(fila.get("valor_del_contrato")), "estado": fila.get("estado_contrato"),
            "fecha_firma": a_fecha(fila.get("fecha_de_firma")), "es_pyme": fila.get("es_pyme") == "Si"}
