(function () {
    function appendMessage(thread, text, role, options = {}) {
        const message = document.createElement("div");
        message.className = `cityrise-ai-message cityrise-ai-message-${role}`;
        const paragraph = document.createElement("p");
        paragraph.textContent = text;
        message.appendChild(paragraph);

        if (options.sources && options.sources.length) {
            const meta = document.createElement("div");
            meta.className = "cityrise-ai-meta";
            meta.textContent = `Nguồn: ${options.sources.join(", ")}`;
            message.appendChild(meta);
        }

        if (options.suggestions && options.suggestions.length) {
            const suggestions = document.createElement("div");
            suggestions.className = "cityrise-ai-suggestions";
            options.suggestions.slice(0, 4).forEach((suggestion) => {
                const button = document.createElement("button");
                button.type = "button";
                button.textContent = suggestion;
                button.dataset.question = suggestion;
                suggestions.appendChild(button);
            });
            message.appendChild(suggestions);
        }

        thread.appendChild(message);
        thread.scrollTop = thread.scrollHeight;
        return message;
    }

    function bindPromptButtons(root, submitQuestion) {
        root.addEventListener("click", (event) => {
            const button = event.target.closest("[data-question]");
            if (!button) {
                return;
            }
            submitQuestion(button.dataset.question || button.textContent || "");
        });
    }

    function initCityRiseAI() {
        const root = document.querySelector(".cityrise-ai");
        if (!root || root.dataset.aiBound === "1") {
            return;
        }
        root.dataset.aiBound = "1";

        const form = root.querySelector(".cityrise-ai-form");
        const thread = root.querySelector(".cityrise-ai-thread");
        const questionInput = form && form.querySelector("[name='question']");
        const submitButton = form && form.querySelector("[type='submit']");
        const endpoint = root.dataset.endpoint || "/cityrise_ai/ask";
        if (!form || !thread || !questionInput || !submitButton) {
            return;
        }

        function fieldValue(selector) {
            const field = form.querySelector(selector);
            return field ? field.value : "";
        }

        async function submitQuestion(rawQuestion) {
            const question = (rawQuestion || questionInput.value || "").trim();
            if (!question || submitButton.disabled) {
                return;
            }

            appendMessage(thread, question, "user");
            questionInput.value = "";
            submitButton.disabled = true;
            submitButton.textContent = "Đang gửi";
            const waiting = appendMessage(thread, "Đang xử lý...", "bot");
            const payload = {
                question,
                visitor_name: fieldValue("[name='visitor_name']"),
                visitor_phone: fieldValue("[name='visitor_phone']"),
                visitor_email: fieldValue("[name='visitor_email']"),
            };

            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                waiting.querySelector("p").textContent = data.answer || "Mình chưa thể trả lời câu hỏi này.";
                if (data.sources && data.sources.length) {
                    const meta = document.createElement("div");
                    meta.className = "cityrise-ai-meta";
                    meta.textContent = `Nguồn: ${data.sources.join(", ")}`;
                    waiting.appendChild(meta);
                }
                if (data.suggestions && data.suggestions.length) {
                    const suggestions = document.createElement("div");
                    suggestions.className = "cityrise-ai-suggestions";
                    data.suggestions.slice(0, 4).forEach((suggestion) => {
                        const button = document.createElement("button");
                        button.type = "button";
                        button.textContent = suggestion;
                        button.dataset.question = suggestion;
                        suggestions.appendChild(button);
                    });
                    waiting.appendChild(suggestions);
                }
            } catch (error) {
                waiting.querySelector("p").textContent = "Kết nối đang gặp lỗi. Bạn vui lòng thử lại sau.";
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = "Gửi";
                thread.scrollTop = thread.scrollHeight;
            }
        }

        form.addEventListener("submit", (event) => {
            event.preventDefault();
            submitQuestion();
        });

        questionInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submitQuestion();
            }
        });

        bindPromptButtons(root, submitQuestion);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initCityRiseAI);
    } else {
        initCityRiseAI();
    }
})();
