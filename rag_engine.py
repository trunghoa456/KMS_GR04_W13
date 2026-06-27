#!/usr/bin/env python3
"""Week 12 RAG core engine.

This file implements the technical RAG pipeline required by the assignment:
1. Receive a user question.
2. Embed/search the existing Week 11 Chroma vector database.
3. Extract top-k secure context chunks using role metadata filters.
4. Merge the chunks into the BA system prompt template.
5. Send the prompt to an LLM provider when configured, or return a safe local
   extractive fallback when no API key/model server is available.

The engine never answers from general world knowledge. If the vector database
does not contain enough context, it returns an explicit fallback warning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import requests
from dotenv import load_dotenv
from langchain_chroma import Chroma


TEAM_DIR = Path(__file__).resolve().parent
ROOT_DIR = TEAM_DIR.parent


load_dotenv(TEAM_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


INTERNAL_ACCESS_ROLES = (
    "public",
    "internal",
    "admin",
    "it_staff",
    "hr_manager",
    "sales_staff",
    "purchase_staff",
    "support_staff",
)

SYSTEM_PROMPT_TEMPLATE = """You are CityRise Internal RAG Assistant.

Persona:
- Be factual, concise, and operational.
- Use only the provided corporate context from the vector database.
- If the context is weak, missing, or unrelated, say that the retrieved data is insufficient.
- Do not invent figures, policies, names, tickets, orders, contacts, or database details.
- Do not answer competitor comparisons, salary questions, private credentials, or unrelated general knowledge.

Audience rule:
- Audience is {audience}.
- For public/customer audiences, only surface public information.
- For internal audiences, you may summarize internal chunks that were retrieved through the role filter.
- For internal audiences, do not refuse just because the retrieved context contains orders, tickets, product names, prices, or staff records.

Retrieved context:
{context}

User question:
{question}

Answer in Vietnamese unless the user asks in English. Include a short "Nguon" line with the source titles you used."""

FALLBACK_ANSWER = (
    "Mình chưa có đủ ngữ cảnh đáng tin cậy trong Vector DB để trả lời chắc chắn. "
    "Vui lòng hỏi cụ thể hơn hoặc yêu cầu nhân sự phụ trách kiểm tra dữ liệu gốc trong Odoo."
)

PUBLIC_RESTRICTED_ANSWER = (
    "Mình chỉ có thể hỗ trợ thông tin công khai ở mức tổng quan cho khách hàng. "
    "Các thông tin nội bộ như nhân viên, đăng nhập, đơn sales/purchase, ticket, database hoặc vector "
    "không được chia sẻ qua chế độ public."
)


@dataclass
class RetrievedChunk:
    title: str
    access_role: str
    workspace_dimension: str
    source_model: str
    source_id: str
    content: str


class KmsLocalEmbeddings:
    """Deterministic local embedding model for CityRise vector searches.

    Week 12 keeps this class inside rag_engine.py so the submitted repository can
    run without importing private files from the larger Odoo workspace.
    """

    FEATURES = [
        ("onboarding", 1.2, ["onboarding", "welcome", "welcoming", "new developer", "new hire", "incoming", "arrival", "orientation", "nhan vien moi", "chao don"]),
        ("knowledge", 1.1, ["knowledge", "kms", "article", "sop", "policy", "protocol", "guideline", "quy trinh", "huong dan", "kien thuc"]),
        ("it", 1.0, ["it", "engineering", "developer", "technical", "github", "system", "network", "firewall", "port", "infrastructure", "vpn"]),
        ("security", 1.3, ["security", "safety", "firewall", "protocol", "isolation", "infraction", "violation", "policy", "bao mat", "an toan"]),
        ("discipline", 2.8, ["disciplinary", "discipline", "actions", "violation", "conduct", "penalty", "ky luat", "vi pham"]),
        ("hardware", 1.4, ["hardware", "equipment", "computing", "device", "laptop", "allocation", "acceptable", "thiet bi"]),
        ("sales", 1.4, ["sales", "sale", "quotation", "customer", "order", "payment", "sales order", "don hang", "bao gia", "khach hang", "doanh thu"]),
        ("purchase", 1.4, ["purchase", "purchasing", "vendor", "receipt", "tax", "po", "rfq", "purchase order", "mua hang", "nha cung cap", "hoa don"]),
        ("helpdesk", 1.5, ["helpdesk", "ticket", "support", "sla", "urgent", "deadline", "assigned", "ho tro", "khieu nai", "cham soc"]),
        ("employee", 1.2, ["employee", "staff", "admin", "administrator", "salesperson", "buyer", "login", "email", "phone", "department", "nhan vien", "nhan su"]),
        ("product", 1.1, ["product", "apartment", "real estate", "shop", "price", "can ho", "bat dong san", "gia", "san pham"]),
        ("public", 1.0, ["public", "general", "workspace", "conduct", "cross-functional", "environment", "corporate", "cong khai", "chung"]),
        ("hr", 1.0, ["hr", "human resources", "employee", "personnel", "manager", "staff", "nhan su"]),
    ]
    HASH_BUCKETS = 48

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        normalized = self._normalize(text)
        vector = []
        for _, weight, terms in self.FEATURES:
            score = 0.0
            for term in terms:
                if " " in term:
                    score += normalized.count(term) * 1.7
                else:
                    score += len(re.findall(rf"\b{re.escape(term)}\b", normalized))
            vector.append(score * weight)

        buckets = [0.0] * self.HASH_BUCKETS
        for token in self._tokens(normalized):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=2).digest()
            bucket = int.from_bytes(digest, "little") % self.HASH_BUCKETS
            buckets[bucket] += 0.15
        vector.extend(buckets)
        return self._unit(vector)

    def _normalize(self, text: str) -> str:
        value = (text or "").lower().replace("đ", "d").replace("Đ", "d")
        value = unicodedata.normalize("NFKD", value)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        replacements = {
            "how do we welcome": "welcome onboarding",
            "new developers": "new developer",
            "new technical hires": "new hire developer",
            "incoming personnel": "incoming new hire",
            "disciplinary action": "disciplinary actions",
            "safety infractions": "safety violation",
            "port isolation": "firewall security isolation protocol",
            "don ban hang": "sales order",
            "don hang ban": "sales order",
            "bao gia": "quotation",
            "don mua hang": "purchase order",
            "yeu cau mua hang": "rfq purchase order",
            "phieu ho tro": "helpdesk ticket",
            "nhan vien": "employee staff",
        }
        for src, dst in replacements.items():
            value = value.replace(src, dst)
        return value

    def _tokens(self, text: str) -> Iterable[str]:
        return re.findall(r"[a-z0-9_]{2,}", text)

    def _unit(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            return [0.0] * len(vector)
        return [value / norm for value in vector]


def vector_persist_dir() -> Path:
    configured = os.getenv("VECTOR_PERSIST_DIR", "../chroma_db")
    path = Path(configured)
    if not path.is_absolute():
        path = TEAM_DIR / path
    return path.resolve()


def role_filter(audience: str) -> dict[str, Any]:
    if audience == "public":
        return {"access_role": "public"}
    return {"$or": [{"access_role": role} for role in INTERNAL_ACCESS_ROLES]}


def is_public_restricted_question(question: str) -> bool:
    q = (question or "").lower()
    restricted_markers = [
        "access_role",
        "buyer",
        "database",
        "employee",
        "embedding",
        "internal",
        "login",
        "metadata",
        "password",
        "purchase order",
        "quotation",
        "rfq",
        "salary",
        "sales order",
        "ticket",
        "vector",
        "vendor",
        "báo giá",
        "cơ sở dữ liệu",
        "doanh thu",
        "đăng nhập",
        "đơn hàng",
        "đơn mua",
        "email",
        "khách hàng nào",
        "lương",
        "mật khẩu",
        "nhân viên",
        "phiếu mua",
        "số điện thoại",
    ]
    return any(marker in q for marker in restricted_markers)


def compact(text: str, limit: int = 900) -> str:
    value = re.sub(r"\s+", " ", text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def load_vector_db() -> Chroma:
    persist_dir = vector_persist_dir()
    if not (persist_dir / "chroma.sqlite3").exists():
        raise FileNotFoundError(
            f"Vector DB not found at {persist_dir}. Run python ingest_to_vector.py first."
        )
    return Chroma(
        persist_directory=str(persist_dir),
        embedding_function=KmsLocalEmbeddings(),
        collection_name=os.getenv("VECTOR_COLLECTION", "kms_collection"),
    )


def exact_source_ids(question: str) -> list[str]:
    """Return business record codes that should be boosted before semantic search."""

    ids = []
    for match in re.findall(r"\b[A-Z]\d{5}\b", (question or "").upper()):
        if match not in ids:
            ids.append(match)
    return ids


def retrieve_context(question: str, top_k: int = 4, audience: str = "internal") -> list[RetrievedChunk]:
    db = load_vector_db()
    safe_top_k = max(1, min(int(top_k), 10))
    chunks = []
    seen = set()

    def allowed(metadata: dict[str, Any]) -> bool:
        access_role = metadata.get("access_role") or "unknown"
        if audience == "public":
            return access_role == "public"
        return access_role in INTERNAL_ACCESS_ROLES

    def add_chunk(metadata: dict[str, Any], content: str) -> None:
        if not allowed(metadata):
            return
        key = (metadata.get("title"), compact(content, 160))
        if key in seen:
            return
        seen.add(key)
        chunks.append(
            RetrievedChunk(
                title=metadata.get("title") or "Untitled",
                access_role=metadata.get("access_role") or "unknown",
                workspace_dimension=metadata.get("workspace_dimension") or "unknown",
                source_model=metadata.get("source_model") or "vector",
                source_id=str(metadata.get("source_id") or ""),
                content=compact(content),
            )
        )

    for source_id in exact_source_ids(question):
        exact = db._collection.get(where={"source_id": source_id}, include=["documents", "metadatas"])
        for content, metadata in zip(exact.get("documents") or [], exact.get("metadatas") or []):
            add_chunk(metadata or {}, content or "")

    docs = db.similarity_search(question, k=safe_top_k, filter=role_filter(audience))
    for doc in docs:
        metadata = doc.metadata or {}
        add_chunk(metadata, doc.page_content)
    return chunks[:safe_top_k]


def context_to_prompt(chunks: list[RetrievedChunk], max_context_chars: int = 4000) -> str:
    parts = []
    budget = max(800, int(max_context_chars))
    used = 0
    for index, chunk in enumerate(chunks, start=1):
        block = (
            f"[{index}] title={chunk.title}; role={chunk.access_role}; "
            f"workspace={chunk.workspace_dimension}; source={chunk.source_model}:{chunk.source_id}\n"
            f"{chunk.content}"
        )
        if used + len(block) > budget:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


def build_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    audience: str = "internal",
    max_context_chars: int = 4000,
) -> str:
    context = context_to_prompt(chunks, max_context_chars=max_context_chars)
    if not context:
        context = "NO_RELEVANT_CONTEXT_RETRIEVED"
    return SYSTEM_PROMPT_TEMPLATE.format(audience=audience, context=context, question=question)


def is_insufficient_context(chunks: list[RetrievedChunk]) -> bool:
    if not chunks:
        return True
    combined = " ".join(chunk.content for chunk in chunks).lower()
    useful_tokens = [token for token in re.findall(r"[a-z0-9]{3,}", combined)]
    return len(useful_tokens) < 12


def call_openai(prompt: str, model: str, temperature: float) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def call_gemini(prompt: str, model: str, temperature: float) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    generation_config = {"temperature": temperature}
    response = genai.GenerativeModel(model).generate_content(prompt, generation_config=generation_config)
    return response.text or ""


def call_ollama(prompt: str, model: str, temperature: float) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    response = requests.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": temperature}},
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("response", "")


def local_context_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return FALLBACK_ANSWER
    lines = ["Mình tìm thấy các ngữ cảnh liên quan trong Vector DB:"]
    for chunk in chunks[:4]:
        lines.append(f"- {chunk.title}: {compact(chunk.content, 260)}")
    sources = ", ".join(chunk.title for chunk in chunks[:4])
    lines.append(f"Nguon: {sources}")
    return "\n".join(lines)


def is_low_quality_llm_answer(answer: str, chunks: list[RetrievedChunk], audience: str) -> bool:
    if audience != "internal" or not chunks:
        return False
    normalized = (answer or "").strip().lower()
    if not normalized:
        return True
    refusal_markers = [
        "không thể cung cấp",
        "không thể giúp",
        "không thể chia sẻ",
        "không có đủ thông tin",
        "không có quyền",
        "không được phép",
        "i cannot provide",
        "i can't provide",
        "cannot provide information",
    ]
    return any(marker in normalized for marker in refusal_markers)


def choose_provider(provider: str) -> str:
    provider = (provider or os.getenv("RAG_PROVIDER", "local")).lower()
    if provider != "auto":
        return provider
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    return "local"


def generate_answer(
    question: str,
    top_k: int = 4,
    temperature: float = 0.2,
    audience: str = "internal",
    provider: str = "auto",
    model: str | None = None,
    max_context_chars: int = 4000,
) -> dict[str, Any]:
    question = (question or "").strip()
    audience = "public" if audience == "public" else "internal"
    if not question:
        return {
            "answer": "Vui lòng nhập câu hỏi.",
            "fallback": True,
            "warning": "empty_question",
            "sources": [],
            "chunks": [],
            "provider": "none",
        }

    if audience == "public" and is_public_restricted_question(question):
        return {
            "answer": PUBLIC_RESTRICTED_ANSWER,
            "fallback": True,
            "warning": "public_access_guard",
            "sources": ["CityRise public access guard"],
            "chunks": [],
            "provider": "none",
        }

    chunks = retrieve_context(question, top_k=top_k, audience=audience)
    prompt = build_prompt(question, chunks, audience=audience, max_context_chars=max_context_chars)
    sources = [chunk.title for chunk in chunks]

    if is_insufficient_context(chunks):
        return {
            "answer": FALLBACK_ANSWER,
            "fallback": True,
            "warning": "insufficient_vector_context",
            "sources": sources,
            "chunks": [asdict(chunk) for chunk in chunks],
            "provider": "none",
            "prompt": prompt,
        }

    selected_provider = choose_provider(provider)
    fallback = False
    warning = ""
    try:
        if selected_provider == "openai":
            answer = call_openai(prompt, model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature)
        elif selected_provider == "gemini":
            answer = call_gemini(prompt, model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"), temperature)
        elif selected_provider == "ollama":
            answer = call_ollama(prompt, model or os.getenv("OLLAMA_MODEL", "llama3.2:1b"), temperature)
        else:
            answer = local_context_answer(question, chunks)
            fallback = True
            warning = "local_extractive_mode_no_llm_provider"
            selected_provider = "local"
    except Exception as error:
        answer = local_context_answer(question, chunks)
        fallback = True
        warning = f"llm_provider_failed_using_local_context: {error}"

    if not fallback and is_low_quality_llm_answer(answer, chunks, audience):
        answer = local_context_answer(question, chunks)
        fallback = True
        warning = "llm_answer_failed_context_guard_using_local_context"

    if sources and "nguon" not in answer.lower() and "source" not in answer.lower():
        answer = answer.rstrip() + "\nNguon: " + ", ".join(sources[:4])

    return {
        "answer": answer.strip() or FALLBACK_ANSWER,
        "fallback": fallback,
        "warning": warning,
        "sources": sources,
        "chunks": [asdict(chunk) for chunk in chunks],
        "provider": selected_provider,
        "prompt": prompt,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask the Week 12 CityRise RAG engine from the terminal.")
    parser.add_argument("question", nargs="?", default="")
    parser.add_argument("--top-k", type=int, default=int(os.getenv("RAG_TOP_K", "4")))
    parser.add_argument("--temperature", type=float, default=float(os.getenv("RAG_TEMPERATURE", "0.2")))
    parser.add_argument("--audience", choices=["internal", "public"], default=os.getenv("RAG_AUDIENCE", "internal"))
    parser.add_argument("--provider", choices=["auto", "local", "openai", "gemini", "ollama"], default=os.getenv("RAG_PROVIDER", "auto"))
    parser.add_argument("--model", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    question = args.question or input("Question: ").strip()
    result = generate_answer(
        question,
        top_k=args.top_k,
        temperature=args.temperature,
        audience=args.audience,
        provider=args.provider,
        model=args.model,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result["fallback"]:
        print(f"[WARNING] {result['warning']}")
    print(result["answer"])


if __name__ == "__main__":
    main()
