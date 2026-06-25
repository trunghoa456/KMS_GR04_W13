{
    "name": "KMS App Dashboard",
    "version": "1.0",
    "category": "Productivity/Dashboard",
    "summary": "Home dashboard for active Odoo apps",
    "author": "Local",
    "depends": ["web"],
    "data": [
        "views/app_dashboard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "kms_app_dashboard/static/src/app_dashboard/app_dashboard.js",
            "kms_app_dashboard/static/src/app_dashboard/app_dashboard.xml",
            "kms_app_dashboard/static/src/app_dashboard/app_dashboard.scss",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
