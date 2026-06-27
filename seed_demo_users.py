r"""Create the Week 12/13 demo login accounts in the active Odoo database.

Run this file through ``odoo shell`` so it can use the pre-created ``env``:

PowerShell:
    Get-Content .\seed_demo_users.py | docker compose exec -T odoo `
        odoo shell -d cityrise_w13 --no-http --db_host=db --db_port=5432 `
        --db_user=odoo --db_password=odoo

The script is idempotent: running it again updates the same accounts, resets
their demo passwords, and restores the expected security groups.
"""


def group(xmlid):
    record = env.ref(xmlid, raise_if_not_found=False)
    if not record:
        print(f"Skipping unavailable group: {xmlid}")
    return record


def group_ids(xmlids):
    return [record.id for record in (group(xmlid) for xmlid in xmlids) if record]


def upsert_user(values, xmlids):
    Users = env["res.users"].sudo().with_context(
        no_reset_password=True,
        tracking_disable=True,
    )
    user = Users.search([("login", "=", values["login"])], limit=1)
    groups = group_ids(xmlids)
    payload = {
        "name": values["name"],
        "login": values["login"],
        "email": values["login"],
        "active": True,
        "group_ids": [(6, 0, groups)],
    }

    if user:
        user.write(payload)
        user._change_password(values["password"])
        action = "Updated"
    else:
        user = Users.create({**payload, "password": values["password"]})
        action = "Created"

    print(f"{action}: {user.login} ({values['role']})")


ACCOUNTS = [
    {
        "name": "CityRise Demo Employee",
        "login": "employee@cityrise.demo",
        "password": "employee123",
        "role": "Employee",
        "groups": [
            "base.group_user",
            "sales_team.group_sale_salesman",
            "purchase.group_purchase_user",
        ],
    },
    {
        "name": "CityRise Demo Manager",
        "login": "manager@cityrise.demo",
        "password": "manager123",
        "role": "Manager/Admin",
        "groups": [
            "base.group_user",
            "base.group_erp_manager",
            "base.group_system",
            "sales_team.group_sale_manager",
            "hr.group_hr_manager",
            "purchase.group_purchase_manager",
            "purchase.group_purchase_user",
            "stock.group_stock_user",
            "account.group_account_readonly",
            "account.group_account_user",
        ],
    },
    {
        "name": "CityRise Demo Customer",
        "login": "customer@cityrise.demo",
        "password": "customer123",
        "role": "Customer/Portal",
        "groups": [
            "base.group_portal",
        ],
    },
]


for account in ACCOUNTS:
    upsert_user(account, account["groups"])

env.cr.commit()
print("Demo accounts are ready.")
