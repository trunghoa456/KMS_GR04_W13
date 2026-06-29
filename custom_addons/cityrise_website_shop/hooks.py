import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


MODULE_DIR = Path(__file__).resolve().parent
LOGO_PATH = MODULE_DIR / "static" / "src" / "img" / "cityrise_logo.png"

PURPLE = "#714b67"
SOFT_PURPLE = "#b99acc"
TEAL = "#00a09d"
INK = "#1f2430"


def _jpeg_data(image):
    stream = BytesIO()
    image.convert("RGB").save(stream, format="JPEG", quality=88, optimize=True)
    return base64.b64encode(stream.getvalue())


def _logo_data():
    if not LOGO_PATH.exists():
        return False
    return base64.b64encode(LOGO_PATH.read_bytes())


def _gradient(width, height, top, bottom):
    image = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(
            int(top[i] * (1 - ratio) + bottom[i] * ratio)
            for i in range(3)
        )
        draw.line([(0, y), (width, y)], fill=color)
    return image


def _image_modern_villa():
    image = _gradient(1200, 900, (177, 207, 230), (237, 240, 233))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 690, 1200, 900), fill=(118, 146, 105))
    draw.rectangle((105, 410, 1095, 690), fill=(206, 213, 210))
    draw.rectangle((145, 455, 1055, 690), fill=(64, 95, 111))
    for x in range(180, 1030, 170):
        draw.rectangle((x, 465, x + 110, 670), fill=(105, 142, 158), outline=(230, 238, 238), width=5)
    draw.polygon([(80, 390), (1120, 390), (1060, 455), (130, 455)], fill=(137, 75, 45))
    draw.rectangle((115, 690, 1090, 715), fill=(236, 236, 226))
    draw.ellipse((500, 610, 720, 820), fill=(67, 102, 72))
    draw.rectangle((605, 705, 625, 835), fill=(83, 69, 48))
    draw.ellipse((492, 570, 736, 710), fill=(74, 118, 83))
    draw.ellipse((735, 710, 1065, 780), fill=(230, 230, 221))
    draw.ellipse((170, 724, 520, 800), fill=(229, 229, 219))
    return image.filter(ImageFilter.SMOOTH)


def _image_classic_villa():
    image = _gradient(1200, 900, (190, 220, 239), (247, 239, 216))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 705, 1200, 900), fill=(121, 151, 104))
    draw.rectangle((210, 305, 990, 725), fill=(226, 214, 190), outline=(177, 158, 126), width=6)
    draw.polygon([(170, 305), (1030, 305), (945, 225), (255, 225)], fill=(194, 177, 146))
    draw.rectangle((250, 252, 950, 305), fill=(238, 227, 203), outline=(162, 143, 111), width=4)
    for x in [310, 460, 610, 760]:
        draw.rectangle((x, 390, x + 92, 635), fill=(122, 163, 181), outline=(246, 241, 224), width=8)
        draw.arc((x + 2, 346, x + 90, 434), 180, 360, fill=(246, 241, 224), width=8)
    for x in [265, 545, 825]:
        draw.rectangle((x, 330, x + 35, 720), fill=(244, 238, 218), outline=(178, 159, 130), width=3)
        draw.ellipse((x - 12, 318, x + 47, 345), fill=(244, 238, 218), outline=(178, 159, 130))
    draw.rectangle((542, 515, 658, 725), fill=(104, 83, 68), outline=(238, 226, 199), width=6)
    draw.ellipse((420, 715, 780, 795), fill=(228, 228, 218))
    draw.rectangle((160, 725, 1040, 750), fill=(238, 232, 214))
    return image.filter(ImageFilter.SMOOTH_MORE)


def _image_apartment_room():
    image = Image.new("RGB", (1200, 900), (232, 221, 205))
    draw = ImageDraw.Draw(image)
    draw.polygon([(0, 0), (260, 110), (260, 900), (0, 900)], fill=(220, 205, 190))
    draw.rectangle((740, 165, 1120, 610), fill=(197, 222, 235), outline=(40, 54, 62), width=12)
    draw.line((930, 165, 930, 610), fill=(40, 54, 62), width=8)
    draw.rectangle((0, 660, 1200, 900), fill=(222, 199, 171))
    draw.rectangle((400, 545, 820, 710), fill=(75, 148, 91))
    draw.polygon([(360, 630), (830, 630), (900, 805), (300, 805)], fill=(68, 137, 84))
    draw.rectangle((160, 575, 430, 720), fill=(133, 107, 95))
    draw.polygon([(430, 590), (565, 625), (565, 790), (430, 720)], fill=(146, 121, 109))
    draw.ellipse((610, 645, 820, 780), fill=(245, 239, 228))
    draw.rectangle((685, 760, 705, 865), fill=(142, 97, 52))
    draw.rectangle((298, 705, 1110, 870), fill=(198, 187, 180))
    draw.ellipse((510, 93, 560, 138), fill=(255, 245, 221))
    draw.ellipse((880, 95, 930, 140), fill=(255, 245, 221))
    return image.filter(ImageFilter.SMOOTH)


def _image_townhouse():
    image = _gradient(1200, 900, (170, 204, 223), (245, 237, 220))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 685, 1200, 900), fill=(142, 139, 128))
    colors = [(214, 206, 190), (198, 214, 216), (225, 213, 198), (205, 198, 213)]
    for i, x in enumerate(range(95, 980, 220)):
        draw.rectangle((x, 265, x + 185, 700), fill=colors[i % len(colors)], outline=(142, 134, 126), width=4)
        draw.rectangle((x + 32, 335, x + 153, 455), fill=(94, 137, 155), outline=(245, 245, 235), width=5)
        draw.rectangle((x + 32, 500, x + 153, 620), fill=(94, 137, 155), outline=(245, 245, 235), width=5)
        draw.rectangle((x + 67, 625, x + 118, 700), fill=(92, 76, 66))
        draw.polygon([(x - 8, 265), (x + 92, 195), (x + 193, 265)], fill=(128, 72, 58))
    return image.filter(ImageFilter.SMOOTH)


def _image_penthouse():
    image = _gradient(1200, 900, (154, 198, 229), (239, 236, 227))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 600, 1200, 900), fill=(91, 108, 123))
    for x in range(80, 1120, 90):
        height = 250 + (x % 270)
        draw.rectangle((x, 600 - height, x + 62, 720), fill=(70, 88, 105), outline=(146, 166, 181), width=3)
        for y in range(620 - height, 680, 50):
            draw.rectangle((x + 12, y, x + 50, y + 22), fill=(202, 224, 233))
    draw.rectangle((250, 455, 950, 735), fill=(218, 218, 212), outline=(238, 238, 228), width=8)
    draw.rectangle((300, 495, 900, 675), fill=(79, 115, 135), outline=(238, 238, 228), width=7)
    draw.rectangle((560, 680, 640, 735), fill=(98, 78, 68))
    return image.filter(ImageFilter.SMOOTH_MORE)


def _image_courtyard_home():
    image = _gradient(1200, 900, (174, 215, 241), (249, 245, 231))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 640, 1200, 900), fill=(219, 209, 190))
    draw.rectangle((130, 355, 1070, 665), fill=(246, 242, 232), outline=(198, 188, 169), width=4)
    draw.polygon([(90, 355), (1110, 355), (1005, 255), (195, 255)], fill=(178, 106, 72))
    for x in [230, 430, 760, 930]:
        draw.rectangle((x, 440, x + 125, 585), fill=(103, 148, 158), outline=(150, 101, 65), width=8)
    draw.rectangle((520, 430, 675, 665), fill=(128, 78, 52), outline=(232, 218, 196), width=7)
    draw.rectangle((90, 665, 1110, 710), fill=(232, 226, 211))
    draw.rectangle((760, 705, 1080, 825), fill=(177, 198, 142))
    return image.filter(ImageFilter.SMOOTH)


def _image_bright_studio():
    image = Image.new("RGB", (1200, 900), (236, 222, 205))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 620, 1200, 900), fill=(218, 198, 174))
    draw.rectangle((85, 160, 470, 620), fill=(237, 230, 216))
    draw.rectangle((125, 210, 430, 330), fill=(184, 215, 229))
    draw.rectangle((150, 360, 465, 600), fill=(248, 246, 239))
    draw.rectangle((650, 170, 1085, 635), fill=(205, 168, 126))
    draw.rectangle((760, 270, 990, 635), fill=(86, 84, 79))
    draw.rectangle((560, 535, 945, 690), fill=(202, 177, 148))
    draw.ellipse((160, 620, 430, 770), fill=(235, 231, 222))
    for x in [210, 315]:
        draw.ellipse((x, 550, x + 52, 610), fill=(210, 218, 225))
    draw.ellipse((335, 42, 525, 118), fill=(63, 72, 84))
    return image.filter(ImageFilter.SMOOTH)


def _image_minimal_shopfront():
    image = _gradient(1200, 900, (226, 239, 242), (248, 244, 233))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 690, 1200, 900), fill=(204, 203, 193))
    draw.rectangle((105, 300, 1095, 690), fill=(246, 245, 238), outline=(205, 198, 185), width=5)
    draw.polygon([(85, 300), (1115, 300), (1000, 210), (205, 210)], fill=(225, 230, 230))
    draw.rectangle((190, 405, 420, 690), fill=(199, 224, 211), outline=(235, 235, 226), width=6)
    draw.rectangle((715, 385, 970, 690), fill=(152, 116, 74), outline=(238, 232, 214), width=8)
    draw.ellipse((585, 410, 690, 515), fill=(179, 210, 188), outline=(110, 150, 125), width=4)
    draw.rectangle((220, 350, 370, 378), fill=(184, 154, 100))
    draw.text((235, 345), "BARBER", fill=(150, 116, 82))
    draw.rectangle((980, 300, 1095, 690), fill=(163, 116, 73))
    return image.filter(ImageFilter.SMOOTH_MORE)


def _image_night_villa():
    image = _gradient(1200, 900, (45, 83, 112), (141, 174, 191))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 675, 1200, 900), fill=(52, 62, 62))
    draw.rectangle((265, 265, 935, 710), fill=(222, 214, 191), outline=(93, 76, 70), width=6)
    draw.polygon([(235, 265), (965, 265), (875, 180), (325, 180)], fill=(54, 66, 82))
    for x in [340, 515, 690]:
        draw.rectangle((x, 370, x + 105, 570), fill=(210, 229, 225), outline=(70, 63, 65), width=7)
        draw.arc((x + 2, 322, x + 103, 424), 180, 360, fill=(70, 63, 65), width=7)
    draw.rectangle((545, 560, 655, 710), fill=(91, 65, 52))
    for x in [240, 940]:
        draw.rectangle((x, 585, x + 28, 760), fill=(230, 223, 204))
    draw.rectangle((160, 755, 1040, 800), fill=(46, 47, 48))
    return image.filter(ImageFilter.SMOOTH_MORE)


def _image_waterfront_row():
    image = _gradient(1200, 900, (176, 216, 241), (247, 240, 219))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 625, 1200, 900), fill=(128, 178, 170))
    for i, x in enumerate(range(105, 1040, 190)):
        draw.rectangle((x, 280, x + 150, 620), fill=(235, 236, 229), outline=(177, 171, 157), width=4)
        draw.polygon([(x - 10, 280), (x + 75, 220), (x + 160, 280)], fill=(62, 79, 85))
        draw.rectangle((x + 35, 365, x + 115, 500), fill=(108, 155, 174), outline=(236, 236, 228), width=5)
        draw.rectangle((x + 48, 515, x + 102, 620), fill=(110, 86, 67))
        draw.ellipse((x + 112, 585, x + 182, 665), fill=(101, 153, 91))
    draw.line((0, 695, 1200, 650), fill=(225, 244, 244), width=5)
    return image.filter(ImageFilter.SMOOTH)


def _image_white_interior():
    image = Image.new("RGB", (1200, 900), (238, 238, 238))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1200, 625), fill=(246, 246, 244))
    draw.rectangle((0, 625, 1200, 900), fill=(218, 213, 206))
    draw.rectangle((80, 255, 430, 620), fill=(228, 227, 222))
    draw.rectangle((125, 315, 400, 490), fill=(248, 248, 246))
    draw.rectangle((600, 305, 1040, 650), fill=(242, 242, 239))
    draw.rectangle((820, 360, 1030, 610), fill=(70, 72, 75))
    draw.ellipse((510, 590, 745, 735), fill=(238, 236, 229))
    draw.rectangle((140, 585, 520, 735), fill=(68, 68, 70))
    draw.ellipse((525, 42, 675, 110), fill=(230, 230, 224))
    return image.filter(ImageFilter.SMOOTH)


def _cityrise_shop_products():
    return [
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0075\u0031\u0038", 79_000_000_000, 0, _image_modern_villa(), "Modern luxury apartment with garden-facing glass facade."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0063\u0037\u0037", 12_000_000_000, 0, _image_classic_villa(), "Premium city residence with classical architecture."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0039\u0030\u0078", 13_500_000_000, 15_000_000_000, _image_apartment_room(), "Compact serviced apartment with bright interior and city view."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0072\u0031\u0032", 10_000_000_000, 0, _image_courtyard_home(), "Courtyard apartment with a calm tiled-roof exterior."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0073\u0069\u00ea\u0075 \u0073\u0061\u006f", 50_000_000_000, 0, _image_bright_studio(), "Premium serviced apartment with integrated living and dining space."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0079\u0032\u0032", 12_000_000_000, 0, _image_minimal_shopfront(), "Minimal white-front residence with bright garden-facing entry."),
        ("\u0043\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0031\u0030\u0032", 10_000_000_000, 0, _image_townhouse(), "High-end townhouse apartment in a quiet residential row."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0031\u0030\u0033", 11_000_000_000, 0, _image_classic_villa(), "Classic villa-style residence with private gate and greenery."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0032\u0030\u0035", 15_000_000_000, 0, _image_night_villa(), "Elegant frontage apartment with premium architectural details."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0031\u0030\u0030", 10_000_000_000, 0, _image_night_villa(), "Luxury residence with a grand facade and evening lighting."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0031\u0030\u0036", 11_050_000_000, 0, _image_townhouse(), "Modern row-house apartment with warm street-facing details."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0031\u0030\u0038", 20_000_000_000, 0, _image_waterfront_row(), "Waterfront apartment row with garden and open view."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0035\u0030\u0035", 9_000_000_000, 0, _image_white_interior(), "Bright white interior apartment with open living area."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0045\u0031\u0031", 12_310_000_000, 0, _image_courtyard_home(), "Green-entry premium apartment with private balcony."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u0061\u006f \u0063\u1ea5\u0070 \u0041\u0038\u0038", 15_000_000_000, 0, _image_waterfront_row(), "Modern residential row apartment with bright facade."),
        ("\u0063\u0103\u006e \u0068\u1ed9 river r09", 9_700_000_000, 10_500_000_000, _image_waterfront_row(), "River-view apartment with open balcony and riverside walking access."),
        ("\u0063\u0103\u006e \u0068\u1ed9 sunrise s18", 7_900_000_000, 0, _image_bright_studio(), "Morning-light residence for young families near daily amenities."),
        ("\u0063\u0103\u006e \u0068\u1ed9 metro m12", 6_800_000_000, 0, _image_apartment_room(), "Compact city apartment near transit and retail services."),
        ("\u0063\u0103\u006e \u0068\u1ed9 garden g11", 11_800_000_000, 0, _image_modern_villa(), "Green courtyard apartment with quiet family-friendly layout."),
        ("\u0063\u0103\u006e \u0068\u1ed9 sky a01", 18_600_000_000, 0, _image_night_villa(), "High-floor sky residence with premium evening skyline view."),
        ("\u0063\u0103\u006e \u0068\u1ed9 duplex d08", 24_500_000_000, 26_000_000_000, _image_white_interior(), "Two-level duplex residence with large living room and private study."),
        ("\u0063\u0103\u006e \u0068\u1ed9 ocean o22", 16_900_000_000, 0, _image_waterfront_row(), "Waterfront-inspired apartment with resort-style public spaces."),
        ("\u0063\u0103\u006e \u0068\u1ed9 central c12", 14_200_000_000, 0, _image_classic_villa(), "Central residence with fast access to school, office and shopping areas."),
        ("\u0062\u0069\u1ec7\u0074 \u0074\u0068\u1ef1 lake l09", 92_000_000_000, 0, _image_classic_villa(), "Lake-facing villa for premium family living and private entertaining."),
        ("shophouse avenue a05", 36_500_000_000, 0, _image_townhouse(), "Avenue shophouse suitable for living, showroom and rental income."),
        ("penthouse river p18", 64_000_000_000, 68_000_000_000, _image_penthouse(), "Penthouse with river-facing terrace and private entertainment zone."),
        ("villa garden v20", 78_000_000_000, 0, _image_modern_villa(), "Garden villa with wide frontage and calm residential landscaping."),
        ("studio smart s09", 4_900_000_000, 0, _image_apartment_room(), "Efficient smart studio for first-time buyers or rental investment."),
        ("\u0063\u0103\u006e \u0068\u1ed9 family f15", 12_800_000_000, 0, _image_courtyard_home(), "Family apartment with balanced bedrooms, storage and dining space."),
        ("\u0063\u0103\u006e \u0068\u1ed9 smart h06", 8_400_000_000, 0, _image_white_interior(), "Smart-home apartment with bright interior and flexible furniture plan."),
        ("\u0063\u0103\u006e \u0068\u1ed9 \u0063\u00f4\u006e\u0067 \u0076\u0069\u00ea\u006e v11", 13_900_000_000, 0, _image_modern_villa(), "Park-view apartment with balcony facing green public space."),
        ("\u0063\u0103\u006e \u0068\u1ed9 premium p25", 21_300_000_000, 0, _image_night_villa(), "Premium residence for executives needing privacy and refined finishes."),
        ("\u006e\u0068\u00e0 \u0070\u0068\u1ed1 city n07", 28_900_000_000, 0, _image_townhouse(), "City townhouse with flexible ground-floor commercial frontage."),
        ("\u0063\u0103\u006e \u0068\u1ed9 balcony b14", 10_600_000_000, 0, _image_minimal_shopfront(), "Balcony apartment with simple facade and bright street-facing entry."),
        ("\u0063\u0103\u006e \u0068\u1ed9 sunrise s22", 9_300_000_000, 0, _image_bright_studio(), "Sunrise-view apartment with efficient plan and comfortable daily living."),
    ]


def _create_attachment(env, name, image):
    Attachment = env["ir.attachment"].sudo()
    old = Attachment.search([("name", "=", name), ("res_model", "=", "cityrise.website.shop")])
    old.unlink()
    return Attachment.create({
        "name": name,
        "type": "binary",
        "datas": _jpeg_data(image),
        "mimetype": "image/jpeg",
        "public": True,
        "res_model": "cityrise.website.shop",
    })


def _set_view_active(env, xmlid, active):
    view = env.ref(xmlid, raise_if_not_found=False)
    if view:
        view.sudo().write({"active": active})


def _page_arch(title, subtitle, body):
    return f"""<t name="{title}" t-name="cityrise_website_shop.{title.lower().replace(' ', '_')}">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure cityrise-page">
            <section class="cityrise-simple-hero">
                <div class="container">
                    <p class="cityrise-eyebrow">CityRise</p>
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
            </section>
            <section class="cityrise-copy-band">
                <div class="container">
                    {body}
                </div>
            </section>
        </div>
    </t>
</t>"""


def _write_page(env, website, url, name, arch):
    Page = env["website.page"].sudo()
    page = Page.search([("url", "=", url), ("website_id", "=", website.id)], limit=1)
    values = {
        "name": name,
        "url": url,
        "website_id": website.id,
        "is_published": True,
        "website_published": True,
        "website_indexed": True,
        "type": "qweb",
        "key": f"cityrise_website_shop.{name.lower().replace(' ', '_')}",
        "arch": arch,
    }
    if page:
        page.write(values)
        return page
    return Page.create(values)


def _configure_pages(env, website):
    hero = _create_attachment(env, "cityrise_hero_real_estate.jpg", _image_modern_villa())
    home_arch = f"""<t name="CityRise Home" t-name="cityrise_website_shop.cityrise_home">
    <t t-call="website.layout" pageName.f="homepage">
        <div id="wrap" class="oe_structure cityrise-homepage">
            <section class="cityrise-hero" style="background-image: linear-gradient(90deg, rgba(31, 36, 48, 0.70), rgba(31, 36, 48, 0.24)), url('/web/image/{hero.id}');">
                <div class="container">
                    <p class="cityrise-eyebrow">CityRise Real Estate</p>
                    <h1>Modern homes for people building their next chapter</h1>
                    <p>Explore curated apartments, villas, and investment-ready properties with a clean Odoo-powered commerce experience.</p>
                    <div class="cityrise-hero-actions">
                        <a class="btn btn-primary" href="/shop">View Properties</a>
                        <a class="btn btn-light" href="/contactus">Contact Us</a>
                    </div>
                </div>
            </section>
            <section class="cityrise-copy-band">
                <div class="container">
                    <div class="cityrise-feature-grid">
                        <article>
                            <span>01</span>
                            <h2>Premium catalog</h2>
                            <p>Each listing is organized as an Odoo product so your team can update price, images, and availability directly.</p>
                        </article>
                        <article>
                            <span>02</span>
                            <h2>Fast consultation</h2>
                            <p>Customers can browse, search, add favorites, and contact the CityRise team from the same website flow.</p>
                        </article>
                        <article>
                            <span>03</span>
                            <h2>Sales-ready data</h2>
                            <p>The shop connects naturally with quotation and order workflows already available in your database.</p>
                        </article>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>"""
    _write_page(env, website, "/", "CityRise Home", home_arch)
    _write_page(
        env,
        website,
        "/help",
        "Help",
        _page_arch(
            "Help",
            "Need support choosing a property or updating your order?",
            "<h2>Customer Care</h2><p>Send us your question and the CityRise team will help you with property details, visit schedules, and after-sales requests.</p><p><a class=\"btn btn-primary\" href=\"/contactus\">Contact Support</a></p>",
        ),
    )
    _write_page(
        env,
        website,
        "/appointment",
        "Appointment",
        _page_arch(
            "Appointment",
            "Book a consultation or property visit with CityRise.",
            "<h2>Schedule a visit</h2><p>Use this page to collect appointment details, preferred time, property interest, and contact information.</p><p><a class=\"btn btn-primary\" href=\"/contactus\">Request Appointment</a></p>",
        ),
    )


def _configure_menu(env, website):
    Menu = env["website.menu"].sudo()
    root = Menu.search([("website_id", "=", website.id), ("parent_id", "=", False)], limit=1)
    if not root:
        root = env.ref("website.main_menu").sudo().copy({
            "name": f"Top Menu for Website {website.id}",
            "website_id": website.id,
        })
    root.child_id.unlink()
    for sequence, name, url in [
        (10, "Home", "/"),
        (20, "Shop", "/shop"),
        (30, "Help", "/help"),
        (40, "Appointment", "/appointment"),
        (50, "Contact us", "/contactus"),
    ]:
        page = env["website.page"].sudo().search([
            ("url", "=", url),
            ("website_id", "=", website.id),
        ], limit=1)
        Menu.create({
            "name": name,
            "url": url,
            "parent_id": root.id,
            "website_id": website.id,
            "sequence": sequence,
            "page_id": page.id if page else False,
        })


def _configure_shop_options(env, website):
    vnd = _ensure_vnd_pricelist(env, website)
    logo = _logo_data()
    website.write({
        "name": "CityRise",
        "shop_page_container": "regular",
        "shop_ppg": 36,
        "shop_ppr": 3,
        "shop_gap": "20px",
        "shop_default_sort": "website_sequence asc",
        "shop_opt_products_design_classes": (
            "o_wsale_products_opt_layout_catalog "
            "o_wsale_products_opt_design_thumbs "
            "o_wsale_products_opt_name_color_regular "
            "o_wsale_products_opt_thumb_cover "
            "o_wsale_products_opt_img_hover_zoom_out_light "
            "o_wsale_products_opt_has_wishlist "
            "o_wsale_products_opt_wishlist_fixed "
            "o_wsale_products_opt_rounded_2 "
            "o_wsale_products_opt_has_comparison"
        ),
    })
    if logo:
        website.write({"logo": logo})
    if website.company_id:
        company_values = {
            "name": "CityRise",
            "phone": "+1 555-555-5556",
            "email": "customer-care@edu-cityrise.odoo.com",
        }
        if logo:
            company_values.update({
                "logo": logo,
                "logo_web": logo,
            })
        website.company_id.write(company_values)
    for xmlid, active in [
        ("website_sale.products_categories", False),
        ("website_sale.products_categories_top", True),
        ("website_sale.products_attributes", True),
        ("website_sale.products_attributes_top", False),
        ("website_sale.filter_products_price", True),
        ("website_sale.search", True),
        ("website_sale.sort", True),
        ("website_sale.products_shop_title", True),
        ("website_sale.products_shop_title_align", False),
        ("website_sale.floating_bar", False),
    ]:
        _set_view_active(env, xmlid, active)
    env["res.config.settings"].sudo().create({
        "website_id": website.id,
        "group_product_pricelist": True,
        "group_product_price_comparison": True,
    }).execute()
    if vnd:
        public_partner = env.ref("base.public_partner", raise_if_not_found=False)
        website.company_id.partner_id.property_product_pricelist = vnd
        if public_partner:
            public_partner.property_product_pricelist = vnd


def _ensure_vnd_pricelist(env, website):
    Currency = env["res.currency"].sudo()
    vnd = Currency.with_context(active_test=False).search([("name", "=", "VND")], limit=1)
    if vnd:
        vnd.write({
            "active": True,
            "symbol": "đ",
            "position": "after",
            "rounding": 1.0,
        })
    else:
        currency_values = {
            "name": "VND",
            "symbol": "đ",
            "position": "after",
            "rounding": 1.0,
            "active": True,
        }
        if "currency_unit_label" in Currency._fields:
            currency_values["currency_unit_label"] = "Dong"
        if "currency_subunit_label" in Currency._fields:
            currency_values["currency_subunit_label"] = "Xu"
        vnd = Currency.create(currency_values)
    Rate = env["res.currency.rate"].sudo()
    if not Rate.search([("currency_id", "=", vnd.id), ("company_id", "=", website.company_id.id)], limit=1):
        Rate.create({
            "currency_id": vnd.id,
            "company_id": website.company_id.id,
            "rate": 1.0,
        })
    Pricelist = env["product.pricelist"].sudo()
    pricelist = Pricelist.search([("name", "=", "CityRise VND"), ("website_id", "=", website.id)], limit=1)
    values = {
        "name": "CityRise VND",
        "currency_id": vnd.id,
        "website_id": website.id,
        "company_id": website.company_id.id,
        "selectable": True,
        "active": True,
        "sequence": 1,
    }
    if pricelist:
        pricelist.write(values)
    else:
        pricelist = Pricelist.create(values)
    return pricelist


def _configure_livechat(env, website):
    user = env["res.users"].sudo().search([("login", "=", "tran.trung.hoa@cityrise.local")], limit=1)
    if not user:
        user = env.user
    Channel = env["im_livechat.channel"].sudo()
    channel = Channel.search([("name", "=", "CityRise Customer Care")], limit=1)
    values = {
        "name": "CityRise Customer Care",
        "button_text": "Chat with us",
        "user_ids": [(6, 0, [user.id])],
    }
    if channel:
        channel.write(values)
    else:
        channel = Channel.create(values)
    website.write({"channel_id": channel.id})


def _configure_products(env, website):
    Category = env["product.public.category"].sudo()
    stale_categories = Category.search([("name", "!=", "Căn hộ hạng sang")])
    stale_categories.filtered(lambda category: not env["product.template"].sudo().search_count([("public_categ_ids", "=", category.id)])).unlink()
    category = Category.search([("name", "=", "Căn hộ hạng sang"), ("website_id", "in", [False, website.id])], limit=1)
    category_values = {
        "name": "Căn hộ hạng sang",
        "website_id": website.id,
        "sequence": 1,
        "show_category_title": False,
        "show_category_description": False,
        "align_category_content": False,
    }
    if category:
        category.write(category_values)
    else:
        category = Category.create(category_values)

    products = [
        ("căn hộ u18", 79_000_000_000, 0, _image_modern_villa(), "Modern luxury apartment with garden-facing glass facade."),
        ("căn hộ cao cấp c77", 12_000_000_000, 0, _image_classic_villa(), "Premium city residence with classical architecture."),
        ("căn hộ 90x", 13_500_000_000, 15_000_000_000, _image_apartment_room(), "Compact serviced apartment with bright interior and city view."),
        ("biệt thự ven sông c88", 85_000_000_000, 0, _image_classic_villa(), "Signature riverside villa for high-end living."),
        ("nhà phố thương mại a12", 32_500_000_000, 0, _image_townhouse(), "Shophouse suitable for residence and commercial use."),
        ("penthouse skyview p01", 58_000_000_000, 0, _image_penthouse(), "Penthouse with skyline view and private terrace."),
        ("căn hộ garden g05", 8_800_000_000, 0, _image_modern_villa(), "Garden apartment designed for family living."),
        ("studio city s02", 5_500_000_000, 0, _image_apartment_room(), "Efficient studio option near central amenities."),
        ("gói tư vấn chọn căn hộ", 5_000_000, 0, _image_townhouse(), "Consultation package for viewing and property shortlisting."),
    ]
    products = _cityrise_shop_products()
    Product = env["product.template"].sudo().with_context(tracking_disable=True)
    target_names = [product[0] for product in products]
    Product.search([
        ("public_categ_ids", "=", category.id),
        ("name", "not in", target_names),
    ]).write({
        "website_published": False,
        "is_published": False,
        "public_categ_ids": [(3, category.id)],
    })
    for index, (name, price, compare_price, image, description) in enumerate(products, start=1):
        product = Product.search([("name", "=", name)], limit=1)
        values = {
            "name": name,
            "sale_ok": True,
            "purchase_ok": False,
            "type": "service",
            "list_price": price,
            "compare_list_price": compare_price,
            "description_sale": description,
            "website_description": f"<p>{description}</p>",
            "website_published": True,
            "is_published": True,
            "website_id": website.id,
            "website_sequence": index,
            "sequence": index,
            "public_categ_ids": [(6, 0, [category.id])],
            "image_1920": _jpeg_data(image),
        }
        if product:
            product.write(values)
        else:
            Product.create(values)


def post_init_hook(env):
    website = env["website"].sudo().search([], order="id", limit=1)
    if not website:
        return
    _configure_pages(env, website)
    _configure_menu(env, website)
    _configure_shop_options(env, website)
    _configure_livechat(env, website)
    _configure_products(env, website)
