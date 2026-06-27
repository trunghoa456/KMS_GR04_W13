import json

from odoo import http
from odoo.http import request


class CityRiseAIController(http.Controller):
    def _chat_context(self, embedded=False, force_public=False):
        engine = request.env["cityrise.ai.engine"]
        is_internal = False if force_public else engine._is_internal_user(request.env.user)
        is_manager = is_internal and engine._is_manager_user(request.env.user)
        return {
            "is_internal": is_internal,
            "embedded": embedded,
            "endpoint": "/cityrise_ai/ask_internal" if is_internal else "/cityrise_ai/ask",
            "role_label": "admin" if is_manager else ("employee" if is_internal else "public"),
            "audience_label": "Admin/Manager"
            if is_manager
            else ("Employee/Internal" if is_internal else "Customer/Public"),
        }

    @http.route("/ai-assistant", type="http", auth="public", website=True)
    def ai_assistant_page(self, **kwargs):
        return request.render(
            "cityrise_ai_assistant.ai_assistant_page",
            self._chat_context(embedded=False, force_public=True),
        )

    @http.route("/cityrise_ai/backend_frame", type="http", auth="user", website=False)
    def ai_assistant_backend_frame(self, **kwargs):
        return request.render(
            "cityrise_ai_assistant.ai_assistant_backend_frame",
            self._chat_context(embedded=True),
        )

    @http.route(
        "/cityrise_ai/ask",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        website=True,
    )
    def ask(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.get_data(as_text=True) or "{}")
        except json.JSONDecodeError:
            payload = {}
        result = request.env["cityrise.ai.engine"].with_context(cityrise_force_public=True).ask(
            payload.get("question", ""),
            visitor_name=payload.get("visitor_name"),
            visitor_email=payload.get("visitor_email"),
            visitor_phone=payload.get("visitor_phone"),
        )
        return request.make_json_response(result)

    @http.route(
        "/cityrise_ai/ask_internal",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        website=False,
    )
    def ask_internal(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.get_data(as_text=True) or "{}")
        except json.JSONDecodeError:
            payload = {}
        result = request.env["cityrise.ai.engine"].ask(
            payload.get("question", ""),
            visitor_name=payload.get("visitor_name"),
            visitor_email=payload.get("visitor_email"),
            visitor_phone=payload.get("visitor_phone"),
        )
        return request.make_json_response(result)
