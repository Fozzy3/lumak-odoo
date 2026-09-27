from odoo import api, fields, models

RETENCION_IVA = 0.15  # la entidad pública, o cualquier comprador responsable de IVA, retiene el 15 % del IVA (ET art. 437-2)


class AccountMove(models.Model):
    _inherit = "account.move"

    lumak_cufe = fields.Char("CUFE (DIAN)", copy=False,
                             help="La factura legal se emite en la solución gratuita de la DIAN; aquí va su CUFE para cruzarlas.")
    lumak_estampillas = fields.Float("Estampillas (%)", compute="_compute_lumak_estampillas", store=True, readonly=False,
                                     help="Las descuenta la entidad al pagar, sobre la base sin IVA. Vienen del proceso SECOP.")
    lumak_neto_esperado = fields.Monetary("Neto que debe llegar al banco", compute="_compute_lumak_neto_esperado",
                                          currency_field="currency_id")

    @api.depends("invoice_line_ids.sale_line_ids")
    def _compute_lumak_estampillas(self):
        for factura in self:
            factura.lumak_estampillas = factura.invoice_line_ids.sale_line_ids.order_id.opportunity_id[:1].secop_estampillas

    @api.depends("amount_total", "amount_tax", "amount_untaxed", "lumak_estampillas")
    def _compute_lumak_neto_esperado(self):
        for factura in self:
            factura.lumak_neto_esperado = (factura.amount_total - RETENCION_IVA * factura.amount_tax
                                           - factura.lumak_estampillas / 100 * factura.amount_untaxed)
