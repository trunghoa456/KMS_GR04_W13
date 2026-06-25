{
    "name": "CityRise AI Assistant",
    "version": "19.0.1.0.0",
    "category": "Productivity",
    "summary": "Guarded AI-style assistant for CityRise website and operators",
    "author": "CityRise",
    "license": "LGPL-3",
    "depends": [
        "web",
        "crm",
        "hr",
        "website_sale",
        "cityrise_helpdesk",
        "cityrise_website_shop",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/ai_templates.xml",
        "views/ai_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cityrise_ai_assistant/static/src/backend/ai_iframe_action.js",
            "cityrise_ai_assistant/static/src/backend/ai_iframe_action.xml",
            "cityrise_ai_assistant/static/src/backend/ai_iframe_action.scss",
        ],
        "web.assets_frontend": [
            "cityrise_ai_assistant/static/src/css/ai_assistant.css",
            "cityrise_ai_assistant/static/src/js/ai_assistant.js",
        ],
    },
    "application": True,
    "installable": True,
}
