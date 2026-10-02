from datetime import date

from secop_estadistica.normalizar import (a_fecha, a_numero, acepta_experiencia_socios, alertas, clasificar, exige_rup,
                                         nit_base, oferta, proceso)


def test_nit_base_ignores_check_digit_and_format():
    assert nit_base("900.664.738-2") == "900664738"
    assert nit_base("9006647382") == "900664738"  # NIT de empresa con dígito de verificación pegado
    assert nit_base("900664738") == "900664738"
    assert nit_base("1084259682") == "1084259682"  # cédula: no se recorta
    assert nit_base("No Definido") is None
    assert nit_base(None) is None


def test_numbers_and_dates_from_socrata():
    assert a_numero("42292000.00") == 42_292_000.0
    assert a_numero("") is None
    assert a_fecha("2025-03-20T00:00:00.000") == date(2025, 3, 20)
    assert a_fecha(None) is None


def test_niche_is_software_not_hardware():
    assert clasificar("Desarrollo e implementación de un sistema de información para PQRSD", "V1.81111500", "Prestación de servicios")[0]
    assert clasificar("Soporte y mantenimiento del software de nómina", "V1.81112200", "Prestación de servicios")[0]
    assert not clasificar("Suministro de computadores portátiles e impresoras", "V1.43211500", "Compraventa")[0]
    nicho, etiquetas = clasificar("Chatbot con inteligencia artificial para atención ciudadana", "V1.81111500", "Prestación de servicios")
    assert nicho and "ia_chatbot" in etiquetas
    # Reventa: certificados, licencias y suscripciones no son software a la medida, aunque digan «soporte de la plataforma»
    assert not clasificar("Adquisición de certificados de firma digital y soporte de la plataforma", "V1.43233200", "Compraventa")[0]
    assert not clasificar("Renovación de licencias y soporte del software antivirus", "V1.43233200", "Prestación de servicios")[0]
    assert clasificar("Desarrollo de un aplicativo con licencia de uso a perpetuidad", "V1.81111500", "Prestación de servicios")[0]
    # Casos reales que se colaban: nombran un aplicativo o un sitio web, pero compran tokens o certificados
    assert not clasificar("Adquirir tokens para uso en el aplicativo externo SIIF y de firma digital para los funcionarios",
                          "V1.43233200", "Compraventa")[0]
    assert not clasificar("Adquirir certificado SSL con servicio de soporte técnico para el sitio web de la alcaldía",
                          "V1.81112000", "Prestación de servicios")[0]


def test_niche_catches_custom_work_said_in_other_words():
    # Casos reales de abr-sep 2026 que el clasificador dejaba fuera
    for texto, codigo, tipo in [
        ("Desarrollo de nuevas funcionalidades, optimización de módulos existentes y capacitación del personal en el sistema",
         "V1.81112000", "Prestación de servicios"),  # Imprenta Nacional
        ("Diseño, desarrollo, implementación e integración de un módulo del sistema de información y atención al usuario",
         "UNSPECIFIED", "Prestación de servicios"),  # Guaca
        ("Soporte, alojamiento, actualización, mantenimiento preventivo, correctivo y evolutivo que incluya hosting en la "
         "modalidad cloud computing de los sistemas de información", "V1.81112000", "Otro"),  # Artesanías de Colombia
        ("Plataforma web y app de monitoreo ambiental comunitario", "V1.81112000", "Prestación de servicios"),  # Cortolima
        ("Consultoría para el diagnóstico, diseño y formulación del sistema de información exógena tributaria municipal",
         "V1.80101500", "Consultoría"),  # Calima
        ("Adquirir, implementar y poner en funcionamiento un software para el Centro de Documentación", "V1.81111500", "Compraventa"),
        # Fuera de los segmentos de tecnología, pero el texto no deja duda
        ("Desarrollo e implementación del geoportal verde y fortalecimiento del geovisor ambiental", "V1.86101700",
         "Prestación de servicios"),
        ("Habilitación y operación del canal de atención digital mediante la plataforma WhatsApp Business API", "V1.93151500",
         "Prestación de servicios"),
        ("Prestar el servicio de migración de los aplicativos históricos", "V1.80111600", "Suministros"),
    ]:
        assert clasificar(texto, codigo, tipo)[0], texto


def test_rented_software_and_saas_are_in_the_niche_but_flagged():
    nicho, etiquetas = clasificar("Alquiler de software para la correspondencia de la ventanilla única", "V1.43232300", "Otro")
    assert nicho and "saas" in etiquetas
    assert [a[0] for a in alertas("Contratar en modalidad SaaS (software como servicio) la gestión de correspondencia")] == ["Producto"]


def test_what_only_looks_like_software_stays_out():
    # Convenios con entidades sin ánimo de lucro: una SAS no puede ser el asociado
    assert not clasificar("Aunar esfuerzos para el desarrollo e implementación de una plataforma web", "V1.81111500",
                          "Decreto 092 de 2017")[0]
    assert not clasificar("Mantenimiento preventivo de la plataforma salvaescaleras", "V1.72101500", "Prestación de servicios")[0]
    assert not clasificar("Compra de ropa de trabajo en cumplimiento del artículo 79 de IA convención colectiva",
                          "V1.53101500", "Compraventa")[0]
    assert not clasificar("Arrendamiento de plataforma de comunicaciones vía radio con torre y antenas", "V1.81161700",
                          "Prestación de servicios")[0]


def test_digital_skills_training_is_tagged_apart_from_the_software_niche():
    nicho, etiquetas = clasificar("Diplomado en analítica de datos para servidores públicos", "V1.86101700", "Prestación de servicios")
    assert not nicho and "capacitacion" in etiquetas, "no entra al nicho: no se mezcla con los precios de software"
    assert [a[0] for a in alertas("Capacitación en inteligencia artificial y TIC para docentes")] == ["Capacitación"]
    assert "capacitacion" not in clasificar("Compraventa de equipos para la formación en TIC", "V1.43211500", "Compraventa")[1]
    assert "capacitacion" not in clasificar("Auditoría al sistema de gestión del Fondo Único de Tecnologías de la Información",
                                            "V1.84111600", "Consultoría")[1], "«formación» no está en «información»"
    assert "capacitacion" not in clasificar("Aunar esfuerzos para cursos en habilidades digitales", "V1.86101700",
                                            "Decreto 092 de 2017")[1]


def test_licence_and_subscription_resale_is_tagged_apart_from_the_niche():
    # SENA Cesar, 30 sep 2026: 25 suscripciones de Claude Code, Google AI Pro y Figma
    nicho, etiquetas = clasificar("Adquisición de suscripciones de inteligencia artificial en la nube para Tecnoparque",
                                  "UNSPECIFIED", "Prestación de servicios")
    assert not nicho and "reventa" in etiquetas, "no entra al nicho: sus precios no son los del software a la medida"
    for texto, codigo in [("Renovación de licencias Adobe Creative Cloud por un año", "V1.43232300"),
                          ("Adquirir certificados digitales SSL wildcard", "V1.43233200"),
                          ("Renovación de la suscripción de Google Workspace por un año", "V1.81112000")]:
        assert "reventa" in clasificar(texto, codigo, "Prestación de servicios")[1], texto
    assert "reventa" not in clasificar("Trámite de la licencia ambiental", "V1.77101500", "Prestación de servicios")[1]
    assert "reventa" not in clasificar("Suministro de computadores portátiles con licencia de Office", "V1.43211500",
                                       "Compraventa")[1], "es hardware"
    assert "reventa" not in clasificar("Desarrollo de un aplicativo con licencia de uso a perpetuidad", "V1.81111500",
                                       "Prestación de servicios")[1], "es desarrollo"


def test_warnings_flag_likely_dead_ends_without_dropping_them_from_the_niche():
    # Casos reales de septiembre de 2026: pedían ser el periódico o ser distribuidor de Aranda
    medios = "Publicación en periódico de alta circulación regional, portal web, redes sociales del mismo medio"
    assert clasificar(medios, "V1.82101500", "Prestación de servicios")[0], "sigue en el nicho: no se pierde nada"
    assert [a[0] for a in alertas(medios)] == ["Medios"]
    assert [a[0] for a in alertas("Soporte, actualización y configuración de la plataforma ARANDA")] == ["Marca"]
    # El software libre no es de una marca: cualquiera puede darle soporte
    assert alertas("Soporte y mantenimiento de la plataforma Moodle") == []
    assert alertas("Actualización y soporte técnico del sistema de información RIPS") == []
    assert alertas("Ajustes al sistema de francisco") == [], "palabra completa: «cisco» no está en «francisco»"


def test_rup_is_flagged_only_when_the_documents_require_it():
    # Frases reales de 31 invitaciones del nicho (jun-sep 2026)
    assert exige_rup("Para este caso, no se exigirá ninguna clase de registro mercantil. Sin embargo, si será obligatorio que "
                     "esté registrado en el Registro Único de Proponentes, de acuerdo a lo solicitado en el presente pliego")
    assert exige_rup("g. Cuando el RUP no se encuentre renovado con vigencia según normatividad, ni esté en firme para el "
                     "momento de la adjudicación. h. La presentación de ofertas parciales")
    assert exige_rup("que pretendan acreditar la experiencia de sus socios, accionistas o constituyentes, de conformidad con el "
                     "numeral 2.5 del artículo 2.2.1.1.1.5.2. del Decreto 1082 de 2015, además del RUP deben adjuntar un documento")
    # Lo que casi todas dicen sin exigirlo
    assert not exige_rup("PARÁGRAFO 1. En todo caso, las Mipyme también podrán acreditar esta condición con la copia del "
                         "certificado del Registro Único de Proponentes, el cual deberá encontrarse vigente y en firme")
    assert not exige_rup("Nota 4. Aunque en el presente proceso no se exige el RUP, las Mipyme también podrán acreditar esta "
                         "condición con la copia del certificado del Registro Único de Proponentes")
    assert not exige_rup("para el presente proceso no es necesario como requisito habilitante la inscripción en el RUP")
    assert not exige_rup("1.5. Registro Único de Proponentes (RUP) NO APLICA 1.6. Registro Único Tributario (RUT)")
    assert not exige_rup("A los proponentes que deban estar inscritos en el Registro Único de Proponentes, el INSTITUTO les "
                         "hará la verificación del cumplimiento de los requisitos")
    assert not exige_rup("")


def test_partners_experience_counts_only_when_the_invitation_accepts_it():
    # Caldas, MIC-SED-054-2026 (sep 2026), y la fórmula del Decreto 1082 que copian muchas invitaciones
    assert acepta_experiencia_socios("G. La entidad tendrá en cuenta la experiencia individual de los accionistas, socios o "
                                     "constituyentes de las sociedades con menos de tres años de constituida.")
    assert acepta_experiencia_socios("que pretendan acreditar la experiencia de sus socios, accionistas o constituyentes, de "
                                     "conformidad con el numeral 2.5 del artículo 2.2.1.1.1.5.2. del Decreto 1082 de 2015")
    assert not acepta_experiencia_socios("No se tendrá en cuenta la experiencia de los socios del proponente.")
    assert not acepta_experiencia_socios("El proponente debe acreditar experiencia en contratos similares.")
    assert not acepta_experiencia_socios("")


# Fila real (recortada) de p6dx-8zbt y de wi7w-2nvm
FILA_PROCESO = {
    "id_del_proceso": "CO1.REQ.7996823", "id_del_portafolio": "CO1.BDOS.7857804", "referencia_del_proceso": "MC-01-2025",
    "entidad": "ALCALDIA MUNICIPAL DE PRUEBA", "nit_entidad": "800100200", "ordenentidad": "Territorial",
    "departamento_entidad": "Cundinamarca", "ciudad_entidad": "Chía", "modalidad_de_contratacion": "Mínima cuantía",
    "tipo_de_contrato": "Prestación de servicios", "codigo_principal_de_categoria": "V1.81111500",
    "nombre_del_procedimiento": "Soporte del sistema de información de PQRSD", "descripci_n_del_procedimiento": "Soporte",
    "fase": "Presentación de oferta", "estado_del_procedimiento": "Seleccionado",
    "fecha_de_publicacion_del": "2025-03-10T00:00:00.000", "fecha_de_recepcion_de": "2025-03-17T00:00:00.000",
    "fecha_adjudicacion": "2025-03-25T00:00:00.000", "precio_base": "42292000", "respuestas_al_procedimiento": "10",
    "numero_de_lotes": "0", "adjudicado": "Si", "id_adjudicacion": "CO1.AWD.2231746",
    "nit_del_proveedor_adjudicado": "901178261", "nombre_del_proveedor": "HDC Soporte a la Ingeniería SAS",
    "valor_total_adjudicacion": "42292000", "urlproceso": {"url": "https://community.secop.gov.co/x"},
}


def test_process_row_maps_to_columns_and_award():
    p, adj = proceso(FILA_PROCESO)
    assert p["id_proceso"] == "CO1.REQ.7996823" and p["id_portafolio"] == "CO1.BDOS.7857804"
    assert p["precio_base"] == 42_292_000.0 and p["respuestas"] == 10 and p["adjudicado"] is True
    assert p["fecha_publicacion"] == date(2025, 3, 10) and p["segmento"] == "81"
    assert p["nicho"] is True and p["tipo_entidad"] == "alcaldia"
    assert adj == {"id_adjudicacion": "CO1.AWD.2231746", "id_proceso": "CO1.REQ.7996823", "nit": "901178261",
                   "nombre": "HDC Soporte a la Ingeniería SAS", "valor": 42_292_000.0}


def test_offer_row_keeps_how_many_times_socrata_repeated_it():
    o = oferta({"identificador_de_la_oferta": "CO1.RPL.4768862", "id_del_proceso_de_compra": "CO1.BDOS.7857804",
                "nit_del_proveedor": "901323318", "nombre_proveedor": "MYH INGENIERIA SAS", "valor_de_la_oferta": "38062800.00",
                "fecha_de_registro": "2025-03-20T00:00:00.000", "invitacion_directa": "No", "filas": "92"})
    assert o == {"id_oferta": "CO1.RPL.4768862", "id_portafolio": "CO1.BDOS.7857804", "nit": "901323318",
                 "nombre": "MYH INGENIERIA SAS", "valor": 38_062_800.0, "fecha": date(2025, 3, 20),
                 "invitacion_directa": False, "filas": 92}
