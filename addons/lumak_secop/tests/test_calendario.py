from datetime import date, datetime

import pytz

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCalendario(TransactionCase):
    """Los cierres y el límite de observaciones aparecen en el Calendario, con recordatorio."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.usuario = cls.env["res.users"].create({
            "name": "Responsable", "login": "responsable_secop", "tz": "America/Bogota",
            "group_ids": [(6, 0, [cls.env.ref("sales_team.group_sale_salesman").id])]})
        cls.team = cls.env.ref("lumak_secop.team_secop")
        cls.detectado = cls.env.ref("lumak_secop.stage_detectado")

    def _lead(self, **vals):
        return self.env["crm.lead"].create({"name": "Sistema de PQRSD", "type": "opportunity", "team_id": self.team.id,
                                            "stage_id": self.detectado.id, "user_id": self.usuario.id, **vals})

    def _eventos(self, lead, tipo):
        return self.env["calendar.event"].search([("opportunity_id", "=", lead.id), ("secop_tipo", "=", tipo)])

    def test_closing_with_hour_becomes_a_timed_event_in_bogota_time(self):
        lead = self._lead(date_deadline=date(2026, 10, 2), secop_hora_cierre=15.0)
        evento = self._eventos(lead, "cierre")
        self.assertEqual(len(evento), 1)
        self.assertEqual(evento.name, "Cierre: Sistema de PQRSD")
        self.assertFalse(evento.allday)
        self.assertEqual(evento.start, datetime(2026, 10, 2, 20, 0))  # 3:00 p. m. en Bogotá = 20:00 UTC
        self.assertIn(self.usuario.partner_id, evento.partner_ids)
        self.assertTrue(evento.alarm_ids)

    def test_moving_the_date_moves_the_same_event(self):
        lead = self._lead(date_deadline=date(2026, 10, 2))
        evento = self._eventos(lead, "cierre")
        self.assertTrue(evento.allday)
        # un evento de todo el día se ve ese mismo día en Bogotá, no la noche anterior
        self.assertEqual(pytz.utc.localize(evento.start).astimezone(pytz.timezone("America/Bogota")).date(), date(2026, 10, 2))
        lead.write({"date_deadline": date(2026, 10, 5), "secop_hora_cierre": 9.5})
        self.assertEqual(self._eventos(lead, "cierre"), evento)
        self.assertEqual(evento.start, datetime(2026, 10, 5, 14, 30))
        lead.date_deadline = False
        self.assertFalse(evento.exists())

    def test_questions_deadline_is_its_own_event(self):
        lead = self._lead(secop_limite_observaciones=date(2026, 9, 30))
        evento = self._eventos(lead, "observaciones")
        self.assertEqual(evento.name, "Observaciones: Sistema de PQRSD")
        self.assertEqual(evento.start_date, date(2026, 9, 30))

    def test_closed_processes_leave_the_calendar(self):
        lead = self._lead(date_deadline=date(2026, 10, 2), secop_limite_observaciones=date(2026, 9, 30))
        lead.action_set_lost()
        self.assertFalse(self._eventos(lead, "cierre") | self._eventos(lead, "observaciones"))
