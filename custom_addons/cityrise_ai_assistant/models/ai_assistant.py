"""Giai thich file phan tich hop CityRise AI.

File nay la engine tra loi cua module cityrise_ai_assistant trong Odoo.
No nhan cau hoi tu website/controller, phan loai nguoi hoi la public customer
hay internal operator, sau do tra loi theo dung phan quyen.

Phan Week 11 duoc tich hop qua _answer_from_vector: engine goi ChromaDB thong
qua CityRiseVectorStore. Khach hang chi nhan cau tra loi tu chunk public va bi
chan khi hoi sau ve database/vector/ticket/order/login. Nhan vien/admin duoc
search nhanh tren vector noi bo gom knowledge, sales, purchase, helpdesk va
nhan vien.
"""

import re
import unicodedata
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher

from odoo import api, fields, models
from odoo.tools import html2plaintext

from .vector_store import CityRiseVectorStore, compact_text


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,5}\d{2,4}")
STOP_WORDS = {
    "anh", "chi", "ban", "toi", "minh", "cho", "hoi", "can", "muon", "ve", "la", "co",
    "khong", "bao", "nhieu", "gia", "san", "pham", "can", "ho", "cityrise", "shop",
}

RAG_SYSTEM_PROMPT = """You are CityRise RAG Assistant inside Odoo.

Rules:
- Answer only from the retrieved CityRise/Odoo context below.
- Do not invent orders, tickets, employee data, prices, policies, or database facts.
- If the context is not enough, say the retrieved data is insufficient.
- Public/customer users may only receive surface-level public information.
- Internal users may receive internal chunks that passed the metadata access filter.
- Answer in Vietnamese and include a short "Nguon:" line with source titles.

Audience: {audience}

Retrieved context:
{context}

Question:
{question}
"""

GENERAL_CHAT_PROMPT = """You are CityRise AI inside Odoo, but the user is asking a general question outside CityRise.

Answer rules:
- Answer in Vietnamese.
- Keep the answer shallow and helpful: maximum 4 short sentences or 4 bullets, under 120 words.
- Do not provide deep step-by-step instructions, professional legal/medical/financial advice, or unsafe guidance.
- Do not claim access to live internet, weather, news, prices, exchange rates, or sports scores.
- If the question needs live/current data, say you cannot verify live data and suggest checking a reliable live source.
- Do not expose or mention CityRise internal database, vector metadata, employees, orders, tickets, or private data.

Question:
{question}
"""


class CityRiseAIConversation(models.Model):
    _name = "cityrise.ai.conversation"
    _description = "CityRise AI Conversation"
    _order = "create_date desc, id desc"

    question = fields.Text(required=True)
    answer = fields.Text()
    audience = fields.Selection(
        [("public", "Public Customer"), ("internal", "Internal Operator")],
        required=True,
        default="public",
    )
    confidence = fields.Selection(
        [("high", "High"), ("medium", "Medium"), ("low", "Low"), ("lead", "Lead Created")],
        default="high",
    )
    intent = fields.Char()
    source_summary = fields.Char()
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    partner_id = fields.Many2one("res.partner")
    contact_name = fields.Char()
    contact_email = fields.Char()
    contact_phone = fields.Char()
    lead_id = fields.Many2one("crm.lead", readonly=True)


class CityRiseAIEngine(models.AbstractModel):
    _name = "cityrise.ai.engine"
    _description = "CityRise AI Guarded Answer Engine"

    @api.model
    def ask(self, question, visitor_name=None, visitor_email=None, visitor_phone=None):
        question = (question or "").strip()
        is_internal = False if self.env.context.get("cityrise_force_public") else self._is_internal_user(self.env.user)
        is_manager = is_internal and self._is_manager_user(self.env.user)
        contact = self._extract_contact(question, visitor_name, visitor_email, visitor_phone)
        if not question:
            return self._result(
                "Bạn muốn hỏi CityRise về sản phẩm, công ty, hỗ trợ khách hàng hay cần nhân viên tư vấn?",
                "low",
                is_internal,
                question,
                contact,
                intent="empty",
                suggestions=self._suggestions(is_internal),
            )

        intent = self._detect_intent(question)
        if self._is_public_privacy_request(question) and not is_internal:
            return self._result(
                self._public_privacy_answer(question),
                "high",
                is_internal,
                question,
                contact,
                intent="privacy_guard",
                sources=["Quy tắc phân quyền CityRise"],
                suggestions=["Tôi muốn tư vấn căn hộ 90x", "Danh sách sản phẩm đang bán"],
            )

        if is_internal and self._is_admin_only_question(question):
            if not is_manager:
                return self._result(
                    self._employee_restricted_answer(question),
                    "high",
                    is_internal,
                    question,
                    contact,
                    intent="access_denied",
                    sources=["access_matrix.md", "Odoo role check"],
                    suggestions=["Hoi thong tin san pham", "Purchase order P00030", "Thong tin helpdesk"],
                )
            answer, sources, suggestions, confidence = self._answer_admin_only_question(question)
            return self._result(
                answer,
                confidence,
                is_internal,
                question,
                contact,
                intent="admin_live_data",
                sources=sources,
                suggestions=suggestions,
            )

        if self._wants_human(question):
            return self._lead_or_contact_request(question, contact, is_internal, intent="lead_request")

        vector_response = self._answer_from_vector(question, is_internal, intent)
        if vector_response:
            answer, sources, suggestions, confidence = vector_response
            return self._result(
                answer,
                confidence,
                is_internal,
                question,
                contact,
                intent=intent,
                sources=sources,
                suggestions=suggestions,
            )

        handlers = {
            "knowledge": lambda: self._answer_knowledge(question, is_internal),
            "database": lambda: self._answer_database_overview(is_internal),
            "staff": lambda: self._answer_staff(question, is_internal),
            "business": lambda: self._answer_internal_business(question, is_internal),
            "helpdesk": lambda: self._answer_helpdesk(is_internal),
            "product": lambda: self._answer_products(question),
            "company": lambda: self._answer_company(is_internal),
            "website": lambda: self._answer_website_content(question),
            "general": lambda: self._answer_general(question, is_internal),
        }
        answer, sources, suggestions, confidence = handlers.get(intent, handlers["product"])()
        if answer:
            return self._result(
                answer,
                confidence,
                is_internal,
                question,
                contact,
                intent=intent,
                sources=sources,
                suggestions=suggestions,
            )

        return self._lead_or_contact_request(question, contact, is_internal, intent="fallback")

    def _result(
        self,
        answer,
        confidence,
        is_internal,
        question,
        contact=None,
        lead=False,
        intent=False,
        sources=None,
        suggestions=None,
    ):
        contact = contact or {}
        sources = sources or []
        suggestions = suggestions or self._suggestions(is_internal)
        role = self._role_label(is_internal)
        if not is_internal:
            answer = self._sanitize_public_answer(answer)
        values = {
            "question": question or "",
            "answer": answer,
            "audience": "internal" if is_internal else "public",
            "confidence": "lead" if lead else confidence,
            "intent": intent,
            "source_summary": ", ".join(sources[:4]),
            "user_id": self.env.user.id,
            "partner_id": self.env.user.partner_id.id if self.env.user.partner_id else False,
            "contact_name": contact.get("name"),
            "contact_email": contact.get("email"),
            "contact_phone": contact.get("phone"),
        }
        conversation = self.env["cityrise.ai.conversation"].sudo().create(values)
        return {
            "answer": answer,
            "confidence": values["confidence"],
            "audience": values["audience"],
            "role": role,
            "intent": intent,
            "sources": sources,
            "suggestions": suggestions,
            "conversation_id": conversation.id,
            "need_contact": confidence == "low" and not lead,
            "lead_id": False,
        }

    def _lead_or_contact_request(self, question, contact, is_internal, intent="fallback"):
        if contact.get("email") or contact.get("phone"):
            lead = self._create_lead(question, contact)
            answer = (
                "Mình đã ghi nhận yêu cầu của bạn cho đội ngũ CityRise. "
                "Một nhân viên sẽ dùng thông tin bạn cung cấp để liên hệ tư vấn."
            )
            response = self._result(
                answer,
                "lead",
                is_internal,
                question,
                contact,
                lead=True,
                intent=intent,
                sources=["CRM Lead"],
                suggestions=["Xem căn hộ rẻ nhất", "Danh sách căn hộ cao cấp"],
            )
            conversation = self.env["cityrise.ai.conversation"].sudo().browse(response["conversation_id"])
            conversation.lead_id = lead.id
            response["lead_id"] = lead.id
            response["need_contact"] = False
            return response
        answer = (
            "Mình chưa có đủ dữ liệu để trả lời chắc chắn. "
            "Bạn có thể để lại tên và số điện thoại hoặc email để CityRise tư vấn trực tiếp."
        )
        return self._result(
            answer,
            "low",
            is_internal,
            question,
            contact,
            intent=intent,
            sources=["CRM Lead"],
            suggestions=["Tư vấn căn hộ r12, số điện thoại 0909123456", "Danh sách sản phẩm đang bán"],
        )

    def _create_lead(self, question, contact):
        name = contact.get("name") or self.env.user.name or "Website Visitor"
        return self.env["crm.lead"].sudo().create({
            "name": "AI Assistant - Customer request",
            "contact_name": name,
            "email_from": contact.get("email"),
            "phone": contact.get("phone"),
            "type": "lead",
            "description": "Created by CityRise AI Assistant.\n\nQuestion:\n%s\n" % question,
        })

    def _detect_intent(self, question):
        q = self._norm(question)
        if self._wants_human(question):
            return "lead_request"
        if self._is_out_of_scope_question(question):
            return "general"
        if any(word in q for word in ["database", "du lieu", "bang nao", "he thong co gi", "tong quan"]):
            return "database"
        if self._is_knowledge_question(question):
            return "knowledge"
        if self._is_internal_business_question(question):
            return "business"
        if self._is_helpdesk_question(question):
            return "helpdesk"
        if self._is_staff_question(question):
            return "staff"
        if self._is_product_question(question):
            return "product"
        if any(word in q for word in ["trang web", "website", "lien he", "appointment", "dat lich", "help"]):
            return "website"
        if self._is_company_question(question):
            return "company"
        return "general"

    def _extract_contact(self, question, visitor_name, visitor_email, visitor_phone):
        email = (visitor_email or "").strip()
        phone = (visitor_phone or "").strip()
        name = (visitor_name or "").strip()
        if not email:
            match = EMAIL_RE.search(question or "")
            email = match.group(0) if match else ""
        if not phone:
            matches = [m.group(0).strip() for m in PHONE_RE.finditer(question or "")]
            phone = next((m for m in matches if len(re.sub(r"\D", "", m)) >= 8), "")
        return {"name": name, "email": email, "phone": phone}

    def _is_internal_user(self, user):
        return bool(not user._is_public() and user.has_group("base.group_user"))

    def _has_any_group(self, user, xmlids):
        for xmlid in xmlids:
            try:
                if user.has_group(xmlid):
                    return True
            except Exception:
                continue
        return False

    def _is_manager_user(self, user):
        return self._has_any_group(user, [
            "base.group_system",
            "base.group_erp_manager",
            "sales_team.group_sale_manager",
            "purchase.group_purchase_manager",
            "hr.group_hr_manager",
        ])

    def _role_label(self, is_internal):
        if not is_internal:
            return "public"
        return "admin" if self._is_manager_user(self.env.user) else "employee"

    def _norm(self, text):
        text = (text or "").lower()
        text = text.replace("đ", "d").replace("Đ", "d")
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", text).strip()

    def _tokens(self, text):
        return [token for token in re.findall(r"[a-z0-9]+", self._norm(text)) if token not in STOP_WORDS]

    def _plain(self, html):
        return html2plaintext(html or "").strip()

    def _money(self, amount):
        return f"{amount:,.0f} đ"

    def _sanitize_public_answer(self, answer):
        answer = EMAIL_RE.sub("[email đã ẩn]", answer or "")
        return PHONE_RE.sub("[số điện thoại đã ẩn]", answer)

    def _suggestions(self, is_internal):
        public = [
            "Danh sách sản phẩm đang bán",
            "Căn hộ rẻ nhất là gì?",
            "Căn hộ 90x giá bao nhiêu?",
            "Tôi cần tư vấn căn hộ r12",
        ]
        if not is_internal:
            return public
        return public + [
            "Tổng quan database",
            "Tình hình helpdesk",
            "Thông tin nhân viên",
            "Tổng sales và purchase",
            "Tìm ticket urgent trong vector",
            "Purchase order P00030",
            "SOP onboarding nhân viên IT",
        ]

    def _answer_from_vector(self, question, is_internal, intent):
        public_vector_intents = {"knowledge"}
        internal_vector_intents = {"knowledge", "business", "helpdesk", "staff", "database"}
        if is_internal:
            allowed = intent in internal_vector_intents
        else:
            allowed = intent in public_vector_intents and not self._is_public_deep_vector_probe(question)
        if not allowed:
            return False
        if is_internal and self._should_use_orm_overview(question, intent):
            return False
        if is_internal and intent == "business" and self._extract_business_code(question):
            return False
        if is_internal and intent == "staff" and self._find_employee_from_question(question):
            return False

        vector_query = question
        if is_internal and intent == "database":
            vector_query = question + " knowledge sales purchase helpdesk employee product"
        docs, info = CityRiseVectorStore.search(vector_query, is_internal=is_internal, k=5 if is_internal else 3)
        if not docs:
            return False

        sources = self._vector_sources(docs, info)
        if is_internal:
            answer = self._format_rag_vector_answer(question, docs, info, is_internal=True)
            if not answer:
                answer = self._format_internal_vector_answer(docs, info)
            return answer, sources, self._suggestions(True), "high"

        answer = self._format_public_vector_answer(docs)
        return answer, sources, self._suggestions(False), "high"

    def _should_use_orm_overview(self, question, intent):
        q = self._norm(question)
        overview_words = ["tong", "tong quan", "tinh hinh", "bao cao", "overview", "summary"]
        wants_overview = any(word in q for word in overview_words)
        if intent == "database" and wants_overview:
            return True
        if intent == "business" and wants_overview:
            return True
        if intent == "helpdesk" and wants_overview and "ticket" not in q:
            return True
        return False

    def _vector_sources(self, docs, info):
        sources = []
        if info.get("status") == "ok":
            sources.append("ChromaDB:%s" % info.get("collection", "kms_collection"))
        for doc in docs[:4]:
            metadata = doc.metadata or {}
            title = metadata.get("title") or "Untitled"
            model = metadata.get("source_model") or "vector"
            sources.append("%s:%s" % (model, title))
        return sources

    def _format_rag_vector_answer(self, question, docs, info, is_internal):
        if not CityRiseVectorStore.odoo_use_llm():
            return False
        if CityRiseVectorStore.rag_provider() not in ("ollama", "auto"):
            return False
        context = self._rag_context(docs)
        if not context:
            return False
        prompt = RAG_SYSTEM_PROMPT.format(
            audience="internal" if is_internal else "public",
            context=context,
            question=question,
        )
        answer, llm_info = CityRiseVectorStore.ollama_generate(prompt)
        if not answer:
            fallback = self._format_internal_vector_answer(docs, info) if is_internal else self._format_public_vector_answer(docs)
            return (
                fallback
                + "\n\n[Lưu ý] Ollama chưa trả lời được, hệ thống đã dùng fallback từ Vector DB. "
                + llm_info.get("error", "")
            )
        source_titles = self._source_titles(docs)
        if source_titles and "nguon" not in answer.lower() and "source" not in answer.lower():
            answer += "\nNguon: " + ", ".join(source_titles[:4])
        return answer

    def _rag_context(self, docs, max_chars=4000):
        parts = []
        used = 0
        for index, doc in enumerate(docs[:5], start=1):
            metadata = doc.metadata or {}
            block = (
                "[%s] title=%s; role=%s; workspace=%s; source=%s:%s\n%s"
                % (
                    index,
                    metadata.get("title") or "Untitled",
                    metadata.get("access_role") or "unknown",
                    metadata.get("workspace_dimension") or "unknown",
                    metadata.get("source_model") or "vector",
                    metadata.get("source_id") or "",
                    compact_text(doc.page_content, 900),
                )
            )
            if used + len(block) > max_chars:
                break
            parts.append(block)
            used += len(block)
        return "\n\n".join(parts)

    def _source_titles(self, docs):
        titles = []
        for doc in docs:
            title = (doc.metadata or {}).get("title")
            if title and title not in titles:
                titles.append(title)
        return titles

    def _format_internal_vector_answer(self, docs, info):
        lines = []
        for doc in docs[:5]:
            metadata = doc.metadata or {}
            title = metadata.get("title") or "Untitled"
            source_model = metadata.get("source_model") or "vector"
            role = metadata.get("access_role") or "unknown"
            snippet = compact_text(doc.page_content, 260)
            lines.append(f"- {title} ({source_model}, role={role}): {snippet}")
        elapsed = info.get("elapsed")
        suffix = ""
        if elapsed is not None:
            suffix = f"\nThời gian tìm vector: {elapsed:.2f}s."
        return "Mình tìm trong vector database CityRise và thấy:\n" + "\n".join(lines) + suffix

    def _format_public_vector_answer(self, docs):
        lines = []
        for doc in docs[:3]:
            metadata = doc.metadata or {}
            title = metadata.get("title") or "CityRise public info"
            snippet = compact_text(doc.page_content, 180)
            lines.append(f"- {title}: {snippet}")
        return (
            "Ở mức thông tin công khai, mình có thể chia sẻ:\n"
            + "\n".join(lines)
            + "\nCác chi tiết nội bộ như đơn hàng, ticket, login, email cá nhân hoặc dữ liệu vector bảo mật sẽ không được hiển thị cho khách hàng."
        )

    def _answer_knowledge(self, question, is_internal):
        if not is_internal and self._is_public_deep_vector_probe(question):
            return self._public_privacy_answer(question), ["Quy tắc phân quyền CityRise"], self._suggestions(False), "high"
        return (
            "Mình chưa tìm thấy bài knowledge phù hợp trong vector database. Bạn có thể hỏi rõ hơn theo tên SOP, policy hoặc quy trình cần tra cứu.",
            ["ChromaDB:kms_collection"],
            self._suggestions(is_internal),
            "medium",
        )

    def _is_product_question(self, question):
        q = self._norm(question)
        keywords = [
            "san pham", "product", "shop", "can ho", "gia", "bao nhieu", "bao gia",
            "biet thu", "nha", "mua", "danh sach", "re nhat", "dat nhat", "duoi",
            "tren", "ty", "cao cap", "so sanh",
        ]
        product_names = [self._norm(name) for name in self._product_records().mapped("name")]
        product_names = [name for name in product_names if name]
        return any(word in q for word in keywords) or any(name in q for name in product_names)

    def _is_company_question(self, question):
        q = self._norm(question)
        return any(word in q for word in ["cong ty", "cityrise", "dia chi", "lien he", "gioi thieu"])

    def _is_staff_question(self, question):
        q = self._norm(question)
        if any(word in q for word in [
            "nhan vien", "nguoi lam", "salesperson", "sale", "buyer", "van hanh",
            "nhan su", "thong tin nhan vien", "noi bo", "truong", "hoa", "minh",
            "anh tu", "pham anh tu", "admin", "administrator",
        ]):
            return True
        if "hr.employee" in self.env:
            raw_question = (question or "").lower()
            for employee in self.env["hr.employee"].sudo().search([], limit=120):
                employee_name = self._norm(employee.name)
                if employee_name and employee_name in q:
                    return True
                employee_email = (employee.work_email or "").lower()
                if employee_email and employee_email in raw_question:
                    return True
        return False

    def _is_helpdesk_question(self, question):
        q = self._norm(question)
        return any(word in q for word in ["helpdesk", "ho tro", "ticket", "khieu nai", "bao loi", "cham soc", "sla"])

    def _is_knowledge_question(self, question):
        q = self._norm(question)
        return any(word in q for word in [
            "knowledge", "kms", "sop", "policy", "protocol", "quy trinh", "huong dan",
            "onboarding", "welcome", "developer", "firewall", "hardware", "disciplinary",
            "ky luat", "nhan vien moi", "bao mat", "thiet bi",
        ])

    def _is_internal_business_question(self, question):
        q = self._norm(question)
        return any(word in q for word in [
            "don hang", "sales order", "purchase", "mua hang", "bao gia", "rfq",
            "doanh thu", "nha cung cap", "tong tien", "quotation",
        ])

    def _wants_human(self, question):
        q = self._norm(question)
        return any(word in q for word in [
            "goi lai", "tu van", "lien he toi", "contact me", "nhan vien goi",
            "gap nhan vien", "dat lich", "hen lich", "xem nha",
        ])

    def _is_out_of_scope_question(self, question):
        q = self._norm(question)
        out_of_scope_keywords = [
            "thoi tiet", "nhiet do", "du bao", "troi mua", "troi nang", "hom nay mua khong",
            "tin tuc", "thoi su", "bong da", "lich thi dau", "ket qua tran", "xem phim",
            "nau an", "mon an", "cong thuc", "gia vang", "bitcoin", "crypto", "chung khoan",
            "ty gia", "usd", "xang dau", "xsst", "xo so", "ket qua xo so",
            "ai la tong thong", "thu do", "lich su", "vat ly", "hoa hoc", "toan hoc",
        ]
        return any(keyword in q for keyword in out_of_scope_keywords)

    def _out_of_scope_answer(self):
        return (
            "Tôi không biết. Mình chỉ trả lời các câu hỏi liên quan đến dữ liệu CityRise/Odoo "
            "trong hệ thống này, ví dụ: sản phẩm trên shop, giá căn hộ, website, liên hệ, "
            "helpdesk hoặc dữ liệu nội bộ được phân quyền."
        )

    def _answer_general(self, question, is_internal):
        prompt = GENERAL_CHAT_PROMPT.format(question=question)
        answer = ""
        if CityRiseVectorStore.rag_provider() in ("ollama", "auto"):
            answer, _info = CityRiseVectorStore.ollama_generate(prompt, temperature=0.2, timeout=12)
            answer = self._compact_general_answer(answer)
            if self._is_low_quality_general_answer(answer):
                answer = ""
        if not answer:
            answer = self._general_fallback_answer(question)
        suffix = (
            "\n\nLưu ý: Đây là câu trả lời thông tin chung, không dùng dữ liệu nội bộ CityRise "
            "và không thay thế nguồn chuyên môn hoặc dữ liệu thời gian thực."
        )
        return answer + suffix, ["General chat guard"], self._general_suggestions(is_internal), "medium"

    def _compact_general_answer(self, answer):
        value = re.sub(r"\n{3,}", "\n\n", (answer or "").strip())
        value = re.sub(r"[ \t]+", " ", value)
        if not value:
            return ""
        words = value.split()
        if len(words) > 120:
            value = " ".join(words[:120]).rstrip(".,;:") + "..."
        if len(value) > 850:
            value = value[:847].rstrip(".,;: ") + "..."
        return value

    def _is_low_quality_general_answer(self, answer):
        normalized = self._norm(answer)
        refusal_markers = [
            "khong the giup",
            "khong the tra loi",
            "toi khong the",
            "i cannot",
            "i can't",
            "cannot answer",
            "khong co thong tin",
            "ban can tro giup gi khac",
        ]
        return any(marker in normalized for marker in refusal_markers)

    def _general_suggestions(self, is_internal):
        suggestions = ["Hỏi ngắn gọn tiếp", "Quay lại sản phẩm CityRise", "Tôi cần tư vấn căn hộ"]
        if is_internal:
            suggestions.append("Tổng quan database")
        return suggestions

    def _general_fallback_answer(self, question):
        q = self._norm(question)
        if any(word in q for word in ["thoi tiet", "nhiet do", "du bao", "troi mua", "troi nang"]):
            return (
                "Mình không có dữ liệu thời tiết trực tiếp. Bạn nên xem ứng dụng thời tiết hoặc Google Weather "
                "theo vị trí hiện tại. Nếu cần chuẩn bị chung: kiểm tra mưa, nhiệt độ và thời gian di chuyển trước khi ra ngoài."
            )
        if any(word in q for word in ["tin tuc", "thoi su", "gia vang", "bitcoin", "crypto", "chung khoan", "ty gia", "xang dau", "bong da", "lich thi dau"]):
            return (
                "Mình không xác minh được dữ liệu thời gian thực trong câu hỏi này. Bạn nên kiểm tra nguồn cập nhật trực tiếp "
                "như trang tin chính thống, sàn giao dịch hoặc ứng dụng thể thao/tài chính."
            )
        if any(word in q for word in ["nau an", "nau mon", "mon an", "mon gi", "cong thuc", "an gi", "hom nay an"]):
            return (
                "Gợi ý nhanh: chọn món theo nguyên liệu đang có, ưu tiên món dễ làm và đủ tinh bột, đạm, rau. "
                "Nếu bạn đưa nguyên liệu cụ thể, mình có thể gợi ý 1-2 món đơn giản."
            )
        if any(word in q for word in ["suc khoe", "dau", "benh", "thuoc", "trieu chung"]):
            return (
                "Mình chỉ có thể góp ý ở mức chung: nghỉ ngơi, uống đủ nước và theo dõi triệu chứng. "
                "Nếu đau nhiều, kéo dài, sốt cao hoặc khó thở, bạn nên liên hệ bác sĩ."
            )
        if any(word in q for word in ["tinh yeu", "doi song", "stress", "buon", "lo lang", "hoc tap"]):
            return (
                "Gợi ý nhẹ: nhìn vấn đề thành vài việc nhỏ, chọn một bước dễ làm nhất trước, "
                "rồi nói chuyện với người bạn tin tưởng nếu thấy quá tải."
            )
        return (
            "Mình có thể trả lời ngắn ở mức thông tin chung, nhưng sẽ không đi quá sâu ngoài phạm vi CityRise. "
            "Bạn có thể hỏi lại cụ thể hơn để mình tóm tắt ngắn gọn."
        )

    def _is_public_privacy_request(self, question):
        q = self._norm(question)
        wants_contact = any(word in q for word in ["so dien thoai", "sdt", "phone", "email", "mail", "login"])
        wants_person = self._is_staff_question(question)
        wants_internal = any(word in q for word in [
            "luong", "mat khau", "password", "noi bo", "don hang", "purchase",
            "doanh thu", "database", "vector", "chroma", "rfq", "bao cao",
            "ticket", "sla", "ma ticket", "du lieu khach hang", "customer email",
        ])
        return (wants_contact and wants_person) or wants_internal

    def _is_admin_only_question(self, question):
        q = self._norm(question)
        salary_words = ["salary", "luong", "wage", "payroll"]
        executive_words = ["ceo", "giam doc", "tong giam doc", "ban giam doc"]
        revenue_words = ["gross revenue", "revenue", "doanh thu", "loi nhuan", "profit"]
        company_scope = ["company", "cong ty", "cityrise", "month", "thang", "this month", "thang nay"]
        asks_salary = any(word in q for word in salary_words) and (
            any(word in q for word in executive_words) or "nhan vien" in q
        )
        asks_revenue = any(word in q for word in revenue_words) and any(word in q for word in company_scope)
        return asks_salary or asks_revenue

    def _employee_restricted_answer(self, question):
        return (
            "Ban dang o quyen Employee nen khong duoc xem cau hoi nay theo access_matrix.md. "
            "Du lieu cap quan tri nhu gross revenue, profit, payroll/luong CEO va bao cao tai chinh chi danh cho Admin/Manager. "
            "Ban van co the hoi thong tin san pham, knowledge, purchase/sales order phu hop cong viec hoac ticket ho tro."
        )

    def _answer_admin_only_question(self, question):
        q = self._norm(question)
        if any(word in q for word in ["salary", "luong", "wage", "payroll"]):
            return self._answer_admin_salary_question(question)
        return self._answer_admin_revenue_question(question)

    def _answer_admin_revenue_question(self, question):
        if "sale.order" not in self.env:
            return (
                "Admin live data: he thong hien khong co model sale.order de tinh doanh thu.",
                ["Odoo ORM"],
                ["Tong sales va purchase", "Tong quan database"],
                "medium",
            )

        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        month_end = next_month - timedelta(days=1)
        start_dt = datetime.combine(month_start, datetime.min.time())
        end_dt = datetime.combine(next_month, datetime.min.time())

        SaleOrder = self.env["sale.order"].sudo()
        confirmed_domain = [("state", "in", ("sale", "done"))]
        month_orders = SaleOrder.search(confirmed_domain + [
            ("date_order", ">=", fields.Datetime.to_string(start_dt)),
            ("date_order", "<", fields.Datetime.to_string(end_dt)),
        ])
        all_confirmed = SaleOrder.search(confirmed_domain)

        month_total = sum(month_orders.mapped("amount_total"))
        all_total = sum(all_confirmed.mapped("amount_total"))
        answer = (
            "Admin live data tu Odoo sale.order:\n"
            f"- Ky hien tai: {month_start.strftime('%d/%m/%Y')} - {month_end.strftime('%d/%m/%Y')}\n"
            f"- Sales Order da xac nhan trong ky: {len(month_orders)}\n"
            f"- Gross revenue trong ky (amount_total): {self._money(month_total)}\n"
            f"- Tong gross revenue tat ca Sales Order da xac nhan: {self._money(all_total)}"
        )

        if not month_orders and all_confirmed:
            latest = all_confirmed.sorted("date_order", reverse=True)[:1]
            latest_date = latest.date_order.date() if latest.date_order else None
            if latest_date:
                latest_start = latest_date.replace(day=1)
                latest_next = (
                    latest_start.replace(year=latest_start.year + 1, month=1)
                    if latest_start.month == 12
                    else latest_start.replace(month=latest_start.month + 1)
                )
                latest_orders = SaleOrder.search(confirmed_domain + [
                    ("date_order", ">=", fields.Datetime.to_string(datetime.combine(latest_start, datetime.min.time()))),
                    ("date_order", "<", fields.Datetime.to_string(datetime.combine(latest_next, datetime.min.time()))),
                ])
                latest_total = sum(latest_orders.mapped("amount_total"))
                answer += (
                    f"\n- Luu y: thang hien tai chua co Sales Order xac nhan; "
                    f"thang gan nhat co du lieu la {latest_start.strftime('%m/%Y')} voi "
                    f"{len(latest_orders)} don, tong {self._money(latest_total)}."
                )

        return answer, ["sale.order", "Odoo ORM live query"], ["Tong sales va purchase", "Tong quan database"], "high"

    def _answer_admin_salary_question(self, question):
        if "hr.employee" not in self.env:
            return (
                "Admin live data: he thong hien khong co model hr.employee de kiem tra CEO/manager.",
                ["Odoo ORM"],
                ["Doanh thu thang nay", "Thong tin nhan vien"],
                "medium",
            )

        employees = self.env["hr.employee"].sudo().search([], limit=300)
        executives = employees.filtered(
            lambda employee: any(
                marker in self._norm("%s %s" % (employee.name, employee.job_title or ""))
                for marker in ("ceo", "giam doc", "tong giam doc")
            )
        )
        if not executives:
            return (
                "Admin live data: khong tim thay nhan vien co chuc danh CEO/Giam Doc trong hr.employee.",
                ["hr.employee"],
                ["Doanh thu thang nay", "Thong tin nhan vien"],
                "medium",
            )

        if "hr.contract" not in self.env or "wage" not in self.env["hr.contract"]._fields:
            names = ", ".join(executives.mapped("name")[:6])
            return (
                "Admin live data tu Odoo: tim thay executive trong hr.employee: "
                f"{names}. Tuy nhien database hien chua cai/payroll hoac khong co truong hr.contract.wage, "
                "nen khong co so lieu luong CEO de hien thi. He thong khong tu bia so luong.",
                ["hr.employee", "hr.contract availability check"],
                ["Doanh thu thang nay", "Tong quan database"],
                "high",
            )

        Contract = self.env["hr.contract"].sudo()
        contracts = Contract.search([("employee_id", "in", executives.ids)], order="date_start desc, id desc")
        if not contracts:
            names = ", ".join(executives.mapped("name")[:6])
            return (
                f"Admin live data: tim thay executive {names}, nhung khong co hop dong hr.contract nao gan voi cac nhan vien nay.",
                ["hr.employee", "hr.contract"],
                ["Doanh thu thang nay", "Tong quan database"],
                "high",
            )

        lines = []
        for contract in contracts[:6]:
            employee = contract.employee_id
            state = getattr(contract, "state", "") or "unknown"
            lines.append(f"- {employee.name}: wage {self._money(contract.wage)}, contract state {state}")
        return (
            "Admin live data tu hr.contract:\n" + "\n".join(lines),
            ["hr.employee", "hr.contract"],
            ["Doanh thu thang nay", "Tong quan database"],
            "high",
        )

    def _is_public_deep_vector_probe(self, question):
        q = self._norm(question)
        return any(word in q for word in [
            "raw", "vector", "chroma", "embedding", "metadata", "access_role",
            "noi bo", "bao mat", "database", "don hang", "purchase", "rfq",
            "ticket", "sla", "login", "email", "so dien thoai", "sdt", "doanh thu",
        ])

    def _extract_business_code(self, question):
        match = re.search(r"\b([SP]\d{4,})\b", (question or "").upper())
        return match.group(1) if match else ""

    def _find_employee_from_question(self, question):
        if "hr.employee" not in self.env:
            return False
        q = self._norm(question)
        raw_question = (question or "").lower()
        for employee in self.env["hr.employee"].sudo().search([], limit=120):
            employee_email = (employee.work_email or "").lower()
            if employee_email and employee_email in raw_question:
                return employee
            employee_name = self._norm(employee.name)
            if employee_name and employee_name in q:
                return employee
        return False

    def _public_privacy_answer(self, question=None):
        q = self._norm(question or "")
        business_words = [
            "don hang", "sales", "sale order", "purchase", "rfq", "doanh thu",
            "bao cao", "database", "vector", "chroma", "ticket", "sla",
            "du lieu khach hang", "customer email",
        ]
        if any(word in q for word in business_words):
            return (
                "Phần này là dữ liệu nội bộ của CityRise, nên khách hàng chỉ xem được thông tin công khai "
                "như sản phẩm, giá niêm yết và hướng hỗ trợ chung. Mình không chia sẻ chi tiết sales, "
                "purchase, ticket, database/vector, email khách hàng hoặc báo cáo nội bộ. Nếu bạn cần hỗ trợ "
                "về một đơn hàng hay yêu cầu cụ thể, hãy để lại thông tin liên hệ để nhân viên CityRise kiểm tra."
            )
        return (
            "Mình có thể cung cấp tên và vai trò chung của nhân sự CityRise, "
            "nhưng không chia sẻ email, số điện thoại cá nhân, login hoặc dữ liệu nội bộ. "
            "Nếu bạn cần tư vấn, hãy để lại thông tin liên hệ để đội ngũ CityRise hỗ trợ."
        )

    def _product_records(self):
        return self.env["product.template"].sudo().search(
            [("website_published", "=", True), ("sale_ok", "=", True)],
            order="website_sequence asc, id asc",
            limit=120,
        )

    def _answer_products(self, question):
        products = self._product_records()
        if not products:
            return False, ["product.template"], self._suggestions(False), "low"
        q = self._norm(question)
        filters = self._extract_price_filters(q)
        matched = self._rank_products(products, question)
        source_note = "product.template"

        if filters:
            min_price, max_price = filters
            matched = products.filtered(
                lambda product: (min_price is None or product.list_price >= min_price)
                and (max_price is None or product.list_price <= max_price)
            )
            source_note = "product.template + price filter"
        elif "re nhat" in q or "gia thap" in q:
            matched = products.sorted("list_price")[:5]
        elif "dat nhat" in q or "gia cao" in q:
            matched = products.sorted("list_price", reverse=True)[:5]
        elif any(word in q for word in ["danh sach", "tat ca", "san pham", "shop", "can ho"]) and not matched:
            matched = products[:15]

        if not matched:
            matched = products[:8]
        limit = 15 if any(word in q for word in ["danh sach", "tat ca"]) or filters else 6
        matched = matched[:limit]
        lines = []
        for product in matched:
            line = f"- {product.name}: {self._money(product.list_price)}"
            if product.compare_list_price and product.compare_list_price > product.list_price:
                line += f" (giá cũ {self._money(product.compare_list_price)})"
            description = self._plain(product.description_sale or product.website_description)
            if len(matched) <= 3 and description:
                line += f". {description}"
            lines.append(line)
        header = "Mình tìm thấy %s sản phẩm phù hợp trên shop CityRise:" % len(matched)
        if filters and not matched:
            header = "Mình chưa thấy sản phẩm nào khớp khoảng giá đó. Một vài sản phẩm đang bán:"
            lines = [f"- {product.name}: {self._money(product.list_price)}" for product in products[:6]]
        answer = header + "\n" + "\n".join(lines) + "\nBạn có thể xem chi tiết tại /shop."
        return answer, [source_note, "website_sale"], ["Căn hộ rẻ nhất là gì?", "Căn hộ từ 10 đến 15 tỷ", "Tôi cần tư vấn căn hộ này"], "high"

    def _rank_products(self, products, question):
        q_norm = self._norm(question)
        q_tokens = set(self._tokens(question))
        ranked = []
        for product in products:
            name_norm = self._norm(product.name)
            name_tokens = set(self._tokens(product.name))
            score = 0
            if name_norm and name_norm in q_norm:
                score += 100
            score += len(q_tokens & name_tokens) * 12
            for token in q_tokens:
                if token in name_norm:
                    score += 7
            score += int(SequenceMatcher(None, q_norm, name_norm).ratio() * 20)
            if score >= 18:
                ranked.append((score, product))
        ranked.sort(key=lambda item: (-item[0], item[1].website_sequence, item[1].id))
        return self.env["product.template"].browse([product.id for _, product in ranked])

    def _extract_price_filters(self, q):
        number_unit = r"(\d+(?:[.,]\d+)?)\s*(ty|ti|trieu|nghin|k|m|b)?"
        range_match = re.search(r"(?:tu|khoang)\s*%s\s*(?:den|toi|-)\s*%s" % (number_unit, number_unit), q)
        if range_match:
            first = self._amount_from_match(range_match.group(1), range_match.group(2) or range_match.group(4))
            second = self._amount_from_match(range_match.group(3), range_match.group(4) or range_match.group(2))
            return min(first, second), max(first, second)
        max_match = re.search(r"(?:duoi|nho hon|it hon|<=|khong qua)\s*%s" % number_unit, q)
        if max_match:
            return None, self._amount_from_match(max_match.group(1), max_match.group(2))
        min_match = re.search(r"(?:tren|lon hon|cao hon|>=|tu)\s*%s" % number_unit, q)
        if min_match:
            return self._amount_from_match(min_match.group(1), min_match.group(2)), None
        return None

    def _amount_from_match(self, value, unit):
        amount = float((value or "0").replace(",", "."))
        unit = unit or "ty"
        if unit in ("ty", "ti", "b"):
            return amount * 1_000_000_000
        if unit in ("trieu", "m"):
            return amount * 1_000_000
        if unit in ("nghin", "k"):
            return amount * 1_000
        return amount

    def _answer_company(self, is_internal):
        company = self.env.company.sudo()
        parts = [
            f"{company.name or 'CityRise'} là website bán và tư vấn bất động sản/căn hộ.",
            "Khách hàng có thể xem sản phẩm tại /shop, gửi yêu cầu qua Contact Us hoặc dùng AI Assistant để được gợi ý sản phẩm.",
        ]
        if is_internal:
            contact = []
            if company.phone:
                contact.append(f"điện thoại công ty: {company.phone}")
            if company.email:
                contact.append(f"email công ty: {company.email}")
            if contact:
                parts.append("Thông tin nội bộ: " + ", ".join(contact) + ".")
        return " ".join(parts), ["res.company", "website"], ["Danh sách sản phẩm đang bán", "Tôi cần tư vấn"], "high"

    def _answer_website_content(self, question):
        q = self._norm(question)
        pages = self.env["website.page"].sudo().search([("website_published", "=", True)], limit=80)
        scored = []
        for page in pages:
            text = self._norm((page.name or "") + " " + (page.url or "") + " " + self._plain(page.arch or ""))
            score = sum(1 for token in self._tokens(q) if token in text)
            if score:
                scored.append((score, page))
        scored.sort(key=lambda item: -item[0])
        pages = [page for _, page in scored[:4]]
        if not pages:
            pages = self.env["website.page"].sudo().search([("url", "in", ["/shop", "/contactus", "/help", "/appointment"])])
        lines = [f"- {page.name}: {page.url}" for page in pages if page.url]
        answer = "Các trang hữu ích trên website CityRise:\n" + "\n".join(lines or ["- Shop: /shop", "- Contact Us: /contactus"])
        return answer, ["website.page"], ["Mở shop", "Tôi muốn đặt lịch xem nhà", "Tôi cần hỗ trợ"], "high"

    def _answer_staff(self, question, is_internal):
        employees = self.env["hr.employee"].sudo().search([], order="name", limit=30)
        users = self.env["res.users"].sudo().search([("share", "=", False), ("active", "=", True)], order="name", limit=30)
        if is_internal:
            exact_employee = self._find_employee_from_question(question)
            if exact_employee:
                details = [
                    f"Nhân viên: {exact_employee.name}",
                    f"Chức danh: {exact_employee.job_title or 'chưa cập nhật'}",
                    f"Phòng ban: {exact_employee.department_id.name or 'chưa cập nhật'}",
                    f"Quản lý: {exact_employee.parent_id.name or 'không có'}",
                    f"Email: {exact_employee.work_email or 'chưa cập nhật'}",
                    f"Điện thoại: {exact_employee.mobile_phone or exact_employee.work_phone or 'chưa cập nhật'}",
                ]
                if exact_employee.category_ids:
                    details.append("Tag: " + ", ".join(exact_employee.category_ids.mapped("name")))
                if exact_employee.birthday:
                    details.append(f"Sinh nhật: {exact_employee.birthday.strftime('%d/%m')}")
                return "\n".join(details), ["hr.employee"], ["Thông tin nhân viên", "Tổng sales và purchase"], "high"
            lines = []
            seen = set()
            for employee in employees:
                seen.add(employee.user_id.id)
                details = [employee.name]
                if employee.job_title:
                    details.append(employee.job_title)
                if employee.department_id:
                    details.append(employee.department_id.name)
                if employee.parent_id:
                    details.append(f"manager: {employee.parent_id.name}")
                if employee.work_email:
                    details.append(f"email: {employee.work_email}")
                if employee.work_phone:
                    details.append(f"phone: {employee.work_phone}")
                if employee.mobile_phone:
                    details.append(f"mobile: {employee.mobile_phone}")
                lines.append("- " + " | ".join(details))
            for user in users.filtered(lambda item: item.id not in seen):
                details = [user.name]
                if user.login:
                    details.append(f"login: {user.login}")
                if user.partner_id.email:
                    details.append(f"email: {user.partner_id.email}")
                if user.partner_id.phone:
                    details.append(f"phone: {user.partner_id.phone}")
                lines.append("- " + " | ".join(details))
            return "Thông tin nhân sự nội bộ:\n" + "\n".join(lines[:24]), ["hr.employee", "res.users"], ["Tổng sales và purchase", "Tình hình helpdesk"], "high"
        public_people = []
        for employee in employees[:8]:
            role = employee.job_title or employee.department_id.name or "nhân sự CityRise"
            public_people.append(f"- {employee.name}: {role}")
        if not public_people:
            public_people = [f"- {user.name}: nhân sự CityRise" for user in users[:8]]
        answer = (
            "Một số nhân sự CityRise có thể hỗ trợ khách hàng:\n"
            + "\n".join(public_people)
            + "\nMình không chia sẻ email, số điện thoại cá nhân hoặc login. Bạn có thể để lại nhu cầu để CityRise liên hệ."
        )
        return answer, ["hr.employee public fields", "res.users public fields"], ["Tôi cần tư vấn căn hộ", "Danh sách sản phẩm"], "high"

    def _answer_helpdesk(self, is_internal):
        teams = self.env["cityrise.helpdesk.team"].sudo().search([], order="sequence, name")
        if not teams:
            return "CityRise có bộ phận hỗ trợ khách hàng. Bạn có thể gửi yêu cầu qua Contact Us.", ["cityrise.helpdesk.team"], ["Contact Us"], "medium"
        if not is_internal:
            return (
                "CityRise có đội hỗ trợ khách hàng để tiếp nhận câu hỏi về sản phẩm, lịch xem nhà và yêu cầu sau bán. "
                "Bạn có thể để lại thông tin liên hệ để nhân viên hỗ trợ."
            ), ["cityrise.helpdesk.team public"], ["Tôi cần hỗ trợ căn hộ 90x", "Tôi muốn đặt lịch xem nhà"], "high"
        lines = []
        for team in teams:
            lines.append(
                f"- {team.name}: open {team.open_ticket_count}, "
                f"unassigned {team.unassigned_ticket_count}, urgent {team.urgent_ticket_count}, "
                f"failed {team.failed_ticket_count}, closed {team.closed_ticket_count}"
            )
        return "Tình hình Helpdesk nội bộ:\n" + "\n".join(lines), ["cityrise.helpdesk.team", "cityrise.helpdesk.ticket"], ["Thông tin nhân viên", "Tổng quan database"], "high"

    def _answer_internal_business(self, question, is_internal):
        if not is_internal:
            return (
                "Mình không thể chia sẻ dữ liệu đơn hàng, mua hàng hoặc doanh thu nội bộ. "
                "Mình có thể hỗ trợ bạn về sản phẩm đang bán trên shop."
            ), ["Quy tắc phân quyền CityRise"], ["Danh sách sản phẩm đang bán", "Căn hộ rẻ nhất"], "high"
        code = self._extract_business_code(question)
        if code:
            exact_answer = self._answer_business_code(code)
            if exact_answer:
                return exact_answer
        lines = []
        if "sale.order" in self.env:
            orders = self.env["sale.order"].sudo().search([])
            confirmed = orders.filtered(lambda order: order.state in ("sale", "done"))
            total = sum(confirmed.mapped("amount_total"))
            lines.append(f"Sales: {len(orders)} báo giá/đơn, {len(confirmed)} đơn đã xác nhận, tổng {self._money(total)}.")
        if "purchase.order" in self.env:
            purchases = self.env["purchase.order"].sudo().search([])
            confirmed_po = purchases.filtered(lambda order: order.state in ("purchase", "done"))
            total_po = sum(confirmed_po.mapped("amount_total"))
            lines.append(f"Purchase: {len(purchases)} RFQ/PO, {len(confirmed_po)} PO đã xác nhận, tổng {self._money(total_po)}.")
        answer = "\n".join(lines) if lines else "Chưa tìm thấy dữ liệu sales/purchase trong database."
        return answer, ["sale.order", "purchase.order"], ["Tình hình helpdesk", "Thông tin nhân viên"], "high"

    def _answer_business_code(self, code):
        if code.startswith("S") and "sale.order" in self.env:
            order = self.env["sale.order"].sudo().search([("name", "=", code)], limit=1)
            if not order:
                return False
            state_label = {
                "draft": "Quotation",
                "sent": "Quotation Sent",
                "sale": "Sales Order",
                "done": "Locked Sales Order",
                "cancel": "Cancelled",
            }.get(order.state, order.state)
            line_summary = "; ".join(
                f"{line.name} qty {line.product_uom_qty:g} subtotal {self._money(line.price_subtotal)}"
                for line in order.order_line[:4]
            )
            answer = (
                f"{order.name} là {state_label}.\n"
                f"- Khách hàng: {order.partner_id.display_name}\n"
                f"- Salesperson: {order.user_id.name or 'chưa gán'}\n"
                f"- Ngày: {order.date_order}\n"
                f"- Tổng: {self._money(order.amount_total)}\n"
                f"- Dòng hàng: {line_summary or 'chưa có dòng hàng'}"
            )
            return answer, ["sale.order"], ["Tổng sales và purchase", "Tìm sales order khác"], "high"

        if code.startswith("P") and "purchase.order" in self.env:
            order = self.env["purchase.order"].sudo().search([("name", "=", code)], limit=1)
            if not order:
                return False
            state_label = {
                "draft": "RFQ",
                "sent": "RFQ Sent",
                "to approve": "To Approve",
                "purchase": "Purchase Order",
                "done": "Locked Purchase Order",
                "cancel": "Cancelled",
            }.get(order.state, order.state)
            line_summary = "; ".join(
                f"{line.name} qty {line.product_qty:g} subtotal {self._money(line.price_subtotal)}"
                for line in order.order_line[:4]
            )
            answer = (
                f"{order.name} là {state_label}.\n"
                f"- Vendor: {order.partner_id.display_name}\n"
                f"- Buyer: {order.user_id.name or 'chưa gán'}\n"
                f"- Ngày đặt: {order.date_order}\n"
                f"- Ngày duyệt: {order.date_approve or 'chưa duyệt'}\n"
                f"- Tổng: {self._money(order.amount_total)}\n"
                f"- Dòng hàng: {line_summary or 'chưa có dòng hàng'}"
            )
            return answer, ["purchase.order"], ["Tổng sales và purchase", "Tìm purchase order khác"], "high"

        return False

    def _answer_database_overview(self, is_internal):
        if not is_internal:
            answer = (
                "Với khách hàng, mình chỉ dùng dữ liệu công khai như sản phẩm trên shop, trang website và thông tin hỗ trợ chung. "
                "Dữ liệu nội bộ như đơn hàng, mua hàng, nhân viên, email và số điện thoại được bảo vệ."
            )
            return answer, ["Quy tắc phân quyền CityRise"], ["Danh sách sản phẩm", "Tôi cần tư vấn"], "high"
        model_counts = []
        for model, label in [
            ("product.template", "Products"),
            ("sale.order", "Sales Orders"),
            ("purchase.order", "Purchase Orders"),
            ("crm.lead", "CRM Leads"),
            ("cityrise.helpdesk.ticket", "Helpdesk Tickets"),
            ("hr.employee", "Employees"),
            ("res.partner", "Contacts"),
        ]:
            if model in self.env:
                model_counts.append(f"- {label}: {self.env[model].sudo().search_count([])}")
        return "Tổng quan dữ liệu CityRise:\n" + "\n".join(model_counts), ["ir.model", "Odoo ORM"], ["Tổng sales và purchase", "Tình hình helpdesk"], "high"
