#!/usr/bin/env python3
"""Week 13 retained ingestion entrypoint.

This file is kept from the vector database work because the Week 13 Dockerized
chatbot depends on a persistent ChromaDB collection. Running this script
refreshes the vector database before testing rag_engine.py or app.py.

Command:
    python KMS_TEAM_GR04_W13/ingest_to_vector.py
"""

import os
import sys
import xmlrpc.client
from pathlib import Path

TEAM_DIR = Path(__file__).resolve().parent
ROOT_DIR = TEAM_DIR.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(TEAM_DIR))

from rag_engine import vector_persist_dir

try:
    from cityrise_vector_pipeline import main as week11_main
except ModuleNotFoundError:
    week11_main = None


FIXTURE_DOCS = [
    {
        "content": (
            "IT Engineer Onboarding Protocol. Welcome to the Engineering team. "
            "New IT technical hires must initialize GitHub, confirm VPN access, "
            "complete secure workstation setup, and join internal channels."
        ),
        "metadata": {
            "title": "IT Engineer Onboarding Protocol",
            "workspace_dimension": "it",
            "access_role": "it_staff",
            "tags": "SOP, IT, Onboarding",
            "source_model": "kms.knowledge.article",
            "source_id": "fixture-it-001",
            "record_type": "knowledge",
        },
    },
    {
        "content": (
            "Network Security and System Firewall Policy. Technical staff must trigger "
            "automated port isolation after system safety infractions and review firewall "
            "logs for suspicious network activity. This policy is restricted to IT staff."
        ),
        "metadata": {
            "title": "Network Security & System Firewall Policy",
            "workspace_dimension": "it",
            "access_role": "it_staff",
            "tags": "SOP, IT, Security",
            "source_model": "kms.knowledge.article",
            "source_id": "fixture-it-002",
            "record_type": "knowledge",
        },
    },
    {
        "content": (
            "HR Employee Disciplinary Action Policy. Disciplinary actions for employee "
            "violations must be reviewed by the HR manager and documented in confidential "
            "personnel records."
        ),
        "metadata": {
            "title": "HR Employee Disciplinary Action Policy",
            "workspace_dimension": "hr",
            "access_role": "hr_manager",
            "tags": "SOP, HR, Restricted",
            "source_model": "kms.knowledge.article",
            "source_id": "fixture-hr-001",
            "record_type": "knowledge",
        },
    },
    {
        "content": (
            "General Workspace Conduct Guideline. CityRise maintains an open and welcoming "
            "environment for incoming cross-functional personnel, new developers, and new "
            "teammates. This is general guidance."
        ),
        "metadata": {
            "title": "General Workspace Conduct Guideline",
            "workspace_dimension": "ops",
            "access_role": "public",
            "tags": "SOP, Public, Conduct",
            "source_model": "kms.knowledge.article",
            "source_id": "fixture-public-001",
            "record_type": "knowledge",
        },
    },
    {
        "content": (
            "Acceptable Hardware Use Agreement. Employees must protect assigned laptops, "
            "devices, and other corporate equipment. Misuse of company hardware follows "
            "the acceptable use agreement."
        ),
        "metadata": {
            "title": "Acceptable Hardware Use Agreement",
            "workspace_dimension": "ops",
            "access_role": "public",
            "tags": "SOP, Public, Hardware",
            "source_model": "kms.knowledge.article",
            "source_id": "fixture-public-002",
            "record_type": "knowledge",
        },
    },
    {
        "content": (
            "Purchase Order P00030 - FLC GROUP. Vendor FLC GROUP JOINT STOCK COMPANY. "
            "Buyer Tran Trung Hoa. Confirmed purchase value 742,500,000,000 VND. "
            "Internal procurement teams must validate receipt and order approval."
        ),
        "metadata": {
            "title": "Purchase Order P00030 - FLC GROUP",
            "workspace_dimension": "purchase",
            "access_role": "internal",
            "tags": "Purchase, PO, Internal",
            "source_model": "purchase.order",
            "source_id": "P00030",
            "record_type": "purchase_order",
        },
    },
    {
        "content": (
            "Sales Order S00028 - ECOPARK GROUP. Customer ECOPARK GROUP JOINT STOCK COMPANY. "
            "Salesperson Tran Trung Hoa. Confirmed value 67,500,000,000 VND. "
            "Internal sales users may review quotation and payment follow-up context."
        ),
        "metadata": {
            "title": "Sales Order S00028 - ECOPARK GROUP",
            "workspace_dimension": "sales",
            "access_role": "internal",
            "tags": "Sales, Order, Internal",
            "source_model": "sale.order",
            "source_id": "S00028",
            "record_type": "sales_order",
        },
    },
    {
        "content": (
            "Helpdesk Ticket T00002 - Sales Order Verification. The ticket asks the support "
            "team to verify a sales order total for ECOPARK GROUP. Priority urgent, stage "
            "in progress, assigned to Lu Cong Minh."
        ),
        "metadata": {
            "title": "Helpdesk Ticket T00002 - Sales Order Verification",
            "workspace_dimension": "support",
            "access_role": "internal",
            "tags": "Helpdesk, Ticket, Internal",
            "source_model": "cityrise.helpdesk.ticket",
            "source_id": "T00002",
            "record_type": "helpdesk_ticket",
        },
    },
    {
        "content": (
            "Employee Directory - Sales and Purchase Operators. Internal operators include "
            "Tran Trung Hoa for sales and purchasing, Lu Cong Minh for purchase and helpdesk, "
            "and Pham Anh Tu for purchase and helpdesk. Internal users may see role, login, "
            "and assignment context."
        ),
        "metadata": {
            "title": "Employee Directory - Sales and Purchase Operators",
            "workspace_dimension": "hr",
            "access_role": "internal",
            "tags": "Employee, Internal",
            "source_model": "hr.employee",
            "source_id": "employee-directory",
            "record_type": "employee",
        },
    },
    {
        "content": (
            "CityRise Public Product Overview. CityRise publicly provides apartment and "
            "real estate product information through the shop page. Customers can ask "
            "for product names, public prices, and general consultation."
        ),
        "metadata": {
            "title": "CityRise Public Product Overview",
            "workspace_dimension": "product",
            "access_role": "public",
            "tags": "Product, Public",
            "source_model": "product.template",
            "source_id": "public-products",
            "record_type": "product",
        },
    },
]


ACCESS_ROLE_BY_DIMENSION = {
    "hr": "hr_manager",
    "it": "it_staff",
    "legal": "public",
    "ops": "public",
    "sales": "public",
    "purchase": "public",
}


def relation_name(value) -> str:
    if isinstance(value, (list, tuple)) and len(value) > 1:
        return str(value[1])
    return ""


def plain_text(value) -> str:
    from bs4 import BeautifulSoup

    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)


def fetch_odoo_documents() -> list[dict]:
    """Fetch available live business records over the Compose bridge network."""

    base_url = os.getenv("ODOO_URL", "").rstrip("/")
    database = os.getenv("ODOO_DB", "cityrise_w13")
    login = os.getenv("ODOO_LOGIN", "admin")
    password = os.getenv("ODOO_LOGIN_PASSWORD", "admin")
    limit = max(1, int(os.getenv("ODOO_DATA_LIMIT", "50")))
    if not base_url:
        return []

    try:
        common = xmlrpc.client.ServerProxy(f"{base_url}/xmlrpc/2/common")
        uid = common.authenticate(database, login, password, {})
        if not uid:
            raise RuntimeError("Odoo authentication failed")
        models = xmlrpc.client.ServerProxy(f"{base_url}/xmlrpc/2/object")
    except Exception as error:
        print(f"[WARN] Odoo XML-RPC connection failed, using fixtures: {error}")
        return []

    def model_exists(model_name: str) -> bool:
        return bool(
            models.execute_kw(
                database,
                uid,
                password,
                "ir.model",
                "search_count",
                [[["model", "=", model_name]]],
            )
        )

    def search_read(model_name: str, domain: list, fields: list[str]) -> list[dict]:
        if not model_exists(model_name):
            return []
        return models.execute_kw(
            database,
            uid,
            password,
            model_name,
            "search_read",
            [domain],
            {"fields": fields, "limit": limit, "order": "id desc"},
        )

    documents: list[dict] = []

    for row in search_read(
        "kms.knowledge.article",
        [],
        ["name", "body_html", "properties_note", "workspace_dimension"],
    ):
        dimension = row.get("workspace_dimension") or "ops"
        content = " ".join(
            part
            for part in [
                row.get("name") or "Knowledge Article",
                plain_text(row.get("body_html")),
                row.get("properties_note") or "",
            ]
            if part
        )
        documents.append(
            {
                "content": content,
                "metadata": {
                    "title": row.get("name") or f"Knowledge Article {row['id']}",
                    "workspace_dimension": dimension,
                    "access_role": ACCESS_ROLE_BY_DIMENSION.get(dimension, "public"),
                    "tags": "Knowledge, Odoo",
                    "source_model": "kms.knowledge.article",
                    "source_id": str(row["id"]),
                    "record_type": "knowledge",
                },
            }
        )

    for row in search_read(
        "sale.order",
        [],
        ["name", "partner_id", "user_id", "amount_total", "state"],
    ):
        name = row.get("name") or f"Sale Order {row['id']}"
        documents.append(
            {
                "content": (
                    f"Sales Order {name}. Customer {relation_name(row.get('partner_id'))}. "
                    f"Salesperson {relation_name(row.get('user_id'))}. "
                    f"Total value {row.get('amount_total') or 0} VND. State {row.get('state') or ''}."
                ),
                "metadata": {
                    "title": f"Sales Order {name}",
                    "workspace_dimension": "sales",
                    "access_role": "internal",
                    "tags": "Sales, Order, Odoo, Internal",
                    "source_model": "sale.order",
                    "source_id": str(row["id"]),
                    "record_type": "sales_order",
                },
            }
        )

    for row in search_read(
        "purchase.order",
        [],
        ["name", "partner_id", "user_id", "amount_total", "state"],
    ):
        name = row.get("name") or f"Purchase Order {row['id']}"
        documents.append(
            {
                "content": (
                    f"Purchase Order {name}. Vendor {relation_name(row.get('partner_id'))}. "
                    f"Buyer {relation_name(row.get('user_id'))}. "
                    f"Total value {row.get('amount_total') or 0} VND. State {row.get('state') or ''}."
                ),
                "metadata": {
                    "title": f"Purchase Order {name}",
                    "workspace_dimension": "purchase",
                    "access_role": "internal",
                    "tags": "Purchase, Order, Odoo, Internal",
                    "source_model": "purchase.order",
                    "source_id": str(row["id"]),
                    "record_type": "purchase_order",
                },
            }
        )

    for row in search_read(
        "cityrise.helpdesk.ticket",
        [],
        ["number", "name", "partner_id", "partner_name", "partner_email", "user_id", "priority", "stage", "description", "deadline"],
    ):
        number = row.get("number") or f"T{row['id']}"
        customer = relation_name(row.get("partner_id")) or row.get("partner_name") or ""
        documents.append(
            {
                "content": (
                    f"Helpdesk Ticket {number}: {row.get('name') or ''}. Customer {customer}. "
                    f"Customer email {row.get('partner_email') or ''}. "
                    f"Assigned to {relation_name(row.get('user_id'))}. Priority {row.get('priority') or ''}. "
                    f"Stage {row.get('stage') or ''}. Deadline {row.get('deadline') or ''}. "
                    f"{plain_text(row.get('description'))}"
                ),
                "metadata": {
                    "title": f"Helpdesk Ticket {number} - {row.get('name') or ''}".strip(),
                    "workspace_dimension": "support",
                    "access_role": "internal",
                    "tags": "Helpdesk, Ticket, Odoo, Internal",
                    "source_model": "cityrise.helpdesk.ticket",
                    "source_id": str(row["id"]),
                    "record_type": "helpdesk_ticket",
                },
            }
        )

    for row in search_read(
        "hr.employee",
        [],
        ["name", "job_title", "department_id", "work_email", "work_phone"],
    ):
        documents.append(
            {
                "content": (
                    f"Employee {row.get('name') or ''}. Job title {row.get('job_title') or ''}. "
                    f"Department {relation_name(row.get('department_id'))}. "
                    f"Work email {row.get('work_email') or ''}. Work phone {row.get('work_phone') or ''}."
                ),
                "metadata": {
                    "title": f"Employee {row.get('name') or row['id']}",
                    "workspace_dimension": "hr",
                    "access_role": "internal",
                    "tags": "Employee, Odoo, Internal",
                    "source_model": "hr.employee",
                    "source_id": str(row["id"]),
                    "record_type": "employee",
                },
            }
        )

    for row in search_read(
        "product.template",
        [["website_published", "=", True]],
        ["name", "list_price", "description_sale", "website_published"],
    ):
        documents.append(
            {
                "content": (
                    f"Public Product {row.get('name') or ''}. Published shop price "
                    f"{row.get('list_price') or 0} VND. {plain_text(row.get('description_sale'))}"
                ),
                "metadata": {
                    "title": f"Public Product {row.get('name') or row['id']}",
                    "workspace_dimension": "product",
                    "access_role": "public",
                    "tags": "Product, Odoo, Public",
                    "source_model": "product.template",
                    "source_id": str(row["id"]),
                    "record_type": "product",
                },
            }
        )

    print(f"[INFO] Odoo XML-RPC records fetched: {len(documents)}")
    return documents


def fallback_main() -> None:
    """Create the Week 13 vector DB from Odoo plus a secure fixture baseline."""

    import shutil

    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from rag_engine import KmsLocalEmbeddings

    persist_dir = vector_persist_dir()
    persist_dir.mkdir(parents=True, exist_ok=True)
    for child in persist_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    live_documents = fetch_odoo_documents()
    source_documents = live_documents + FIXTURE_DOCS
    documents = [Document(page_content=item["content"], metadata=item["metadata"]) for item in source_documents]
    chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100).split_documents(documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    Chroma.from_documents(
        documents=chunks,
        embedding=KmsLocalEmbeddings(),
        collection_name="kms_collection",
        persist_directory=str(persist_dir),
        collection_metadata={"hnsw:space": "cosine"},
    )

    print("\n=================== CITYRISE WEEK 13 VECTOR INGESTION COMPLETE ===================")
    source_name = "odoo_xmlrpc+fixture_baseline" if live_documents else "fallback_fixture"
    print(f"Source             : {source_name}")
    print(f"Records fetched    : {len(source_documents)}")
    print(f"Chunks generated   : {len(chunks)}")
    print("Collection         : kms_collection")
    print(f"Persistent path    : {persist_dir}")


if __name__ == "__main__":
    if week11_main:
        week11_main(
            default_matrix=str(TEAM_DIR / "access_matrix.md"),
            default_persist_dir=str(vector_persist_dir()),
        )
    else:
        fallback_main()
