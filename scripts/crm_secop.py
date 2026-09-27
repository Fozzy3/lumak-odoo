"""Configura el CRM de licitaciones SECOP en el Odoo local de Lumak.

Uso: python3 scripts/crm_secop.py
Idempotente: cada registro lleva un ID externo `lumak.*`; si ya existe se actualiza, no se duplica.
Detalle y fuentes del diseño: docs/licitaciones-secop.md
"""
import os
import xmlrpc.client

URL = os.environ.get("ODOO_URL", "http://127.0.0.1:8069")
DB = os.environ.get("ODOO_DB", "lumak")
USER = os.environ.get("ODOO_USER", "admin")
PWD = os.environ.get("ODOO_PASSWORD", "admin")

# ponytail: XML-RPC está deprecado en Odoo 19 y se elimina en Odoo 22; migrar a /json/2 entonces
UID = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common").authenticate(DB, USER, PWD, {})
RPC = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def call(model, method, *args, **kw):
    return RPC.execute_kw(DB, UID, PWD, model, method, list(args), kw)


def ref(xmlid):
    module, name = xmlid.split(".")
    rec = call("ir.model.data", "search_read", [["module", "=", module], ["name", "=", name]], fields=["res_id"])
    return rec[0]["res_id"]


def ensure(name, model, vals):
    """Crea o actualiza el registro con ID externo lumak.<name>."""
    imd = call("ir.model.data", "search_read", [["module", "=", "lumak"], ["name", "=", name]], fields=["res_id"])
    if imd and call(model, "search_count", [["id", "=", imd[0]["res_id"]]]):
        call(model, "write", [imd[0]["res_id"]], vals)
        return imd[0]["res_id"]
    call("ir.model.data", "unlink", [i["id"] for i in imd]) if imd else None
    rid = call(model, "create", vals)
    call("ir.model.data", "create", {"module": "lumak", "name": name, "model": model, "res_id": rid, "noupdate": True})
    return rid


# --- Equipo y campos propios (propiedades) -------------------------------------------------
PROPIEDADES = [
    {"name": "numero_proceso", "string": "N.º de proceso", "type": "char", "view_in_cards": True},
    {"name": "enlace_secop", "string": "Enlace SECOP II", "type": "char"},
    {"name": "modalidad", "string": "Modalidad", "type": "selection", "selection": [
        ["minima", "Mínima cuantía"], ["samc", "Selección abreviada menor cuantía"],
        ["licitacion", "Licitación pública"], ["concurso", "Concurso de méritos"],
        ["directa", "Contratación directa"], ["especial", "Régimen especial"]]},
    {"name": "unspsc", "string": "Código UNSPSC", "type": "char"},
    {"name": "presupuesto", "string": "Presupuesto oficial", "type": "float"},
    {"name": "limite_observaciones", "string": "Límite de observaciones", "type": "datetime"},
    {"name": "cierre", "string": "Cierre (fecha y hora)", "type": "datetime", "view_in_cards": True},
    {"name": "limitado_mipyme", "string": "¿Limitado a MiPyME?", "type": "boolean"},
    {"name": "pago_contra_entrega", "string": "Pago contra entrega", "type": "boolean"},
    {"name": "exige_garantias", "string": "Exige garantías", "type": "boolean"},
    {"name": "estampillas", "string": "Estampillas (%)", "type": "float"},
    {"name": "oferentes", "string": "N.º de oferentes", "type": "integer"},
    {"name": "precio_ganador", "string": "Precio ganador", "type": "float"},
]
equipo = ensure("team_secop", "crm.team", {
    "name": "Licitaciones SECOP", "use_leads": False, "use_opportunities": True,
    "lead_properties_definition": PROPIEDADES,
})

# Las etapas por defecto de Odoo son globales: se dejan solo para el equipo de Ventas.
ventas = ref("sales_team.team_sales_department")
for etapa_std in ("crm.stage_lead1", "crm.stage_lead2", "crm.stage_lead3", "crm.stage_lead4"):
    call("crm.stage", "write", [ref(etapa_std)], {"team_ids": [[6, 0, [ventas]]]})

# --- Etapas (nombre, días antes de marcar estancado, qué debe estar listo) ------------------
ETAPAS = [
    ("detectado", "Detectado", 1,
     "Número de proceso, enlace, entidad (contacto), modalidad y fecha y hora de cierre. "
     "En SECOP II: clic en «Suscribirme»; sin eso no se puede observar ni ofertar."),
    ("evaluando", "Evaluando", 1,
     "Leer la invitación: objeto, presupuesto, experiencia, garantías, forma de pago y estampillas. "
     "Descartar si está limitado a MiPyME (Lumak no es elegible hasta el 26 sep 2027) o cubierto por "
     "acuerdo marco. Observaciones dentro del plazo. Si no vamos: marcar perdido con el motivo."),
    ("preparando", "Preparando oferta", 1,
     "Lanzar el plan «Oferta mínima cuantía» con la fecha de cierre. Kit al día: certificado de "
     "existencia de 30 días o menos, aportes art. 50, antecedentes. "
     "Precio: base sin IVA ≥ costo ÷ (1 − 0,073 − estampillas); la lista de precios de SECOP debe ser igual al anexo."),
    ("presentada", "Oferta presentada", 3,
     "Estado «Presentada» verificado en SECOP II. Si una adenda cambia el cuestionario: retirar y volver "
     "a presentar. Lanzar el plan «Después del cierre»."),
    ("evaluacion", "En evaluación", 3,
     "Revisar el informe de evaluación. Subsanar por «Mensajes» dentro del plazo preclusivo (la oferta "
     "económica nunca se subsana). Registrar n.º de oferentes y precio ganador."),
    ("adjudicado", "Adjudicado", 0,
     "Aprobar el contrato electrónico con el usuario del representante legal. Crear el proyecto desde la "
     "plantilla «Contrato SECOP»."),
]
for seq, (key, nombre, dias, requisitos) in enumerate(ETAPAS, start=1):
    ensure(f"stage_{key}", "crm.stage", {
        "name": nombre, "sequence": 100 + seq, "team_ids": [[6, 0, [equipo]]], "requirements": requisitos,
        "rotting_threshold_days": dias, "is_won": key == "adjudicado",
    })

# --- Motivos de pérdida y etiquetas --------------------------------------------------------
for key, nombre in [
    ("no_ofertamos", "Decidimos no ofertar"), ("mipyme", "Limitado a MiPyME (no elegible)"),
    ("acuerdo_marco", "Cubierto por acuerdo marco"), ("precio", "Otro oferente con menor precio"),
    ("no_subsano", "No subsanamos a tiempo"), ("no_subsanable", "Rechazada por requisito no subsanable"),
    ("precio_bajo", "Precio artificialmente bajo"), ("desierto", "Proceso desierto"),
    ("cancelado", "Proceso cancelado o revocado"), ("tarde", "Llegamos tarde al cierre"),
]:
    ensure(f"lost_{key}", "crm.lost.reason", {"name": nombre})

for key, nombre, color in [
    ("software", "Software a la medida", 4), ("saas", "SaaS", 10), ("soporte", "Soporte y mantenimiento", 2),
    ("capacitacion", "Capacitación", 3), ("territorial", "Territorial", 7), ("nacional", "Nacional", 8),
    ("sim", "SIM", 1),
]:
    ensure(f"tag_{key}", "crm.tag", {"name": nombre, "color": color})

# --- Planes de actividades (fechas contadas desde el cierre) --------------------------------
TODO, DOC = ref("mail.mail_activity_data_todo"), ref("mail.mail_activity_data_upload_document")
PLANES = {
    "plan_oferta_mc": ("Oferta mínima cuantía", "before_plan_date", [
        (TODO, 2, "Leer la invitación y decidir si vamos",
         "Objeto, presupuesto, experiencia, garantías, forma de pago, estampillas. ¿Limitado a MiPyME?"),
        (TODO, 2, "Enviar observaciones en SECOP II (si hay dudas)", "Pestaña «Observaciones», dentro del plazo."),
        (DOC, 1, "Certificado de existencia (30 días o menos)", "CCB en línea, $12.100."),
        (DOC, 1, "RUT actualizado con responsabilidad 47", "La 47 evita retención en la fuente y de ICA."),
        (DOC, 1, "Cédula del representante legal", ""),
        (DOC, 1, "Antecedentes: Procuraduría y Contraloría (empresa y RL), Policía, RNMC y REDAM", "Gratis; regenerar por oferta."),
        (DOC, 1, "Certificación de aportes (Ley 789 art. 50)", "Firma el RL; cubre desde la constitución."),
        (DOC, 1, "Certificación bancaria", "Caja Social, gratis en línea."),
        (DOC, 1, "Certificación MiPyME (desempate)", "RL + contador, con corte al mes anterior."),
        (DOC, 1, "Experiencia exigida (certificaciones, actas o contratos)", "Solo contratos ejecutados antes del cierre."),
        (DOC, 1, "Carta de presentación firmada", ""),
        (DOC, 1, "Formatos de la invitación", "Anticorrupción, inhabilidades, conflicto de intereses, anexo técnico."),
        (TODO, 1, "Precio final y lista de precios",
         "Lista de SECOP = anexo; IVA bien puesto; estampillas; desglose de costos por si parece bajo."),
        (TODO, 0, "Revisar adendas y «Aplicar modificación»", "Si cambian el cuestionario: retirar y volver a presentar."),
        (TODO, 0, "Presentar la oferta y verificar el estado «Presentada»", "El cronómetro cierra a la hora exacta."),
    ]),
    "plan_post_cierre": ("Después del cierre", "after_plan_date", [
        (TODO, 1, "Revisar el acta de cierre", "Registrar n.º de oferentes y sus precios."),
        (TODO, 2, "Revisar el informe de evaluación y subsanar", "Por «Mensajes», dentro del plazo preclusivo."),
        (TODO, 3, "Observaciones al informe (si aplica)", "Traslado de al menos 1 día hábil."),
        (TODO, 3, "Si ganamos: aprobar el contrato electrónico", "Solo con el usuario del representante legal."),
    ]),
}
for key, (nombre, desde, tareas) in PLANES.items():
    plan = ensure(key, "mail.activity.plan", {"name": nombre, "res_model": "crm.lead"})
    for i, (tipo, dias, resumen, nota) in enumerate(tareas, start=1):
        ensure(f"{key}_{i:02d}", "mail.activity.plan.template", {
            "plan_id": plan, "sequence": i, "activity_type_id": tipo, "summary": resumen, "note": nota,
            "delay_count": dias, "delay_unit": "days", "delay_from": desde, "responsible_type": "on_demand",
        })

# --- Plantilla de proyecto para ejecutar lo ganado -----------------------------------------
ETAPAS_PROYECTO = ["Legalización", "Ejecución", "Facturación y pago", "Liquidación y cierre"]
etapas_proyecto = [ensure(f"task_stage_{i}", "project.task.type", {"name": n, "sequence": i})
                   for i, n in enumerate(ETAPAS_PROYECTO, start=1)]
proyecto = ensure("project_contrato_secop", "project.project", {
    "name": "Plantilla – Contrato SECOP", "is_template": True, "type_ids": [[6, 0, etapas_proyecto]],
})
TAREAS = [
    (0, "Aprobar el contrato electrónico (usuario del representante legal)"),
    (0, "Comprar la póliza y cargarla en SECOP II (si la exigen)"),
    (0, "Confirmar garantía aprobada y registro presupuestal"),
    (0, "Acta de inicio (si se pactó)"),
    (1, "Plan de trabajo y entregables"),
    (1, "Informes de ejecución al supervisor"),
    (2, "Radicar factura electrónica + certificado art. 50 + informe"),
    (2, "Cargar la factura en el plan de pagos de SECOP II"),
    (2, "Verificar el pago y los descuentos (IVA retenido, estampillas)"),
    (3, "Acta de liquidación"),
    (3, "Pedir la certificación de experiencia (derecho de petición)"),
    (3, "Guardar soportes para el RUP"),
]
for i, (etapa, nombre) in enumerate(TAREAS, start=1):
    ensure(f"task_tpl_{i:02d}", "project.task", {
        "name": nombre, "project_id": proyecto, "stage_id": etapas_proyecto[etapa], "sequence": i,
    })

# --- Verificación ---------------------------------------------------------------------------
assert call("crm.stage", "search_count", [["team_ids", "in", [equipo]]]) == len(ETAPAS)
assert call("crm.stage", "search_count", [["team_ids", "=", False]]) == 0, "quedaron etapas globales"
assert len(call("crm.team", "read", [equipo], fields=["lead_properties_definition"])[0]["lead_properties_definition"]) == len(PROPIEDADES)
for key, (_, _, tareas) in PLANES.items():
    assert call("mail.activity.plan.template", "search_count", [["plan_id", "=", ref(f"lumak.{key}")]]) == len(tareas)
assert call("project.task", "search_count", [["project_id", "=", proyecto]]) == len(TAREAS)
print(f"OK: equipo {equipo}, {len(ETAPAS)} etapas, {len(PROPIEDADES)} campos, "
      f"{sum(len(t) for _, _, t in PLANES.values())} actividades en planes, {len(TAREAS)} tareas en la plantilla")
