"""Mercado SECOP: procesos de mínima cuantía de TIC y sus ofertas, para buscar a mano lo publicado y ver estadísticas.

Los datos vienen de la base estadística (estadistica/, DuckDB): el monitor diario manda todo el nicho y lo publicado en los
últimos 60 días con `sincronizar`. En Odoo son solo lectura; lo que interesa se trae al flujo con un botón.
"""
from datetime import timedelta

from odoo import Command, api, fields, models
from odoo.tools.misc import file_open


def _estrategia_inicial(_empresa):
    with file_open("lumak_secop/data/estrategia.html") as archivo:
        return archivo.read()


class LumakSecopProceso(models.Model):
    _name = "lumak.secop.proceso"
    _description = "Proceso publicado en SECOP"
    _order = "fecha_publicacion desc, id desc"
    _rec_name = "nombre"

    secop_id = fields.Char("ID en SECOP", required=True, index=True)
    referencia = fields.Char()
    nombre = fields.Char("Objeto", required=True)
    entidad = fields.Char(index=True)
    departamento = fields.Char()
    ciudad = fields.Char()
    modalidad = fields.Char()
    estado = fields.Char("Estado en SECOP")
    fecha_publicacion = fields.Date("Publicado", index=True)
    fecha_cierre = fields.Date("Cierra")
    presupuesto = fields.Float(digits=(16, 0))
    url = fields.Char("Enlace a SECOP")
    nicho = fields.Boolean("Del nicho", help="Software a la medida, soporte de software, web, analítica, IA y automatización.")
    n_ofertas = fields.Integer("Ofertas", aggregator="avg")
    ganador = fields.Char()
    precio_ganador = fields.Float(digits=(16, 0))
    descuento_ganador = fields.Float(
        "Descuento del ganador (%)", digits=(16, 1), aggregator="avg",
        help="Cuánto por debajo del presupuesto ofertó el ganador. Vacío cuando los valores de SECOP no son confiables.")
    lead_id = fields.Many2one("crm.lead", "En mi flujo", index="btree_not_null", ondelete="set null")
    oferta_ids = fields.One2many("lumak.secop.oferta", "proceso_id", "Ofertas recibidas")

    _secop_id_unico = models.Constraint("unique(secop_id)", "Ese proceso de SECOP ya está.")

    @api.model
    def sincronizar(self, procesos):
        """Crea o actualiza los procesos por su ID de SECOP y reemplaza sus ofertas. Enlaza los que ya están en el flujo."""
        ids = [p["secop_id"] for p in procesos]
        existentes = {p.secop_id: p for p in self.search([("secop_id", "in", ids)])}
        leads = {l.secop_id: l.id for l in self.env["crm.lead"].with_context(active_test=False).search([("secop_id", "in", ids)])}
        nuevos = []
        for p in procesos:
            # ponytail: las ofertas se borran y se vuelven a crear cada día; son pocas (unas 5.000)
            vals = {**p, "oferta_ids": [Command.clear()] + [Command.create(o) for o in p.get("ofertas", [])]}
            vals.pop("ofertas", None)
            if p["secop_id"] in leads:
                vals["lead_id"] = leads[p["secop_id"]]
            if p["secop_id"] in existentes:
                existentes[p["secop_id"]].write(vals)
            else:
                nuevos.append(vals)
        self.create(nuevos)
        return {"creados": len(nuevos), "actualizados": len(procesos) - len(nuevos)}

    def action_traer_al_flujo(self):
        """Lo crea en «Por revisar» con el importador de siempre (una sola vez) y lo abre con la ficha de SECOP."""
        self.ensure_one()
        if not self.lead_id:
            accion = self.env["lumak.secop.import"].create({"referencia": self.secop_id}).action_import()
            self.lead_id = accion["res_id"]
        return self.lead_id._secop_accion_ficha()

    @api.model
    def resumen_semana(self):
        hoy = fields.Date.context_today(self)
        semana = self.search([("fecha_publicacion", ">=", hoy - timedelta(days=7))])
        return {"semana": len(semana), "semana_nicho": len(semana.filtered("nicho")),
                "abiertos_nicho": self.search_count([("nicho", "=", True), ("fecha_cierre", ">=", hoy)])}


class LumakSecopOferta(models.Model):
    _name = "lumak.secop.oferta"
    _description = "Oferta en un proceso de SECOP"
    _order = "proceso_id, puesto"
    _rec_name = "proveedor"

    proceso_id = fields.Many2one("lumak.secop.proceso", required=True, ondelete="cascade", index=True)
    proveedor = fields.Char(index=True)
    nit = fields.Char("NIT")
    valor = fields.Float(digits=(16, 0))
    puesto = fields.Integer("Puesto por precio", aggregator="avg")
    descuento = fields.Float("Descuento (%)", digits=(16, 1), aggregator="avg",
                             help="Cuánto por debajo del presupuesto ofertó. Vacío cuando el valor de SECOP no es confiable.")
    gano = fields.Integer("Ganadas", aggregator="sum", help="1 si ganó el proceso")
    # Promedio de 0 y 100: la tasa de éxito del proveedor en cualquier agrupación
    tasa_exito = fields.Float("Tasa de éxito (%)", digits=(16, 0), aggregator="avg", compute="_compute_tasa_exito", store=True)
    fecha_publicacion = fields.Date(related="proceso_id.fecha_publicacion", store=True, string="Publicado")
    entidad = fields.Char(related="proceso_id.entidad", store=True)
    departamento = fields.Char(related="proceso_id.departamento", store=True)
    nicho = fields.Boolean(related="proceso_id.nicho", store=True, string="Del nicho")

    @api.depends("gano")
    def _compute_tasa_exito(self):
        for oferta in self:
            oferta.tasa_exito = 100 * bool(oferta.gano)


class ResCompany(models.Model):
    _inherit = "res.company"

    # Al crear la columna, Odoo llena la empresa con el análisis de arranque (data/estrategia.html); después la edita el usuario
    lumak_estrategia = fields.Html("Estrategia", default=_estrategia_inicial)

    @api.model
    def action_lumak_estrategia(self):
        """Mercado → Estrategia: qué tiene la competencia y cómo ganarle, en una página que el usuario edita."""
        return {"type": "ir.actions.act_window", "name": "Estrategia", "res_model": "res.company",
                "res_id": self.env.company.id, "view_mode": "form",
                "views": [(self.env.ref("lumak_secop.res_company_form_estrategia").id, "form")]}
