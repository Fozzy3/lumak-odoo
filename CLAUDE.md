# Odoo local de Lumak

Odoo 19 Community en Docker para aprender y simular la operación de LUMAK SOLUTIONS S.A.S. (NIT 902.110.349-9, Bogotá, SIMPLE). No es producción: nada de aquí se factura de verdad.

- Arrancar: `docker compose up -d`. URL http://127.0.0.1:8069, base `lumak`, usuario `admin`.
- Apps: Contactos, CRM, Ventas, Facturación, Proyectos, localización colombiana (COP).
- Claude opera Odoo con el MCP `odoo` (API JSON-2 de Odoo 19, clave de API del admin que vence el 27 sep 2027).

## Reglas para simular

- Todo registro simulado lleva la etiqueta `SIM` (categoría de contacto o etiqueta de CRM), para poder filtrarlo o borrarlo después.
- Entidades públicas colombianas reales como clientes simulados están bien; personas naturales, inventadas.
- Antes de borrar o archivar algo, preguntar.
- Responder en español sencillo.

## CRM de licitaciones SECOP

- Configuración en `scripts/crm_secop.py` (idempotente, IDs externos `lumak.*`). Si se cambia algo del diseño, cambiarlo en el script y volver a correrlo; no crear a mano lo que el script ya crea.
- Diseño y fuentes: `docs/licitaciones-secop.md`. Un proceso = una oportunidad del equipo «Licitaciones SECOP»; lo ganado se ejecuta con la plantilla de proyecto «Plantilla – Contrato SECOP».
- Las propiedades de fecha y hora se guardan en UTC (Bogotá = UTC−5). Los planes de actividades cuentan días calendario, no hábiles.
- Módulo `addons/lumak_secop` (TDD: pruebas en `tests/`, correrlas en una base aparte `lumak_test`): importa desde el dataset `p6dx-8zbt` de datos.gov.co y agenda los planes por etapa usando la «Fecha de cierre esperada» (`date_deadline`). Tras cambiar Python: `-u lumak_secop` y `docker compose restart odoo`.
