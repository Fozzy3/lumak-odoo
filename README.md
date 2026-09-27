# Odoo 19 Community · Lumak

Odoo local para aprender y simular la operación de LUMAK SOLUTIONS S.A.S.

```bash
docker compose up -d      # arrancar
docker compose down       # detener (los datos quedan en los volúmenes)
```

- URL: http://127.0.0.1:8069 · base de datos `lumak` · usuario `admin` / clave `admin` (solo local).
- Apps instaladas: Contactos, CRM, Ventas, Facturación, Proyectos y localización colombiana (`l10n_co`, pesos COP).
- Módulos propios: carpeta `addons/` (montada en `/mnt/extra-addons`).
- CRM de licitaciones SECOP: `python3 scripts/crm_secop.py` (se puede correr varias veces). Investigación y diseño en `docs/licitaciones-secop.md`.
- Módulo `addons/lumak_secop`: menú CRM → «Importar desde SECOP» (enlace, ID o referencia) y planes que se agendan solos al pasar a «Preparando oferta» u «Oferta presentada». Depende de la configuración del script.
- Pruebas del módulo: `docker compose run --rm -T odoo odoo server -d lumak_test -i lumak_secop --test-enable --test-tags /lumak_secop --stop-after-init --no-http` (crea la base `lumak_test`; bórrala al terminar).
- Claude Code: el MCP `odoo` ([odoo-mcp-19](https://github.com/AlanOgic/odoo-mcp-19), fijado en `b33e51f`) queda registrado solo para esta carpeta. La clave de API del admin se guardó en `~/.claude.json`, no en el repo, y vence el 27 sep 2027.
