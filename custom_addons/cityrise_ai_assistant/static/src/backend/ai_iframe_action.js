import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class CityRiseAIIframeAction extends Component {
    static template = "cityrise_ai_assistant.IframeAction";
}

registry.category("actions").add("cityrise_ai_assistant.iframe_action", CityRiseAIIframeAction);
