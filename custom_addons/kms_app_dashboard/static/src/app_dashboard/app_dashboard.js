import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const SELF_XMLID = "kms_app_dashboard.menu_kms_app_dashboard_root";
const ICONS_BASE = "/kms_app_dashboard/static/src/app_dashboard/icons";
const DASHBOARD_APPS = [
    { key: "discuss", name: "Discuss", iconFile: "mail.svg" },
    { key: "calendar", name: "Calendar", iconFile: "calendar.svg" },
    { key: "appointments", name: "Appointments", aliases: ["Appointment"], iconFile: "appointment.svg" },
    { key: "to-do", name: "To-do", aliases: ["To-Do", "Todo", "To Do"], iconFile: "project_todo.svg" },
    { key: "knowledge", name: "Knowledge", iconFile: "knowledge.svg" },
    { key: "contacts", name: "Contacts", iconFile: "contacts.svg" },
    { key: "crm", name: "CRM", iconFile: "crm.svg" },
    { key: "sales", name: "Sales", iconFile: "sale.svg" },
    { key: "dashboards", name: "Dashboards", aliases: ["Dashboard"], iconFile: "board.svg" },
    { key: "ai", name: "AI", aliases: ["Odoo AI", "Artificial Intelligence"], iconFile: "ai_app.svg" },
    { key: "project", name: "Project", iconFile: "project.svg" },
    { key: "planning", name: "Planning", iconFile: "planning.svg" },
    { key: "helpdesk", name: "Helpdesk", iconFile: "helpdesk.svg" },
    { key: "website", name: "Website", iconFile: "website.svg" },
    { key: "purchase", name: "Purchase", iconFile: "purchase.svg" },
    { key: "inventory", name: "Inventory", iconFile: "stock.svg" },
    { key: "manufacturing", name: "Manufacturing", aliases: ["MRP"], iconFile: "mrp.svg" },
    { key: "shop-floor", name: "Shop Floor", aliases: ["Shopfloor"], iconFile: "mrp_workorder.svg" },
    { key: "barcode", name: "Barcode", aliases: ["Warehouse Management Barcode Scanning"], iconFile: "stock_barcode.svg" },
    { key: "sign", name: "Sign", iconFile: "sign.svg" },
    { key: "employees", name: "Employees", iconFile: "hr.svg" },
    { key: "time-off", name: "Time Off", iconFile: "hr_holidays.svg" },
    { key: "live-chat", name: "Live Chat", aliases: ["Livechat"], iconFile: "im_livechat.svg" },
    { key: "apps", name: "Apps", iconFile: "base.svg" },
    { key: "settings", name: "Settings", iconFile: "settings.png" },
];
const EXTRA_ICON_FILES = {
    "artificialintelligence": "ai_app.svg",
    "ai": "ai_app.svg",
    "invoicing": "account.svg",
    "accounting": "account.svg",
    "elearning": "website_slides.svg",
    "events": "website_event.svg",
    "recruitment": "hr_recruitment.svg",
    "shopfloor": "mrp_workorder.svg",
    "barcode": "stock_barcode.svg",
};
const FALLBACK_COLORS = [
    ["#22D3C5", "#0F172A"],
    ["#FB7185", "#1F1720"],
    ["#F59E0B", "#20170A"],
    ["#60A5FA", "#101827"],
    ["#A78BFA", "#171124"],
    ["#34D399", "#0D1F18"],
    ["#F472B6", "#22111B"],
    ["#F97316", "#21140A"],
];

export class KmsAppDashboard extends Component {
    static template = "kms_app_dashboard.AppDashboard";

    setup() {
        this.menuService = useService("menu");
        this.state = useState({
            isDrawerOpen: false,
            query: "",
        });
        onMounted(() => {
            document.body.classList.add("o_kms_dashboard_open");
            this.bindScrolling();
        });
        onWillUnmount(() => {
            document.body.classList.remove("o_kms_dashboard_open");
            this.unbindScrolling();
        });
    }

    get rawApps() {
        return this.menuService
            .getApps()
            .filter((app) => app.actionID && app.xmlid !== SELF_XMLID);
    }

    get apps() {
        const rawApps = this.rawApps;
        const usedMenuIds = new Set();
        const standardApps = DASHBOARD_APPS.map((spec, index) => {
            const menu = this.findAppMenu(spec, rawApps);
            if (menu) {
                usedMenuIds.add(menu.id);
                return this.buildRealApp(menu, spec.name, index, spec);
            }
            return this.buildPlaceholderApp(spec, index);
        });
        const extraApps = rawApps
            .filter((app) => !usedMenuIds.has(app.id))
            .sort((a, b) => (a.sequence || 0) - (b.sequence || 0))
            .map((app, index) => this.buildRealApp(app, app.name, DASHBOARD_APPS.length + index));

        return [...standardApps, ...extraApps];
    }

    get filteredApps() {
        const query = this.normalize(this.state.query);
        if (!query) {
            return this.apps;
        }
        return this.apps.filter((app) => this.normalize(app.name).includes(query));
    }

    get appCount() {
        return this.apps.length;
    }

    get hasQuery() {
        return Boolean(this.state.query.trim());
    }

    buildRealApp(menu, displayName, index, spec = null) {
        return {
            ...menu,
            name: displayName,
            menu,
            isAvailable: true,
            icon: this.getDashboardIcon(spec, menu, index),
            href: this.getAppHref(menu),
        };
    }

    buildPlaceholderApp(spec, index) {
        const appsMenu = this.findAppMenu({ name: "Apps" }, this.rawApps);
        return {
            id: `placeholder-${spec.key}`,
            name: spec.name,
            menu: null,
            isAvailable: false,
            fallbackMenu: appsMenu,
            href: appsMenu ? this.getAppHref(appsMenu) : "/odoo/apps",
            icon: spec.iconFile ? this.getStaticIcon(spec.iconFile) : this.getPlaceholderIcon(spec, index),
        };
    }

    findAppMenu(spec, apps) {
        const names = [spec.name, ...(spec.aliases || [])].map((name) => this.normalizeKey(name));
        return apps.find((app) => names.includes(this.normalizeKey(app.name)));
    }

    normalize(value) {
        return String(value || "")
            .trim()
            .toLowerCase();
    }

    normalizeKey(value) {
        return this.normalize(value).replace(/[\s_-]+/g, "");
    }

    bindKeyboard() {
        if (this._keyboardHandler) {
            return;
        }
        this._keyboardHandler = (ev) => {
            const target = ev.target;
            const isTyping = Boolean(
                target &&
                    (["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) ||
                        target.isContentEditable)
            );
            if (isTyping) {
                return;
            }
            if (ev.key === "Escape") {
                this.clearSearch();
                this.state.isDrawerOpen = false;
                return;
            }
            if (ev.key === "/" || /^[a-zA-Z0-9]$/.test(ev.key)) {
                ev.preventDefault();
                this.state.isDrawerOpen = true;
                if (ev.key !== "/") {
                    this.state.query = `${this.state.query}${ev.key}`;
                }
                setTimeout(() => this.focusSearch(), 0);
            }
        };
        document.addEventListener("keydown", this._keyboardHandler);
    }

    unbindKeyboard() {
        if (!this._keyboardHandler) {
            return;
        }
        document.removeEventListener("keydown", this._keyboardHandler);
        this._keyboardHandler = null;
    }

    bindScrolling() {
        if (this._wheelHandler) {
            return;
        }
        this._wheelHandler = (ev) => {
            if (ev.ctrlKey || this.shouldLetNativeScroll(ev.target)) {
                return;
            }
            const container = this.getScrollContainer();
            if (!container) {
                return;
            }
            const before = container.scrollTop;
            container.scrollTop += ev.deltaY;
            if (container.scrollTop !== before) {
                ev.preventDefault();
            }
        };
        this._touchStartHandler = (ev) => {
            if (this.shouldLetNativeScroll(ev.target)) {
                this._lastTouchY = null;
                return;
            }
            this._lastTouchY = ev.touches?.[0]?.clientY ?? null;
        };
        this._touchMoveHandler = (ev) => {
            if (this._lastTouchY === null || this.shouldLetNativeScroll(ev.target)) {
                return;
            }
            const currentY = ev.touches?.[0]?.clientY;
            if (currentY === undefined) {
                return;
            }
            const container = this.getScrollContainer();
            if (!container) {
                return;
            }
            const before = container.scrollTop;
            container.scrollTop += this._lastTouchY - currentY;
            this._lastTouchY = currentY;
            if (container.scrollTop !== before) {
                ev.preventDefault();
            }
        };
        document.addEventListener("wheel", this._wheelHandler, { capture: true, passive: false });
        document.addEventListener("touchstart", this._touchStartHandler, { capture: true, passive: true });
        document.addEventListener("touchmove", this._touchMoveHandler, { capture: true, passive: false });
    }

    unbindScrolling() {
        if (this._wheelHandler) {
            document.removeEventListener("wheel", this._wheelHandler, { capture: true });
            this._wheelHandler = null;
        }
        if (this._touchStartHandler) {
            document.removeEventListener("touchstart", this._touchStartHandler, { capture: true });
            this._touchStartHandler = null;
        }
        if (this._touchMoveHandler) {
            document.removeEventListener("touchmove", this._touchMoveHandler, { capture: true });
            this._touchMoveHandler = null;
        }
        this._lastTouchY = null;
    }

    shouldLetNativeScroll(target) {
        return Boolean(
            target?.closest?.(
                ".kms_app_dashboard__drawer, .o_menu_systray, .dropdown-menu, .modal, input, textarea, select"
            )
        );
    }

    getScrollContainer() {
        const dashboard = document.querySelector(".kms_app_dashboard");
        const candidates = [
            dashboard,
            dashboard?.closest(".o_content"),
            dashboard?.closest(".o_action"),
            document.scrollingElement,
        ];
        return candidates.find((candidate) => this.canScroll(candidate)) || dashboard || document.scrollingElement;
    }

    canScroll(element) {
        if (!element) {
            return false;
        }
        return element.scrollHeight - element.clientHeight > 1;
    }

    getAppHref(app) {
        return `/odoo/${app.actionPath || `action-${app.actionID}`}`;
    }

    getIcon(app, index) {
        if (app.webIconData) {
            return {
                type: "image",
                src: app.webIconData,
            };
        }
        const parts = (app.webIcon || "").split(",");
        if (parts.length === 3) {
            return {
                type: "font",
                iconClass: parts[0] || "fa fa-cube",
                color: parts[1] || "#FFFFFF",
                backgroundColor: parts[2] || "#24313F",
            };
        }
        const [color, backgroundColor] = FALLBACK_COLORS[index % FALLBACK_COLORS.length];
        return {
            type: "initial",
            label: (app.name || "?").trim().slice(0, 1).toUpperCase(),
            color,
            backgroundColor,
        };
    }

    getDashboardIcon(spec, menu, index) {
        if (spec?.iconFile) {
            return this.getStaticIcon(spec.iconFile);
        }
        const iconFile = EXTRA_ICON_FILES[this.normalizeKey(menu.name)];
        return iconFile ? this.getStaticIcon(iconFile) : this.getIcon(menu, index);
    }

    getStaticIcon(fileName) {
        return {
            type: "image",
            src: `${ICONS_BASE}/${fileName}`,
        };
    }

    getPlaceholderIcon(spec, index) {
        const [color, backgroundColor] = FALLBACK_COLORS[index % FALLBACK_COLORS.length];
        return {
            type: "tile",
            className: `kms_app_dashboard__tile_icon--${spec.key}`,
            color,
            backgroundColor,
            symbol: spec.name.slice(0, 2).toUpperCase(),
        };
    }

    async openApp(app) {
        this.state.isDrawerOpen = false;
        const menu = app.menu || app.fallbackMenu;
        if (menu) {
            await this.menuService.selectMenu(menu);
            return;
        }
        window.location.href = app.href;
    }

    toggleDrawer() {
        this.state.isDrawerOpen = !this.state.isDrawerOpen;
        if (this.state.isDrawerOpen) {
            setTimeout(() => this.focusSearch(), 0);
        }
    }

    focusSearch() {
        document.querySelector(".kms_app_dashboard__search_input")?.focus();
    }

    onSearchInput(ev) {
        this.state.query = ev.target.value;
    }

    clearSearch() {
        this.state.query = "";
    }
}

registry.category("actions").add("kms_app_dashboard.client_action", KmsAppDashboard);
