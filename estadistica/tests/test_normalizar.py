from datetime import date

from secop_estadistica.normalizar import a_fecha, a_numero, clasificar, nit_base, oferta, proceso


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
