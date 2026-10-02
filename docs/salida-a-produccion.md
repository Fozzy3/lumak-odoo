# Salida a producción del Odoo de Lumak

Estado al 28 sep 2026. Odoo corre en este portátil, con Docker, y arranca solo al prender el equipo.

## Lo que ya quedó

**Datos de práctica borrados** (28 sep 2026, con respaldo previo): procesos SIM y sus cotizaciones, proyectos, factura, actividades viejas y contactos. Quedan solo datos reales.

**Usuarios**
- **carlos**: administrador, con todos los permisos.
- **dayana**: CRM y ventas (ve todos los procesos) y proyectos. No entra a ajustes ni a contabilidad. Odoo sí le deja ver las facturas, porque ventas las necesita.
- **admin**: cuenta técnica, para no usarla a diario. Claude la usa por el MCP con su propia clave de API.

Las contraseñas están en `privado/credenciales-produccion.txt`, que git ignora.

Lo que estaba a nombre de admin pasó a Carlos: 11 procesos, 2 cotizaciones, 3 proyectos, 24 tareas, 42 actividades y 32 eventos. Los avisos de las fechas legales ahora le llegan a Carlos.

**Seguridad**
- Clave maestra propia: en `config/odoo.conf` solo queda su hash. Antes era `admin`, y con ella cualquiera podía copiar o borrar la base.
- El gestor de bases de la web está apagado (`list_db = False`) y Odoo sirve una sola base (`dbfilter = ^lumak$`).
- PostgreSQL tiene clave propia, en `.env`.
- Contraseñas de 8 caracteres o más, y nadie se registra solo: las cuentas se crean por invitación (`data/seguridad.xml`).
- Las imágenes de Docker quedan fijas por digest, así que no cambian sin querer.

**Automático**
- **En el tablero**, la sección «Automático» muestra cuándo corrió cada tarea: verde si va al día, ámbar si se atrasó. Cada tarea avisa a Odoo al terminar.
- **Monitor de SECOP** (7:30 a. m.): entra con una clave de API de carlos, guardada en `~/.config/lumak/odoo.env` (el monitor, la carga semanal y el respaldo leen ese archivo solos). Los procesos que trae quedan a nombre de Carlos. La clave sigue sirviendo aunque Carlos active el doble factor.
- **Respaldo diario** (7:00 p. m.): `scripts/lumak-respaldo.timer` guarda los últimos 30 en `~/Respaldos/lumak`. Si el equipo estaba apagado, corre al prenderlo.

## Lo que falta, en orden

1. **Guardar las contraseñas** en un gestor (KeePassXC, gratis) y borrar después el archivo de `privado/`. A Dayana, la suya en persona o por Signal. Cada quien la puede cambiar en *Mis preferencias*.
2. **Doble factor, cada uno** (2 minutos):
   - tu foto, arriba a la derecha → *Mis preferencias* → pestaña de seguridad → *Habilitar la autenticación de dos factores*;
   - escanear el código con una app gratis (Aegis en Android, o Google Authenticator).
3. **Acceso de Dayana desde su equipo.** Hoy Odoo solo responde en este portátil. Con Cloudflare Tunnel (gratis; el dominio ya está en Cloudflare):
   1. En Cloudflare, *Zero Trust → Networks → Tunnels → Create a tunnel → Cloudflared*, con el nombre `lumak-odoo`. Copiar el token.
   2. En el túnel, *Public hostname*: `odoo.lumak.co` → tipo `HTTP`, URL `odoo:8069`.
   3. Pegar el token en `.env` (`TUNNEL_TOKEN=…`) y correr `docker compose --profile tunel up -d`.
   4. Recomendado: *Zero Trust → Access → Applications*, una aplicación *self-hosted* para `odoo.lumak.co` que solo deje pasar el correo de Carlos y el de Dayana. Es gratis hasta 50 usuarios, y pide un código por correo antes de mostrar Odoo.
   5. Entrar una vez como carlos por `https://odoo.lumak.co`: Odoo adopta esa dirección para sus enlaces.

   **Límite:** si el portátil está apagado o suspendido, nadie entra. Si eso estorba, hay dos caminos:
   - pasar Odoo a un servidor gratuito (Oracle Cloud Always Free, que pide tarjeta);
   - o pagarlo (un VPS desde unos US$5 al mes).
4. **Copia fuera del equipo, una vez al mes**, en un disco externo:
   - los libros se conservan 10 años;
   - si el portátil se pierde, los respaldos se pierden con él;
   - si la copia va a una nube, primero se cifra (`gpg -c archivo`), porque lleva datos personales.
5. **Correo de salida**, cuando exista el correo de lumak.co. Sirve para enviar cotizaciones y facturas desde Odoo.
   - Se configura en *Ajustes → Técnico → Servidores de correo saliente*, con Gmail y una contraseña de aplicación (gratis).
   - Mientras tanto, los avisos llegan a *Conversaciones*, dentro de Odoo.
6. **Logo de Lumak**, en *Ajustes → Compañías*.

## Actualizar Odoo (cada 1 a 3 meses, o cuando salga un parche de seguridad)

1. `scripts/respaldo.sh`
2. `docker pull odoo:19.0` y `docker image inspect odoo:19.0 --format '{{index .RepoDigests 0}}'`. El digest nuevo va en `docker-compose.yml`.
3. `docker compose up -d`, luego `docker compose run --rm -T odoo odoo -d lumak -u all --stop-after-init --no-http`, y `docker compose restart odoo`.
4. Si algo falla, se vuelve al digest anterior y se restaura el respaldo; los pasos están al inicio de `scripts/respaldo.sh`.

## Dónde está cada secreto (nada va a git)

| Secreto | Dónde |
|---|---|
| Contraseñas de usuarios y clave maestra | `privado/credenciales-produccion.txt` (pasarlas al gestor) |
| Clave de PostgreSQL y token del túnel | `.env` |
| Hash de la clave maestra | `config/odoo.conf` |
| Clave de API del monitor | `~/.config/lumak/odoo.env` |
| Clave de API de Claude (MCP) | `~/.claude.json` |

- **En un equipo nuevo:**
  - copiar `config/odoo.conf.example` a `config/odoo.conf` y poner el hash, con el comando que trae el mismo archivo;
  - crear `.env` con `POSTGRES_PASSWORD`.
- **Cambiar la clave del monitor:**
  - entrar como carlos → *Mis preferencias* → *Claves API* → borrar la del monitor y crear otra;
  - pegar la nueva en `~/.config/lumak/odoo.env`.
