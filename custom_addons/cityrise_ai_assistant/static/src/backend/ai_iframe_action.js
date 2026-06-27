import { Component, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

export class CityRiseAIIframeAction extends Component {
    static template = "cityrise_ai_assistant.IframeAction";
}

registry.category("actions").add("cityrise_ai_assistant.iframe_action", CityRiseAIIframeAction);

export class CityRiseAISystray extends Component {
    static template = "cityrise_ai_assistant.Systray";
    static props = ["*"];

    setup() {
        this.threadRef = useRef("thread");
        this.state = useState({
            open: false,
            minimized: false,
            busy: false,
            input: "",
            messages: [],
        });
    }

    get audienceLabel() {
        return user.isAdmin || user.isSystem ? "Admin/Manager" : "Employee/Internal";
    }

    get promptChips() {
        return [
            "Latest PO from supplier Azure interior",
            "Doanh thu hien tai cua cong ty la bao nhieu?",
            "Purchase order P00030",
        ];
    }

    openAssistant() {
        this.state.open = true;
        this.state.minimized = false;
        if (!this.state.messages.length) {
            this.state.messages.push({
                id: "welcome",
                role: "bot",
                answer: "Hello, what can I help you with?",
                sources: [],
                suggestions: this.promptChips,
            });
        }
        this.scrollThreadSoon();
    }

    toggleAssistant() {
        if (this.state.open) {
            this.state.minimized = !this.state.minimized;
        } else {
            this.openAssistant();
        }
    }

    closeAssistant() {
        this.state.open = false;
        this.state.minimized = false;
    }

    minimizeAssistant() {
        this.state.minimized = true;
    }

    onInput(ev) {
        this.state.input = ev.target.value;
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    askPrompt(question) {
        this.state.input = question;
        this.sendMessage(question);
    }

    async sendMessage(rawQuestion = null) {
        const question = (rawQuestion || this.state.input || "").trim();
        if (!question || this.state.busy) {
            return;
        }

        this.state.messages.push({
            id: `${Date.now()}-user`,
            role: "user",
            answer: question,
            sources: [],
            suggestions: [],
        });
        this.state.input = "";
        this.state.busy = true;

        const waiting = {
            id: `${Date.now()}-bot`,
            role: "bot",
            answer: "Dang xu ly...",
            sources: [],
            suggestions: [],
            warning: "",
        };
        this.state.messages.push(waiting);
        this.scrollThreadSoon();

        try {
            const response = await fetch("/cityrise_ai/ask_internal", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question }),
            });
            const data = await response.json();
            waiting.answer = data.answer || "Minh chua the tra loi cau hoi nay.";
            waiting.sources = data.sources || [];
            waiting.suggestions = data.suggestions || [];
            waiting.warning = data.warning || "";
        } catch (error) {
            waiting.answer = "Ket noi AI dang gap loi. Ban vui long thu lai sau.";
            waiting.sources = ["CityRise AI backend"];
            waiting.suggestions = [];
            waiting.warning = "request_failed";
        } finally {
            this.state.busy = false;
            this.scrollThreadSoon();
        }
    }

    scrollThreadSoon() {
        window.setTimeout(() => {
            const thread = this.threadRef.el;
            if (thread) {
                thread.scrollTop = thread.scrollHeight;
            }
        }, 0);
    }
}

registry.category("systray").add(
    "cityrise_ai_assistant.internal_systray",
    {
        Component: CityRiseAISystray,
        isDisplayed: () => user.isInternalUser,
    },
    { sequence: 35 }
);
