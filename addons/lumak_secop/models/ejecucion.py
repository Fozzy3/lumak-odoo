from odoo import api, fields, models

from .documentos import fecha_en_letras, periodo_aportes, valor_en_letras


class ProjectProject(models.Model):
    _inherit = "project.project"

    contrato_numero = fields.Char("N.º de contrato", help="El que asigna la entidad en SECOP II, distinto al del proceso.")
    supervisor = fields.Char(help="Nombre y cargo de quien recibe a satisfacción.")
    contrato_objeto = fields.Char("Objeto del contrato", compute="_compute_contrato")
    contrato_valor = fields.Monetary("Valor del contrato", compute="_compute_contrato", currency_field="currency_id")
    experiencia_ids = fields.One2many("lumak.experiencia", "proyecto_id")

    @api.depends("sale_line_id.name", "sale_line_id.order_id.amount_total")
    def _compute_contrato(self):
        for proyecto in self:
            proyecto.contrato_objeto = proyecto.sale_line_id.name or proyecto.name
            proyecto.contrato_valor = proyecto.sale_line_id.order_id.amount_total

    def action_registrar_experiencia(self):
        """Al cerrar el contrato: lo que se pida a la entidad en la certificación queda listo para las próximas ofertas."""
        self.ensure_one()
        experiencia = self.experiencia_ids[:1] or self.env["lumak.experiencia"].create({
            "proyecto_id": self.id, "contratante_id": self.partner_id.id, "publico": bool(self.secop_lead_id),
            "contrato_numero": self.contrato_numero, "objeto": self.contrato_objeto, "valor": self.contrato_valor,
            "unspsc": self.secop_lead_id.secop_unspsc, "fecha_inicio": self.date_start, "fecha_fin": self.date,
        })
        return {"type": "ir.actions.act_window", "res_model": "lumak.experiencia", "res_id": experiencia.id,
                "view_mode": "form", "views": [(False, "form")]}

    def _secop_docs(self):
        """Datos para los documentos de cada pago (mismas plantillas de membrete y firma que la oferta)."""
        self.ensure_one()
        company = self.company_id or self.env.company
        hoy = fields.Date.context_today(self)
        desde = periodo_aportes(company.lumak_fecha_constitucion or hoy, hoy)[0]
        facturado = sum(self.sale_line_id.order_id.invoice_ids.filtered(lambda f: f.state == "posted").mapped("amount_total"))
        return {
            "company": company, "fecha": fecha_en_letras(hoy), "inicio": fecha_en_letras(self.date_start or hoy),
            "aportes_desde": fecha_en_letras(desde), "desde_constitucion": desde == company.lumak_fecha_constitucion,
            "valor_letras": valor_en_letras(self.contrato_valor), "facturado": facturado,
            "saldo": self.contrato_valor - facturado,
            "hechas": self.task_ids.filtered(lambda t: t.state == "1_done"),
            "en_curso": self.task_ids.filtered(lambda t: t.state not in ("1_done", "1_canceled")),
        }


class LumakExperiencia(models.Model):
    """Contratos ejecutados que prueban experiencia: los de la empresa y, sus primeros tres años, los del socio."""
    _name = "lumak.experiencia"
    _description = "Experiencia certificable"
    _order = "fecha_fin desc, id desc"
    _rec_name = "objeto"

    contratante_id = fields.Many2one("res.partner", "Contratante", required=True)
    publico = fields.Boolean("Entidad pública", default=True)
    de_socio = fields.Boolean("Experiencia del socio", help="Vale para la empresa durante sus tres primeros años, vía RUP.")
    contrato_numero = fields.Char("N.º de contrato")
    objeto = fields.Text(required=True)
    unspsc = fields.Char("Códigos UNSPSC")
    fecha_inicio = fields.Date("Inicio")
    fecha_fin = fields.Date("Terminación")
    currency_id = fields.Many2one(related="proyecto_id.currency_id")
    valor = fields.Float("Valor final (COP)")
    contacto = fields.Char("Contacto de verificación", help="Correo o teléfono de quien puede confirmar el contrato.")
    soporte = fields.Binary("Certificación o acta", attachment=True)
    soporte_nombre = fields.Char()
    en_oferta = fields.Boolean("Va en el formato de experiencia", default=True)
    proyecto_id = fields.Many2one("project.project", "Proyecto", ondelete="set null")
    correccion = fields.Char("Qué corregir en la certificación",
                             help="Si la certificación que expidieron tiene un error, la solicitud pide corregirlo.")

    def _secop_docs(self):
        self.ensure_one()
        return {"company": self.env.company, "fecha": fecha_en_letras(fields.Date.context_today(self))}
