def migrate(cr, version):
    # La configuración que creaba scripts/crm_secop.py (IDs «lumak.*») pasa a los datos del módulo.
    # noupdate=False para que el XML la actualice; lo que no esté en el XML se borraría al terminar.
    cr.execute("UPDATE ir_model_data SET module = 'lumak_secop', noupdate = false WHERE module = 'lumak'")
    # La marca de planes ya agendados guarda los IDs: sin esto, el plan se agendaría otra vez.
    cr.execute("UPDATE crm_lead SET secop_planes = replace(secop_planes, 'lumak.', 'lumak_secop.') WHERE secop_planes LIKE '%lumak.%'")
