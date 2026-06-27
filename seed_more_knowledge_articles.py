r"""Seed extra CityRise KMS Knowledge articles.

Run inside the Odoo container:

    Get-Content .\seed_more_knowledge_articles.py | docker compose exec -T odoo `
        odoo shell -d cityrise_w13 --no-http

The script is idempotent: existing articles with the same title are updated
instead of duplicated.
"""

from odoo.tools import html_escape


PARENTS = {
    "sales": "SALES",
    "purchase": "PURCHASE",
    "ops": "TICKETS",
    "hr": "HR",
    "it": "IT",
    "legal": "LEGAL",
}


ARTICLES = [
    {
        "name": "Sales Lead Qualification Checklist",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Lead", "Qualification"],
        "summary": "How sales staff qualify a buyer before creating a quotation.",
        "steps": [
            "Confirm customer name, phone, preferred area, budget range, and purpose: living, rental, or investment.",
            "Map the request to available product templates and record any must-have criteria.",
            "Escalate to manager when the buyer requests discount, unusual payment terms, or reserved stock.",
        ],
    },
    {
        "name": "Property Viewing Appointment Script",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Appointment", "Customer"],
        "summary": "Standard call script for booking a property viewing.",
        "steps": [
            "Confirm customer availability and preferred channel before proposing the viewing time.",
            "Mention property name, address context, estimated duration, and required identification documents.",
            "Create the calendar appointment and attach the related quotation or CRM lead.",
        ],
    },
    {
        "name": "Quotation Approval Thresholds",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Quotation", "Approval"],
        "summary": "When a quotation needs manager approval before being sent.",
        "steps": [
            "Salesperson may send standard-price quotations without additional approval.",
            "Manager approval is required for discount, custom payment schedule, or priority reservation.",
            "Attach reason, customer risk, and expected close date in the quotation chatter.",
        ],
    },
    {
        "name": "Deposit Reservation Handling SOP",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Deposit", "Reservation"],
        "summary": "How to handle customer deposits and unit reservation notes.",
        "steps": [
            "Verify the selected property, quoted price, expected deposit amount, and reservation expiry.",
            "Record the deposit follow-up activity and notify accounting when payment evidence arrives.",
            "Do not mark a unit as reserved without payment evidence or manager approval.",
        ],
    },
    {
        "name": "Payment Follow-up Escalation Matrix",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Payment", "Escalation"],
        "summary": "Follow-up timing for unpaid quotations and confirmed sales orders.",
        "steps": [
            "Day 1: send polite reminder and confirm payment channel.",
            "Day 3: call customer and log the reason for delay in Odoo activity.",
            "Day 5: escalate to manager for risk review or revised closing plan.",
        ],
    },
    {
        "name": "Discount Exception Request Procedure",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Discount", "Approval"],
        "summary": "Required evidence before requesting a discount exception.",
        "steps": [
            "Capture competitor offer, customer budget, target property, and expected payment date.",
            "Manager compares margin impact against inventory priority before approval.",
            "Approved discount must be written in quotation notes and retained for audit.",
        ],
    },
    {
        "name": "Customer Objection Handling Playbook",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Customer", "Playbook"],
        "summary": "Common responses for price, location, timing, and trust objections.",
        "steps": [
            "Acknowledge the objection first and restate the customer's concern.",
            "Answer with public product facts, viewing options, payment schedule, or support channel.",
            "Do not promise unavailable discounts, legal guarantees, or private internal data.",
        ],
    },
    {
        "name": "Sales Handover to Operations",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Operations", "Handover"],
        "summary": "What sales must hand over after a customer confirms.",
        "steps": [
            "Attach signed quotation, payment evidence, customer contact, and promised move-in expectations.",
            "Create an operations task when documentation or property viewing support is required.",
            "Keep sensitive customer documents restricted to internal users only.",
        ],
    },
    {
        "name": "Contract Document Checklist",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Contract", "Checklist"],
        "summary": "Minimum documents before contract preparation.",
        "steps": [
            "Confirm customer identity, selected property, agreed price, payment schedule, and deposit status.",
            "Check whether legal or manager review is needed before sharing a contract draft.",
            "Store final customer-facing files in the related sales order chatter.",
        ],
    },
    {
        "name": "Lost Deal Review Template",
        "workspace_dimension": "sales",
        "tags": ["Sales", "Review", "CRM"],
        "summary": "Review questions for lost quotations and CRM opportunities.",
        "steps": [
            "Identify the lost reason: price, timing, location, competitor, financing, or no response.",
            "Record lessons learned and whether product catalog data needs correction.",
            "Use the review to improve future recommendations and follow-up timing.",
        ],
    },
    {
        "name": "Vendor Onboarding Checklist",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Vendor", "Onboarding"],
        "summary": "Required checks before adding a new supplier to procurement.",
        "steps": [
            "Collect legal name, tax code, bank information, contact person, and product/service scope.",
            "Validate vendor category, expected lead time, and document requirements.",
            "Manager approval is required for high-value or strategic suppliers.",
        ],
    },
    {
        "name": "RFQ Comparison and Shortlist SOP",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "RFQ", "Comparison"],
        "summary": "How buyers compare supplier quotations.",
        "steps": [
            "Compare unit price, taxes, delivery time, payment terms, warranty, and supplier reliability.",
            "Keep at least two comparable offers for non-urgent high-value purchases when possible.",
            "Document the selected vendor rationale in the purchase order notes.",
        ],
    },
    {
        "name": "Purchase Approval Threshold Matrix",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Approval", "Control"],
        "summary": "Approval control for purchase orders by value and risk.",
        "steps": [
            "Routine low-value purchases may be confirmed by assigned buyer.",
            "High-value, urgent, or exception purchases require manager approval before confirmation.",
            "Approval evidence must remain attached to the purchase order for audit.",
        ],
    },
    {
        "name": "Three-Way Match Receipt Validation",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Receipt", "Invoice"],
        "summary": "Validating purchase order, receipt, and vendor bill.",
        "steps": [
            "Confirm ordered quantity, received quantity, and invoiced quantity match or explain the exception.",
            "Investigate price, tax, or delivery discrepancy before payment approval.",
            "Escalate unresolved mismatch to purchasing manager and accounting.",
        ],
    },
    {
        "name": "Vendor Bill Exception Handling",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Billing", "Exception"],
        "summary": "What to do when a vendor bill cannot be posted.",
        "steps": [
            "Check vendor, tax, receipt state, product lines, and approval status.",
            "If receipt is missing, contact warehouse or responsible buyer before billing.",
            "Do not force payment when the purchase order and bill disagree.",
        ],
    },
    {
        "name": "Late Supplier Delivery Escalation",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Delivery", "Escalation"],
        "summary": "Escalation path for delayed supplier delivery.",
        "steps": [
            "Confirm revised ETA and impact on sales, operations, or customer commitment.",
            "Create follow-up activity on the purchase order and notify impacted teams.",
            "Manager decides whether to wait, split delivery, or source from another vendor.",
        ],
    },
    {
        "name": "Procurement Tax Document Checklist",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Tax", "Compliance"],
        "summary": "Tax documents required before vendor payment.",
        "steps": [
            "Verify invoice number, tax code, vendor name, amount, and VAT/tax rate.",
            "Attach scanned receipt or invoice evidence to the purchase record.",
            "Accounting should reject incomplete tax evidence for high-value purchases.",
        ],
    },
    {
        "name": "Bulk Purchase Risk Review",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Bulk", "Risk"],
        "summary": "Risk review before confirming bulk purchases.",
        "steps": [
            "Review storage capacity, cash impact, demand forecast, and supplier reliability.",
            "Confirm whether phased delivery is safer than one large receipt.",
            "Record manager approval and risk notes in the purchase order chatter.",
        ],
    },
    {
        "name": "Purchase Order Change Control",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Change", "Audit"],
        "summary": "How to handle changes after a purchase order is confirmed.",
        "steps": [
            "Document requested change, reason, requester, and financial impact.",
            "Manager approval is required for price, quantity, vendor, or delivery-date changes.",
            "Keep the original and revised context traceable through chatter messages.",
        ],
    },
    {
        "name": "Vendor Performance Scorecard",
        "workspace_dimension": "purchase",
        "tags": ["Purchase", "Vendor", "Performance"],
        "summary": "Supplier review dimensions after repeated purchases.",
        "steps": [
            "Track delivery timeliness, document completeness, quality issues, and responsiveness.",
            "Use ticket and purchase history to identify recurring vendor risks.",
            "Preferred vendor status should be reviewed periodically by purchasing manager.",
        ],
    },
    {
        "name": "Ticket Severity Classification",
        "workspace_dimension": "ops",
        "tags": ["Ticket", "Support", "SLA"],
        "summary": "How support classifies normal, high, and urgent tickets.",
        "steps": [
            "Urgent: service down, payment blocked, legal risk, or VIP customer impact.",
            "High: repeated customer issue, deadline risk, or unresolved handoff.",
            "Normal: general question, documentation update, or non-blocking request.",
        ],
    },
    {
        "name": "SLA Breach Prevention Checklist",
        "workspace_dimension": "ops",
        "tags": ["Ticket", "SLA", "Checklist"],
        "summary": "Daily checks to prevent support SLA breach.",
        "steps": [
            "Review urgent tickets first and confirm every ticket has an owner.",
            "Update next action and deadline before ending the workday.",
            "Escalate tickets without response, missing data, or cross-team dependency.",
        ],
    },
    {
        "name": "Customer Complaint Triage Script",
        "workspace_dimension": "ops",
        "tags": ["Ticket", "Customer", "Triage"],
        "summary": "First-response script for customer complaints.",
        "steps": [
            "Acknowledge the issue and confirm customer contact, product, and order context.",
            "Classify severity without blaming another team or exposing internal notes.",
            "Share next step and expected response time with the customer.",
        ],
    },
    {
        "name": "Handover Notes for Reassigned Tickets",
        "workspace_dimension": "ops",
        "tags": ["Ticket", "Handover", "Support"],
        "summary": "Required note format when reassigning a ticket.",
        "steps": [
            "Include problem summary, customer impact, evidence checked, and pending decision.",
            "Mention previous promises made to the customer and current SLA risk.",
            "New owner must confirm acceptance before the old owner stops monitoring.",
        ],
    },
    {
        "name": "Warranty Support Escalation SOP",
        "workspace_dimension": "ops",
        "tags": ["Ticket", "Warranty", "Escalation"],
        "summary": "Escalating warranty-related support cases.",
        "steps": [
            "Validate purchase or contract context before discussing warranty scope.",
            "Collect photos, documents, property information, and customer timeline.",
            "Escalate to operations manager if liability, cost, or legal interpretation is unclear.",
        ],
    },
    {
        "name": "Website Inquiry to Helpdesk Conversion",
        "workspace_dimension": "ops",
        "tags": ["Ticket", "Website", "Lead"],
        "summary": "When website inquiries become support tickets instead of leads.",
        "steps": [
            "Create a CRM lead for purchase interest and a ticket for service or complaint issues.",
            "If the message contains both, link the records and assign the support owner.",
            "Public AI should only ask for contact details and avoid internal diagnosis.",
        ],
    },
    {
        "name": "Urgent Ticket Daily Review Routine",
        "workspace_dimension": "ops",
        "tags": ["Ticket", "Urgent", "Review"],
        "summary": "Daily manager routine for urgent support tickets.",
        "steps": [
            "Check urgent tickets at the start and end of day.",
            "Confirm owner, blocker, next action, customer update, and expected resolution.",
            "Move unresolved urgent tickets to manager review before SLA breach.",
        ],
    },
    {
        "name": "Customer Privacy in Support Responses",
        "workspace_dimension": "ops",
        "tags": ["Ticket", "Privacy", "Support"],
        "summary": "How support protects customer privacy in ticket responses.",
        "steps": [
            "Do not expose customer email, phone, login, payment proof, or private documents in public answers.",
            "Summarize the issue at a safe level when responding through customer-facing channels.",
            "Only authorized internal users may inspect raw ticket details.",
        ],
    },
    {
        "name": "Employee Access Request SOP",
        "workspace_dimension": "hr",
        "tags": ["HR", "Access", "Onboarding"],
        "summary": "How managers request Odoo access for employees.",
        "steps": [
            "Manager submits role, department, expected modules, and business justification.",
            "HR validates employee status before IT creates or changes access.",
            "Access must match least-privilege needs and be reviewed after role changes.",
        ],
    },
    {
        "name": "New Employee Knowledge Handoff",
        "workspace_dimension": "hr",
        "tags": ["HR", "Knowledge", "Onboarding"],
        "summary": "Knowledge handoff routine for new employees.",
        "steps": [
            "Assign onboarding article list based on department and role.",
            "Pair the new employee with a mentor for first-week operational questions.",
            "Collect missing documentation gaps and update KMS articles after onboarding.",
        ],
    },
    {
        "name": "Role Change Access Review",
        "workspace_dimension": "hr",
        "tags": ["HR", "Security", "Access"],
        "summary": "Access review when an employee changes role.",
        "steps": [
            "Compare old and new responsibilities before keeping any existing group permissions.",
            "Remove unnecessary module access before granting new permissions.",
            "Record approval from both previous and new manager.",
        ],
    },
    {
        "name": "Offboarding Account Closure Checklist",
        "workspace_dimension": "hr",
        "tags": ["HR", "Offboarding", "Security"],
        "summary": "Steps for employee offboarding and account closure.",
        "steps": [
            "Disable user account, revoke access tokens, and recover assigned devices.",
            "Reassign open tickets, sales orders, purchase follow-ups, and knowledge ownership.",
            "Archive sensitive records according to retention policy.",
        ],
    },
    {
        "name": "Odoo Module Change Request SOP",
        "workspace_dimension": "it",
        "tags": ["IT", "Odoo", "Change"],
        "summary": "Change-control process before modifying Odoo modules.",
        "steps": [
            "Record business request, affected users, expected behavior, and rollback plan.",
            "Test module update on non-production data before applying to demo or production.",
            "Update technical notes and user-facing knowledge articles after deployment.",
        ],
    },
    {
        "name": "Backup and Restore Drill Checklist",
        "workspace_dimension": "it",
        "tags": ["IT", "Backup", "Docker"],
        "summary": "Checklist for database backup and restore drill.",
        "steps": [
            "Confirm latest PostgreSQL backup exists before risky migration or demo changes.",
            "Test restore process on a separate database or container where possible.",
            "Do not submit backup folders, database volumes, or image files to Moodle.",
        ],
    },
    {
        "name": "Incident Communication Template",
        "workspace_dimension": "it",
        "tags": ["IT", "Incident", "Communication"],
        "summary": "Template for internal technical incident updates.",
        "steps": [
            "State impact, affected service, current workaround, owner, and next update time.",
            "Avoid exposing credentials, raw logs, or private customer data in broad channels.",
            "Close the incident with root cause, fix, and prevention note.",
        ],
    },
    {
        "name": "Public Website Content Approval",
        "workspace_dimension": "ops",
        "tags": ["Website", "Public", "Approval"],
        "summary": "Approval workflow for public website content.",
        "steps": [
            "Verify product information, price, contact flow, and customer-facing language.",
            "Remove internal notes, supplier details, or private record identifiers before publishing.",
            "Manager approval is required for homepage, promotion, or price changes.",
        ],
    },
    {
        "name": "CRM Lead Handoff Standard",
        "workspace_dimension": "ops",
        "tags": ["CRM", "Lead", "Handoff"],
        "summary": "Standard for handing off AI/customer inquiries to sales.",
        "steps": [
            "Capture customer need, contact details, preferred property type, and urgency.",
            "Assign the lead to sales owner and link related website or chat conversation.",
            "Follow up within one working day for high-intent buyer requests.",
        ],
    },
    {
        "name": "Data Privacy Handling for Customer Records",
        "workspace_dimension": "legal",
        "tags": ["Legal", "Privacy", "Customer"],
        "summary": "Privacy baseline for customer and contact records.",
        "steps": [
            "Only collect data needed for consultation, support, appointment, or transaction processing.",
            "Do not expose customer contact details through public AI or public website answers.",
            "Limit sensitive record access to employees with a business reason.",
        ],
    },
    {
        "name": "Legal Document Retention Policy",
        "workspace_dimension": "legal",
        "tags": ["Legal", "Retention", "Document"],
        "summary": "Retention expectations for contract and compliance documents.",
        "steps": [
            "Keep final signed customer documents attached to authorized Odoo records.",
            "Archive obsolete drafts and mark final versions clearly.",
            "Do not delete legal evidence without manager and compliance approval.",
        ],
    },
    {
        "name": "Admin Audit Trail Review Procedure",
        "workspace_dimension": "legal",
        "tags": ["Legal", "Audit", "Admin"],
        "summary": "How managers review sensitive operational activity.",
        "steps": [
            "Review conversation logs, role decisions, and source summaries during security checks.",
            "Investigate repeated access-denied attempts or public prompts for restricted data.",
            "Document corrective action and update access rules when gaps are found.",
        ],
    },
]


def article_html(article):
    items = "".join("<li>%s</li>" % html_escape(step) for step in article["steps"])
    return """
        <section>
            <h2>%s</h2>
            <p>%s</p>
            <h3>Procedure</h3>
            <ol>%s</ol>
        </section>
    """ % (
        html_escape(article["name"]),
        html_escape(article["summary"]),
        items,
    )


def seed_extra_knowledge_articles(env, commit=True):
    Article = env["kms.knowledge.article"].sudo()
    Tag = env["res.partner.category"].sudo()
    tag_cache = {}

    def tag_ids(names):
        result = []
        for name in names:
            tag = tag_cache.get(name)
            if not tag:
                tag = Tag.search([("name", "=", name)], limit=1)
                if not tag:
                    tag = Tag.create({"name": name})
                tag_cache[name] = tag
            result.append(tag.id)
        return result

    parents = {}
    for dimension, title in PARENTS.items():
        parent = Article.search([("name", "=", title)], limit=1)
        values = {
            "name": title,
            "workspace_dimension": dimension,
            "body_html": "<section><h2>%s</h2><p>Workspace index for CityRise %s knowledge articles.</p></section>"
            % (html_escape(title), html_escape(title.lower())),
            "tag_ids": [(6, 0, tag_ids(["Workspace", title.title()]))],
            "active": True,
        }
        if parent:
            parent.write(values)
        else:
            parent = Article.create(values)
        parents[dimension] = parent

    created = 0
    updated = 0
    for article in ARTICLES:
        values = {
            "name": article["name"],
            "workspace_dimension": article["workspace_dimension"],
            "body_html": article_html(article),
            "parent_id": parents.get(article["workspace_dimension"]).id if article["workspace_dimension"] in parents else False,
            "tag_ids": [(6, 0, tag_ids(article["tags"]))],
            "active": True,
        }
        record = Article.search([("name", "=", article["name"])], limit=1)
        if record:
            record.write(values)
            updated += 1
        else:
            Article.create(values)
            created += 1

    if commit:
        env.cr.commit()
    return created, updated


if "env" in globals():
    created, updated = seed_extra_knowledge_articles(env)
    print(
        "Seeded extra KMS knowledge articles: %s created, %s updated, %s total requested."
        % (created, updated, len(ARTICLES))
    )
