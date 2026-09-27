from datetime import date, datetime, time

from odoo import api, fields, models

from .documentos import MESES
from .licitaciones import monto_corto

# Primero lo que ya no sirve, luego lo que falta, luego lo que está por vencer
ORDEN_KIT = {"vencido": 0, "falta": 1, "por_vencer": 2}


def dia_corto(fecha):
    return f"{fecha.day} {MESES[fecha.month - 1][:3]}"


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def get_secop_dashboard(self):
        """El tablero de Lumak: además de licitaciones, contratos en ejecución, cartera, kit y fechas legales."""
        data = super().get_secop_dashboard()
        hoy = fields.Date.context_today(self)

        contratos = []
        for proyecto in self.env["project.project"].search([("is_template", "=", False), ("sale_line_id", "!=", False)]):
            hito = proyecto.milestone_ids.filtered(lambda m: not m.is_reached).sorted(
                lambda m: (m.deadline or date.max, m.sequence))[:1]
            contratos.append({"id": proyecto.id, "nombre": proyecto.name, "entidad": proyecto.partner_id.name or "",
                              "hito": hito.name or "", "hito_fecha": dia_corto(hito.deadline) if hito.deadline else ""})

        facturas = self.env["account.move"].search([("move_type", "=", "out_invoice"), ("state", "=", "posted"),
                                                    ("payment_state", "in", ("not_paid", "partial"))])

        kit = self.env["lumak.documento"].search([("en_oferta", "=", True)])
        pendientes = kit.filtered(lambda d: d.estado in ORDEN_KIT).sorted(lambda d: (ORDEN_KIT[d.estado], d.sequence))
        etiqueta = {"falta": lambda d: "Falta", "vencido": lambda d: f"Venció el {dia_corto(d.vence)}",
                    "por_vencer": lambda d: f"Vence el {dia_corto(d.vence)}"}

        eventos = self.env["calendar.event"].search([("secop_tipo", "=", "obligacion"),
                                                     ("stop", ">=", datetime.combine(hoy, time.min))], order="start", limit=5)
        data.update({
            "contratos": contratos,
            "por_cobrar": monto_corto(sum(facturas.mapped("amount_residual_signed"))) or "$0",
            "facturas_pendientes": len(facturas),
            "facturas_vencidas": len(facturas.filtered(lambda f: f.invoice_date_due and f.invoice_date_due < hoy)),
            "kit_total": len(kit),
            "kit_ok": len(kit) - len(kit.filtered(lambda d: d.estado in ("falta", "vencido"))),
            "kit_pendientes": [{"id": d.id, "nombre": d.name, "estado": d.estado, "etiqueta": etiqueta[d.estado](d)}
                               for d in pendientes[:5]],
            "obligaciones": [{"id": e.id, "nombre": e.name, "fecha": dia_corto(e.start_date or e.start.date()),
                              "dias": ((e.start_date or e.start.date()) - hoy).days} for e in eventos],
        })
        return data
