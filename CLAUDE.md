# Odoo local de Lumak

Odoo 19 Community en Docker para aprender y simular la operación de LUMAK SOLUTIONS S.A.S. (NIT 902.110.349-9, Bogotá, SIMPLE). No es producción: nada de aquí se factura de verdad.

- Arrancar: `docker compose up -d`. URL http://127.0.0.1:8069, base `lumak`, usuario `admin`.
- Claude opera Odoo con el MCP `odoo` (API JSON-2 de Odoo 19, clave de API del admin que vence el 27 sep 2027).
- El plan de la empresa y el recorrido completo en Odoo: `docs/plan-operacion-lumak.md`. Mantenerlo al día cuando cambie el diseño.

## Reglas para simular

- Todo registro simulado lleva la etiqueta `SIM` (categoría de contacto o etiqueta de CRM), para poder filtrarlo o borrarlo después.
- Entidades públicas colombianas reales como clientes simulados están bien; personas naturales, inventadas.
- Antes de borrar o archivar datos del usuario, preguntar.
- Los datos personales (cédula, dirección, teléfono) viven solo en la base local. Los documentos que los llevan se guardan en `privado/`, que git ignora.
- Responder en español sencillo.
- Solo software libre y sin costo (Odoo Community y OCA, soluciones gratuitas de la DIAN). Decir claro lo que sí cuesta.

## Módulo `addons/lumak_secop`

- **Toda la configuración vive en el módulo** (`data/`, IDs `lumak_secop.*`), no en scripts. Lo que el usuario edita (productos, kit, fechas legales) va en bloques `noupdate`.
- Carpetas por capacidad. En `models/`:
  - `licitaciones.py`: procesos, importación, planes y tablero de licitaciones.
  - `contratos.py`: cotización, adjudicación, proyecto e impuestos.
  - `documentos.py`: kit y paquete de oferta.
  - `ejecucion.py`: contrato y experiencia.
  - `facturas.py`, `calendario.py` y `tablero.py` (panel de empresa).

  Cada una tiene su `views/`, `report/` y prueba en `tests/`.
- TDD: pruebas en `tests/`, en una base aparte `lumak_test`. Tras cambiar Python, XML o SCSS: `-u lumak_secop` y `docker compose restart odoo`.
- Cambios de datos en la base real: migración en `migrations/<versión>/`. Probarla antes en una copia (`createdb -T lumak lumak_copy`): los IDs sin `noupdate` que falten en el XML se borran al actualizar.

## Base estadística `estadistica/`

- Histórico de mínima cuantía de SECOP II (software y TIC) con cada oferta, en DuckDB (`estadistica/datos/secop.duckdb`, fuera de git). Guía completa en `estadistica/README.md`.
- Se actualiza cada lunes con el temporizador de `estadistica/systemd/`. Tras una carga interrumpida: `uv run python -m secop_estadistica completar`.
- TDD con `uv run pytest`. DuckDB admite un solo proceso escribiendo: mientras carga, leer una copia del archivo.
- Las ofertas vienen repetidas una vez por renglón de la lista de precios: se agrupan en el servidor. Se unen al proceso por el portafolio (`CO1.BDOS…`).

## Diseño y gotchas

- En las vistas, el color se reserva para la urgencia: rojo hoy/mañana o vencido, ámbar pronto, verde con tiempo. La modalidad va en gris. Colores Lumak: tinta #1F2A44, ámbar #E8A33D.
- La fecha de cierre es `date_deadline`; la hora, `secop_hora_cierre` (hora de Bogotá). Los planes de actividades cuentan días calendario.
- Los documentos de la oferta llevan línea de firma, **no imagen de firma**: la CCE puede tomar una imagen pegada como documento sin firma (`docs/investigacion/documentos-secop.md`, sección 3).
- SIMPLE: tarifa 5,9 % hasta 6.000 UVT al año (`TARIFA_SIMPLE` en `contratos.py`).
- Un nombre en XML solo cambia el inglés. Si el módulo de origen trae traducción, usar `update_field_translations`.
- Eventos de todo el día: guardarlos a mediodía UTC. A medianoche, Bogotá los ve la noche anterior.
- Los PDF solo se generan con el servidor corriendo: en `odoo shell` sin HTTP, wkhtmltopdf se queda esperando los estilos. Para revisarlos, bajarlos por `/report/pdf/<reporte>/<id>`.
