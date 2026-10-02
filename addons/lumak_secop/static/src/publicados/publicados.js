import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";

// «Todo lo publicado»: la lista de siempre con una explicación arriba, para no confundirla con «Mis procesos»
export class PublicadosListRenderer extends ListRenderer {
    static template = "lumak_secop.PublicadosListRenderer";
}

registry.category("views").add("lumak_publicados_list", { ...listView, Renderer: PublicadosListRenderer });
