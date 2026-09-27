def migrate(cr, version):
    # Los eventos de todo el día creados a medianoche UTC se veían la noche anterior en Bogotá: pasan a mediodía UTC.
    cr.execute("""
        UPDATE calendar_event SET start = start + interval '12 hours', stop = stop + interval '12 hours'
        WHERE allday AND secop_tipo IS NOT NULL AND start::time = '00:00'
    """)
