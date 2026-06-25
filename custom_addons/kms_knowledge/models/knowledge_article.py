from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class KmsKnowledgeArticle(models.Model):
    _name = "kms.knowledge.article"
    _description = "KMS Knowledge Article"
    _order = "workspace_dimension, parent_id, name"

    name = fields.Char(string="Title", required=True)
    body_html = fields.Html(string="Rich-text SOP Content")
    parent_id = fields.Many2one(
        "kms.knowledge.article",
        string="Parent Article",
        index=True,
        ondelete="set null",
    )
    child_ids = fields.One2many(
        "kms.knowledge.article",
        "parent_id",
        string="Child Articles",
    )
    workspace_dimension = fields.Selection(
        [
            ("hr", "HR"),
            ("it", "IT"),
            ("legal", "Legal"),
            ("ops", "Operations"),
            ("sales", "Sales"),
            ("purchase", "Purchase"),
        ],
        string="Workspace Dimension",
        required=True,
        default="ops",
    )
    tag_ids = fields.Many2many(
        "res.partner.category",
        "kms_article_res_partner_category_rel",
        "article_id",
        "category_id",
        string="Metadata Tags",
    )
    icon = fields.Char(string="Icon")
    cover_url = fields.Char(string="Cover Image URL")
    properties_note = fields.Text(string="Properties")
    is_locked = fields.Boolean(string="Locked")
    is_template = fields.Boolean(string="Template")
    is_full_width = fields.Boolean(string="Full Width")
    active = fields.Boolean(default=True)

    @api.constrains("parent_id")
    def _check_parent_id_recursion(self):
        if self._has_cycle("parent_id"):
            raise ValidationError(_("An article cannot be its own parent."))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._create_version_snapshot(_("Created"))
        return records

    def write(self, vals):
        tracked_fields = {
            "name",
            "body_html",
            "parent_id",
            "workspace_dimension",
            "tag_ids",
            "icon",
            "cover_url",
            "properties_note",
            "is_locked",
            "is_template",
            "is_full_width",
            "active",
        }
        if tracked_fields.intersection(vals) and not self.env.context.get("skip_kms_version"):
            self._create_version_snapshot(_("Before update"))
        return super().write(vals)

    def copy_article(self):
        self.ensure_one()
        copy = self.with_context(skip_kms_version=True).copy(
            {
                "name": _("Copy of %s") % self.name,
                "is_locked": False,
                "active": True,
            }
        )
        copy._create_version_snapshot(_("Copied from %s") % self.name)
        return copy.read(self._client_fields())[0]

    def restore_version(self, version_id):
        self.ensure_one()
        version = self.env["kms.knowledge.article.version"].browse(version_id).exists()
        if not version or version.article_id != self:
            raise ValidationError(_("The selected version does not belong to this article."))
        self.write(
            {
                "name": version.name,
                "body_html": version.body_html,
                "workspace_dimension": version.workspace_dimension,
                "icon": version.icon,
                "cover_url": version.cover_url,
                "properties_note": version.properties_note,
                "is_locked": version.is_locked,
                "is_template": version.is_template,
                "is_full_width": version.is_full_width,
                "active": True,
            }
        )
        return self.read(self._client_fields())[0]

    def _client_fields(self):
        return [
            "id",
            "name",
            "body_html",
            "workspace_dimension",
            "tag_ids",
            "parent_id",
            "write_uid",
            "write_date",
            "active",
            "icon",
            "cover_url",
            "properties_note",
            "is_locked",
            "is_template",
            "is_full_width",
        ]

    def _create_version_snapshot(self, change_summary):
        values = []
        for article in self:
            values.append(
                {
                    "article_id": article.id,
                    "name": article.name,
                    "body_html": article.body_html,
                    "workspace_dimension": article.workspace_dimension,
                    "icon": article.icon,
                    "cover_url": article.cover_url,
                    "properties_note": article.properties_note,
                    "is_locked": article.is_locked,
                    "is_template": article.is_template,
                    "is_full_width": article.is_full_width,
                    "active": article.active,
                    "change_summary": change_summary,
                }
            )
        if values:
            self.env["kms.knowledge.article.version"].create(values)


class KmsKnowledgeArticleVersion(models.Model):
    _name = "kms.knowledge.article.version"
    _description = "KMS Knowledge Article Version"
    _order = "create_date desc, id desc"

    article_id = fields.Many2one(
        "kms.knowledge.article",
        string="Article",
        required=True,
        index=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Title", required=True)
    body_html = fields.Html(string="Rich-text SOP Content")
    workspace_dimension = fields.Selection(
        selection=lambda self: self.env["kms.knowledge.article"]._fields["workspace_dimension"].selection,
        string="Workspace Dimension",
        required=True,
        default="ops",
    )
    icon = fields.Char(string="Icon")
    cover_url = fields.Char(string="Cover Image URL")
    properties_note = fields.Text(string="Properties")
    is_locked = fields.Boolean(string="Locked")
    is_template = fields.Boolean(string="Template")
    is_full_width = fields.Boolean(string="Full Width")
    active = fields.Boolean(default=True)
    change_summary = fields.Char(string="Change Summary")
