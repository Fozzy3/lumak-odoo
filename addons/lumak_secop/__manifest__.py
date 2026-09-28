{
    "name": "Lumak SECOP",
    "summary": "Operación de Lumak: licitaciones SECOP, cotizaciones, documentos de oferta, contratos, cobro, calendario legal y tablero de la empresa",
    "version": "19.0.1.9.0",
    "author": "Lumak Solutions S.A.S.",
    "license": "LGPL-3",
    "depends": ["crm", "sale_crm", "sale_project", "calendar", "account"],
    "data": [
        "security/ir.model.access.csv",
        "data/licitaciones.xml",
        "data/contratos.xml",
        "data/ventas.xml",
        "data/documentos.xml",
        "data/obligaciones.xml",
        "report/documentos_oferta.xml",
        "report/documentos_contrato.xml",
        "report/politica_datos.xml",
        "views/licitaciones.xml",
        "views/contratos.xml",
        "views/documentos.xml",
        "views/facturas.xml",
        "views/calendario.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            ("prepend", "lumak_secop/static/src/scss/lumak_variables.scss"),
        ],
        "web.assets_backend": [
            "lumak_secop/static/src/scss/secop.scss",
            "lumak_secop/static/src/dashboard/*",
        ],
    },
    "installable": True,
}
