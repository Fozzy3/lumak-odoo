# Módulos libres (LGPL/AGPL) para Odoo 19.0 Community — estado a 27-sep-2026

Método: clonado de las ramas `19.0` de OCA (y `18.0` para comparar), lectura de `__manifest__.py`, README y `git log`; PRs abiertos vía API de GitHub; código fuente de `odoo/odoo` rama 19.0 (HEAD `4e7b84d`, 2026-09-26).

Convenciones:
- **Madurez**: sale del badge del README OCA. Si el manifiesto no declara `development_status`, OCA lo publica como **Beta**.
- **"Última actividad"**: último commit que toca la carpeta del módulo (incluye commits de bots y traducciones).
- **"Merge 19.0"**: primer merge del módulo en la rama 19.0.
- **(no verificado)**: no pude confirmarlo en código ni en una fuente primaria.

Los módulos que no están en `odoo/odoo` 19.0 son de Enterprise. Verifiqué que no existen: `sign`, `documents`, `knowledge`, `account_accountant`, `account_reports`, `hr_payroll`, `hr_appraisal`, `planning`, `helpdesk`, `l10n_co_edi`, `l10n_co_dian`, `l10n_co_reports`, `hr_contract`.

---

## 1. Firma electrónica

| Repo | Módulo | ¿En 19.0? | Madurez | Merge 19.0 / última actividad | Qué da |
|---|---|---|---|---|---|
| odoo/odoo (core, LGPL) | `sale`: `require_signature` / `portal_confirmation_sign` | Sí, core Community | Estable (core) | HEAD 2026-09-26 | El cliente firma la cotización en el portal (ruta JSON-RPC `/my/orders/<id>/accept`) y la orden se confirma. La firma se incrusta en el PDF. Se activa en Ajustes de Ventas con "Online Signature" (por defecto `True`). |
| [OCA/sign](https://github.com/OCA/sign/tree/19.0/sign_oca) | `sign_oca` (AGPL-3) | **Sí, merged** (PR #155) | Beta | 2026-06-04 / 2026-06-04 | Plantillas PDF con campos, roles y firmantes internos o externos por portal, y solicitud de firma desde cualquier modelo. Guarda un hash SHA por firmante. **No hace firma PKI con certificado**: el ROADMAP propone pyHanko y OTP, sin implementar. Solo depende de `portal`. |
| OCA/sign | `agreement_sign_oca`, `project_task_sign_oca` | No (existen en 18.0) | — | — | Integraciones con otros módulos, sin migrar. |
| OCA/sign | `sign_docuseal` (conector a DocuSeal, autoalojado, AGPL) | No. Solo el PR [#164](https://github.com/OCA/sign/pull/164) para **16.0** | — | PR 2026-08-13 | Alternativa con firma más robusta. No hay versión 19.0. |

Evidencia core: [`sale/models/sale_order.py`](https://github.com/odoo/odoo/blob/19.0/addons/sale/models/sale_order.py) (`require_signature` se calcula desde `company.portal_confirmation_sign`), [`sale/controllers/portal.py`](https://github.com/odoo/odoo/blob/19.0/addons/sale/controllers/portal.py) (`portal_quote_accept`) y [`sale/models/res_company.py`](https://github.com/odoo/odoo/blob/19.0/addons/sale/models/res_company.py).

**Recomendación:** para cotizaciones, usar la firma nativa del portal de `sale`, que es gratis y estable. Para contratos o actas, usar `sign_oca` 19.0 (Beta). Es una firma manuscrita sobre PDF con hash, no una firma digital certificada. Su valor probatorio como firma electrónica en Colombia (Ley 527/1999, Decreto 2364/2012) depende del mecanismo de autenticación que se use (no verificado jurídicamente).

---

## 2. Nómina

| Repo | Módulo | ¿En 19.0? | Madurez | Merge 19.0 / última actividad | Qué da |
|---|---|---|---|---|---|
| [OCA/payroll](https://github.com/OCA/payroll/tree/19.0/payroll) | `payroll` (LGPL-3) | **Sí, merged** (PR #227) | Beta | 2026-04-27 / 2026-09-25 | Motor genérico de nómina (backport del antiguo `hr_payroll` de Odoo SA): estructuras, reglas salariales, nóminas y lotes. Trabaja sobre `hr.version`. **Sin reglas colombianas.** |
| OCA/payroll | `payroll_account` | **No. Hay 3 PRs abiertos que compiten:** [#260](https://github.com/OCA/payroll/pull/260), [#269](https://github.com/OCA/payroll/pull/269), [#294](https://github.com/OCA/payroll/pull/294) | — | PRs de may–sep 2026 | Asientos contables de la nómina. Hoy no existe en 19.0. |
| OCA/payroll | `payroll_hr_public_holidays`, `payroll_contract_advantages`, `hr_payroll_document` | No, solo PRs abiertos (#278, #277, #279) | — | — | Extensiones. |
| [OCA/account-financial-tools](https://github.com/OCA/account-financial-tools/tree/19.0/account_payroll_sheet_import) | `account_payroll_sheet_import` (AGPL-3) | **Sí, merged** (PR #2363) | Beta | 2026-07-28 / 2026-08-17 | Importa la nómina desde una hoja de cálculo y genera el asiento contable. Depende solo de `account` y `hr`. |
| [OCA/l10n-colombia](https://github.com/OCA/l10n-colombia/pull/19) | `l10n_co_hr_payroll` | **No.** PR #19 contra **16.0**, abierto desde 2023-10 y abandonado | — | 2023-10-13 | Nómina colombiana. No existe para 19.0. |
| [jorels-community/jorels-odoo-addons](https://github.com/jorels-community/jorels-odoo-addons/tree/19.0) | `l10n_co_hr_payroll` (manifiesto AGPL-3; el README dice LGPL) | Sí, rama 19.0 (no es OCA) | "En producción" según el autor | última 2026-06-26 | Nómina colombiana con modelo propio `hr.payslip` y nómina electrónica. **El envío a la DIAN pasa por la API de Jorels (`edipo.jorels.com`) con token de pago por consumo.** No sé si el cálculo local funciona sin token (no verificado). |
| [creandowebcolombia/l10n_co_airdav_payroll](https://github.com/creandowebcolombia/l10n_co_airdav_payroll) | nómina electrónica "sin terceros" | **No.** Solo rama 18.0, sin licencia declarada en GitHub | — | push 2026-02-14 | No sirve para 19.0. |

Otras vías:
- **Solución gratuita de Nómina Electrónica de la DIAN** ([micrositio](https://micrositios.dian.gov.co/sistema-de-facturacion-electronica/solucion-gratuita-de-nomina-electronica/)). La DIAN entrega gratis el certificado para usarlo dentro de su solución. Requisitos: estar inscrito en el RUT y habilitado antes como facturador electrónico.
- **Community 19:** `hr_payroll` es Enterprise y `hr_contract` ya no existe (se fusionó en `hr` como `hr.version`).

**Recomendación:** no existe hoy en 19.0 una nómina colombiana libre y completa (cálculo, contabilidad y DIAN) sin pagar a terceros. Para una empresa con pocos empleados, lo más simple es:
1. Liquidar la nómina en una hoja de cálculo.
2. Emitir el documento soporte con la solución gratuita de la DIAN.
3. Contabilizar en Odoo con `account_payroll_sheet_import`.

---

## 3. Contabilidad: reportes y conciliación bancaria

Qué trae **Odoo 19 Community**, verificado en código:
- Solo la app "Invoicing". Los comentarios de [`account/security/account_security.xml`](https://github.com/odoo/odoo/blob/19.0/addons/account/security/account_security.xml) dicen que la conciliación bancaria básica llega con `account_accountant`, que es Enterprise. Con solo `account`, los grupos contables "solo son visibles vía server action".
- **No hay widget de conciliación bancaria** (`account.reconcile.wizard` no existe en `account`).
- **No hay P&L ni Balance general.** [`account/data/account_reports_data.xml`](https://github.com/odoo/odoo/blob/19.0/addons/account/data/account_reports_data.xml) solo define el reporte genérico de impuestos. El menú "Statement Reports" queda vacío sin `account_reports` (Enterprise).
- Sí incluye: "Invoice Analysis", "Analytic Report" y el casado de pagos con facturas desde la propia factura.

| Repo | Módulo | ¿En 19.0? | Madurez | Merge 19.0 / última actividad | Qué da |
|---|---|---|---|---|---|
| [OCA/account-financial-tools](https://github.com/OCA/account-financial-tools/tree/19.0/account_usability) | `account_usability` | **Sí** (PR #2174) | Beta | 2025-12-22 / 2026-08-07 | Muestra los menús ocultos en CE (extractos bancarios, grupos, etiquetas) y el grupo "Show Full Accounting Features". |
| [OCA/account-financial-reporting](https://github.com/OCA/account-financial-reporting/tree/19.0/account_financial_report) | `account_financial_report` | **Sí** (PR #1413) | Beta | 2026-01-28 / 2026-09-15 | Libro mayor, balance de prueba, partidas abiertas, cartera por edades, reporte de IVA y libro diario, en PDF y XLSX. Depende de `date_range` (server-ux) y `report_xlsx` (reporting-engine), ambos en 19.0. |
| OCA/account-financial-reporting | `account_tax_balance` | **Sí** | Mature | — / 2026-08-16 | Saldos de impuestos por rango de fechas. |
| OCA/account-financial-reporting | `partner_statement` | **Sí** | Beta | — / 2026-08-16 | Estados de cuenta de clientes y proveedores. |
| [OCA/mis-builder](https://github.com/OCA/mis-builder/tree/19.0/mis_builder) | `mis_builder`, `mis_builder_budget` | **Sí** | **Production/Stable** | 2025-09-26 / 2026-09-21 | Motor de reportes tipo P&L, Balance y KPI con periodos en columnas; exporta a PDF y XLSX. |
| OCA/account-financial-reporting | `mis_template_financial_report` (plantillas P&L y Balance para MIS) | **No.** PR [#1485](https://github.com/OCA/account-financial-reporting/pull/1485) abierto | — | PR 2026-03-16, actualizado 2026-09-21 | Mientras tanto, el P&L y el Balance hay que armarlos a mano como plantilla MIS. |
| OCA/account-financial-reporting | `mis_builder_cash_flow` | Sí en rama; también hay PR #1484 | Beta | — / 2026-09-07 | Flujo de caja proyectado. |
| [OCA/account-reconcile](https://github.com/OCA/account-reconcile/tree/19.0/account_reconcile_oca) | `account_reconcile_oca` + `account_statement_base` | **Sí** (PR #974 / #924) | Beta / Mature | 2026-04-13 / 2026-09-21 | **Widget de conciliación bancaria para CE.** |
| OCA/account-reconcile | `account_mass_reconcile`, `account_reconcile_model_oca`, `account_partner_reconcile` y otros | No (en 18.0). Varios PRs abiertos (#982–#992) | — | — | Conciliación masiva y extras. |
| [OCA/bank-statement-import](https://github.com/OCA/bank-statement-import/tree/19.0) | `account_statement_import_file`, `..._sheet_file` (CSV/XLSX), `..._camt`, `..._qif`, `..._file_reconcile_oca` | **Sí** | file: Mature; resto: Beta | sheet: 2026-05-21 / 2026-07-08 | Importar extractos. `sheet_file` sirve para los Excel/CSV de bancos colombianos. |
| OCA/bank-statement-import | `account_statement_import_ofx` | **No.** PR [#924](https://github.com/OCA/bank-statement-import/pull/924) abierto | — | — | OFX. |
| OCA/account-financial-tools | `account_asset_management` (Mature), `account_fiscal_year` (Prod/Stable), `account_chart_update`, `account_move_name_sequence` | **Sí** | varias | — | Activos fijos, años fiscales, actualización del plan de cuentas. |

**Recomendación:** instalar `account_usability`, `account_financial_report`, `mis_builder`, `account_reconcile_oca` y `account_statement_import_sheet_file`. Todo está merged en 19.0 y es libre. El único faltante relevante es la plantilla P&L/Balance: se arma una plantilla MIS propia con los grupos del PUC o se espera el PR #1485.

---

## 4. Localización colombiana y facturación electrónica DIAN

**Core [`l10n_co`](https://github.com/odoo/odoo/tree/19.0/addons/l10n_co) en 19 Community (LGPL-3)**, verificado en código:
- **Plan de cuentas PUC:** 378 cuentas y 401 grupos (ids `co_puc_*`), con contabilidad anglosajona activada.
- **Impuestos (65 plantillas):**
  - IVA 19%, 5% y 0% (exento/excluido).
  - INC 4%, 8% y 16%.
  - **ReteFuente:** unas 35 tarifas (servicios, honorarios, compras, arrendamientos, software 3.5%, etc.).
  - **ReteIVA 15%.**
  - **ReteICA:** 0.414%, 0.69%, 0.966%, 1.104% y 1.38%.
  - Grupos de impuestos "R REN", "R IVA" y "R ICA".
  - No sé si aplica bases mínimas en UVT automáticamente (no verificado; no vi lógica para eso).
- **Tipos de identificación** (`l10n_latam.identification.type` con `l10n_co_document_code`): NIT, CC, RC, TI, TE, CE, pasaporte, PEP, PPT, NIUP, NIT de otro país y cédula extranjera.
- El NIT y su dígito de verificación se validan con `base_vat`, que usa `stdnum co.vat`.
- **Sin campos DIAN de facturación electrónica:** CUFE, resolución, responsabilidades fiscales y CIIU no están. `l10n_co_edi` (Carvajal), `l10n_co_dian` (software propio directo) y `l10n_co_reports` son **Enterprise** ([docs 19.0](https://www.odoo.com/documentation/19.0/applications/finance/fiscal_localizations/colombia.html)).

| Repo | Módulo | ¿En 19.0? | Madurez | Merge 19.0 / última actividad | Qué da |
|---|---|---|---|---|---|
| [OCA/l10n-colombia](https://github.com/OCA/l10n-colombia/tree/19.0) | `l10n_co_electronic_invoice` (AGPL-3) | **Sí, merged** (PR [#26](https://github.com/OCA/l10n-colombia/pull/26)) | Beta | 2026-04-03 / 2026-04-03 | Datos maestros DIAN: CIIU, UNSPSC, responsabilidades y tipos de impuesto DIAN, medios de pago, ciudades/departamentos DIAN y UoM UNECE. |
| OCA/l10n-colombia | `l10n_co_electronic_invoice_self` (AGPL-3) | **Sí, merged** (PR #26) | Beta | 2026-04-03 / 2026-04-03 | **FE directa con la DIAN en modo software propio.** Detalle debajo de la tabla. |
| OCA/l10n-colombia | `l10n_co_withholding_advance` | **Sí** | Beta | 2026-02-06 / 2026-02-07 | Autorretención en facturas de venta. |
| OCA/l10n-colombia | `l10n_co_withholding`, `l10n_co_verification_digit`, `l10n_co_check_vat`, `l10n_co_currency_rate_update` (TRM) | **No** (existen en 18.0) | — | — | Retenciones extra, dígito de verificación y TRM. Sin migrar. |
| [jorels-community/jorels-odoo-addons](https://github.com/jorels-community/jorels-odoo-addons/tree/19.0) | `l10n_co_edi_jorels` (LGPL-3) | Sí, rama 19.0 (no OCA) | "En producción" según el autor | 2026-07-28 | FE, RADIAN y POS. El código es libre, pero **el envío pasa por la API de pago de Jorels**. |

Detalle de `l10n_co_electronic_invoice_self`:
- **Funciones:** XML UBL 2.1, firma XAdES-EPES, SOAP con WS-Security, SendTestSetAsync/SendBillSync, GetStatus y GetNumberingRange, AttachedDocument, eventos RADIAN (030 a 033), importación de XML de proveedores y PDF gráfico.
- **Documentos:** factura (01), exportación (02), nota crédito (91), nota débito (92), documento soporte (05) y nota de ajuste (95).
- **Dependencias:** `account_edi`, `account_edi_ubl_cii` y `certificate` (todos core CE 19) más librerías Python (`xmlsig`, `cryptography`, `xmltodict` y otras).

Riesgo del módulo OCA de FE:
- Un solo autor (Yan Chirino, IKU Solutions).
- El PR #26 (+62.711 líneas) **lo fusionó el propio autor, con 0 revisiones**.
- No hay commits desde 2026-04-03.
- Funcionalmente es lo que se necesita, pero es código no revisado. Antes de producción hay que probarlo a fondo en habilitación.

Qué exige el modo software propio:
- **Registro y habilitación en el portal de la DIAN (gratis).** Se registra el software y se obtienen Software ID, PIN y TestSetId; luego se pasa el set de pruebas.
- **Resolución de numeración (gratis).**
- **Certificado de firma digital de una entidad acreditada por ONAC (pago anual).** Certicámara, GSE o Andes SCD cobran aprox. **$120.000–$300.000 COP al año**, según [POS Colombia](https://poscolombia.com/blog/certificado-digital-dian-donde-comprar-cuanto-cuesta). La cifra de Andes SCD ($250.000 + IVA al año) sale de un resultado de búsqueda (no verificado en su web).

Alternativa sin costo: la solución gratuita de facturación de la DIAN, por fuera de Odoo. Que incluya certificado gratis para facturación (como sí pasa en nómina) está sin verificar.

**Recomendación:** usar `l10n_co` core para contabilidad e impuestos. Para FE, evaluar `l10n_co_electronic_invoice_self` en ambiente de habilitación. Si el volumen es bajo, facturar en la solución gratuita de la DIAN y registrar en Odoo es lo más seguro por ahora.

---

## 5. Gestión documental y descarga ZIP

| Repo | Módulo | ¿En 19.0? | Madurez | Merge 19.0 / última actividad | Qué da |
|---|---|---|---|---|---|
| odoo (Enterprise) | `documents` | **No existe en Community** | — | — | Solo Enterprise. |
| [OCA/dms](https://github.com/OCA/dms/tree/19.0/dms) | `dms` (LGPL-3) | **Sí, merged** (PR #475) | Beta | **2026-09-03** (muy reciente) / 2026-09-08 | Repositorios, directorios y archivos con permisos, acceso por portal y enlaces con token para compartir. |
| OCA/dms | `dms_field` (DMS dentro de cualquier registro), `hr_dms_field`, `dms_user_role`, `dms_auto_classification` | **No.** PRs abiertos [#486](https://github.com/OCA/dms/pull/486), #489, #488 y #485 | — | PRs 2026-06-22 | Extensiones. |
| [OCA/knowledge](https://github.com/OCA/knowledge/tree/19.0/attachment_zipped_download) | `attachment_zipped_download` (AGPL-3) | **Sí** (PR #579) | Beta | 2026-03-19 / 2026-06-26 | Descargar varios adjuntos seleccionados como ZIP (Ajustes → Técnico → Adjuntos → Acción "Download") y un mixin para añadir ese botón a cualquier modelo. |
| OCA/knowledge | `document_page`, `document_knowledge` | **Sí** | Beta | — / 2026-09-01 | Wiki o páginas de documentación simples. |

**ZIP en el chatter (core 19):** la ruta existe y es **`/mail/attachment/zip`**, definida en [`mail/controllers/attachment.py`](https://github.com/odoo/odoo/blob/19.0/addons/mail/controllers/attachment.py):
- Método: `http`, POST, `auth="public"`.
- Parámetros: `file_ids` (ids separados por coma) y `zip_name`.
- En la UI aparece como la acción **"Download Files"** de un **mensaje** que tenga más de un adjunto, solo para usuarios internos ([`message_actions.js`](https://github.com/odoo/odoo/blob/19.0/addons/mail/static/src/core/common/message_actions.js)).
- **No hay un botón "descargar todos los adjuntos del registro"** en la caja de adjuntos. La ruta sí acepta cualquier lista de ids, así que un botón propio de pocas líneas o `attachment_zipped_download` cubren ese caso.

**Recomendación:** empezar con los adjuntos del chatter y la descarga ZIP nativa. Agregar `dms` solo si hace falta un árbol de carpetas o compartir por portal; es Beta y recién migrado.

---

## 6. Recursos humanos en 19 Community

Todo lo siguiente está en `odoo/odoo` 19.0 con licencia **LGPL-3**, es decir, Community:

| Módulo core | Estado en 19 CE | Qué da |
|---|---|---|
| `hr` | Community | Empleados, departamentos y cargos. **Los contratos se fusionaron en `hr` como `hr.version`** ([`hr_version.py`](https://github.com/odoo/odoo/blob/19.0/addons/hr/models/hr_version.py)): `date_version`, `contract_date_start/end`, `wage`, `contract_type_id`, `structure_type_id` y `resource_calendar_id`. `hr_contract` ya no existe. |
| `hr_timesheet` | Community | Partes de horas por proyecto o tarea. |
| `hr_expense` | Community | Gastos de empleados con aprobación y refacturación. |
| `hr_holidays` | Community | Ausencias y asignaciones. |
| `hr_skills` | Community | Habilidades y hoja de vida. |
| `hr_recruitment` | Community | Pipeline de reclutamiento. |
| `hr_attendance`, `hr_work_entry`, `hr_homeworking`, `hr_org_chart` | Community | Asistencia, entradas de trabajo, teletrabajo y organigrama. |
| `hr_payroll`, `hr_appraisal`, `planning` | **Enterprise** (ausentes en odoo/odoo 19.0) | — |

OCA útil en 19.0 (todo Beta):
- `hr_employee_firstname` y `hr_employee_second_lastname`: nombres y dos apellidos, útil en Colombia.
- `hr_employee_document`: documentos del empleado.
- `hr_holidays_public`: festivos. Depende de `calendar_public_holiday`, disponible en OCA/calendar 19.0.

El repo OCA/hr-expense 19.0 no tiene módulos todavía.

**Recomendación:** el core cubre lo necesario. Agregar `hr_employee_second_lastname` y `hr_holidays_public` para los festivos colombianos.

---

## 7. Proyectos: hitos, `sale_project` y plantillas

Todo es core Community (LGPL-3), verificado en código:
- **Facturación por hitos:** la política de servicio `delivered_milestones` ("Based on Milestones") aparece si el grupo de hitos está activo ([`sale_project/models/product_template.py`](https://github.com/odoo/odoo/blob/19.0/addons/sale_project/models/product_template.py)). La línea de venta usa `qty_delivered_method = 'milestones'`: la cantidad entregada es la suma de `quantity_percentage` de los hitos alcanzados multiplicada por la cantidad pedida.
- **Proyecto desde plantilla al confirmar la venta:** el producto tiene el campo **`project_template_id`** (dominio `is_template = True`) y `service_tracking` (`project_only` o `task_in_project`). Al confirmar, `_action_confirm` llama a `_timesheet_service_generation`, que usa `project_template.action_create_from_template(values)` ([`sale_order_line.py`](https://github.com/odoo/odoo/blob/19.0/addons/sale_project/models/sale_order_line.py)).
- **Plantillas de proyecto:** en `project` core, con `is_template`, `action_toggle_project_template_mode` ("Convert to Template") y `action_create_from_template`. **Son Community.**
- **Matiz:** los hitos se copian de la plantilla (`milestone_ids` con `copy=True`). El código que revisé enlaza las **tareas** con la línea de venta, pero no asigna `sale_line_id` a los **hitos** copiados. Probablemente hay que asignarlo a mano o con el default del contexto (no verificado en ejecución).
  - **Corrección (verificado después):** sí los enlaza. `sale_order_line._handle_milestones` asigna `sale_line_id` a los hitos copiados que no lo tengan y reparte la cantidad entre ellos. Lo prueba `test_award_confirms_quotation_and_opens_contract_project` en `addons/lumak_secop/tests/test_contratos.py`.

| Repo | Módulo | ¿En 19.0? | Madurez | Merge 19.0 / última actividad | Qué da |
|---|---|---|---|---|---|
| [OCA/project](https://github.com/OCA/project/tree/19.0/project_milestone_status) | `project_milestone_status` | **Sí** (PR #1700) | Beta | 2026-05-04 / 2026-07-03 | Porcentaje de ejecución del proyecto por hitos. Depende de `hr_timesheet`. |
| OCA/project | `sale_project_copy_tasks` (LGPL-3) | **Sí** (PR #1646) | Beta | 2026-05-29 / 2026-07-03 | Copia las tareas de la plantilla en un proyecto **existente** desde la venta. |
| OCA/project | `project_type`, `project_timeline` (depende de `web_timeline`, en OCA/web 19.0) | **Sí** | Beta | — / 2026-08-25 | Tipos de proyecto y vista de línea de tiempo. |

**Recomendación:** el core 19 CE ya cubre el flujo "venta → proyecto desde plantilla → facturar por hitos". Solo hay que probar el enlace hito ↔ línea de venta cuando los hitos vienen de la plantilla.

---

## Fuentes principales
- Ramas OCA 19.0: sign, payroll, l10n-colombia, account-financial-reporting, mis-builder, account-reconcile, bank-statement-import, account-financial-tools, dms, knowledge, project, hr, hr-holidays, timesheet, server-ux, reporting-engine, web y calendar (clonadas el 2026-09-27).
- `odoo/odoo` rama 19.0, commit `4e7b84d` (2026-09-26).
- Documentación de Odoo 19, Colombia: https://www.odoo.com/documentation/19.0/applications/finance/fiscal_localizations/colombia.html
- Jorels: https://www.jorels.com/edi y https://github.com/jorels-community/jorels-odoo-addons
- Solución gratuita de nómina electrónica de la DIAN: https://micrositios.dian.gov.co/sistema-de-facturacion-electronica/solucion-gratuita-de-nomina-electronica/
- Costo del certificado: https://poscolombia.com/blog/certificado-digital-dian-donde-comprar-cuanto-cuesta
