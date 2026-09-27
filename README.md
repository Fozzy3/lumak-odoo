# Odoo 19 Community · Lumak

Odoo local para aprender y simular la operación de LUMAK SOLUTIONS S.A.S.

```bash
docker compose up -d      # arrancar
docker compose down       # detener (los datos quedan en los volúmenes)
```

- URL: http://127.0.0.1:8069 · base de datos `lumak` · usuario `admin` / clave `admin` (solo local).
- Apps instaladas: Contactos, CRM, Ventas, Facturación, Proyectos y localización colombiana (`l10n_co`, pesos COP).
- Módulos propios: carpeta `addons/` (montada en `/mnt/extra-addons`).
- Claude Code: el MCP `odoo` ([odoo-mcp-19](https://github.com/AlanOgic/odoo-mcp-19), fijado en `b33e51f`) queda registrado solo para esta carpeta. La clave de API del admin se guardó en `~/.claude.json`, no en el repo, y vence el 27 sep 2027.
