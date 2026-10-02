# Plan de operación de Lumak en Odoo

27 de septiembre de 2026. Qué hace la empresa, cómo queda conectado todo en Odoo, qué quedó listo y qué sigue.

Las fuentes están en `docs/investigacion/`:
- `documentos-secop.md`: documentos de una oferta, plantillas, firmas y plazos.
- `impuestos-nomina-obligaciones.md`: IVA, SIMPLE, factura electrónica, contratistas, nómina y calendario legal.
- `modulos-odoo-libres.md`: qué hay gratis para Odoo 19 Community.
- `empresa-bien-constituida.md`: libros, gobierno, datos personales, propiedad intelectual, lavado de activos y permisos (sección 12).

Lo marcado *(no verificado)* sale así de esas investigaciones: confírmalo con el contador o con la norma antes de apoyarte en ello.

---

## 1. En una página

**Qué es Lumak.** Una SAS de una persona, en el SIMPLE. Vende sistemas de información a la medida (con soporte, SaaS y nube; la capacitación es una línea secundaria):
- a entidades públicas pequeñas, por SECOP II;
- a clientes privados: cajas de compensación, universidades privadas, cooperativas y clínicas.

**La idea del plan.** En Odoo todo es una sola cadena:

```
Proceso ─► Cotización (oferta económica) ─► Documentos de la oferta ─► Adjudicado
   ▲                                                                       │
   │                                                                       ▼
Experiencia ◄── Certificación ◄── Liquidación ◄── Pago ◄── Factura ◄── Proyecto del contrato (hitos)
```

Antes cada app era una isla. Ahora cada paso crea o abre el siguiente, y la app **Lumak** muestra en una sola pantalla:
- los cierres;
- los contratos en ejecución;
- lo que falta por cobrar;
- el kit de documentos;
- las fechas legales.

**Estado al 27 sep 2026.** Los datos de la compañía ya están, tomados del certificado de Cámara, el RUT y la cédula. El kit tiene la Cámara (vence el 26 oct), el RUT y la cédula. Tu experiencia quedó registrada: 6 contratos, 2 listos para ofertar.

**Lo que falta** (detalle en la sección 10):
1. Renovar los antecedentes del representante legal. Los que hay son del 22 jul y ya vencieron.
2. Sacar los de la empresa: Procuraduría y Contraloría con el NIT.
3. Sacar el REDAM.
4. La certificación bancaria, cuando abras la cuenta de Lumak.

---

## 2. Qué hace Lumak y qué necesita cada parte

| Línea | Canal | IVA | Cómo se ejecuta en Odoo |
|---|---|---|---|
| Sistema de información a la medida (**principal**) | SECOP y privados | 19 % | Proyecto desde plantilla, facturado por hitos |
| Soporte y mantenimiento (mes) | Ambos | 19 % (el remoto dejó de estar excluido en 2019) | Factura mensual |
| Suscripción SaaS y hosting o nube (mes) | Ambos | **Excluido** (ET art. 476 num. 21) | Factura mensual |
| Capacitación (secundaria) | Ambos | 19 % (la exclusión de educación no cubre a una SAS de software) | Por horas |
| Exportación de servicios (si sale el contrato remoto en dólares) | Exterior | **Exento** (ET art. 481 lit. c; RUT con calidad de exportador) | Posición fiscal «Cliente del exterior» |

### Fases de crecimiento

Cada fase dice qué encender. Nada se enciende antes de tiempo.

| Fase | Señal | Qué se activa |
|---|---|---|
| **0. Solo** (hoy) | Sin contratos | Lo que ya está: licitaciones, cotizaciones, kit, calendario legal |
| **1. Primer contrato** | Un «Adjudicado» o un cliente que firma | Proyecto y hitos, facturas en la DIAN (gratis), informe de actividades, certificación de aportes por pago |
| **2. Contratista** (la socia u otro) | Alguien trabaja por proyecto | Documento soporte (DIAN, gratis), revisar su PILA antes de cada pago, afiliarlo a la ARL si el contrato dura más de un mes |
| **3. Compuerta** | 3 contratos ganados, una renovación de soporte y 6 meses de caja | Dedicación completa. RUP (feb–mar 2027) y menor cuantía (desde el 26 sep 2027) |
| **4. Primer empleado** | Nómina fija | Apps Empleados y Ausencias; PILA mensual; SG-SST; certificación de aportes «con empleados» |
| **5. Equipo** (licitador y desarrollador) | Más de $314 M al año o más de 10 facturas al mes | Horas por proyecto (`hr_timesheet`); informes contables y conciliación bancaria (OCA); pensar en facturación electrónica propia |

Ojo con el SIMPLE: la tarifa de Lumak es **5,9 %** hasta 6.000 UVT de ingresos al año ($314 M en 2026). Por encima sube a **7,3 %** (hasta 15.000 UVT) y luego a **12 %**. La tarifa se aplica a **todo** el ingreso del año, no por escalones. Por eso pasar de un tramo encarece todo el año.

---

## 3. El recorrido completo en Odoo

### 3.1 Licitación en SECOP

| Paso | Dónde | Qué hace Odoo solo | Qué haces tú |
|---|---|---|---|
| 1. Detectar | **Automático cada mañana** (7:30): el monitor trae los procesos abiertos del nicho a «Por revisar». A mano: *Todo lo publicado* → «Traer a mi flujo», o «Importar con enlace» | Crea el proceso con la entidad (NIT y DV), el presupuesto, la modalidad, la fecha de cierre y el plazo | Pegar el enlace, el ID o la referencia |
| 2. Revisar | «Por revisar» | Cuenta regresiva de colores. El cierre y el límite de observaciones quedan en el **Calendario**, con recordatorio. El botón **«Preguntar a la IA»** copia una pregunta con el perfil de la empresa, la experiencia y el proceso, para pegarla en cualquier IA | Leer la invitación, decidir y hacer observaciones. El perfil se ajusta en *Empresa → Datos de la empresa*, pestaña «Ofertas SECOP» |
| 3. Preparar la oferta | Pasar a «Preparando oferta» | **Crea la cotización** (la oferta económica) al tope del presupuesto. Agenda 4 actividades obligatorias contadas desde el cierre | Poner el costo estimado. Bajar el precio en la cotización |
| 4. Documentos | Botón **«Preparar documentos de la oferta»** | Genera carta de presentación, oferta económica, certificación de aportes (art. 50), compromiso anticorrupción, declaración de inhabilidades y formato de experiencia. Les suma los certificados del kit vigentes al cierre. Todo queda en un mensaje: **«Descargar archivos» baja un ZIP**. Avisa lo que falta o vence, si la oferta supera el presupuesto o si el precio no cubre el costo | Firmar (sección 5.3) y subir a SECOP II |
| 5. Cierre y evaluación | «Presentada» | Agenda revisar el informe y subsanar | Subsanar a tiempo; anotar el n.º de oferentes y el precio ganador |
| 6. Adjudicado | Pasar a «Adjudicado» | **Confirma la cotización y abre el proyecto del contrato** desde la plantilla, con sus tareas y su hito de pago | Aprobar el contrato en SECOP II **con tu usuario de representante legal** |

**Precio mínimo.** En la pestaña SECOP pones el costo estimado y Odoo calcula el precio mínimo sin IVA:

```
costo ÷ (1 − 0,059 − estampillas)
```

Si la cotización queda por debajo, la ficha lo dice en rojo.

**Precio para ganar.** El monitor diario escribe en la pestaña SECOP:
- el precio sugerido y la probabilidad de ganar;
- las opciones para ganar con 50 %, 70 % y 85 % de probabilidad;
- los competidores probables.

Todo sale del histórico de SECOP (`estadistica/README.md`). Con el costo estimado, el sugerido es el que deja la mejor utilidad esperada.

**Lista de precios de SECOP.** Es el total de la cotización, con IVA. Si no coincide con el anexo, manda la plataforma, y la oferta económica no se subsana.

### 3.2 Cliente privado

1. *CRM → Ventas → Clientes privados*: la oportunidad.
2. «Nueva cotización» con el producto «Proyecto de software a la medida».
3. El cliente **la firma en línea** desde el enlace que le mandas. Esa firma es de Odoo Community, gratis, y sirve de firma electrónica entre privados.
4. Al confirmarse, Odoo abre el proyecto desde la plantilla privada, con dos hitos: «Anticipo al firmar» y «Entrega final aprobada».
5. Cada hito cumplido queda listo para facturar.
6. Al entregar, la tarea «Ofrecer contrato de soporte mensual» te recuerda la venta que da ingreso fijo.

### 3.3 Ejecución y cobro

1. **Proyecto → pestaña Contrato**: número de contrato y supervisor. El objeto y el valor vienen solos de la cotización.
2. Para cada pago, desde **Imprimir** en el proyecto:
   - «Informe de actividades»: tareas hechas y en curso, hitos y ejecución financiera, con Vo. Bo. del supervisor.
   - «Certificación de aportes (pago)»: se exige en cada pago (Ley 1150 art. 23).
3. Marcar el hito como cumplido, y en la orden de venta, «Crear factura».
4. **Emitir la factura legal en la solución gratuita de la DIAN**. En la factura de Odoo pegas el CUFE y adjuntas el XML y el PDF de la DIAN.
5. **Radicar** la factura en la entidad y luego cargarla en SECOP II, en el plan de pagos, con el número de radicación.
6. **Registrar el pago.** La factura muestra el **«Neto que debe llegar al banco»**:

   ```
   total − 15 % del IVA (lo retiene la entidad) − estampillas sobre la base
   ```

   Si llega eso, se registra el pago y la diferencia se cierra con «Marcar como pagada», contra la cuenta que te indique el contador. La retención de IVA se recupera en la declaración de IVA; las estampillas se pierden.

### 3.4 Cierre y experiencia

1. Acta de liquidación. Luego *Imprimir → «Derecho de petición (certificación de experiencia)»*. La entidad responde en 10 días hábiles (Ley 1755).
2. Botón **«Registrar experiencia»** en el proyecto: deja el contrato listo en *Lumak → Empresa → Experiencia*. Cuando llegue la certificación, se adjunta allí.
3. Los 5 contratos de mayor valor van solos en el **Formato de experiencia** de cada oferta.
4. Tu experiencia personal (UD y Agencia Catastral) se registra igual, marcada «Experiencia del socio»: vale para la empresa sus tres primeros años, vía RUP.

---

## 4. Las apps: qué queda y qué se quitó

**Quedan:**
- **Lumak**: es la primera app y abre al entrar. Tiene el tablero, el kit, la experiencia, las fechas legales y los datos de la empresa.
- CRM: los procesos SECOP y los clientes privados.
- Ventas, Proyecto, Facturación, Calendario, Contactos y Conversaciones.

**Se quitaron**, porque no tenían datos y eran de pago o sobraban:
- To-do: repetía las actividades.
- Los servicios IAP de pago: «Generar leads», enriquecimiento, autocompletar empresas, SMS y correo postal.
- Tableros de hojas de cálculo: los reemplaza la app Lumak.
- Constructor de PDF de cotizaciones.
- Formatos europeos de factura electrónica.

**En impuestos:** se archivaron las retenciones de renta y de ICA en ventas, porque en el SIMPLE nadie te las practica (ET art. 911). SaaS y nube quedaron con «IVA excluido» y se creó la posición fiscal «Cliente del exterior (exportación de servicios)».

**Configuración en el código.** Todo lo del CRM de licitaciones (equipo, etapas, planes, plantillas y productos) vive ahora en el módulo `lumak_secop`, no en un script aparte. Instalar el módulo deja la empresa configurada.

---

## 5. Documentos

### 5.1 Kit de la empresa (*Lumak → Empresa → Kit de la empresa*)

Son 14 documentos. Cada uno tiene su emisor, su enlace gratuito (botón «Sacarlo») y su vigencia. Subes el PDF con la fecha de expedición, y Odoo:
- muestra si está vigente, vence pronto, está vencido o falta;
- junta al paquete de la oferta solo los que siguen vigentes **en la fecha de cierre**.

Reglas que vale la pena recordar:
- **Cámara de Comercio:** expedido dentro de los 30 días anteriores al cierre. Cuesta $12.100.
- **Procuraduría:** si el NIT no aparece, hay que registrarlo **en persona**. Pruébalo antes de la primera oferta.
- **REDAM:** pide autenticarse en Carpeta Ciudadana.
- **Ley 1918 (menores de edad):** solo aplica si el contrato implica trato con menores, también virtual (Ley 2375 de 2024). Por ejemplo, una capacitación a colegios. La entidad hace la consulta con tu autorización.

### 5.2 Documentos que genera Odoo

| Documento | Cuándo | Nota |
|---|---|---|
| Carta de presentación | Cada oferta | Si llega una adenda después, se genera otra vez: la carta cita las adendas |
| Oferta económica | Cada oferta | Salen de las líneas de la cotización. **No se subsana** |
| Certificación de aportes (art. 50) | Cada oferta y cada pago | Variante «sin empleados» mientras no tengas nómina |
| Compromiso anticorrupción | Si la invitación lo pide aparte | En el Documento Tipo basta con la carta |
| Declaración de inhabilidades y conflicto de intereses | Si la piden aparte | — |
| Formato de experiencia | Cada oferta, si hay experiencia registrada | Máximo 5 contratos |
| Certificación MiPyME | Cada oferta, cuando los datos del contador estén en *Datos de la empresa* | Sirve para desempatar y **no se subsana**. Odoo calcula los ingresos (sin los registros SIM) y la clasificación. La firma también el contador |
| Autorización Ley 1918 | Si marcas «Trato con menores de edad» en el proceso | Por ejemplo, capacitaciones a colegios, también virtuales (Ley 2375 de 2024) |
| Anexo de cumplimiento | Si marcas «Incluir anexo de cumplimiento» | Datos personales, IA, accesibilidad WCAG 2.1 AA y seguridad. Son compromisos: úsalo cuando el sistema los cumpla |
| Informe de actividades | Cada pago | Con Vo. Bo. del supervisor |
| Derecho de petición | Al terminar un contrato | Pide la certificación de experiencia |
| Solicitud de certificación | Desde cada experiencia registrada | Si la certificación trae un error, pide corregirlo. La del socio va a su nombre, sin membrete de Lumak |

Textos adaptados de los formatos oficiales del Documento Tipo de mínima cuantía de Colombia Compra Eficiente (V3, 2024). Detalle en `investigacion/documentos-secop.md`.

**Lo que Odoo no puede hacer por ti:**
- La **firma del contador** en la certificación MiPyME. Odoo la genera, pero él la revisa y la firma.
- Los formatos propios de cada entidad.
- El **Formato único de hoja de vida de persona jurídica** de Función Pública: se llena una vez y va en el kit.
- Los estados financieros.

### 5.3 Firmas

- **En SECOP II, tu usuario y contraseña son tu firma electrónica**: lo dicen los Términos de Uso, con base en la Ley 527 art. 7. La oferta y el contrato los envía y aprueba **tu usuario de representante legal**.
- **Firma a mano y escaneada: válida** (concepto CCE C-921 de 2024). Es lo más seguro para la carta y las declaraciones.
- **Imagen de firma pegada: riesgosa.** La CCE dice que puede tomarse como documento sin firma. Por eso Odoo **no** pega una imagen: deja la línea para firmar.
- **Firma digital con certificado ONAC:** ninguna norma la exige para una oferta de mínima cuantía, y es de pago. La factura electrónica sí va firmada, pero con el certificado que la DIAN entrega gratis en su solución.
- **Firma de contratos con privados:** la de la cotización ya sirve. Si hace falta firmar PDFs dentro de Odoo, está `sign_oca`: gratis, en beta para la versión 19.
- **Más adelante, gratis:** firmar los PDF con un certificado propio (pyHanko) para detectar alteraciones. Ningún concepto de CCE lo valida todavía *(inferencia)*.

---

## 6. Ventas, impuestos y cobro

- **Catálogo** (*Ventas → Productos*):
  - contrato SECOP;
  - proyecto privado;
  - soporte (mes);
  - SaaS (mes);
  - nube (mes);
  - hora de desarrollo;
  - capacitación.

  Los precios los pones tú. El IVA de cada producto sigue la tabla de la sección 2.
- **Retenciones que te hacen:** solo la **retención de IVA del 15 %**. La practican las entidades públicas y cualquier comprador responsable de IVA. Renta e ICA **no**: muestra el RUT con la responsabilidad 47.
- **Estampillas:** las entidades territoriales las descuentan al pagar, y se pierden.
  - Bogotá ronda el 4,1 % y Cundinamarca el 4,5 %.
  - Van en la pestaña SECOP del proceso y pasan solas a la factura, al «neto que debe llegar».
- **Factura electrónica:**
  - Se hace en la **solución gratuita de la DIAN**, sin límite de facturas.
  - Hay que habilitarse **antes del 26 nov 2026** (dos meses desde el RUT; confirma la fecha en tu RUT).
  - Por qué no desde Odoo:
    - los módulos colombianos de facturación electrónica de Odoo son Enterprise, de pago;
    - la OCA tiene uno libre para la 19, pero está en beta, lo mantiene un solo autor y necesita un certificado ONAC de pago (unos $120–300 mil al año, *no verificado*).
  - Vale la pena cuando factures muchas veces al mes.
- **Diario de ventas:** cuando la DIAN te dé la numeración, pon en Odoo el **mismo prefijo y consecutivo** para que los números coincidan.
- **Contratista** (persona natural no obligada a facturar):
  - Documento soporte gratis en la DIAN: no es obligatorio en el SIMPLE, pero conviene.
  - Antes de cada pago, verificar su PILA del mes anterior sobre el 40 % de los honorarios.
  - Afiliarlo a la ARL si el contrato escrito dura más de un mes.
  - Sin retenciones.
- **Clientes del exterior:** usar la posición fiscal «Cliente del exterior». Requiere el RUT con calidad de exportador (casilla 54, código 22) y conservar el contrato.

---

## 7. Finanzas y obligaciones

- **Calendario legal en Odoo** (*Lumak → Empresa → Fechas de la empresa*): 22 fechas, también en el Calendario y en el tablero, con recordatorio un día antes. Las más cercanas:

| Fecha | Qué |
|---|---|
| 24 nov 2026 | Anticipo SIMPLE sep–oct (formulario 2593), **aunque dé $0** |
| 26 nov 2026 | Reporte inicial del RUB. Límite para habilitarse como facturador electrónico |
| 25 ene 2027 | Anticipo SIMPLE nov–dic |
| 19 feb 2027 | IVA anual 2026 (formulario 300), solo si hubo operaciones |
| 31 mar 2027 | Renovar la matrícula mercantil y aprobar los estados financieros 2026 |
| ~15 abr 2027 | Declaración anual SIMPLE (formulario 260). Vence hacia el 21 de abril |
| 26 sep 2027 | Lumak cumple un año: ya puede entrar a procesos limitados a MiPyME |

  Las fechas de 2027 son cálculo propio: corrígelas cuando la DIAN publique su calendario. El recordatorio del 1 dic 2026 te lo pide.

- **Contador (sí cuesta):**
  - certificar los estados financieros que pidan SECOP, el RUP o los bancos;
  - **dictaminarlos antes de repartir dividendos** (Ley 1258 art. 28);
  - firmar el IVA con saldo a favor;
  - la certificación MiPyME.

  Tú puedes llevar la contabilidad en Odoo y presentar el 2593, el 260, la PILA, el RUB y la renovación.
- **Informes contables:** Odoo Community no trae estado de resultados, balance ni conciliación bancaria; son Enterprise.
  - Hoy alcanza con registrar los pagos contra cada factura y con los análisis de Facturación.
  - Cuando haya más de unas 10 facturas al mes, instalar de la OCA (gratis, en la rama 19): `account_financial_report`, `mis_builder` y `account_reconcile_oca`.
- **Otros costos que no se evitan:**
  - renovación de la matrícula: el certificado de Cámara dice que Lumak cumple como «pequeña empresa joven» (Ley 1780). La primera renovación es gratis solo si se hace antes del 31 de marzo y sin incumplimientos tributarios (un 2593 tardío basta para perderla). Sin el beneficio cuesta unos $24.200;
  - RUP ($831.000 al año);
  - pólizas cuando las pidan;
  - el diseñador del SG-SST y los exámenes médicos cuando haya empleados.

---

## 8. Personas: RRHH y nómina por fases

- **Hoy (fase 0): no hay nómina.**
  - El plan es no pagarte salario y retirar dividendos después del cierre anual. Los dividendos cotizan como rentista de capital, cerca del 8,3 %.
  - Mientras sea así, la certificación de aportes «sin empleados» es cierta.
  - **Si decides pagarte salario**, ya hay un trabajador: marca «Tiene empleados» en la compañía y la certificación cambia de texto.
- **Contratista (fase 2)**, además de lo de la sección 6:
  - Contrato escrito con **cesión a Lumak de los derechos patrimoniales sobre el código**, con tiempo (todo el término legal), territorio (mundial) e indemnidad. Sin eso, la cesión se limita a 5 años y a Colombia.
  - El SG-SST mínimo (siete estándares de la Resolución 0312 de 2019) aplica también a quien solo tiene contratistas.
- **Primer empleado (fase 4)**:
  - **Qué exige la ley:**
    - Contrato escrito, a término indefinido por regla general (Ley 2466 de 2025).
    - Afiliaciones a EPS, pensión, ARL (antes de empezar) y caja.
    - PILA el 8.º día hábil de cada mes.
    - Máximo 42 horas a la semana desde el 15 jul 2026.
  - **Cuánto cuesta:** unos **38,4 % sobre el salario** (prima, cesantías, intereses, vacaciones, pensión 12 %, caja 4 % y ARL).
    - SENA, ICBF y salud están exonerados por debajo de 10 SMMLV.
    - La pensión del empleador se descuenta del anticipo del SIMPLE.
  - **Nómina electrónica:** no es obligatoria mientras Lumak esté en el SIMPLE.
  - **En Odoo:** instalar Empleados (`hr`) y Ausencias; también Gastos, si hay reembolsos.
    - La liquidación, en una hoja de cálculo más la PILA.
    - El módulo `payroll` de la OCA existe para la 19, pero sin reglas colombianas. No vale la pena con una o dos personas.
  - Checklist completa en `investigacion/impuestos-nomina-obligaciones.md`, sección 5.
- **Equipo (fase 5):**
  - Horas por proyecto (`hr_timesheet`): así el costo estimado de cada oferta sale de datos reales.
  - Permisos por persona: el licitador en CRM y Ventas; el desarrollador en Proyecto.

---

## 9. Lo que quedó hecho esta noche

Todo con pruebas automáticas (50 pasan), en el módulo `addons/lumak_secop`:

1. **Una sola fuente de configuración:** el script `scripts/crm_secop.py` pasó a datos del módulo y se borró. Tu base se migró sin perder nada; queda un respaldo en la base `lumak_respaldo_20260927`.
2. **«Clientes privados»** sin el filtro «Mi flujo», también en español y al recargar.
3. **Proceso → cotización → proyecto:** la cotización se crea sola al preparar la oferta. Al adjudicar se confirma y abre el proyecto con su hito de pago.
4. **Precio mínimo** con SIMPLE (5,9 %) y estampillas, y aviso de precio bajo.
5. **Calendario:** cierres y límites de observaciones como eventos con recordatorio, más 22 fechas legales de la empresa.
6. **Kit de la empresa** con vigencias, enlaces y estado.
7. **Paquete de oferta en un clic:** 5 o 6 PDF más el kit vigente, en un ZIP, con avisos.
8. **Documentos de ejecución:** informe de actividades, certificación de aportes por pago y derecho de petición. Además, un **registro de experiencia** que alimenta las ofertas.
9. **Facturas:** CUFE de la DIAN, estampillas y neto que debe llegar al banco.
10. **Impuestos del SIMPLE:** nube y SaaS sin IVA, sin retenciones de renta e ICA en ventas, y posición fiscal de exportación.
11. **App Lumak:** tablero de toda la empresa, kit, experiencia, fechas legales y datos de la empresa. Es la primera al entrar.
12. **Limpieza:** 5 grupos de apps que sobraban y un plan de oferta de 15 pasos reducido a 8.

**Para verlo andar:** hay un contrato de demostración marcado SIM:
- el proceso «SIM – Demo de punta a punta: mesa de ayuda TIC»;
- su cotización S00002, ya adjudicada;
- su proyecto, con el hito cumplido;
- su factura INV/2026/00001, que muestra el neto que debe llegar al banco.

Se puede borrar cuando quieras, junto con los demás registros SIM.

---

## 10. Siguientes pasos

**Tuyos (sin código):**
1. **Kit:** renovar los cuatro antecedentes del representante legal. Sacar los de la empresa (Procuraduría y Contraloría con el NIT; si la Procuraduría no encuentra el NIT, hay que registrarlo en persona), el REDAM y, cuando abras la cuenta, la certificación bancaria. Cada documento tiene su botón «Sacarlo».
2. **Experiencia** (*Lumak → Empresa → Experiencia*). Hay 6 contratos tuyos cargados con sus soportes. Van en las ofertas los dos que tienen soporte limpio:
   - IGAC 31581 de 2024: $28.285.000 ejecutados. La certificación dice $28.785.000 pactados; confirma cuál pide cada pliego.
   - Agencia Catastral CD-ACC-CPS-169-2023: $17.125.667, con acta de liquidación.

   Los demás esperan, cada uno por una razón:
   - Agencia Catastral CD-ACC-CPS-057-2023: la certificación trae **una cédula que no es la tuya**. Pedir la corrección a la ACC.
   - IGAC 33317 de 2025: solo hay contrato, sin certificación ni fecha de inicio. Pedir la certificación.

   Las dos cartas (derecho de petición) ya están en `privado/`, que queda fuera de git porque llevan tus datos. Se vuelven a imprimir desde *Lumak → Empresa → Experiencia → el contrato → Imprimir → «Solicitud de certificación»*. Cuando llegue cada certificación, se adjunta al registro y se activa «En ofertas».
   - JorjWeb y AFT Solutions: son de empresas privadas, sin valor total ni objeto. Para contar en SECOP necesitan una certificación con esos datos (y de facturación, firmada por contador).
   - UD CPS 2721-2026 y Corprogreso (PNUD-IGAC): siguen en ejecución, así que todavía no cuentan.
3. Hacer una oferta de práctica de punta a punta con un proceso real de mínima cuantía.
4. Confirmar con el contador:
   - las cuentas para la retención de IVA y las estampillas al registrar pagos;
   - el alcance de la exclusión de IVA para SaaS mixto;
   - si te conviene salario o dividendos.

**Siguientes iteraciones en Odoo**, en orden de valor:
1. **Aviso de adendas:** si cambia la fecha de cierre después de generar los documentos, avisar que hay que regenerar la carta.
2. **Informe de actividades por periodo:** elegir desde y hasta, en lugar de desde el inicio.
3. **Leer el XML de la DIAN** para llenar solo el número y el CUFE de la factura. Sería un script propio, sin costo.
4. **Diario de ventas con la numeración DIAN** cuando te habilites.
5. **OCA contable** (`account_financial_report`, `mis_builder`, `account_reconcile_oca`) cuando el volumen lo pida.
6. **Firma PDF con certificado propio** (pyHanko), si la CCE llega a validarla.

---

## 11. Empresa bien constituida: lo que faltaba

Investigación completa, con fuentes, en `investigacion/empresa-bien-constituida.md`.

**Ya está:**
- **Situación de control** del accionista único: inscrita el 26 sep 2026, según el certificado de Cámara.
- **Respaldos** de Odoo: `scripts/respaldo.sh` guarda la base y los adjuntos en `~/Respaldos/lumak`; la restauración está probada.
  - Los libros se conservan **10 años** (Código de Comercio, art. 60), así que una vez al mes hay que copiar un respaldo a un disco externo.
  - Los XML y PDF de la factura electrónica se adjuntan en Odoo: la solución gratuita de la DIAN no garantiza guardarlos.
- **Política de tratamiento de datos personales**: Odoo la genera desde *Lumak → Empresa → Datos de la empresa → ⚙ → Imprimir*, y el kit tiene su espacio.

**Ahora (antes del 26 oct 2026):**
1. **Cesión de tus derechos de autor a Lumak**, con un acta del accionista único que la autorice (Ley 222, art. 23 num. 7). No tienes contrato con Lumak, así que el código que escribes es tuyo; sin cesión, Lumak no puede licenciarlo ni venderlo. Después, registrar el software en la Dirección Nacional de Derecho de Autor (gratis). Queda en el calendario el 5 oct.
2. **Inscribir el libro de actas y el de accionistas** en la Cámara ($24.200 cada uno) y expedir el título de acciones. Calendario, 9 oct.
3. **Cuenta de Lumak en Caja Social** con el capital consignado: las entidades solo pagan a la cuenta registrada de la empresa. Luego, el **balance de apertura** (CCo art. 52) en Odoo: asiento de capital (cuenta 310500) contra el banco.
4. **Revisar a diario el correo inscrito** en la Cámara y el RUT: por ahí llegan las notificaciones.
5. **Datos personales:** guardar la prueba de cada autorización y llevar un registro de incidentes. Los incidentes se reportan a la SIC en 15 días hábiles, también cuando Lumak es encargado.
6. **RIT de Bogotá:** no es automático. Verificarlo antes del 26 nov (está en el calendario del 15 oct).

**Antes del primer contrato:**
- Plantillas de contrato:
  - contratista, con cesión mundial por todo el término legal;
  - acuerdo de transmisión de datos;
  - condiciones para clientes privados;
  - acuerdo de confidencialidad.
- **Debida diligencia** de cada cliente y proveedor, con consulta de listas restrictivas (Ley 2195, art. 12). Aplica porque Lumak reporta al RUB.
- **Ley 2013:** registro de bienes, rentas y conflictos con el primer contrato estatal, y actualización anual. Ya es una tarea de la plantilla del contrato.
- **Suplente o poder general:** sin suplente, nadie más puede firmar por Lumak si tú no puedes (unos $190.000–$307.000, *no verificado*).
- **Marca «Lumak» en la SIC:** $1.455.000 como MiPyME, clases 42 y 9. Es la única protección real del nombre.

**Cierre 2026 (hasta el 31 mar 2027):**
- Una sola acta que apruebe los estados financieros, el **informe de gestión** (Ley 1258, art. 37) y el proyecto de distribución de utilidades.
- **Depositar los estados financieros en la Cámara** dentro del mes siguiente (Ley 222, art. 41). Está en el calendario el 30 abr 2027.

**No aplica hoy** (se revisa al crecer):
- Revisor fiscal: el umbral es 5.000 SMMLV de activos; el de ingresos supera el tope del SIMPLE.
- Registro Nacional de Bases de Datos.
- SAGRILAFT y PTEE.
- Seguros obligatorios.
- Bomberos, Sayco-Acinpro o uso de suelo: se trabaja desde casa, sin atención al público.
- Envío de estados financieros a Supersociedades, salvo que lo pida.

## 12. Decisiones que son tuyas

- ¿Hago commit de todo esto? Está sin commit y sin subir.
- ¿Salario o dividendos? Cambia la certificación de aportes y el costo.
- ¿Vas por el contrato remoto en dólares? La posición fiscal de exportación ya está; falta la calidad de exportador en el RUT.
- ¿Qué contador por evento? Lo necesitas antes del RUP (feb 2027) y antes de repartir dividendos.
