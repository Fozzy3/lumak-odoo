# Lumak Solutions S.A.S.: impuestos, facturación, nómina y obligaciones (base para Odoo 19 Community)

Fecha de corte: 27 de septiembre de 2026. NIT 902.110.349-**9**; dos últimos dígitos sin DV para PILA: **49**.
Regla de lectura: cada afirmación lleva su fuente. Lo marcado **(no verificado)** no se confirmó en fuente oficial en esta sesión. Las fechas de 2027 son **cálculo propio** con las reglas vigentes del DUR 1625 de 2016, porque la DIAN aún no publica el calendario 2027.

Cifras base 2026:
- UVT 2026 = **$52.374** ([Res. DIAN 000238 de 2025](https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0238_2025.htm)). La UVT 2027 aún no está fijada.
- SMMLV 2026 = **$1.750.905** y auxilio de transporte = **$249.095** (Decretos 1469 y 1470 de 2025; [Decreto 159 de 2026](https://www.cancilleria.gov.co/normograma/compilacion/docs/decreto_0159_2026.htm), transitorio). Según la prensa, en julio de 2026 el Consejo de Estado levantó la suspensión del Decreto 1469; el proceso de fondo sigue abierto **(no verificado en fuente oficial)**.

---

## 1. IVA por línea de negocio

### 1.1 ¿Lumak es responsable de IVA?
Sí. Los contribuyentes del SIMPLE son responsables de IVA ([ET art. 915](http://www.secretariasenado.gov.co/senado/basedoc/estatuto_tributario_pr036.html)). Solo quedan fuera quienes desarrollan únicamente actividades del num. 1 del art. 908 (tiendas y peluquerías) y las personas naturales del SIMPLE con ingresos inferiores a 3.500 UVT ([ET art. 437 par. 4](http://www.secretariasenado.gov.co/senado/basedoc/estatuto_tributario_pr017.html)). Ninguna de esas excepciones aplica a Lumak.

### 1.2 Tratamiento por servicio

| Servicio | IVA | Base legal y doctrina |
|---|---|---|
| Desarrollo de software a la medida | **19 %**, servicio gravado | ET art. 420 lit. c y art. 468 ([pr017](http://www.secretariasenado.gov.co/senado/basedoc/estatuto_tributario_pr017.html), [pr019](http://www.secretariasenado.gov.co/senado/basedoc/estatuto_tributario_pr019.html)). El art. 476 no lo excluye. |
| Soporte y mantenimiento remoto de programas | **19 %** | Desde 2019 dejó de estar excluido ([Oficio DIAN 20468 de 2019](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_20468_2019.htm)). El art. 476 num. 21 vigente ya no lo menciona. |
| Licencia de uso de software (on-premise, sin transferir derechos) | **19 %**: el licenciamiento es un servicio | [Oficio DIAN 32247 de 2018](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_32247_2018.htm) |
| Cesión o venta de los derechos patrimoniales de autor del software | **No causa IVA**: el art. 420 lit. b grava solo intangibles de propiedad industrial | [Oficio DIAN 908470 de 2021](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_908470_2021.htm). Advertencia: el desarrollo como servicio sigue gravado. |
| SaaS, PaaS, IaaS, hosting, servidores y páginas web | **Excluido (0 %, sin derecho a descontar el IVA asociado)** | ET art. 476 **num. 21**: "Suministro de páginas web, servidores (hosting), computación en la nube (cloud computing)". El numeral 24 citado en la consulta es la numeración anterior a la Ley 2010 de 2019. |
| Licencias de software para desarrollo comercial de contenidos digitales | Excluido | ET art. 476 num. 20, sujeto a reglamentación de MinTIC. No aplica a licencias generales. |
| Cursos y capacitación | **19 %** | ET art. 476 num. 5: solo excluye la educación de establecimientos reconocidos por el Gobierno. Una SAS sin licencia de educación para el trabajo no califica. El num. 6 ("educación virtual para el desarrollo de contenidos digitales") depende de la reglamentación de MinTIC, que no se revisó **(no verificado)**. |
| Exportación de servicios | **Exento (0 %) con derecho a devolución** | ET art. 481 lit. c ([pr019](http://www.secretariasenado.gov.co/senado/basedoc/estatuto_tributario_pr019.html)). El parágrafo cubre expresamente el desarrollo de software protegido por derecho de autor y difundido desde el exterior. |

Condiciones para que la nube quede excluida:
- La DIAN y MinTIC exigen las cinco características esenciales (autoservicio bajo demanda, acceso amplio, recursos compartidos, elasticidad y servicio medido), un modelo de servicio (SaaS, PaaS o IaaS) y un modelo de implementación. Si falta alguna, el servicio queda gravado. El proveedor debe hacer un autodiagnóstico en el formato de MinTIC ([Concepto DIAN 17056 de 2017](https://normograma.dian.gov.co/dian/compilacion/docs/concepto_tributario_dian_0017056_2017.htm)).
- La exclusión la aplica el **proveedor**. El revendedor también la aplica si su servicio cumple las mismas características ([Concepto DIAN 1959 de 2024](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_1959_2024.htm)).
- Implicación práctica: en contratos que combinan desarrollo o soporte con hosting o SaaS, facture líneas separadas. Así solo el componente de nube va excluido.

### 1.3 Requisitos de la exportación de servicios
1. El servicio se presta desde Colombia y se usa exclusivamente en el exterior, por una empresa o persona sin negocios ni actividades en Colombia (ET art. 481 lit. c).
2. RUT con calidad de exportador: casilla 53 con los códigos 48 (IVA), 19 (productor de bienes o servicios exentos) y 10 (usuario aduanero); casilla 54 con el código 22 (exportador); casillas 55 a 58 con forma y modo de exportación y código CPC ([Concepto DIAN 8660 de 2024](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_8660_2024.htm), que aplica el Decreto 2223 de 2013 compilado en el DUR 1080 de 2015).
3. Conservar la factura y el contrato, o la oferta con su aceptación, donde consten valor, país, descripción y cliente. Así lo resume la doctrina secundaria del Decreto 2223 **(texto literal no verificado)**.
4. Una solicitud de devolución exige relaciones certificadas por contador y una certificación del representante legal de que el servicio se usó exclusivamente en el exterior ([DUR 1625 art. 1.6.1.21.15 lit. h](https://normograma.dian.gov.co/dian/compilacion/docs/decreto_1625_2016.htm)).
5. Dudas abiertas **(no verificado)**:
   - Un exportador del régimen ordinario declara IVA bimestral (ET art. 600). No se confirmó cómo se concilia con la declaración anual del SIMPLE (art. 915). Conviene consultarlo a la DIAN antes de la primera exportación.
   - Si el servicio exportado es SaaS, no se confirmó si prevalece la exclusión o la exención.

### 1.4 Cómo y cuándo declara IVA un contribuyente del SIMPLE
- **Una declaración anual consolidada de IVA en el formulario 300**, que se presenta en febrero del año siguiente. El **IVA por pagar se transfiere cada bimestre con el recibo SIMPLE 2593** (ET art. 915; DUR 1625 art. 1.6.1.13.2.51). La DIAN lo confirma: "Presentar la declaración anual consolidada de IVA en el formulario 300. Sin perjuicio de esto, el IVA mensual deberá pagarse mediante el recibo electrónico SIMPLE" ([Material de apoyo RST, DIAN](https://www.dian.gov.co/impuestos/Rutadelaformalizacion/Material-de-apoyo-RST.pdf)).
- Si en el periodo no hubo operaciones gravadas ni impuestos descontables, no hay que declarar IVA (ET art. 601, [pr025](http://www.secretariasenado.gov.co/senado/basedoc/estatuto_tributario_pr025.html)).
- La declaración de IVA debe firmarla un **contador** cuando el patrimonio bruto o los ingresos superan 100.000 UVT **o cuando la declaración arroja saldo a favor** (ET art. 602). Con retención de IVA del 15 % sobre casi todas las ventas, un saldo a favor es posible.

---

## 2. Mecánica del SIMPLE en 2026

### 2.1 Grupo y tarifa
- Las cuatro actividades CIIU de Lumak (6201, 6202, 6311 y 8559) aparecen en la lista indicativa de la DIAN bajo el **numeral 3 del art. 908: "Servicios profesionales, de consultoría y científicos"** ([DUR 1625 Anexo 4, Decreto 1091 de 2020](https://normograma.dian.gov.co/dian/compilacion/docs/decreto_1091_2020.htm)). También están ahí 6209, 6312, 7020 y 8551.
- La Sentencia **C-540 de 2023** declaró inexequibles los numerales 4 y 5 de la Ley 2277 y **revivió el numeral 3 de la Ley 2155 de 2021** ([C-540/23](https://normograma.dian.gov.co/dian/compilacion/docs/c-540_2023.htm)). La DIAN ratificó las tarifas desde el año gravable 2024 ([Concepto DIAN 978 de 2024](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_0978_2024.htm)).
- Si hay dos o más actividades se aplica la tarifa más alta (ET art. 908 par. 5). A Lumak no le cambia nada, porque todas sus actividades están en el mismo grupo.

| Ingresos brutos anuales (UVT) | En pesos de 2026 | Tarifa consolidada | Anticipo bimestral: ingresos del bimestre (UVT) | Tarifa del anticipo |
|---|---|---|---|---|
| 0 a < 6.000 | < $314.244.000 | **5,9 %** | 0 a < 1.000 (< $52.374.000) | 5,9 % |
| 6.000 a < 15.000 | < $785.610.000 | **7,3 %** | 1.000 a < 2.500 (< $130.935.000) | 7,3 % |
| 15.000 a < 30.000 | < $1.571.220.000 | **12 %** | 2.500 a < 5.000 (< $261.870.000) | 12 % |
| 30.000 a < 100.000 | < $5.237.400.000 | **14,5 %** | 5.000 a < 16.666 | 14,5 % |

- La tarifa se aplica sobre **todo** el ingreso bruto según el tramo, no de forma marginal: "Ingreso bruto X tarifa = impuesto" ([Material de apoyo RST](https://www.dian.gov.co/impuestos/Rutadelaformalizacion/Material-de-apoyo-RST.pdf)). Hay por eso un salto brusco al cruzar 15.000 UVT: con $785 millones se paga 7,3 % (unos $57 millones) y con $800 millones se paga 12 % (unos $96 millones).
- Consecuencia para el plan del año 2: $500 millones caen en 7,3 %. $1.000 millones, con la UVT de 2026, caen en **12 %** y costarían unos $120 millones. Con la UVT de 2027 el umbral de 15.000 UVT será algo mayor **(UVT 2027 no fijada)**.
- El anticipo usa los tramos bimestrales. Un bimestre con una factura grande puede liquidarse al 12 % aunque el año cierre en 7,3 %. La diferencia vuelve como saldo a favor en la declaración anual (ET art. 910).
- El documento local `odoo/docs/licitaciones-secop.md` usa 0,073 como tarifa. Eso solo es correcto entre 6.000 y 15.000 UVT. El primer año, con ingresos por debajo de $314 millones, la tarifa es 5,9 %.

### 2.2 Tope de ingresos
- **100.000 UVT, unos $5.237 millones en 2026** (ET art. 905 num. 2, modificado por la Ley 2155 de 2021).
- El inciso de la Ley 2277 que fijaba un tope de **12.000 UVT** para servicios profesionales **fue declarado inexequible** (C-540/23, resolutivo primero). El texto compilado del ET, actualizado al 15 de septiembre de 2026, ya no lo trae ([pr036](http://www.secretariasenado.gov.co/senado/basedoc/estatuto_tributario_pr036.html)).
- Algunas fuentes secundarias de 2026 todavía repiten los 12.000 UVT. Es un error.
- Una empresa nueva queda condicionada a que los ingresos del año no superen el límite (art. 905 num. 2).

### 2.3 Qué incluye la tarifa y qué se descuenta
- La tarifa incluye el ICA consolidado: ICA, avisos y tableros y sobretasa bomberil (ET arts. 903 y 907).
- En Bogotá, la tarifa ICA consolidada es de 10 por mil para la agrupación 304 (6201, 6311, 8559) y 7 por mil para la 302 (6202) ([Acuerdo 780 de 2020, art. 11](https://bogota.gov.co/sites/default/files/inline-files/acuerdo-780-de-2020.pdf)). Esa parte se liquida **dentro** del 5,9 % o 7,3 % y va al Distrito; no suma encima (DUR art. 1.5.8.3.7; par. del art. 11 del Acuerdo 780). No se confirmó que las tarifas del Acuerdo 780 sigan iguales en 2026 **(no verificado)**.
- Descuentos sobre el componente nacional, nunca sobre el ICA:
  - El aporte a **pensión a cargo del empleador**, siempre que se haya pagado antes de presentar el 2593 (ET art. 903 par. 4; DUR art. 1.5.8.3.2).
  - El **0,5 % de los ingresos recibidos por tarjeta o pago electrónico**, incluidas transferencias en las que intervenga una entidad vigilada por la Superfinanciera, con certificado del banco. Alternativa excluyente: el 4 x 1000 pagado, hasta el 0,004 % de los ingresos (ET art. 912; DUR arts. 1.5.8.3.3 y 1.5.8.3.4). Los bancos expiden el certificado a más tardar el 10.º día hábil de marzo (DUR art. 1.6.1.13.2.40 par. 4).
- Bogotá permitía descontar del ICA una parte del costo del registro mercantil (30 % el primer año, 50 % el segundo, 75 % el tercero) a quienes se formalizaran en el RIT o en el SIMPLE, **hasta el año gravable 2026** (Acuerdo 780, art. 13 y su par. 5). No se confirmó cómo se aplica dentro del SIMPLE ni si sigue vigente **(no verificado)**.

### 2.4 Anticipos bimestrales (formulario 2593) y declaración anual (formulario 260)
- El recibo 2593 es **obligatorio cada bimestre aunque el valor sea $0** (ET art. 910; DUR art. 1.6.1.13.2.52). Se presenta con pago total; un retraso mayor a un mes saca al contribuyente del régimen (ET arts. 910 par. 2 y 914).
- Plazos para el dígito 9 según el [calendario DIAN 2026](https://www.dian.gov.co/Calendarios/Calendario_Tributario_2026.pdf):

| Obligación | Plazo |
|---|---|
| Anticipo septiembre–octubre 2026 | **24 nov 2026** |
| Anticipo noviembre–diciembre 2026 | **25 ene 2027** |

- La declaración anual (formulario 260) vence en abril y la del dígito 9 corresponde al 15.º día hábil (DUR art. 1.6.1.13.2.50). La firma el representante legal; el revisor fiscal solo firma si la sociedad está obligada a tenerlo, y no se exige contador (DUR art. 1.5.8.3.14).
- Anomalía: en 2026 la DIAN publicó el 24 de abril para los dígitos 9-0, mientras que la regla daba el 23. Para 2027, **presente antes del 15 de abril**.

### 2.5 Retenciones sobre las ventas de Lumak

| Qué | ¿Aplica? | Fuente |
|---|---|---|
| Retención en la fuente a título de renta | **No.** Hay que mostrar el RUT con la responsabilidad 47. | ET art. 911; DUR art. 1.5.8.3.1 |
| Retención de ICA | **No**, "sin perjuicio de lo que establezcan los municipios". No se revisó una norma específica de Bogotá **(no verificado)**. | DUR art. 1.5.8.3.1 |
| **Retención de IVA del 15 %** | **Sí.** La practican las entidades estatales (ET art. 437-2 num. 1) y **cualquier comprador responsable de IVA** que adquiera a un contribuyente del SIMPLE (num. 9). | ET arts. 437-1, 437-2 y 911; [Oficio DIAN 903512 de 2020](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_903512_2020.htm) |
| Estampillas y contribuciones en contratos públicos | Sí. Son descuentos, no retenciones. | Documento local `licitaciones-secop.md`, sección 4 |

### 2.6 Retenciones que practica Lumak
- **No practica** retención de renta ni de ICA, salvo sobre **pagos laborales** (ET art. 911; DUR art. 1.5.8.3.1).
- **Sí practica retención de IVA del 15 %** cuando compra bienes o servicios gravados a otro contribuyente del SIMPLE (ET art. 437-2 num. 9; Oficio 903512 de 2020). En ese caso presenta el formulario 350 en los meses con retención (DUR art. 1.6.1.13.2.33 par. 5) y queda obligada a reportar exógena (sección 6).

### 2.7 Riesgos de exclusión del SIMPLE
- Si el socio o administrador presta, en sustancia, un servicio personal subordinado y habitual a un solo contratante, la sociedad no puede estar en el SIMPLE (ET art. 906 num. 4).
- Lumak tampoco puede ser accionista de otras sociedades (ET art. 906 num. 6).

---

## 3. Facturación electrónica gratuita (DIAN)

### 3.1 Quién la puede usar y qué soporta
- **Cualquier facturador**: la DIAN la describe como un servicio gratuito "para todos los empresarios y responsables" y "sin límite de generación y recepción de documentos electrónicos" ([micrositio Facturación Gratuita DIAN](https://micrositios.dian.gov.co/sistema-de-facturacion-electronica/facturacion-gratuita-dian/)).
- Los requisitos son el RUT y el correo registrado en él.
- La DIAN entrega gratis el certificado de firma para la solución y también el IFE para firmar declaraciones ([micrositio de obligaciones del RST](https://micrositios.dian.gov.co/regimen-simple-tributacion/obligaciones-contribuyentes-del-rst/)).

| Documento | Solución gratuita DIAN | Fuente |
|---|---|---|
| Factura electrónica de venta | Sí | micrositio de la DIAN |
| Notas crédito y débito | Sí; el set de pruebas incluye una de cada una | micrositio y guía de la DIAN |
| Documento soporte en adquisiciones a no obligados, y su nota de ajuste | Sí, en una solución gratuita propia | [PDF DIAN, solución gratuita de documento soporte](https://www.dian.gov.co/impuestos/factura-electronica/Documents/Solucion-Gratuita-Proceso-de-generacion-documento-soporte-en-adquisiciones-efectuadas-a-no-obligados.pdf) |
| Nómina electrónica y notas de ajuste | Sí. Exige estar habilitado antes como facturador. | [micrositio de nómina gratuita](https://micrositios.dian.gov.co/sistema-de-facturacion-electronica/solucion-gratuita-de-nomina-electronica/) |

### 3.2 Plazo
El contribuyente del SIMPLE debe adoptar la factura electrónica **dentro de los dos meses siguientes a su inscripción en el RUT** (ET art. 915 par.). Si el RUT se inscribió el 26 de septiembre de 2026, el plazo vence el **26 de noviembre de 2026**. Hay que confirmar la fecha exacta en el certificado RUT.

### 3.3 Habilitación y numeración, paso a paso
1. Registro en el servicio de facturación electrónica, selección del modo de operación "Software gratuito" y solicitud del certificado digital.
2. Set de pruebas (en el modo gratuito: 2 facturas, 1 nota crédito y 1 nota débito), fecha de inicio de operación y actualización del RUT con la responsabilidad 52 **(código no verificado)**.
3. Solicitar la numeración en MUISCA, opción "Numeración de facturación": se firma el **formato 1302 (solicitud)** y se obtiene el **formato 1876 (autorización)** ([PDF DIAN](https://www.dian.gov.co/impuestos/sociedades/presentacionclientes/Solicitud_de_Autorizacion_de_Numeracion_de_Facturacion.pdf)).
   - La autorización trae número, fecha, **vigencia**, rangos y prefijo de hasta 4 caracteres ([Res. DIAN 227 de 2025, arts. 1.5.1.6.2.1 y 1.5.1.6.2.2](https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0227_2025.htm)).
   - El documento soporte necesita **su propia numeración**, solicitada **antes** de la operación (par. del art. 1.5.1.6.2.2).
   - Si vence la vigencia sin agotar el rango, se pide habilitación con 15 días hábiles de antelación (art. 1.5.1.6.2.3).
   - Según las preguntas frecuentes de la DIAN, la vigencia es de 6, 12 o 18 meses ([FAQ numeración](https://micrositios.dian.gov.co/sistema-de-facturacion-electronica/numeracion-de-facturacion-preguntas-frecuentes/)) **(puede estar desactualizada)**.
4. Asociar prefijos y rangos al software gratuito en el ambiente de producción y empezar a facturar.

### 3.4 Registro en Odoo
- Odoo 19 Community trae `l10n_co` (plan de cuentas e impuestos, licencia LGPL) y `l10n_co_pos`. **No trae** los módulos de facturación electrónica colombiana (`l10n_co_edi`, `l10n_co_dian`), `hr_payroll` ni `account_reports`: devuelven 404 en la rama 19.0 de [github.com/odoo/odoo](https://github.com/odoo/odoo/tree/19.0/addons/l10n_co).
- Por eso cada factura se **emite en la solución DIAN** y se **registra en Odoo** así:
  1. Diario de ventas con la misma secuencia de la DIAN (prefijo y consecutivo).
  2. Campo para el CUFE.
  3. XML y PDF descargados de la solución DIAN y adjuntos.
  4. Mismos impuestos y valores.
- Flujo sugerido:
  1. Borrador en Odoo, que sirve de cotización y de control.
  2. Emisión en la DIAN.
  3. Registro en Odoo con el número y el CUFE de la DIAN.
- Automatizar la lectura del XML sería un script o módulo propio **(no verificado; sin costo de licencia)**.

---

## 4. Documento soporte y pagos al contratista (persona natural no obligada a facturar)

### 4.1 ¿Es obligatorio?
- La DIAN dice que el documento soporte sirve para probar la transacción que da lugar a costos, deducciones o impuestos descontables (ET art. 771-2). En consecuencia, un contribuyente del SIMPLE solo lo necesita cuando requiere soportar **impuestos descontables de IVA** ([Oficio DIAN 901689 de 2021](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_901689_2021.htm)).
- Un contratista no responsable de IVA no cobra IVA. Luego, **no es estrictamente obligatorio** para Lumak mientras siga en el SIMPLE.
- **Recomendación: emitirlo igual.** Es gratis en la solución DIAN y sirve de prueba contable, de sustento frente a la UGPP y de soporte si Lumak pasa al régimen ordinario, donde sí es requisito para deducir el costo.
- La numeración se pide antes del primer pago (Res. 227 de 2025, art. 1.5.1.6.2.2 par.).

### 4.2 Retenciones sobre el pago al contratista
- Retención de renta: ninguna, porque Lumak no es agente de retención de renta (ET art. 911; DUR art. 1.5.8.3.1).
- Retención de ICA: ninguna, por la misma razón.
- Retención de IVA: ninguna, porque el contratista no es responsable de IVA.

### 4.3 Seguridad social del contratista: verificación antes de cada pago
- El contratista es el único responsable de sus aportes, que paga **mes vencido** por PILA, planilla I, tipo de cotizante 59 ([ABC UGPP de enero de 2026](https://www.ugpp.gov.co/wp-content/uploads/2026/01/ABC-Trabajador-Independiente-Contrato-Prestacion-Servicios.pdf)).
- **IBC = 40 % del valor mensual del contrato sin IVA**, con mínimo de 1 SMMLV y máximo de 25 SMMLV (Ley 2277 de 2022, art. 89).
- Tarifas: salud 12,5 %; pensión 16 %; ARL obligatoria si el contrato dura más de un mes (riesgo I: 0,522 %). La caja de compensación es voluntaria.
- La UGPP es explícita: "El contratante deberá verificar que el independiente presente los comprobantes de pago de seguridad social acorde con el monto a cancelar, antes de efectuar los pagos".
- Regla práctica de pago: planilla del mes anterior con IBC mayor o igual al 40 % de los honorarios mensualizados, y como mínimo 1 SMMLV cuando los ingresos del contratista son de 1 SMMLV o más.
- **Obligación de Lumak que se suele omitir**: afiliar al contratista a la **ARL a través del contratante** cuando el contrato escrito dura más de un mes, al menos un día antes de que empiece. El contratista paga la cotización si el riesgo es I, II o III ([Decreto 1072 de 2015, arts. 2.2.4.2.2.5, 2.2.4.2.2.6 y 2.2.4.2.2.13](https://normativa.colpensiones.gov.co/colpens/docs/decreto_1072_2015_pr007.htm)).
- Además, el contratante debe incluir al contratista en su SG-SST (art. 2.2.4.2.2.15).
- El Decreto 1273 de 2018 previó que el contratante retuviera y girara los aportes. No se verificó si esa obligación está vigente hoy para contratantes privados **(no verificado)**; la UGPP en 2026 solo exige verificar.
- Si el contratista supera 3.500 UVT ($183.309.000) o un contrato individual pasa ese valor, debe inscribirse como responsable de IVA (ET art. 437 par. 3). Desde ese momento cobraría IVA.

---

## 5. Nómina: checklist para el primer empleado

**Antes de contratar**
- [ ] **Contrato escrito.** La regla general es el término indefinido. El término fijo no puede pasar de 4 años y debe constar por escrito, igual que el de obra o labor ([Ley 2466 de 2025, arts. 5 y 6](http://www.secretariasenado.gov.co/senado/basedoc/ley_2466_2025.html)).
- [ ] Afiliar a EPS, AFP, **ARL (antes de iniciar labores)** y caja de compensación.
- [ ] Examen médico de ingreso y demás requisitos del SG-SST (ver abajo).

**Cada mes**
- [ ] **PILA** electrónica o asistida. Para los dígitos 49 vence el **8.º día hábil del mes** ([Decreto 780 de 2016, art. 3.2.2.1, texto del Decreto 1990 de 2016](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=78396)).
- [ ] Aportes del empleador:
  - Pensión: **12 %** de 16 % ([Ley 100 de 1993, art. 20](http://www.secretariasenado.gov.co/senado/basedoc/ley_0100_1993.html)).
  - Salud: **8,5 % exonerado**.
  - SENA (2 %) e ICBF (3 %): **exonerados**, por cada trabajador que devengue menos de 10 SMMLV ($17.509.050) (ET art. 114-1 y art. 903 par. 3; DUR art. 1.5.8.3.6).
  - **Caja de compensación 4 %: no se exonera.**
  - ARL según el riesgo; riesgo I = 0,522 %.
- [ ] Descontar la **pensión del empleador** en el 2593 (ET art. 903 par. 4).
- [ ] Retención en la fuente sobre salarios si aplica, con el formulario 350 en los meses con retención. Para el dígito 9 vence el 15.º día hábil del mes siguiente (DUR art. 1.6.1.13.2.33).
- [ ] **Nómina electrónica: no obligatoria mientras Lumak esté en el SIMPLE**, porque no es contribuyente del impuesto de renta ([Oficio DIAN 901689 de 2021](https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_901689_2021.htm)). Si algún día sale del SIMPLE, puede usar gratis la solución DIAN.

**Prestaciones** ([CST en el Senado](http://www.secretariasenado.gov.co/senado/basedoc/codigo_sustantivo_trabajo.html))

| Concepto | Cuánto | Cuándo | Fuente |
|---|---|---|---|
| Prima de servicios | 30 días por año | 50 % a más tardar el 30 jun; 50 % en los primeros 20 días de dic | CST art. 306 |
| Cesantías | 1 mes por año | Liquidación al 31 dic; consignación al fondo **antes del 15 feb** | CST art. 249; Ley 50 de 1990 art. 99 |
| Intereses sobre cesantías | 12 % anual | En enero | Ley 52 de 1975; Decreto 116 de 1976 |
| Vacaciones | 15 días hábiles por año | Según se programen | CST art. 186 |
| Dotación | Calzado y vestido 3 veces al año, si el trabajador gana hasta 2 SMMLV ($3.501.810) y lleva más de 3 meses | 30 abr, 31 ago y 20 dic | CST arts. 230 y 232 |
| Auxilio de transporte | $249.095 en 2026, hasta 2 SMMLV | Mensual | Si hay teletrabajo, se reemplaza por **auxilio de conectividad** (Ley 2466, art. 53) |

- Opción legal de la Ley 2466, art. 64: consignar las cesantías cada mes (8,33 %) y pactar por escrito el pago mensual de los intereses (1 %).

**Costo aproximado del empleador sobre el salario** (sin auxilio de transporte ni dotación): prima 8,33 % + cesantías 8,33 % + intereses 1 % + vacaciones 4,17 % + pensión 12 % + caja 4 % + ARL 0,522 % ≈ **38,4 %**. El 12 % de pensión vuelve como descuento del SIMPLE mientras el componente nacional alcance.

**Jornada y recargos**
- Máximo **42 horas semanales desde el 15 de julio de 2026** (Ley 2101 de 2021, art. 3; Ley 2466, art. 11). Pueden distribuirse en 5 o 6 días.
- **Trabajo nocturno desde las 7:00 p. m.**, vigente desde el 25 de diciembre de 2025 (Ley 2466, art. 10).
- **Recargo por trabajar en día de descanso obligatorio: 90 % desde el 1 de julio de 2026 y 100 % desde el 1 de julio de 2027** (Ley 2466, art. 14).

**Otras obligaciones de la Ley 2466 de 2025**
- Nuevas licencias remuneradas: citas médicas, obligaciones escolares, citaciones judiciales, entre otras (art. 15).
- Debido proceso disciplinario. Las **micro y pequeñas empresas de menos de 10 trabajadores** solo deben oír previamente al trabajador (art. 7 par. 6).
- Cuota de 2 trabajadores con discapacidad por cada 100 (art. 15 num. 17). En la práctica no aplica a una planta de 1 a 3 personas **(interpretación)**.

**Reglamento interno de trabajo**
- Obligatorio solo con **más de 5 trabajadores permanentes** en empresa comercial, o más de 10 si la empresa es mixta o industrial (CST art. 105).
- No se verificó si una empresa de software cuenta como "comercial" para este efecto **(no verificado)**.
- Si lo adopta, debe publicarlo también por medio virtual (Ley 2466, art. 8).

**SG-SST mínimo (Resolución 0312 de 2019, art. 3)** para empresas, empleadores **y contratantes** con 10 trabajadores o menos en riesgo I a III ([texto](https://normograma.sena.edu.co/compilacion/docs/resolucion_mtra_0312_2019.htm), [PDF MinTrabajo](https://www.mintrabajo.gov.co/documents/20147/59995826/Resolucion+0312-2019-+Estandares+minimos+del+Sistema+de+la+Seguridad+y+Salud.pdf)). Son siete estándares:
1. Una persona que diseñe el sistema: técnico, tecnólogo o profesional en SST con licencia vigente y el curso virtual de 50 horas.
2. Afiliación al sistema de seguridad social.
3. Capacitación en SST.
4. Plan anual de trabajo firmado.
5. Evaluaciones médicas ocupacionales.
6. Identificación de peligros con acompañamiento de la ARL.
7. Medidas de prevención y control.

Nota: el comité de convivencia (Res. 652 de 2012) y el vigía de SST no se verificaron en esta sesión **(no verificado)**.

**Proyecto de ley en trámite**, no vigente: la reforma tributaria radicada el 20 de julio de 2026 propone bajar la exoneración del art. 114-1 de 10 a **3 SMMLV** ($5.252.715) desde el 1 de enero de 2027. Afectaría a un desarrollador bien pagado. Fuente de prensa ([siemprealdia](https://siemprealdia.co/colombia/impuestos/reforma-tributaria/)) **(no verificado en fuente oficial)**.

---

## 6. Calendario de obligaciones, septiembre de 2026 a diciembre de 2027 (dígito 9)

Notas sobre obligaciones sin fecha fija:
- **Información exógena**: están obligadas las personas jurídicas con ingresos brutos superiores a **2.400 UVT** en el año reportado o en el anterior ($125.697.600 en 2026). También quien estuvo obligado a practicar retenciones, incluida la retención de IVA del num. 9 ([Res. DIAN 227 de 2025, art. 1.3.1.1](https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0227_2025.htm)). Por el año gravable 2026, Lumak solo reporta si facturó más de ese monto o practicó retenciones. Por 2027 casi seguro reportará, en 2028.
- **RUB**: el reporte inicial vence dos meses después de la inscripción en el RUT. Luego hay que actualizarlo solo si hubo cambios, dentro del mes siguiente al 1 de enero, abril, julio y octubre ([Res. DIAN 164 de 2021, arts. 10 y 11](https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0164_2021.htm)).
- **RIT de Bogotá**: hay que inscribirse o verificar la inscripción; el trámite en la Secretaría de Hacienda es gratuito. Es requisito para los beneficios del Acuerdo 780 (art. 12). No se verificó si la inscripción es automática al matricularse en la CCB **(no verificado)**.

| Obligación | Fecha | Fuente |
|---|---|---|
| Registrar en la CCB el libro de actas y el de registro de accionistas | Antes de la primera acta | [CCo art. 28 num. 7](http://www.secretariasenado.gov.co/senado/basedoc/codigo_comercio.html); Ley 1258 art. 22 par. |
| Facturación electrónica habilitada | **Hasta el 26 nov 2026**, dos meses después de la inscripción en el RUT (confirmar fecha) | ET art. 915 par. |
| RUB: reporte inicial | **Hasta el 26 nov 2026** (confirmar la fecha del RUT) | Res. 164 de 2021 art. 10 |
| Anticipo SIMPLE sep–oct 2026 (2593), aunque sea $0 | **24 nov 2026** | Calendario DIAN 2026; ET art. 910 |
| Formulario 350 (solo si hubo retención de IVA o laboral) | Oct: 24 nov 2026; nov: 22 dic 2026; dic: 25 ene 2027 | Calendario DIAN 2026 |
| Anticipo SIMPLE nov–dic 2026 | **25 ene 2027** | Calendario DIAN 2026 |
| Intereses sobre cesantías (solo si hubo empleados en 2026) | 31 ene 2027 | Ley 52 de 1975 |
| RUB: actualización trimestral (solo si hubo cambios) | 1 feb, 3 may, 2 ago y 2 nov de 2027 (cálculo) | Res. 164 de 2021 art. 11; calendario DIAN 2026 como patrón |
| Consignar cesantías (si hubo empleados) | Antes del 15 feb 2027 | Ley 50 de 1990 art. 99 |
| **IVA anual 2026 (formulario 300)**, solo si hubo operaciones | **19 feb 2027** (cálculo: 15.º día hábil) | DUR art. 1.6.1.13.2.51; ET art. 601 |
| Certificado bancario del descuento del 0,5 % | 10.º día hábil de marzo de 2027 (lo expide el banco) | DUR art. 1.6.1.13.2.40 par. 4 |
| Certificado de ingresos y retenciones, formulario 220 (si hubo empleados) | Último día hábil de marzo de 2027 | DUR art. 1.6.1.13.2.40 |
| **Estados financieros 2026** (grupo 3) aprobados por acta del accionista único | **31 mar 2027**, salvo otra fecha en los estatutos | CCo art. 422; Ley 1258 art. 22 par.; Decreto 2420 art. 1.1.3.1 |
| **Renovación de la matrícula mercantil** | **31 mar 2027** | [CCo art. 33](http://www.secretariasenado.gov.co/senado/basedoc/codigo_comercio_pr001.html) |
| **Renovación del RUP** (si está inscrito) | **7 abr 2027** (cálculo: 5.º día hábil de abril) | [Decreto 1082 de 2015, art. 2.2.1.1.1.5.1](https://www.cancilleria.gov.co/normograma/compilacion/docs/decreto_1082_2015.htm) |
| **Declaración anual SIMPLE 2026 (formulario 260)** | **21 abr 2027** (cálculo). Presentar antes del 15 abr. | DUR art. 1.6.1.13.2.50 |
| Dotación (si hay empleados de hasta 2 SMMLV) | 30 abr, 31 ago y 20 dic de 2027 | CST art. 232 |
| Exógena del año gravable 2026 (solo si se cumple un criterio) | Mayo–junio de 2027 **(no verificado; lo fija la DIAN)** | Res. 227 de 2025 |
| Anticipo SIMPLE ene–feb 2027 | **24 may 2027** (cálculo) | DUR art. 1.6.1.13.2.52 |
| Anticipo SIMPLE mar–abr 2027 | **22 jun 2027** (cálculo) | ídem |
| Prima, primera mitad | 30 jun 2027 | CST art. 306 |
| Recargo dominical y festivo pasa a 100 % | 1 jul 2027 | Ley 2466 art. 14 |
| Anticipo SIMPLE may–jun 2027 | **23 jul 2027** (cálculo) | DUR art. 1.6.1.13.2.52 |
| Anticipo SIMPLE jul–ago 2027 | **21 sep 2027** (cálculo) | ídem |
| Anticipo SIMPLE sep–oct 2027 | **23 nov 2027** (cálculo) | ídem |
| Prima, segunda mitad | Hasta el 20 dic 2027 | CST art. 306 |
| PILA (con empleados) | **8.º día hábil de cada mes** | Decreto 780 art. 3.2.2.1 |
| Formulario 350 en 2027 (meses con retención) | 15.º día hábil del mes siguiente | DUR art. 1.6.1.13.2.33 |
| Anticipo nov–dic 2027 (fuera del rango) | 24 ene 2028 (cálculo) | DUR art. 1.6.1.13.2.52 |

Reglas de cálculo de las fechas de 2027:
- Hábiles de lunes a viernes, con los festivos colombianos de la Ley Emiliani.
- La Semana Santa de 2027 es el 25 y 26 de marzo.
- En mayo de 2027 son festivos el 1 y el 10 (Ascensión) y el 31 (Corpus). En junio, el 7. En julio, el 5 y el 20. En noviembre, el 1 y el 15.
- **Hay que confirmar todo contra el calendario DIAN 2027.**

---

## 7. Contabilidad mínima: qué exige contador y qué puede llevar el dueño

**Exige contador público**
1. **Certificar los estados financieros** cuando se entregan a terceros: SECOP, RUP, bancos, clientes. Los firman el representante legal y el contador ([Ley 222 de 1995, art. 37](http://www.secretariasenado.gov.co/senado/basedoc/ley_0222_1995.html)). El RUP pide estados financieros suscritos por el representante legal y el "auditor o contador"; una sociedad nueva puede usar el estado de apertura o un corte trimestral (Decreto 1082, art. 2.2.1.1.1.5.2 num. 2.3). También pide un certificado de tamaño empresarial (num. 2.6).
2. **Repartir dividendos.** "En todo caso las utilidades se justificarán en estados financieros ... dictaminados por un contador público independiente" ([Ley 1258 de 2008, art. 28](http://www.secretariasenado.gov.co/senado/basedoc/ley_1258_2008.html)). Es clave para el plan del dueño.
3. Firmar la **declaración de IVA con saldo a favor**, o cuando el patrimonio o los ingresos superan 100.000 UVT (ET art. 602).
4. Certificar las relaciones de una **solicitud de devolución de IVA** por exportación (DUR art. 1.6.1.21.15).

**Puede hacerlo el dueño**
- Llevar la contabilidad en Odoo.
- Facturar y emitir documentos soporte en la solución DIAN.
- Presentar el 2593 y el 260: los firma el representante legal y **no requieren contador** (DUR art. 1.5.8.3.14).
- Presentar el formulario 300 sin saldo a favor.
- Pagar la PILA y hacer el reporte RUB, el RIT, la renovación de la matrícula y las actas del accionista único.
- No se verificó si la ley reserva al contador la teneduría de libros propiamente dicha (Ley 43 de 1990) **(no verificado)**.

**Revisor fiscal**: no aplica por ahora. La Ley 1258 lo exige solo "por exigencia de la ley". El umbral usual, activos de 5.000 SMMLV o ingresos de 3.000 SMMLV (Ley 43 de 1990, art. 13 par. 2), no se verificó en esta sesión **(no verificado)**.

**Marco contable: grupo 3** (Decreto 2420 de 2015, art. 1.1.3.1, modificado por el Decreto 1670 de 2021, [texto](https://www.cancilleria.gov.co/normograma/compilacion/docs/decreto_2420_2015.htm))
- Aplica a microempresas según el Decreto 957 de 2019: en servicios, ingresos de hasta **32.988 UVT** ($1.727.713.512 en 2026) ([Decreto 957 de 2019](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=94550)).
- Una entidad nueva puede quedarse en el grupo 3 **hasta 3 años** aunque no cumpla los requisitos.
- Libros de comercio: la contabilidad es obligatoria (CCo art. 19). Solo se registran en la CCB los libros de actas y de accionistas (CCo art. 28 num. 7).
- Nota Odoo: los informes de libro mayor, balance y estado de resultados de Odoo están en `account_reports`, que es Enterprise (404 en la rama 19.0 Community). Para verlos sin costo habría que usar módulos de la OCA, como `account-financial-reporting` o `mis_builder` **(no verificada su disponibilidad para la v19)**.

---

## 8. Costos inevitables (cero gasto en software)

- **Renovación de la matrícula mercantil** en la CCB, según los activos.
  - Exenta la primera renovación si es "pequeña empresa joven": más del 50 % del capital en manos de menores de 35 años (Ley 1780 de 2016, arts. 2 y 3).
  - Bogotá daba un descuento parcial hasta el año gravable 2026 (Acuerdo 780, art. 13).
- **Inscripción y renovación del RUP** y del libro de actas y el de registro de accionistas en la CCB (valor no verificado).
- **Contador público** para certificar y dictaminar estados financieros, con más razón antes de repartir dividendos o inscribir el RUP. Firma además el IVA con saldo a favor.
- **SG-SST**: diseñador con licencia en SST (la ARL puede apoyar sin costo, **no verificado**) y **exámenes médicos ocupacionales** por empleado.
- **Pólizas** cuando las exija la entidad, y **estampillas** en contratos territoriales (documento local).
- Gratis según la DIAN: factura, notas, documento soporte y nómina en la solución gratuita; certificado de firma; IFE.
- La PILA electrónica sin costo para el aportante está **(no verificado)**.

---

## 9. Datos para configurar Odoo

**Impuestos de venta**
- IVA 19 % para desarrollo, soporte, licencias y cursos.
- **0 % excluido (art. 476 num. 21)** para SaaS, hosting y nube que cumpla los criterios.
- **0 % exento (art. 481 lit. c)** para exportación, con una posición fiscal "Cliente del exterior".
- Retención de IVA del 15 % sufrida, que equivale a −2,85 % de la base cuando el IVA es 19 %. `l10n_co` ya trae "15 % RteVAT 19 %".
- **Desactivar retención de renta y de ICA en ventas** (ET art. 911).

**Compras**
- No aplicar retención de renta ni de ICA, salvo nómina.
- Retención de IVA del 15 % solo al comprar servicios gravados a proveedores del SIMPLE.
- Separar el IVA descontable ligado a ingresos excluidos (SaaS), que no se puede descontar, del ligado a ingresos gravados o exentos, que sí.

**SIMPLE**
- No es un impuesto de factura. Se provisiona por bimestre con la tarifa del tramo sobre los ingresos brutos.
- Al anticipo se le restan el aporte a pensión del empleador y el descuento del 0,5 % por ingresos electrónicos.
- El IVA neto por pagar se transfiere en el mismo 2593.

**Diarios**
- Secuencias con el prefijo y el rango autorizados por la DIAN.
- Campo CUFE y adjuntos XML y PDF.
- Un diario aparte para el documento soporte, con su propia numeración.

**Nómina**
- Odoo Community no trae nómina.
- Fase 0, ahora: contratista. Contrato, afiliación a la ARL por Lumak, verificación de la PILA (40 %) antes de cada pago, documento soporte y SG-SST básico.
- Fase 1, primer empleado: liquidar en una hoja de cálculo o en un módulo propio o de la OCA.
- Pagar la PILA el 8.º día hábil.
- Descontar la pensión del 2593.
- Sin nómina electrónica mientras Lumak esté en el SIMPLE.
