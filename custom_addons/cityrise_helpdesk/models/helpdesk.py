from datetime import datetime

from odoo import _, api, fields, models


class CityRiseHelpdeskTeam(models.Model):
    _name = "cityrise.helpdesk.team"
    _description = "Helpdesk Team"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, tracking=True)
    email = fields.Char(string="Email Alias", tracking=True)
    color = fields.Integer(default=10)
    user_id = fields.Many2one("res.users", string="Team Leader", tracking=True)
    member_ids = fields.Many2many("res.users", string="Members")
    daily_target = fields.Integer(default=1)
    sla_success_target = fields.Float(string="SLA Success Target (%)", default=85)
    ticket_ids = fields.One2many("cityrise.helpdesk.ticket", "team_id", string="Tickets")
    open_ticket_count = fields.Integer(compute="_compute_ticket_counts")
    unassigned_ticket_count = fields.Integer(compute="_compute_ticket_counts")
    urgent_ticket_count = fields.Integer(compute="_compute_ticket_counts")
    failed_ticket_count = fields.Integer(compute="_compute_ticket_counts")
    closed_ticket_count = fields.Integer(compute="_compute_ticket_counts")

    def _compute_ticket_counts(self):
        for team in self:
            tickets = team.ticket_ids
            open_tickets = tickets.filtered(lambda ticket: ticket.stage not in ("closed", "failed"))
            team.open_ticket_count = len(open_tickets)
            team.unassigned_ticket_count = len(open_tickets.filtered(lambda ticket: not ticket.user_id))
            team.urgent_ticket_count = len(open_tickets.filtered(lambda ticket: ticket.priority == "2"))
            team.failed_ticket_count = len(tickets.filtered(lambda ticket: ticket.stage == "failed"))
            team.closed_ticket_count = len(tickets.filtered(lambda ticket: ticket.stage == "closed"))

    def action_view_tickets(self):
        self.ensure_one()
        action = self.env.ref("cityrise_helpdesk.action_helpdesk_tickets")._get_action_dict()
        action["domain"] = [("team_id", "=", self.id)]
        action["context"] = {"default_team_id": self.id, "search_default_open": 1}
        return action


class CityRiseHelpdeskTicket(models.Model):
    _name = "cityrise.helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, id desc"
    _rec_names_search = ["number", "name", "partner_name", "partner_email"]

    number = fields.Char(default=lambda self: _("New"), copy=False, readonly=True, index=True)
    name = fields.Char(string="Subject", required=True, tracking=True)
    team_id = fields.Many2one("cityrise.helpdesk.team", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Customer")
    partner_name = fields.Char(string="Customer Name")
    partner_email = fields.Char(string="Customer Email")
    user_id = fields.Many2one("res.users", string="Assigned To", tracking=True)
    priority = fields.Selection(
        [("0", "Normal"), ("1", "High Priority"), ("2", "Urgent")],
        default="0",
        tracking=True,
    )
    stage = fields.Selection(
        [
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("waiting", "Waiting"),
            ("closed", "Closed"),
            ("failed", "Failed"),
        ],
        default="new",
        required=True,
        tracking=True,
    )
    description = fields.Html()
    deadline = fields.Datetime()
    date_closed = fields.Datetime(readonly=True)
    open_hours = fields.Float(compute="_compute_open_hours")
    is_open = fields.Boolean(compute="_compute_is_open", search="_search_is_open")

    @api.depends("stage")
    def _compute_is_open(self):
        for ticket in self:
            ticket.is_open = ticket.stage not in ("closed", "failed")

    def _search_is_open(self, operator, value):
        if (operator == "=" and value) or (operator == "!=" and not value):
            return [("stage", "not in", ("closed", "failed"))]
        return [("stage", "in", ("closed", "failed"))]

    @api.depends("create_date", "date_closed", "stage")
    def _compute_open_hours(self):
        now = fields.Datetime.now()
        for ticket in self:
            start = ticket.create_date or now
            end = ticket.date_closed or now
            ticket.open_hours = max((end - start).total_seconds() / 3600, 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("number", _("New")) == _("New"):
                vals["number"] = self.env["ir.sequence"].next_by_code("cityrise.helpdesk.ticket") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("stage") == "closed" and "date_closed" not in vals:
            vals["date_closed"] = fields.Datetime.now()
        if vals.get("stage") not in (None, "closed") and "date_closed" not in vals:
            vals["date_closed"] = False
        return super().write(vals)

    def action_close(self):
        self.write({"stage": "closed", "date_closed": fields.Datetime.now()})

    def action_fail(self):
        self.write({"stage": "failed"})

    def action_reopen(self):
        self.write({"stage": "in_progress", "date_closed": False})
