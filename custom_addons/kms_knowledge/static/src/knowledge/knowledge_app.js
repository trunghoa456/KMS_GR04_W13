import { Component, markup, onMounted, onPatched, onWillStart, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";

const DIMENSION_LABELS = {
    hr: "HR",
    it: "IT",
    legal: "Legal",
    ops: "Operations",
    sales: "Sales",
    purchase: "Purchase",
};
const FOLDER_DIMENSIONS = {
    OPERATIONS: "ops",
    SALES: "sales",
    PURCHASE: "purchase",
};
const SHARED_DIMENSIONS = Object.values(FOLDER_DIMENSIONS);
const ARTICLE_FIELDS = [
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
];

export class KmsKnowledgeApp extends Component {
    static template = "kms_knowledge.App";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.menuService = useService("menu");
        this.notification = useService("notification");
        this.state = useState({
            articles: [],
            trashArticles: [],
            versionHistory: [],
            selectedId: "welcome",
            query: "",
            isCreating: false,
            isMoreMenuOpen: false,
            isVersionHistoryOpen: false,
            isFullWidth: false,
        });
        onWillStart(async () => {
            await this.loadArticles();
        });
        onMounted(() => {
            document.body.classList.add("o_kms_knowledge_open");
            this.applyActionRoute();
            this.bindHomeMenuClick();
            this.bindDocumentClick();
        });
        onPatched(() => this.applyActionRoute());
        onWillUnmount(() => {
            document.body.classList.remove("o_kms_knowledge_open");
            this.unbindHomeMenuClick();
            this.unbindDocumentClick();
        });
    }

    get actionParams() {
        return this.props.action?.params || {};
    }

    applyActionRoute() {
        const routeKey = `${this.props.action?.id || ""}:${this.actionParams.default_page || ""}`;
        if (routeKey === this._lastActionRouteKey) {
            return;
        }
        this._lastActionRouteKey = routeKey;
        if (this.actionParams.default_page === "home" || window.location.pathname.endsWith("/knowledge_home")) {
            this.openDashboard();
        }
    }

    bindHomeMenuClick() {
        if (this._homeMenuClickHandler) {
            return;
        }
        this._homeMenuClickHandler = (ev) => {
            const target = ev.target.closest(".o_nav_entry, .dropdown-item, [data-menu-xmlid]");
            if (!this.isKnowledgeHomeMenu(target)) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            if (ev.stopImmediatePropagation) {
                ev.stopImmediatePropagation();
            }
            this.openDashboard();
        };
        document.addEventListener("click", this._homeMenuClickHandler, true);
    }

    isKnowledgeHomeMenu(target) {
        if (!target || !document.body.classList.contains("o_kms_knowledge_open")) {
            return false;
        }
        const inNavbar = Boolean(target.closest(".o_main_navbar"));
        const menuXmlid = target.dataset?.menuXmlid || "";
        const label = (target.textContent || "").trim();
        return (
            inNavbar &&
            (menuXmlid === "kms_knowledge.menu_kms_knowledge_home" ||
                menuXmlid === "menu_kms_knowledge_home" ||
                label === "Home")
        );
    }

    unbindHomeMenuClick() {
        if (!this._homeMenuClickHandler) {
            return;
        }
        document.removeEventListener("click", this._homeMenuClickHandler, true);
        this._homeMenuClickHandler = null;
    }

    bindDocumentClick() {
        if (this._documentClickHandler) {
            return;
        }
        this._documentClickHandler = (ev) => {
            if (!ev.target.closest(".kms_knowledge__more")) {
                this.closeMoreMenu();
            }
        };
        document.addEventListener("click", this._documentClickHandler);
    }

    unbindDocumentClick() {
        if (!this._documentClickHandler) {
            return;
        }
        document.removeEventListener("click", this._documentClickHandler);
        this._documentClickHandler = null;
    }

    get articles() {
        const query = this.state.query.trim().toLowerCase();
        if (!query) {
            return this.state.articles;
        }
        return this.state.articles.filter((article) => {
            return `${article.name || ""} ${article.workspace_dimension || ""} ${article.body_html || ""}`
                .toLowerCase()
                .includes(query);
        });
    }

    async loadArticles() {
        const [articles, trashArticles] = await Promise.all([
            this.orm.searchRead("kms.knowledge.article", [["active", "=", true]], ARTICLE_FIELDS, {
                order: "id asc",
            }),
            this.orm.searchRead("kms.knowledge.article", [["active", "=", false]], ARTICLE_FIELDS, {
                order: "write_date desc, id desc",
                context: { active_test: false },
            }),
        ]);
        this.state.articles = articles;
        this.state.trashArticles = trashArticles;
    }

    get selectedArticle() {
        return this.state.articles.find((article) => article.id === this.state.selectedId) || false;
    }

    get articleContent() {
        return markup(this.selectedArticle?.body_html || "");
    }

    get isTrash() {
        return this.state.selectedId === "trash";
    }

    get isTemplates() {
        return this.state.selectedId === "templates";
    }

    get isWelcome() {
        return (
            this.state.selectedId === "welcome" ||
            (!this.isTrash && !this.isTemplates && !this.selectedArticle)
        );
    }

    get canEditSelectedArticle() {
        return Boolean(this.selectedArticle && !this.selectedArticle.is_locked);
    }

    get userDisplayName() {
        return user.login && user.login !== "__system__" ? user.login : user.name || "Administrator";
    }

    get selectedEditorName() {
        const writeUid = this.selectedArticle?.write_uid;
        if (Array.isArray(writeUid) && writeUid[1]) {
            return writeUid[1];
        }
        return this.userDisplayName;
    }

    get selectedEditorInitial() {
        return (this.selectedEditorName || "U").trim().slice(0, 1).toUpperCase();
    }

    get selectedEditedLabel() {
        return this.relativeEditedLabel(this.selectedArticle?.write_date);
    }

    relativeEditedLabel(rawDate) {
        if (!rawDate) {
            return "just now";
        }
        const editedAt = new Date(`${rawDate.replace(" ", "T")}Z`);
        if (Number.isNaN(editedAt.getTime())) {
            return "recently";
        }
        const diffSeconds = Math.max(0, Math.floor((Date.now() - editedAt.getTime()) / 1000));
        const units = [
            ["year", 31536000],
            ["month", 2592000],
            ["day", 86400],
            ["hour", 3600],
            ["minute", 60],
        ];
        for (const [label, seconds] of units) {
            const value = Math.floor(diffSeconds / seconds);
            if (value >= 1) {
                return `${value} ${label}${value > 1 ? "s" : ""} ago`;
            }
        }
        return "just now";
    }

    editedLabel(article) {
        return this.relativeEditedLabel(article?.write_date || article?.create_date);
    }

    get baseArticles() {
        return this.articles.filter((article) => {
            return !SHARED_DIMENSIONS.includes(article.workspace_dimension);
        });
    }

    get templateArticles() {
        return this.articles.filter((article) => article.is_template);
    }

    get operationArticles() {
        return this.dimensionArticles("ops");
    }

    get salesArticles() {
        return this.dimensionArticles("sales");
    }

    get purchaseArticles() {
        return this.dimensionArticles("purchase");
    }

    get otherArticles() {
        return this.baseArticles;
    }

    dimensionArticles(dimension) {
        return this.articles.filter((article) => article.workspace_dimension === dimension);
    }

    shortTitle(title) {
        if (!title) {
            return "Untitled";
        }
        return title.length > 34 ? `${title.slice(0, 31)}...` : title;
    }

    articleIcon(article) {
        return article?.icon || false;
    }

    goHome() {
        this.closeMoreMenu();
        this.closeVersionHistory();
        this.state.selectedId = "welcome";
        this.state.query = "";
        const content = document.querySelector(".kms_knowledge__content");
        if (content) {
            content.scrollTop = 0;
        }
    }

    async openDashboard() {
        this.closeMoreMenu();
        const dashboardApp = this.menuService
            .getApps()
            .find((app) => {
                return (
                    app.xmlid === "kms_app_dashboard.menu_kms_app_dashboard_root" ||
                    app.actionPath === "apps-dashboard" ||
                    app.name === "Dashboard"
                );
            });
        if (dashboardApp) {
            await this.menuService.selectMenu(dashboardApp);
            return;
        }
        window.location.assign("/odoo/apps-dashboard");
    }

    selectWelcome() {
        this.goHome();
    }

    selectArticle(article) {
        this.closeMoreMenu();
        this.closeVersionHistory();
        this.state.selectedId = article.id;
        this.state.isFullWidth = Boolean(article.is_full_width);
    }

    async openTrash() {
        this.closeMoreMenu();
        this.closeVersionHistory();
        this.state.selectedId = "trash";
        this.state.query = "";
        await this.loadArticles();
        const content = document.querySelector(".kms_knowledge__content");
        if (content) {
            content.scrollTop = 0;
        }
    }

    async openTemplates() {
        this.closeMoreMenu();
        this.closeVersionHistory();
        this.state.selectedId = "templates";
        this.state.query = "";
        await this.loadArticles();
        const content = document.querySelector(".kms_knowledge__content");
        if (content) {
            content.scrollTop = 0;
        }
    }

    onSearch(ev) {
        this.state.query = ev.target.value;
        if (
            !this.isTrash &&
            !this.isTemplates &&
            this.state.selectedId !== "welcome" &&
            !this.articles.some((article) => article.id === this.state.selectedId)
        ) {
            this.state.selectedId = "welcome";
        }
    }

    dimensionLabel(dimension) {
        return DIMENSION_LABELS[dimension] || "Unassigned";
    }

    toggleMoreMenu(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.state.isMoreMenuOpen = !this.state.isMoreMenuOpen;
    }

    closeMoreMenu() {
        this.state.isMoreMenuOpen = false;
    }

    async toggleFullWidth(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.state.isFullWidth = !this.state.isFullWidth;
        if (this.selectedArticle) {
            await this.writeSelectedArticle({ is_full_width: this.state.isFullWidth }, "Full width updated.", {
                allowLocked: true,
            });
        }
    }

    showMenuNotice(label, ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }
        this.notification.add(`${label} is available in the full Odoo Knowledge editor.`, { type: "info" });
        this.closeMoreMenu();
    }

    async writeSelectedArticle(values, message, options = {}) {
        const article = this.selectedArticle;
        if (!article?.id) {
            this.closeMoreMenu();
            return false;
        }
        if (article.is_locked && !options.allowLocked) {
            this.notification.add("This article is locked. Unlock it before editing.", { type: "warning" });
            this.closeMoreMenu();
            return false;
        }
        await this.orm.write("kms.knowledge.article", [article.id], values);
        await this.loadArticles();
        const updated = this.state.articles.find((item) => item.id === article.id);
        if (updated) {
            this.state.selectedId = updated.id;
            this.state.isFullWidth = Boolean(updated.is_full_width);
        }
        if (message) {
            this.notification.add(message, { type: "success" });
        }
        this.closeMoreMenu();
        return true;
    }

    async addIcon(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const value = window.prompt("Icon for this article", this.selectedArticle?.icon || "");
        if (value === null) {
            this.closeMoreMenu();
            return;
        }
        await this.writeSelectedArticle({ icon: value.trim() || false }, "Icon updated.");
    }

    async addCover(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const value = window.prompt("Cover image URL", this.selectedArticle?.cover_url || "");
        if (value === null) {
            this.closeMoreMenu();
            return;
        }
        await this.writeSelectedArticle({ cover_url: value.trim() || false }, "Cover updated.");
    }

    async addProperties(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const value = window.prompt("Article properties", this.selectedArticle?.properties_note || "");
        if (value === null) {
            this.closeMoreMenu();
            return;
        }
        await this.writeSelectedArticle({ properties_note: value.trim() || false }, "Properties updated.");
    }

    async moveSelectedArticle(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const value = window.prompt(
            "Move to workspace: ops, sales, purchase, hr, it, legal",
            this.selectedArticle?.workspace_dimension || "ops"
        );
        if (value === null) {
            this.closeMoreMenu();
            return;
        }
        const dimension = value.trim().toLowerCase();
        if (!DIMENSION_LABELS[dimension]) {
            this.notification.add("Invalid workspace. Use ops, sales, purchase, hr, it, or legal.", {
                type: "danger",
            });
            return;
        }
        await this.writeSelectedArticle(
            { workspace_dimension: dimension },
            `Moved to ${this.dimensionLabel(dimension)}.`
        );
    }

    async toggleLockContent(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        await this.writeSelectedArticle(
            { is_locked: !this.selectedArticle?.is_locked },
            this.selectedArticle?.is_locked ? "Content unlocked." : "Content locked.",
            { allowLocked: true }
        );
    }

    async duplicateSelectedArticle(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const article = this.selectedArticle;
        if (!article?.id) {
            this.closeMoreMenu();
            return;
        }
        const copy = await this.orm.call("kms.knowledge.article", "copy_article", [[article.id]]);
        await this.loadArticles();
        this.state.selectedId = copy.id;
        this.state.isFullWidth = Boolean(copy.is_full_width);
        this.notification.add("Copy created.", { type: "success" });
        this.closeMoreMenu();
    }

    async openVersionHistory(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const article = this.selectedArticle;
        if (!article?.id) {
            this.closeMoreMenu();
            return;
        }
        this.state.versionHistory = await this.orm.searchRead(
            "kms.knowledge.article.version",
            [["article_id", "=", article.id]],
            [
                "id",
                "name",
                "workspace_dimension",
                "change_summary",
                "create_uid",
                "create_date",
                "icon",
                "cover_url",
                "properties_note",
                "is_locked",
                "is_template",
                "is_full_width",
            ],
            { order: "create_date desc, id desc" }
        );
        this.state.isVersionHistoryOpen = true;
        this.closeMoreMenu();
    }

    closeVersionHistory() {
        this.state.isVersionHistoryOpen = false;
    }

    async restoreVersion(version, ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const article = this.selectedArticle;
        if (!article?.id || !version?.id) {
            return;
        }
        const restored = await this.orm.call("kms.knowledge.article", "restore_version", [
            [article.id],
            version.id,
        ]);
        await this.loadArticles();
        this.state.selectedId = restored.id;
        this.state.isFullWidth = Boolean(restored.is_full_width);
        this.notification.add("Version restored.", { type: "success" });
        this.closeVersionHistory();
    }

    downloadPdf(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const article = this.selectedArticle;
        if (!article?.id) {
            this.closeMoreMenu();
            return;
        }
        const pdf = this.buildSimplePdf(article);
        const blob = new Blob([pdf], { type: "application/pdf" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${this.safeFileName(article.name)}.pdf`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        this.notification.add("PDF downloaded.", { type: "success" });
        this.closeMoreMenu();
    }

    buildSimplePdf(article) {
        const title = this.asPdfText(article.name || "Knowledge Article");
        const body = this.asPdfText(this.htmlToText(article.body_html || ""));
        const properties = this.asPdfText(article.properties_note || "");
        const lines = [
            title,
            "",
            `Workspace: ${this.dimensionLabel(article.workspace_dimension)}`,
            article.is_locked ? "Status: Locked" : "",
            article.is_template ? "Template: Yes" : "",
            properties ? `Properties: ${properties}` : "",
            "",
            ...this.wrapPdfText(body, 88),
        ].filter((line, index) => line || index < 2);
        const pages = [];
        for (let index = 0; index < lines.length; index += 42) {
            pages.push(lines.slice(index, index + 42));
        }
        if (!pages.length) {
            pages.push([title]);
        }

        const objects = [];
        const addObject = (content) => {
            objects.push(content);
            return objects.length;
        };

        addObject("<< /Type /Catalog /Pages 2 0 R >>");
        addObject("__PAGES__");
        addObject("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");

        const pageObjectIds = [];
        for (const pageLines of pages) {
            const stream = [
                "BT",
                "/F1 12 Tf",
                "50 760 Td",
                "15 TL",
                ...pageLines.map((line) => `(${this.escapePdfString(line)}) Tj T*`),
                "ET",
            ].join("\n");
            const contentId = addObject(`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
            const pageId = addObject(
                `<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 3 0 R >> >> /MediaBox [0 0 612 792] /Contents ${contentId} 0 R >>`
            );
            pageObjectIds.push(pageId);
        }
        objects[1] = `<< /Type /Pages /Kids [${pageObjectIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pageObjectIds.length} >>`;

        let pdf = "%PDF-1.4\n";
        const offsets = [0];
        for (let index = 0; index < objects.length; index++) {
            offsets.push(pdf.length);
            pdf += `${index + 1} 0 obj\n${objects[index]}\nendobj\n`;
        }
        const xrefOffset = pdf.length;
        pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
        for (let index = 1; index < offsets.length; index++) {
            pdf += `${String(offsets[index]).padStart(10, "0")} 00000 n \n`;
        }
        pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
        return pdf;
    }

    htmlToText(html) {
        const element = document.createElement("div");
        element.innerHTML = html;
        return element.textContent || element.innerText || "";
    }

    asPdfText(text) {
        return String(text)
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^\x20-\x7E\n\r\t]/g, "?")
            .replace(/\s+/g, " ")
            .trim();
    }

    wrapPdfText(text, width) {
        const words = String(text || "").split(/\s+/).filter(Boolean);
        const lines = [];
        let line = "";
        for (const word of words) {
            const candidate = line ? `${line} ${word}` : word;
            if (candidate.length > width && line) {
                lines.push(line);
                line = word;
            } else {
                line = candidate;
            }
        }
        if (line) {
            lines.push(line);
        }
        return lines;
    }

    escapePdfString(text) {
        return String(text).replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
    }

    safeFileName(name) {
        return this.asPdfText(name || "knowledge-article")
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-|-$/g, "")
            .slice(0, 80) || "knowledge-article";
    }

    async addToTemplates(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        await this.writeSelectedArticle({ is_template: true }, "Added to templates.");
    }

    async convertIntoArticleItem(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        if (!this.selectedArticle?.is_template) {
            this.notification.add("This page is already an article item.", { type: "info" });
            this.closeMoreMenu();
            return;
        }
        await this.writeSelectedArticle({ is_template: false }, "Converted into article item.");
    }

    async createFromTemplate(article, ev) {
        ev.preventDefault();
        ev.stopPropagation();
        if (!article?.id) {
            return;
        }
        const copy = await this.orm.call("kms.knowledge.article", "copy_article", [[article.id]]);
        await this.loadArticles();
        this.state.selectedId = copy.id;
        this.state.isFullWidth = Boolean(copy.is_full_width);
        this.notification.add("Article created from template.", { type: "success" });
    }

    async sendSelectedToTrash(ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }
        const article = this.selectedArticle;
        if (!article?.id) {
            this.closeMoreMenu();
            return;
        }
        if (article.is_locked) {
            this.notification.add("This article is locked. Unlock it before moving it to trash.", {
                type: "warning",
            });
            this.closeMoreMenu();
            return;
        }
        await this.orm.write("kms.knowledge.article", [article.id], { active: false });
        this.notification.add("Moved to trash.", { type: "success" });
        this.closeMoreMenu();
        this.state.selectedId = "trash";
        await this.loadArticles();
    }

    async restoreArticle(article, ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }
        if (!article?.id) {
            return;
        }
        await this.orm.write("kms.knowledge.article", [article.id], { active: true });
        await this.loadArticles();
        this.state.selectedId = article.id;
        this.notification.add("Article restored.", { type: "success" });
    }

    async createArticle(folderName, ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }
        if (this.state.isCreating) {
            return;
        }
        this.state.isCreating = true;
        try {
            const dimension = FOLDER_DIMENSIONS[folderName] || "ops";
            const values = {
                name: "Untitled",
                body_html: "<section><h2>Untitled</h2><p>Start writing here...</p></section>",
                workspace_dimension: dimension,
                active: true,
            };
            const [articleId] = await this.orm.create("kms.knowledge.article", [values]);
            await this.loadArticles();
            this.state.selectedId = articleId;
        } catch (error) {
            this.notification.add("Could not create article.", { type: "danger" });
            throw error;
        } finally {
            this.state.isCreating = false;
        }
    }

    openArticleForm(article) {
        if (!article?.id) {
            return;
        }
        if (article.is_locked) {
            this.notification.add("This article is locked. Unlock it before editing the form.", {
                type: "warning",
            });
            return;
        }
        this.closeMoreMenu();
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "kms.knowledge.article",
            res_id: article.id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("kms_knowledge.client_action", KmsKnowledgeApp);
