# Odoo 19 Community · Lumak

Odoo de producción de LUMAK SOLUTIONS S.A.S., en este equipo. Salida a producción, secretos y pendientes: [`docs/salida-a-produccion.md`](docs/salida-a-produccion.md).

```bash
docker compose up -d      # arrancar (necesita .env y config/odoo.conf, que no van a git)
docker compose down       # detener (los datos quedan en los volúmenes)
```

- URL: http://127.0.0.1:8069 · base de datos `lumak` · usuarios `carlos` y `dayana` (contraseñas en `privado/`).
- Apps: **Lumak** (tablero de la empresa; abre al entrar), CRM, Ventas, Proyecto, Facturación, Calendario, Contactos y Conversaciones, con la localización colombiana (`l10n_co`, pesos COP).
- **Guía de uso** para leer en el celular: [`docs/guia-de-uso-lumak.pdf`](docs/guia-de-uso-lumak.pdf). Cubre el flujo de una licitación, qué significa cada actividad y si es obligatoria, e incluye un ejemplo con fechas. Fuente en `docs/guia/`; se regenera con `uv run --with playwright python docs/guia/pdf.py`.
- Qué hace la empresa y cómo se conecta todo en Odoo: [`docs/plan-operacion-lumak.md`](docs/plan-operacion-lumak.md). Investigación de soporte en `docs/investigacion/` y `docs/licitaciones-secop.md`.
- Módulo propio `addons/lumak_secop` (montado en `/mnt/extra-addons`). Instalarlo deja la empresa configurada: equipo y etapas de licitaciones, planes de actividades, plantillas de proyecto, catálogo de servicios, kit de documentos, fechas legales e impuestos del SIMPLE.
- Pruebas del módulo: `docker compose run --rm -T odoo odoo server -d lumak_test -i lumak_secop --test-enable --test-tags /lumak_secop --stop-after-init --no-http` (crea la base `lumak_test`; bórrala al terminar).
- Respaldo: `scripts/respaldo.sh`, todos los días a las 7:00 p. m. con `scripts/lumak-respaldo.timer`. Guarda la base de datos y los adjuntos en `~/Respaldos/lumak` y deja los últimos 30; la restauración está al inicio del script. Copia uno al mes a un disco externo: los libros se conservan 10 años.
- Tras cambiar el módulo: `docker compose run --rm -T odoo odoo -d lumak -u lumak_secop --stop-after-init --no-http` y `docker compose restart odoo`.
- Claude Code: el MCP `odoo` ([odoo-mcp-19](https://github.com/AlanOgic/odoo-mcp-19), fijado en `b33e51f`) queda registrado solo para esta carpeta. La clave de API del admin se guardó en `~/.claude.json`, no en el repo, y vence el 27 sep 2027.
