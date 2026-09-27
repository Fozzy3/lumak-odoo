from odoo import Command, _, api, fields, models

# SIMPLE de servicios profesionales hasta 6.000 UVT de ingresos al año ($314 M en 2026). Por encima sube a 7,3 %
# (hasta 15.000 UVT) y 12 %; la tarifa cae sobre todo el ingreso del año. docs/licitaciones-secop.md, sección 4.
TARIFA_SIMPLE = 0.059


def precio_minimo(costo, estampillas):
    """Base sin IVA que todavía cubre el costo después del SIMPLE y de las estampillas que descuenta la entidad."""
    return costo / (1 - TARIFA_SIMPLE - estampillas / 100) if costo else 0


class CrmLead(models.Model):
    _inherit = "crm.lead"

    secop_costo_estimado = fields.Monetary("Costo estimado", currency_field="company_currency",
                                           help="Lo que cuesta ejecutar el contrato: horas, nube, pólizas, viajes.")
    secop_precio_minimo = fields.Monetary("Precio mínimo sin IVA", currency_field="company_currency",
                                          compute="_compute_secop_precio")
    secop_precio_bajo = fields.Boolean(compute="_compute_secop_precio")
    secop_valor_ofertado = fields.Monetary("Valor ofertado", currency_field="company_currency", store=True,
                                           compute="_compute_secop_valor_ofertado",
                                           help="Total con IVA de la cotización: es la lista de precios de SECOP II.")
    secop_proyecto_id = fields.Many2one("project.project", "Proyecto del contrato", compute="_compute_secop_proyecto")

    def _secop_cotizacion(self):
        """La cotización vigente: la última que no esté cancelada."""
        return self.order_ids.filtered(lambda o: o.state != "cancel").sorted("id")[-1:]

    @api.depends("order_ids.state", "order_ids.amount_total")
    def _compute_secop_valor_ofertado(self):
        for lead in self:
            lead.secop_valor_ofertado = lead._secop_cotizacion().amount_total

    @api.depends("secop_costo_estimado", "secop_estampillas", "order_ids.amount_untaxed")
    def _compute_secop_precio(self):
        for lead in self:
            lead.secop_precio_minimo = precio_minimo(lead.secop_costo_estimado, lead.secop_estampillas)
            base = lead._secop_cotizacion().amount_untaxed
            lead.secop_precio_bajo = bool(lead.secop_precio_minimo and base and base < lead.secop_precio_minimo)

    @api.depends("order_ids.state")
    def _compute_secop_proyecto(self):
        for lead in self:
            lead.secop_proyecto_id = lead.order_ids.sudo().project_ids[:1]

    def _secop_al_cambiar_etapa(self):
        super()._secop_al_cambiar_etapa()
        preparando = self.env.ref("lumak_secop.stage_preparando")
        for lead in self.filtered(lambda l: l.stage_id == preparando and not l._secop_cotizacion()):
            lead._secop_crear_cotizacion()
        for lead in self.filtered(lambda l: l.secop_es_licitacion and l.stage_id.is_won):
            lead._secop_confirmar_contrato()

    def _secop_crear_cotizacion(self):
        """Borrador de la oferta económica: una línea con el objeto del proceso, al tope del presupuesto."""
        self.ensure_one()
        if not self.partner_id:
            self.message_post(body=_("Pon la entidad (cliente) para crear la cotización de la oferta."))
            return
        order = self.env["sale.order"].create({
            "partner_id": self.partner_id.id, "opportunity_id": self.id, "team_id": self.team_id.id,
            "user_id": (self.user_id or self.env.user).id, "origin": self.secop_numero or self.name,
            "client_order_ref": self.secop_numero,
            "order_line": [Command.create({"product_id": self.env.ref("lumak_secop.product_contrato_secop").id,
                                           "name": self.name, "product_uom_qty": 1})],
        })
        linea = order.order_line
        # El presupuesto oficial ya incluye los impuestos.
        tasa = sum(t.amount for t in linea.tax_ids if t.amount_type == "percent") / 100
        linea.price_unit = self.expected_revenue / (1 + tasa)

    def _secop_confirmar_contrato(self):
        """Adjudicado: la cotización se confirma y Odoo abre el proyecto desde la plantilla del contrato."""
        self.ensure_one()
        if self.order_ids.filtered(lambda o: o.state == "sale"):
            return
        borradores = self.order_ids.filtered(lambda o: o.state in ("draft", "sent"))
        if len(borradores) == 1:
            borradores.action_confirm()
        elif borradores:
            self.message_post(body=_("Hay varias cotizaciones: confirma la que ganó para abrir el proyecto del contrato."))
        else:
            self.message_post(body=_("No hay cotización para confirmar: créala con el valor adjudicado y confírmala "
                                     "para abrir el proyecto del contrato."))

    def action_open_secop_proyecto(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "project.project", "res_id": self.secop_proyecto_id.id,
                "view_mode": "form", "views": [(False, "form")]}


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_project(self):
        # Odoo lo llama «referencia - orden - plantilla»; se nombra por el objeto, que es como se busca después
        proyecto = super()._timesheet_create_project()
        objeto = (self.name or self.product_id.name).splitlines()[0]
        proyecto.name = f"{objeto} ({self.order_id.client_order_ref})" if self.order_id.client_order_ref else objeto
        return proyecto


class ProjectProject(models.Model):
    _inherit = "project.project"

    secop_lead_id = fields.Many2one("crm.lead", "Proceso", related="sale_order_id.opportunity_id")

    def action_open_secop_lead(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "crm.lead", "res_id": self.secop_lead_id.id,
                "view_mode": "form", "views": [(False, "form")]}


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _lumak_impuestos_colombia(self):
        """Impuestos de una SAS del SIMPLE que vende servicios. Corre en cada actualización; no hace nada sin l10n_co."""
        tax = lambda n: self.env.ref(f"account.{self.env.company.id}_l10n_co_tax_{n}", raise_if_not_found=False)
        iva, exento, excluido = tax("8"), tax("10"), tax("11")
        if not iva:
            return
        # SaaS, hosting y nube: IVA excluido (ET art. 476 num. 21). Lo demás queda con el 19 % por defecto.
        if excluido:
            for xmlid in ("lumak_secop.product_saas_mes", "lumak_secop.product_nube_mes"):
                self.env.ref(xmlid).taxes_id = excluido
        # En el SIMPLE nadie le retiene renta ni ICA a Lumak (ET art. 911): esas retenciones de venta solo confunden
        for n in ("53", "54", "57", "58"):
            if tax(n):
                tax(n).active = False
        # Exportación de servicios: IVA exento (ET art. 481 lit. c), se elige en el cliente o en la factura
        nombre = "Cliente del exterior (exportación de servicios)"
        Posicion = self.env["account.fiscal.position"]
        if exento and not Posicion.search_count([("name", "=", nombre), ("company_id", "=", self.env.company.id)]):
            Posicion.create({"name": nombre, "tax_ids": [Command.link(exento.id)]})
            exento.original_tax_ids |= iva
