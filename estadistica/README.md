# Base estadística de SECOP: mínima cuantía de software y TIC

Histórico de procesos de **mínima cuantía** en SECOP II desde 2018, con **cada oferta**: quién ofertó, cuánto, en qué puesto quedó y quién ganó. Es la base para las predicciones que siguen:
- quién se va a presentar a un proceso;
- a qué precio se gana;
- cuánto se puede llegar a ganar.

Se actualiza sola cada lunes.

```bash
cd estadistica
uv run python -m secop_estadistica actualizar --desde 2018-01-01   # carga completa (una vez)
uv run python -m secop_estadistica actualizar                      # semanal: re-lee los últimos 120 días
uv run python -m secop_estadistica monitor                         # diario: procesos abiertos a Odoo y precio para ganar
uv run python -m secop_estadistica reporte                         # informe en reportes/AAAA-MM-DD.md
uv run pytest                                                      # pruebas
```

- **Base:** `datos/secop.duckdb` ([DuckDB](https://duckdb.org), un solo archivo, gratis). Queda fuera de git.
- **Consultas:** con `uv run python -c "import duckdb; print(duckdb.connect('datos/secop.duckdb').sql('select ...'))"`, o con cualquier cliente de DuckDB.
- **Automatización:** `systemd/` tiene el servicio y el temporizador (lunes 6:00 a. m.; si el equipo estaba apagado, corre al prenderlo).
  - Ver cuándo corre: `systemctl --user list-timers secop-estadistica.timer`.
  - Desactivar: `systemctl --user disable --now secop-estadistica.timer`.

## Fuentes (datos.gov.co)

| Dataset | ID | Qué aporta |
|---|---|---|
| SECOP II - Procesos de Contratación | `p6dx-8zbt` | Proceso, entidad, presupuesto, modalidad, UNSPSC, fechas, respuestas, adjudicación |
| SECOPII - Ofertas Por Proceso | `wi7w-2nvm` | **Cada oferta**: proveedor (NIT y nombre), valor, fecha |
| SECOPII - Ofertas Por Proceso Histórico | `b28v-edj8` | Lo mismo para años anteriores |
| SECOP II - Contratos Electrónicos | `jbjy-vk9h` | Contrato firmado: valor, estado, fechas, si el proveedor es pyme |

**Qué entra:**
- Mínima cuantía en los segmentos UNSPSC 43 (equipos y software) y 81 (servicios de TI).
- En los segmentos 80, 82 y 84, los procesos que nombran software, sistema de información, aplicativo, plataforma, página web, portal, chatbot o inteligencia artificial.

**El nicho de Lumak** (columna `nicho`) sale del clasificador del estudio de mercado de septiembre de 2026:
- entran software a la medida, soporte de software, web, analítica, IA y automatización;
- quedan fuera hardware, licencias, conectividad y publicidad.

## Tablas y vistas

| Nombre | Una fila por | Para qué |
|---|---|---|
| `procesos` | proceso (`CO1.REQ…`) | Datos del proceso. `crudo` guarda la fila original completa, para sacar variables nuevas sin volver a descargar |
| `adjudicaciones` | adjudicación (`CO1.AWD…`) | Quién ganó y por cuánto. Puede haber varias por proceso |
| `ofertas` | oferta (`CO1.RPL…`) | Proveedor, valor y fecha. Se une al proceso por el portafolio (`CO1.BDOS…`) |
| `contratos` | contrato (`CO1.PCCNTR…`) | Valor firmado y estado |
| `cargas` | ejecución | Registro de cada actualización |
| `v_ofertas` | oferta | Puesto por precio, descuento frente al presupuesto, si ganó, si el valor es dudoso |
| `v_procesos` | proceso | N.º de ofertas, ganador, puesto del ganador, precio y descuento ganador, primero y segundo, distancia entre ellos, calidad del dato |
| `v_competidores` | proveedor | Ofertas, ganadas, tasa de éxito, descuento típico (al ofertar y al ganar), entidades y departamentos |
| `v_rivales_por_entidad` | entidad × proveedor | Quién le oferta a cada entidad y cuánto gana: la base para predecir quién se presenta |

## Lo que hay que saber de los datos (investigación del 28 sep 2026)

1. **Cada oferta viene repetida** una vez por renglón de la lista de precios (se vieron 92 copias de la misma oferta). La carga agrupa en el servidor por el ID de la oferta. Después de agrupar, el número de ofertas coincide con las respuestas que reporta SECOP.
2. **Ofertas y procesos se unen por el portafolio** (`CO1.BDOS…`), no por el ID del proceso (`CO1.REQ…`).
3. **Valores dudosos:** en algunos procesos casi todas las ofertas traen exactamente el presupuesto. Parece que SECOP pone el presupuesto cuando el proveedor no diligencia el precio. Esos procesos quedan con `calidad = 'valores_dudosos'` y se excluyen de los descuentos.
4. **El más barato no siempre gana:**
   - en mínima cuantía se evalúa primero la oferta más barata y, si no cumple, se pasa a la siguiente;
   - `puesto_ganador` y `gano_el_mas_barato` miden eso: cuántas ofertas baratas se caen.
5. **Puede haber varias adjudicaciones** por proceso, con valores distintos (correcciones o adiciones). El precio ganador que se usa es el de la **oferta** del ganador.
6. **El mismo proveedor aparece con y sin dígito de verificación.** El NIT se normaliza a 9 dígitos. Los consorcios y uniones temporales a veces traen «No Definido» como NIT.
7. **Rezago:** los datos abiertos llegan con cerca de un día de retraso. Un proceso se adjudica semanas después de publicarse, por eso la carga semanal re-lee 120 días.

## Monitor diario (7:30 a. m.)

`secop_estadistica/monitor.py`, con el temporizador `systemd/secop-monitor.timer`. Necesita Odoo corriendo (`docker compose up -d`).

1. **Trae de SECOP los procesos abiertos del nicho.**
   - Modalidades: mínima cuantía y régimen especial con ofertas.
   - Solo los publicados en los últimos 3 días que todavía reciben ofertas.
   - Todos quedan también en la base.
2. **Los crea en Odoo** en «Detectado», con el mismo importador del menú (entidad, presupuesto, cierre, plazo), y deja una nota. Si ya existen, no los duplica.
3. **Calcula el precio para ganar** en todos los procesos SECOP abiertos de Odoo y lo escribe en la pestaña SECOP:
   - precio sugerido;
   - probabilidad de ganar;
   - análisis con opciones y competidores probables.

   Si pones el **costo estimado** del proceso, el análisis calcula la utilidad; sin costo, solo da la probabilidad por precio.

Credenciales de Odoo: variables `LUMAK_ODOO_URL`, `LUMAK_ODOO_DB`, `LUMAK_ODOO_USUARIO` y `LUMAK_ODOO_CLAVE`. Por defecto son las del Odoo local.

## Precio para ganar (`precio.py`)

- **Probabilidad de ganar con un descuento d.** Se toman los procesos del nicho de los últimos 3 años con datos confiables. La probabilidad es la parte de ellos en que el ganador ofertó un descuento menor o igual a d: con esa oferta, Lumak le habría ganado.
- **Utilidad.** Precio sin IVA, menos SIMPLE (5,9 %) y estampillas, menos el costo.
- **Precio sugerido.** El que maximiza probabilidad × utilidad. Además hay tres opciones, para 50 %, 70 % y 85 % de probabilidad.
- **Competidores probables.** Primero quienes ya le ofertaron a esa entidad en el nicho; si son pocos, los más activos del nicho en el departamento.
- **Supuestos que hay que tener presentes:**
  - Lumak cumple todos los requisitos.
  - La competencia se comporta como en los últimos 3 años.
  - Una oferta nueva no cambia el comportamiento de las demás.

  Con menos de unos 30 comparables, el número es solo orientativo.

## Siguiente paso: predicciones

Con esta base se pueden entrenar, en orden de dificultad:
1. **¿Quién se presenta?** Probabilidad por proveedor, según su historial con la entidad, el departamento, el tipo de objeto y el rango de presupuesto (`v_rivales_por_entidad`).
2. **¿A qué precio se gana?** Hecho en su versión simple (`precio.py`). Lo que sigue: condicionar por el número de ofertas esperadas, el presupuesto, el tipo de entidad y el departamento.
3. **¿Cuánto se puede ganar?** Hecho: utilidad esperada = probabilidad de ganar con un precio × margen sobre el costo.
