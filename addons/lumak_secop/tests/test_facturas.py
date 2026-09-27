from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestFacturas(AccountTestInvoicingCommon):
    """Impuestos de una SAS en el SIMPLE y lo que de verdad llega al banco en cada factura."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cid = cls.env.company.id
        Tax = cls.env["account.tax"]
        # Los mismos IDs externos que crea la localización colombiana (l10n_co)
        cls.l10n = {}
        for clave, nombre, monto in [("8", "19% IVA", 19), ("10", "0% IVA Ee", 0), ("11", "0% IVA Exc", 0),
                                     ("53", "2.5% RteFte", -2.5), ("54", "3.50% RteFte", -3.5),
                                     ("57", "0.414% RteICA", -0.414), ("58", "0.966% RteICA", -0.966)]:
            tax = Tax.create({"name": nombre, "amount": monto, "type_tax_use": "sale"})
            cls.env["ir.model.data"].create({"module": "account", "name": f"{cid}_l10n_co_tax_{clave}",
                                             "model": "account.tax", "res_id": tax.id})
            cls.l10n[clave] = tax

    def test_simple_company_tax_setup(self):
        self.env["product.template"]._lumak_impuestos_colombia()
        self.assertEqual(self.env.ref("lumak_secop.product_nube_mes").taxes_id, self.l10n["11"])
        self.assertEqual(self.env.ref("lumak_secop.product_saas_mes").taxes_id, self.l10n["11"])
        for clave in ("53", "54", "57", "58"):
            self.assertFalse(self.l10n[clave].active, "en el SIMPLE nadie le retiene renta ni ICA a Lumak")
        exterior = self.env["account.fiscal.position"].search([("name", "=", "Cliente del exterior (exportación de servicios)")])
        self.assertEqual(exterior.map_tax(self.l10n["8"]), self.l10n["10"])
        self.env["product.template"]._lumak_impuestos_colombia()  # correr dos veces no duplica
        self.assertEqual(self.env["account.fiscal.position"].search_count([("name", "=", exterior.name)]), 1)

    def test_net_that_reaches_the_bank(self):
        factura = self.init_invoice("out_invoice", amounts=[1_000_000], taxes=self.l10n["8"])
        self.assertAlmostEqual(factura.amount_total, 1_190_000)
        # la entidad retiene el 15 % del IVA (28.500)
        self.assertAlmostEqual(factura.lumak_neto_esperado, 1_161_500)
        factura.lumak_estampillas = 4.1  # y descuenta estampillas sobre la base (41.000)
        self.assertAlmostEqual(factura.lumak_neto_esperado, 1_120_500)
        factura.lumak_cufe = "abc123"
        self.assertEqual(factura.lumak_cufe, "abc123")
