import base64
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from num2words import num2words

from odoo import _, api, fields, models
from odoo.exceptions import UserError

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre")
# (nombre del archivo, reporte). El orden es el de la carpeta que se sube a SECOP II.
DOCUMENTOS_OFERTA = [
    ("Carta de presentación", "lumak_secop.report_carta_presentacion"),
    ("Oferta económica", "lumak_secop.report_oferta_economica"),
    ("Certificación de aportes (art. 50)", "lumak_secop.report_aportes"),
    ("Compromiso anticorrupción", "lumak_secop.report_anticorrupcion"),
    ("Declaración de inhabilidades y conflicto de intereses", "lumak_secop.report_inhabilidades"),
]


def valor_en_letras(valor):
    """11900000 -> ONCE MILLONES NOVECIENTOS MIL PESOS M/CTE (pesos enteros, como se escriben en las ofertas)."""
    return f"{num2words(round(valor), lang='es')} pesos m/cte".upper()


def fecha_en_letras(fecha):
    return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def periodo_aportes(constitucion, hasta):
    """Ley 789 art. 50: los 6 meses anteriores, o desde la constitución si la sociedad es más nueva."""
    return max(constitucion, hasta - relativedelta(months=6)), hasta


class ResCompany(models.Model):
    _inherit = "res.company"

    lumak_representante = fields.Char("Representante legal")
    lumak_representante_cc = fields.Char("Cédula del representante legal")
    lumak_representante_cc_expedida = fields.Char("Cédula expedida en")
    lumak_fecha_constitucion = fields.Date("Fecha de constitución")
    lumak_tiene_empleados = fields.Boolean(
        "Tiene empleados", help="Cambia la certificación de aportes: sin empleados certifica que no ha tenido personal a cargo.")

    @api.model
    def action_lumak_datos_empresa(self):
        return {"type": "ir.actions.act_window", "res_model": "res.company", "res_id": self.env.company.id,
                "view_mode": "form", "views": [(False, "form")]}


class LumakDocumento(models.Model):
    """Kit de la empresa: los certificados de terceros que se renuevan y se adjuntan a cada oferta."""
    _name = "lumak.documento"
    _description = "Documento del kit de la empresa"
    _order = "sequence, id"

    name = fields.Char("Documento", required=True)
    sequence = fields.Integer(default=10)
    emisor = fields.Char()
    url = fields.Char("Dónde se saca")
    vigencia_dias = fields.Integer("Vigencia (días)", help="Días desde la expedición en que la entidad lo acepta. 0 = no vence.")
    en_oferta = fields.Boolean("Va en cada oferta", default=True)
    archivo = fields.Binary(attachment=True)
    archivo_nombre = fields.Char()
    fecha_expedicion = fields.Date("Expedido el")
    vence = fields.Date(compute="_compute_vence", store=True)
    estado = fields.Selection([("falta", "Falta"), ("vencido", "Vencido"), ("por_vencer", "Vence pronto"),
                               ("vigente", "Vigente")], compute="_compute_estado")
    nota = fields.Char()

    @api.depends("fecha_expedicion", "vigencia_dias")
    def _compute_vence(self):
        for doc in self:
            doc.vence = doc.vigencia_dias and doc.fecha_expedicion and doc.fecha_expedicion + timedelta(days=doc.vigencia_dias)

    @api.depends("archivo", "vence")
    def _compute_estado(self):
        hoy = fields.Date.context_today(self)
        for doc in self:
            if not doc.archivo:
                doc.estado = "falta"
            elif doc.vence and doc.vence < hoy:
                doc.estado = "vencido"
            elif doc.vence and doc.vence <= hoy + timedelta(days=7):
                doc.estado = "por_vencer"
            else:
                doc.estado = "vigente"

    def vigente_al(self, fecha):
        self.ensure_one()
        return bool(self.archivo) and (not self.vence or self.vence >= fecha)

    def action_abrir_url(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url", "url": self.url, "target": "new"}


class CrmLead(models.Model):
    _inherit = "crm.lead"

    secop_plazo = fields.Char("Plazo de ejecución", help="Como lo dice la invitación, p. ej. «3 meses».")
    secop_validez_dias = fields.Integer("Validez de la oferta (días)", default=90)
    secop_adendas = fields.Char("Adendas aplicadas", default="ninguna")

    def _secop_datos_faltantes(self):
        company = self.company_id or self.env.company
        faltan = [texto for valor, texto in [
            (company.lumak_representante, _("nombre del representante legal (Lumak → Datos de la empresa)")),
            (company.lumak_representante_cc, _("cédula del representante legal (Lumak → Datos de la empresa)")),
            (company.lumak_fecha_constitucion, _("fecha de constitución (Lumak → Datos de la empresa)")),
            (company.street and company.city, _("dirección de la compañía")),
            (company.email, _("correo de la compañía")),
            (company.phone, _("teléfono de la compañía")),
            (self.partner_id, _("entidad del proceso")),
            (self.secop_numero, _("número del proceso")),
            (self._secop_cotizacion(), _("cotización (se crea sola al pasar a «Preparando oferta»)")),
        ] if not valor]
        return faltan

    def action_secop_preparar_oferta(self):
        """Genera los documentos que firma el representante legal y junta los del kit vigentes al cierre."""
        self.ensure_one()
        if faltan := self._secop_datos_faltantes():
            raise UserError(_("Para generar los documentos de la oferta falta:\n- %s", "\n- ".join(faltan)))
        Report = self.env["ir.actions.report"]
        documentos = DOCUMENTOS_OFERTA + ([("Formato de experiencia", "lumak_secop.report_experiencia")]
                                          if self._secop_experiencias() else [])
        adjuntos = [(f"{i:02d} {nombre} - {self.secop_numero}.pdf", Report._render_qweb_pdf(reporte, self.ids)[0])
                    for i, (nombre, reporte) in enumerate(documentos, start=1)]
        cierre = self.date_deadline or fields.Date.context_today(self)
        kit = self.env["lumak.documento"].search([("en_oferta", "=", True)])
        listos = kit.filtered(lambda d: d.vigente_al(cierre))
        for i, doc in enumerate(listos, start=len(adjuntos) + 1):
            adjuntos.append((f"{i:02d} {doc.archivo_nombre or doc.name}", base64.b64decode(doc.with_context(bin_size=False).archivo)))
        avisos = [_("Del kit falta o vence antes del cierre: %s.", ", ".join((kit - listos).mapped("name")))] if kit - listos else []
        cotizacion = self._secop_cotizacion()
        if self.expected_revenue and cotizacion.amount_total > self.expected_revenue:
            avisos.append(_("La oferta supera el presupuesto oficial: es causal de rechazo."))
        if self.secop_precio_bajo:
            avisos.append(_("La oferta queda por debajo del precio mínimo que cubre el costo."))
        cuerpo = Markup("<p>%s</p><p>%s</p>") % (
            _("Documentos de la oferta listos: %s archivos. Usa «Descargar archivos» para bajarlos en un ZIP.", len(adjuntos)),
            _("Firma a mano y escanea la carta y las declaraciones, o súbelas desde el usuario del representante legal "
              "en SECOP II: ese usuario es su firma electrónica."))
        if avisos:
            cuerpo += Markup("<ul>%s</ul>") % Markup().join(Markup("<li>%s</li>") % a for a in avisos)
        self.message_post(body=cuerpo, attachments=adjuntos)
        return True

    def _secop_experiencias(self):
        # El Documento Tipo de CCE admite hasta 5 contratos: van los de mayor valor
        return self.env["lumak.experiencia"].search([("en_oferta", "=", True)], order="valor desc", limit=5)

    # Datos que usan las plantillas de los documentos
    def _secop_docs(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        hoy = fields.Date.context_today(self)
        cotizacion = self._secop_cotizacion()
        return {
            "company": company,
            "fecha": fecha_en_letras(hoy),
            "cotizacion": cotizacion,
            "valor_letras": valor_en_letras(cotizacion.amount_total),
            "modalidad": dict(self._fields["secop_modalidad"].selection).get(self.secop_modalidad, ""),
            "aportes_desde": fecha_en_letras(periodo_aportes(company.lumak_fecha_constitucion or hoy, hoy)[0]),
            "desde_constitucion": periodo_aportes(company.lumak_fecha_constitucion or hoy, hoy)[0] == company.lumak_fecha_constitucion,
        }
