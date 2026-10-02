import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class SecopDashboard extends Component {
    static template = "lumak_secop.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null });
        this.hoy = new Date().toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" });
        onWillStart(async () => {
            this.state.data = await this.orm.call("crm.lead", "get_secop_dashboard", []);
        });
    }

    get maxEtapa() {
        return Math.max(1, ...this.state.data.etapas.map((e) => e.total));
    }

    async openProcesos(filtro = null) {
        const action = await this.orm.call("crm.lead", "action_secop_pipeline", [], { filtro });
        this.action.doAction(action);
    }

    openContrato(id) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: "project.project", res_id: id, views: [[false, "form"]] });
    }

    openFacturas() {
        this.action.doAction("lumak_secop.action_lumak_por_cobrar");
    }

    openMercado(vista) {
        this.action.doAction(`lumak_secop.action_lumak_secop_${vista}`);
    }

    openKit() {
        this.action.doAction("lumak_secop.action_lumak_documento");
    }

    openCalendario() {
        this.action.doAction("calendar.action_calendar_event");
    }

    openEvento(id) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: "calendar.event", res_id: id, views: [[false, "form"]] });
    }

    openLead(id) {
        this.action.doAction({
            type: "ir.actions.act_window", res_model: "crm.lead", res_id: id, views: [[false, "form"]],
            context: { form_view_ref: "lumak_secop.crm_lead_form_secop" },
        });
    }
}

registry.category("actions").add("lumak_secop_dashboard", SecopDashboard);
