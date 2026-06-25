{
    "name": "CityRise Website Shop",
    "version": "1.0",
    "category": "Website",
    "summary": "CityRise website and eCommerce demo layout",
    "author": "CityRise",
    "license": "LGPL-3",
    "depends": [
        "website_sale",
        "website_sale_wishlist",
        "website_livechat",
    ],
    "assets": {
        "web.assets_frontend": [
            "cityrise_website_shop/static/src/css/cityrise_website.css",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
