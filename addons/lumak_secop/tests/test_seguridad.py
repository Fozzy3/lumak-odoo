from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestSeguridad(TransactionCase):
    def test_short_passwords_are_rejected_and_nobody_signs_up_alone(self):
        with self.assertRaises(UserError):
            self.env["res.users"].create({"name": "Prueba", "login": "prueba_corta", "password": "corta"})
        self.assertEqual(self.env["ir.config_parameter"].sudo().get_param("auth_signup.invitation_scope"), "b2b")
