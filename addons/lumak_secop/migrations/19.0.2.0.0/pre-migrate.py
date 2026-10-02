def migrate(cr, version):
    # 6 etapas → 4: «Evaluando» se une a «Por revisar» y «En evaluación» a «Presentada».
    # Los procesos se mueven antes de que la actualización borre las etapas que ya no están en el XML.
    for vieja, nueva in (("stage_evaluando", "stage_detectado"), ("stage_evaluacion", "stage_presentada")):
        cr.execute("""
            UPDATE crm_lead SET stage_id = (SELECT res_id FROM ir_model_data WHERE module = 'lumak_secop' AND name = %s)
            WHERE stage_id = (SELECT res_id FROM ir_model_data WHERE module = 'lumak_secop' AND name = %s)""", (nueva, vieja))
