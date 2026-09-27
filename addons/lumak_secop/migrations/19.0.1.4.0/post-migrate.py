from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # Los procesos abiertos reciben lo que ya hacen los nuevos: cotización si están en «Preparando oferta»
    # y sus fechas en el Calendario. Ambas cosas son idempotentes.
    env = api.Environment(cr, SUPERUSER_ID, {})
    leads = env["crm.lead"].search([("team_id", "=", env.ref("lumak_secop.team_secop").id), ("won_status", "=", "pending")])
    leads._secop_al_cambiar_etapa()
    leads._secop_sincronizar_calendario()
