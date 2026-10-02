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


SAAS = (r"software como servicio|software as a service|\bsaas\b|"
        r"(arrendamiento|alquiler|arriendo)[^.]{0,40}(software|aplicativo|sistema de informacion)")
CAPACITACION = (r"\b(capacitaci|diplomado|curso|taller|formacion|entrenamiento)\w*[^.]{0,80}(inteligencia artificial|\bia\b|"
                r"competencias digitales|habilidades digitales|alfabetizacion digital|herramientas digitales|"
                r"tecnologias de la informacion|\btic\b|python|ciencia de datos|analitica de datos|power bi|ofimatica)")
# Reventa de licencias, suscripciones, certificados y hosting: Lumak la puede hacer, pero no es nicho (sus precios son otros)
LICENCIAS = (r"(licencia|licenciamiento|suscripci)\w*[^.]{0,60}(software|de uso|plataforma|antivirus|office|microsoft|google|adobe|"
             r"autocad|arcgis|nube|cloud|\bia\b|inteligencia artificial|herramienta)|software[^.]{0,40}(licencia|suscripci)|antivirus|"
             r"office 365|microsoft 365|google workspace|creative cloud|\badobe\b|autocad|arcgis|hosting|alojamiento web|\bssl\b|"
             r"certificados? digital|firma digital|firma electronica|correos? (electronicos? )?corporativos?|servicios? (en la |de )?nube|"
             r"cloud computing")
EQUIPO = r"computador|portatil|impresora|equipos? de computo|tablet|escaner|scanner|\bups\b|camara|videobeam|televisor|mobiliario|papeleria|toner"
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
                   r"procesamiento de lenguaje|agente virtual|whatsapp|\bia\b|generativa"),
    ("analitica", r"analitica|ciencia de datos|tablero de control|dashboard|power bi|big data|mineria de datos|visualizacion de datos"),
    ("automatizacion", r"automatizaci(?!on industrial)|\brpa\b|transcripci"),
    ("web", r"pagina web|sitio web|portal web|portal institucional|sede electronica|1519|plataforma web|intranet"),
    ("app_dev", r"desarrollo de software|desarrollo del software|desarrollo de un software|desarrollo e implementaci|"
                r"desarrollo de aplic|desarrollo de una aplic|desarrollo de un aplicativo|desarrollo del aplicativo|"
                r"desarrollo de sistema|desarrollo de un sistema|desarrollo del sistema|aplicativo|aplicacion web|"
                r"aplicacion movil|app movil|implementacion de un sistema de informacion|implementacion del sistema de informacion|"
                r"software a la medida|desarrollo de modulo|implementacion de software|adquisicion e implementacion de (un )?software|"
                r"desarrollo[^.]{0,60}modulo|nuevas funcionalidades|"
                r"implementa\w*[^.]{0,60}\b(un|una|el|la) (software|sistema de informacion|aplicativo|plataforma)|"
                r"(diseno|diagnostico)[^.]{0,80}(sistemas? de informacion|software|aplicativo)|"
                r"migracion de (los |las )?(aplicativos|sistemas|datos|bases de datos)"),
    ("soporte_sw", r"(soporte|mantenimiento|actualizacion|parametrizaci|evolutivo)[^.]{0,120}(software|sistemas? de informacion|"
                   r"aplicativo|plataforma|pagina web|sitio web|portal)|(software|sistemas? de informacion|aplicativo|plataforma|"
                   r"pagina web|sitio web|portal)[^.]{0,60}(soporte|mantenimiento|actualizacion|evolutivo)"),
    ("saas", SAAS),
    # Línea secundaria: no entra al nicho (sus precios no se parecen a los del software), llega a Odoo con su etiqueta
    ("capacitacion", CAPACITACION),
    ("reventa", LICENCIAS),
]
NUCLEO = {"ia_chatbot", "analitica", "automatizacion", "web", "app_dev", "soporte_sw", "saas"}
# El texto no deja duda de que es software: vale aunque SECOP lo haya puesto en otra categoría o como suministro
FUERTE = (r"desarroll\w*[^.]{0,60}(software|aplicativo|aplicacion|sistemas? de informacion|plataforma (web|digital|tecnologica)|"
          r"portal|geoportal|geovisor|pagina web|sitio web|modulo)|chatbot|whatsapp|software a la medida|\bsaas\b|"
          r"software como servicio|geoportal|geovisor|migracion de (los |las )?(aplicativos|sistemas de informacion)")
# Convenios de asociación y contratos del Decreto 092: solo con entidades sin ánimo de lucro, una SAS no puede
ESAL = r"\b(aunar|unir) (esfuerzos|recursos)"
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


# Señales de que el proceso casi seguro no es para Lumak. Marcan, no descartan: «página web de la emisora» sí es venta.
# ponytail: marcas vistas en el nicho 2018-2026 más las grandes de seguridad; añadir la que aparezca en otro pliego
ALERTAS = [
    ("Medios", "Parece de medios de comunicación (periódico, emisora): suele pedir ser el medio y experiencia en pauta.",
     r"periodico|emisora|perifoneo|medio de comunicacion|alta circulacion|del mismo medio"),
    ("Marca", "Nombra un producto comercial: suele pedir ser distribuidor autorizado del fabricante y técnicos certificados.",
     r"\b(aranda|oracle|sap|ibm|vmware|tableau|siigo|darktrace|cellebrite|hopex|hanwell|sistelab|isoclean|veeam|fortinet|"
     r"fortigate|sophos|kaspersky|eset|citrix|cisco|qlik|esri)\b"),
    ("Producto", "Piden un software ya hecho (arriendo o SaaS): hay que tenerlo o montar uno libre antes del cierre.", SAAS),
    ("Capacitación", "Es de capacitación, la línea secundaria de Lumak.", CAPACITACION),
]


def alertas(texto):
    """[(etiqueta, motivo)] de las señales que aparecen en el nombre o la descripción."""
    t = norm(texto)
    return [(nombre, motivo) for nombre, motivo, rx in ALERTAS if re.search(rx, t)]


# Casi todas las invitaciones nombran el RUP sin exigirlo (las MiPyME «podrán» acreditarse con él, «no se exige»,
# «NO APLICA»). Exigirlo se dice con estas fórmulas, vistas en 31 invitaciones del nicho (jun-sep 2026)
RUP = r"\brup\b|registro unico de proponentes"
EXIGE_RUP = (r"obligatorio que (este|se encuentre) (inscrito|registrado)|(debe|debera|deberan) (estar|encontrarse) "
             r"(inscrito|registrado)s? en el|el rup no se encuentre|ademas del rup")
NO_EXIGE_RUP = r"\bno\b[^.]{0,60}(exig|requier|requerira|necesari|aplica)|mipyme|podran acreditar|podra acreditar"


def exige_rup(texto):
    """¿Los documentos del proceso piden RUP? Se decide frase por frase para no confundirlo con las menciones de rutina."""
    return any(re.search(EXIGE_RUP, f) and not re.search(NO_EXIGE_RUP, f)
               for f in re.split(r"\.\s", norm(texto)) if re.search(RUP, f))


# Una sociedad de menos de tres años puede acreditar la experiencia de sus socios (Decreto 1082 de 2015, art.
# 2.2.1.1.1.5.2), pero en mínima cuantía solo vale si la invitación lo dice
SOCIOS = r"experiencia[^.]{0,80}(socios|accionistas|constituyentes)"


def acepta_experiencia_socios(texto):
    """¿La invitación deja acreditar la experiencia de los socios? Frase por frase, para no tomar una negación por un sí."""
    return any(re.search(SOCIOS, f) and not re.search(r"\bno\b[^.]{0,40}" + SOCIOS, f) for f in re.split(r"\.\s", norm(texto)))


def segmento(codigo):
    m = re.search(r"(\d{8})", codigo or "")
    return m.group(1)[:2] if m else ""


def tipo_entidad(nombre):
    n = norm(nombre)
    return next((tipo for tipo, rx in TIPOS_ENTIDAD if re.search(rx, n)), "otro")


def clasificar(texto, codigo, tipo_contrato):
    """(es del nicho de Lumak, etiquetas): software a la medida, soporte de software, web, analítica, IA, automatización, SaaS.
    «capacitacion» (formación en TIC) y «reventa» (licencias, suscripciones) marcan lo que Lumak puede hacer fuera del nicho."""
    t = norm(texto)
    etiquetas = [e for e, rx in ETIQUETAS if re.search(rx, t)]
    nicho = bool(NUCLEO & set(etiquetas))
    fuerte = bool(re.search(FUERTE, t))
    if re.search(HARDWARE, t) and not {"ia_chatbot", "app_dev", "web", "soporte_sw", "saas"} & set(etiquetas):
        nicho = False
    if re.search(REVENTA, t) and not re.search(DESARROLLO, t):
        nicho = False
    if segmento(codigo) not in ("43", "80", "81", "82", "84", "") and not fuerte:
        nicho = False
    if tipo_contrato in ("Obra", "Interventoría", "Arrendamiento de muebles", "Servicios financieros") or (
            tipo_contrato == "Suministros" and not fuerte):
        nicho = False
    esal = bool(re.search(ESAL, t))
    if esal:
        nicho = False
    if "capacitacion" in etiquetas and (esal or tipo_contrato in ("Compraventa", "Suministros")):
        etiquetas.remove("capacitacion")
    if "reventa" in etiquetas and (nicho or esal or re.search(EQUIPO, t) or segmento(codigo) not in ("43", "81", "") or
                                   tipo_contrato in ("Obra", "Interventoría")):
        etiquetas.remove("reventa")
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
