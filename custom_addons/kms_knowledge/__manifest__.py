{
    "name": "KMS Knowledge",
    "version": "1.0",
    "category": "Productivity/Knowledge",
    "summary": "Knowledge-style workspace for KMS articles",
    "author": "Local",
    "depends": ["web", "kms_app_dashboard"],
    "data": [
        "security/ir.model.access.csv",
        "views/knowledge_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "kms_knowledge/static/src/knowledge/knowledge_app.js",
            "kms_knowledge/static/src/knowledge/knowledge_app.xml",
            "kms_knowledge/static/src/knowledge/knowledge_app.scss",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
    "post_init_hook": "post_init_hook",
}
