# Odoo de Lumak

Odoo 19 Community en Docker: es la **producción** de LUMAK SOLUTIONS S.A.S. (NIT 902.110.349-9, Bogotá, SIMPLE) desde el 28 sep 2026. Los datos son reales: los de práctica (SIM) se borraron el 28 sep 2026.

- Arrancar: `docker compose up -d`. URL http://127.0.0.1:8069, base `lumak`, usuarios `carlos` (administrador) y `dayana` (ventas y proyectos). `admin` es cuenta técnica.
- Secretos fuera de git: `.env`, `config/odoo.conf`, `privado/`, `~/.config/lumak/odoo.env`. Nunca imprimirlos ni subirlos. Pendientes y pasos de actualización: `docs/salida-a-produccion.md`.
- Antes de cambios en la base real, correr `scripts/respaldo.sh`.
- Claude opera Odoo con el MCP `odoo` (API JSON-2 de Odoo 19, clave de API del admin que vence el 27 sep 2027).
- El plan de la empresa y el recorrido completo en Odoo: `docs/plan-operacion-lumak.md`. Mantenerlo al día cuando cambie el diseño.
- **Guía de uso para el celular:** `docs/guia-de-uso-lumak.pdf`, generada desde `docs/guia/guia.html` (capturas en `docs/guia/m/`) con `uv run --with playwright python docs/guia/pdf.py`. Si cambian las pantallas o el flujo, actualizar la guía y sus capturas.
- **Automático** (temporizadores de systemd del usuario; si el equipo estaba apagado, corren al prenderlo):
  - `secop-monitor` a diario a las 7:30: procesos nuevos a «Por revisar» con sus ventajas (✓, una estrella cada una) y avisos (⚠), precio para ganar y Mercado.
  - `secop-estadistica` los lunes a las 6:00: carga del histórico.
  - `lumak-respaldo` a diario a las 7:00 p. m.

  Los tres avisan al tablero («Automático») y leen la clave de API de `~/.config/lumak/odoo.env`.

## Reglas para simular

- Es producción: no crear datos de práctica sin permiso. Para una captura, crear un proceso SIM temporal y borrarlo al terminar, con su cotización y su entidad, y volver a poner en 1 la secuencia `sale.order`. Nunca tocar los procesos reales.
- Todo registro simulado lleva la etiqueta `SIM` (categoría de contacto o etiqueta de CRM), para poder filtrarlo o borrarlo después.
- Entidades públicas colombianas reales como clientes simulados están bien; personas naturales, inventadas.
- Antes de borrar o archivar datos del usuario, preguntar.
- Los datos personales (cédula, dirección, teléfono) viven solo en la base local. Los documentos que los llevan se guardan en `privado/`, que git ignora.
- Responder en español sencillo.
- Solo software libre y sin costo (Odoo Community y OCA, soluciones gratuitas de la DIAN). Decir claro lo que sí cuesta.

## Módulo `addons/lumak_secop`

- **Toda la configuración vive en el módulo** (`data/`, IDs `lumak_secop.*`), no en scripts. Lo que el usuario edita (productos, kit, fechas legales) va en bloques `noupdate`.
- Carpetas por capacidad. En `models/`:
  - `licitaciones.py`: procesos, importación, planes, ficha simple con el siguiente paso y tablero de licitaciones.
  - `contratos.py`: cotización, adjudicación, proyecto e impuestos.
  - `documentos.py`: kit y paquete de oferta.
  - `ejecucion.py`: contrato y experiencia.
  - `facturas.py`, `calendario.py` y `tablero.py` (panel de empresa).
  - `mercado.py`: Mercado SECOP (procesos y ofertas de la base estadística, solo lectura; los llena el monitor diario) y la página *Mercado → Estrategia* (qué tiene la competencia y cómo ganarle; arranca con `data/estrategia.html` y después la edita el usuario, así que actualizar el archivo no cambia la página).

  Cada una tiene su `views/`, `report/` y prueba en `tests/`.
- TDD: pruebas en `tests/`, en una base aparte `lumak_test`:

  ```
  docker compose run --rm -T odoo odoo server -d lumak_test -u lumak_secop --test-enable --test-tags /lumak_secop --stop-after-init --no-http
  ```

  Tras cambiar Python, XML o SCSS en la base real: respaldo, luego `docker compose run --rm -T odoo odoo server -d lumak -u lumak_secop --stop-after-init --no-http`, y `docker compose restart odoo`.
- Cambios de datos en la base real: migración en `migrations/<versión>/`. Los IDs sin `noupdate` que falten en el XML se borran al actualizar.
  - Probarla antes en una copia sacada del último respaldo: `createdb -T` no sirve mientras Odoo está conectado.
  - Pasos: `createdb -U odoo lumak_copia`, `pg_restore -U odoo -d lumak_copia --no-owner < ~/Respaldos/lumak/lumak-FECHA.dump`, actualizar la copia y revisar. Al final, `dropdb lumak_copia`.

## Base estadística `estadistica/`

- Histórico de mínima cuantía de SECOP II (software y TIC) con cada oferta, en DuckDB (`estadistica/datos/secop.duckdb`, fuera de git). Guía completa en `estadistica/README.md`.
- Se actualiza cada lunes con el temporizador de `estadistica/systemd/`. Tras una carga interrumpida: `uv run python -m secop_estadistica completar`.
- TDD con `uv run pytest`. DuckDB admite un solo proceso escribiendo: mientras carga, leer una copia del archivo.
- Las ofertas vienen repetidas una vez por renglón de la lista de precios: se agrupan en el servidor. Se unen al proceso por el portafolio (`CO1.BDOS…`).

## Diseño y gotchas

- **Simple para el usuario** (refactor del 28 sep 2026):
  - Todo SECOP vive en la app Lumak, en orden de trabajo: Tablero · Todo lo publicado · Mis procesos · Contratos · Por cobrar · Mercado · Empresa. Nada de SECOP en el CRM.
  - 4 etapas. Una etapa nueva solo si Odoo hace algo solo al entrar.
  - Las actividades solo para lo obligatorio; lo opcional va en el texto de la etapa (`requirements`).
  - Un proceso se abre con la ficha `crm_lead_form_secop`: `_secop_accion_ficha()` en Python, `form_view_ref` en JS.
  - Lo que corre fuera de Odoo (monitor, carga semanal, respaldo) avisa con `secop_registrar_automatizacion`. El tablero lo muestra en «Automático».

- En las vistas, el color se reserva para la urgencia: rojo hoy/mañana o vencido, ámbar pronto, verde con tiempo. La modalidad va en gris. Colores Lumak: tinta #1F2A44, ámbar #E8A33D.
- La fecha de cierre es `date_deadline`; la hora, `secop_hora_cierre` (hora de Bogotá). Los planes de actividades cuentan días calendario.
- Los documentos de la oferta llevan línea de firma, **no imagen de firma**: la CCE puede tomar una imagen pegada como documento sin firma (`docs/investigacion/documentos-secop.md`, sección 3).
- SIMPLE: tarifa 5,9 % hasta 6.000 UVT al año (`TARIFA_SIMPLE` en `contratos.py`).
- Un nombre en XML solo cambia el inglés. Si el módulo de origen trae traducción, usar `update_field_translations`.
- Eventos de todo el día: guardarlos a mediodía UTC. A medianoche, Bogotá los ve la noche anterior.
- Los PDF solo se generan con el servidor corriendo: en `odoo shell` sin HTTP, wkhtmltopdf se queda esperando los estilos. Para revisarlos, bajarlos por `/report/pdf/<reporte>/<id>`.
