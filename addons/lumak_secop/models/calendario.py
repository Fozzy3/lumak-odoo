from datetime import datetime, time, timedelta

import pytz

from odoo import Command, _, fields, models

# Campos del proceso que cambian lo que se ve en el Calendario
CAMPOS_CALENDARIO = {"name", "user_id", "date_deadline", "secop_hora_cierre", "secop_limite_observaciones",
                     "stage_id", "active", "probability"}


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    secop_tipo = fields.Selection([("cierre", "Cierre"), ("observaciones", "Observaciones"),
                                   ("obligacion", "Obligación de la empresa")], "Fecha de Lumak")


class CrmLead(models.Model):
    _inherit = "crm.lead"

    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._secop_sincronizar_calendario()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if CAMPOS_CALENDARIO & set(vals):
            self._secop_sincronizar_calendario()
        return res

    def _secop_sincronizar_calendario(self):
        """Un evento por fecha de SECOP mientras el proceso siga abierto; se mueve, no se duplica."""
        Evento = self.env["calendar.event"].with_context(dont_notify=True)
        for lead in self.filtered("secop_es_licitacion"):
            abierto = lead.active and lead.won_status == "pending"
            fechas = {
                "cierre": (lead.date_deadline, lead.secop_hora_cierre, _("Cierre: %s", lead.name)),
                "observaciones": (lead.secop_limite_observaciones, 0, _("Observaciones: %s", lead.name)),
            }
            for tipo, (fecha, hora, nombre) in fechas.items():
                evento = Evento.search([("opportunity_id", "=", lead.id), ("secop_tipo", "=", tipo)])
                if not (abierto and fecha):
                    evento.unlink()
                    continue
                vals = {"name": nombre, **lead._secop_horario(fecha, hora)}
                if evento:
                    evento.write(vals)
                    continue
                usuario = lead.user_id or self.env.user
                Evento.create({
                    **vals, "secop_tipo": tipo, "opportunity_id": lead.id, "res_model_id": self.env["ir.model"]._get_id("crm.lead"),
                    "res_id": lead.id, "user_id": usuario.id, "partner_ids": [Command.link(usuario.partner_id.id)],
                    # Una lista no vacía evita que Odoo cree además una actividad «Reunión» en el proceso
                    "activity_ids": [Command.clear()],
                    "alarm_ids": [(6, 0, [self.env.ref("calendar.alarm_notif_5").id, self.env.ref("calendar.alarm_notif_4").id])],
                })

    def _secop_horario(self, fecha, hora):
        """Con hora: evento de media hora en la zona del responsable. Sin hora: todo el día."""
        if not hora:
            # Mediodía UTC: el mismo día en cualquier zona de América (a medianoche UTC, Bogotá lo vería la noche anterior)
            dia = datetime.combine(fecha, time(12))
            return {"allday": True, "start": dia, "stop": dia}
        tz = pytz.timezone(self.user_id.tz or self.env.user.tz or "America/Bogota")
        local = tz.localize(datetime.combine(fecha, time(int(hora), round(hora % 1 * 60))))
        inicio = local.astimezone(pytz.UTC).replace(tzinfo=None)
        return {"allday": False, "start": inicio, "stop": inicio + timedelta(minutes=30)}
