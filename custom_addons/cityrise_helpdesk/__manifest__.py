{
    "name": "CityRise Helpdesk",
    "version": "19.0.1.0.0",
    "category": "Services/Helpdesk",
    "summary": "Simple helpdesk overview and ticket intake for CityRise",
    "author": "CityRise",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/helpdesk_sequence.xml",
        "views/helpdesk_views.xml",
    ],
    "application": True,
    "installable": True,
    "license": "LGPL-3",
}
