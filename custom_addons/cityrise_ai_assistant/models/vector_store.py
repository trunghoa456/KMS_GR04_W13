"""Giai thich file phan tich hop CityRise AI voi Vector DB.

File nay khong tao vector DB; no chi doc lai ./chroma_db/kms_collection de
CityRise AI search thong tin. Ham role_filter la diem bao mat quan trong:
khach hang public chi duoc filter access_role == public, con nhan vien/admin
duoc filter them internal/it_staff/hr_manager va cac role noi bo khac.

File nay cung cache ket noi ChromaDB theo thoi gian sua file chroma.sqlite3 de
tra loi nhanh hon, phu hop yeu cau nhan vien/admin hoi va nhan cau tra loi nhanh.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from cityrise_vector_pipeline import KmsLocalEmbeddings
except Exception:
    KmsLocalEmbeddings = None


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


def compact_text(text, limit=240):
    value = re.sub(r"\s+", " ", text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


class CityRiseVectorStore:
    _db = None
    _cache_key = None
    _env_cache = None

    @classmethod
    def search(cls, query, is_internal, k=4):
        started = time.monotonic()
        if not KmsLocalEmbeddings:
            return [], {"status": "missing_embedding"}

        try:
            from langchain_chroma import Chroma
        except Exception as error:
            return [], {"status": "missing_chroma", "error": str(error)}

        persist_dir = cls.persist_dir()
        sqlite_path = persist_dir / "chroma.sqlite3"
        if not sqlite_path.exists():
            return [], {"status": "missing_db", "path": str(persist_dir)}

        collection = os.getenv("VECTOR_COLLECTION", "kms_collection")
        cache_key = (str(persist_dir.resolve()), collection, sqlite_path.stat().st_mtime)
        try:
            if cls._db is None or cls._cache_key != cache_key:
                cls._db = Chroma(
                    persist_directory=str(persist_dir),
                    embedding_function=KmsLocalEmbeddings(),
                    collection_name=collection,
                )
                cls._cache_key = cache_key

            docs = cls._db.similarity_search(query, k=k, filter=cls.role_filter(is_internal))
            return docs, {
                "status": "ok",
                "path": str(persist_dir),
                "collection": collection,
                "elapsed": time.monotonic() - started,
            }
        except Exception as error:
            return [], {"status": "query_failed", "error": str(error), "path": str(persist_dir)}

    @classmethod
    def persist_dir(cls):
        configured = os.getenv("CITYRISE_VECTOR_DIR") or os.getenv("VECTOR_PERSIST_DIR")
        if configured:
            return Path(configured).expanduser()

        current = Path(__file__).resolve()
        for parent in current.parents:
            candidate = parent / "chroma_db"
            if (candidate / "chroma.sqlite3").exists():
                return candidate

        return current.parents[3] / "chroma_db"

    @classmethod
    def role_filter(cls, is_internal):
        if not is_internal:
            return {"access_role": "public"}
        return {"$or": [{"access_role": role} for role in INTERNAL_ACCESS_ROLES]}

    @classmethod
    def project_root(cls):
        return Path(__file__).resolve().parents[3]

    @classmethod
    def local_env(cls):
        if cls._env_cache is not None:
            return cls._env_cache
        values = {}
        for path in (
            cls.project_root() / "KMS_TEAM_GR04_W12" / ".env",
            cls.project_root() / ".env",
        ):
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
        cls._env_cache = values
        return values

    @classmethod
    def config(cls, key, default=None):
        return os.getenv(key) or cls.local_env().get(key) or default

    @classmethod
    def rag_provider(cls):
        return (cls.config("RAG_PROVIDER", "ollama") or "ollama").lower()

    @classmethod
    def odoo_use_llm(cls):
        value = (cls.config("CITYRISE_ODOO_USE_LLM", "0") or "0").lower()
        return value in ("1", "true", "yes", "on")

    @classmethod
    def odoo_always_use_llm(cls):
        value = (cls.config("CITYRISE_ODOO_ALWAYS_USE_LLM", "0") or "0").lower()
        return value in ("1", "true", "yes", "on")

    @classmethod
    def ollama_model(cls):
        return cls.config("OLLAMA_MODEL", "llama3.2:1b")

    @classmethod
    def ollama_base_url(cls):
        return (cls.config("OLLAMA_BASE_URL", "http://127.0.0.1:11434") or "").rstrip("/")

    @classmethod
    def ollama_generate(cls, prompt, temperature=0.2, timeout=90):
        payload = {
            "model": cls.ollama_model(),
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": float(temperature)},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{cls.ollama_base_url()}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
                return (body.get("response") or "").strip(), {"status": "ok"}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            return "", {"status": "ollama_failed", "error": str(error)}
