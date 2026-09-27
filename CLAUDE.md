# Odoo local de Lumak

Odoo 19 Community en Docker para aprender y simular la operación de LUMAK SOLUTIONS S.A.S. (NIT 902.110.349-9, Bogotá, SIMPLE). No es producción: nada de aquí se factura de verdad.

- Arrancar: `docker compose up -d`. URL http://127.0.0.1:8069, base `lumak`, usuario `admin`.
- Apps: Contactos, CRM, Ventas, Facturación, Proyectos, localización colombiana (COP).
- Claude opera Odoo con el MCP `odoo` (API JSON-2 de Odoo 19, clave de API del admin que vence el 27 sep 2027).

## Reglas para simular

- Todo registro simulado lleva la etiqueta `SIM` (categoría de contacto o etiqueta de CRM), para poder filtrarlo o borrarlo después.
- Entidades públicas colombianas reales como clientes simulados están bien; personas naturales, inventadas.
- Antes de borrar o archivar algo, preguntar.
- Odoo se deja como viene: el flujo de licitaciones SECOP en el CRM por etapas se arma después, cuando Carlos lo pida.
- Responder en español sencillo.
