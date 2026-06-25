# Week 11 Access Control Matrix

This matrix is the BA mapping sheet used by `ingest_to_vector.py` to attach
document-level security metadata before writing chunks into ChromaDB.

## Files to submit and what each file does

| File / Folder | Purpose in the Week 11 assignment |
|---|---|
| `KMS_TEAM_GR04_W11/access_matrix.md` | BA deliverable. Defines article/source access rules for workspace_dimension and access_role. |
| `KMS_TEAM_GR04_W11/ingest_to_vector.py` | Team ingestion wrapper. Uses this team's matrix and calls the shared root pipeline to create persistent `../chroma_db`. |
| `KMS_TEAM_GR04_W11/test_vector_db.py` | Team audit script. Tests semantic search, it_staff/public filtering and public-customer isolation. |
| `../cityrise_vector_pipeline.py` | Shared developer implementation. Extracts Odoo/KMS/business data, chunks 500/100, embeds text and writes ChromaDB metadata. |
| `../chroma_db/` | Generated persistent vector database. Created by ingest script; do not edit manually. |
| `../addons/cityrise_ai_assistant/models/vector_store.py` | CityRise AI ChromaDB connector with role-based filters. |
| `../addons/cityrise_ai_assistant/models/ai_assistant.py` | CityRise AI guarded answer engine for customer vs employee/admin responses. |

Team role split for a 4-member team:

| Role | Primary responsibility |
|---|---|
| BA 1 | Define workspace dimensions and article access rules |
| BA 2 | Define synonym/test queries and validate expected results |
| Dev 1 | Implement Odoo article ingestion and vector persistence |
| Dev 2 | Implement vector search validation and role-based filter tests |

Article-level access mapping:

| Article Title | Workspace Dimension | Access Role | Target Synonym List |
|---|---|---|---|
| IT Engineer Onboarding Protocol | it | it_staff | onboarding; welcome; new developer; new hire; engineering team |
| Network Security & System Firewall Policy | it | it_staff | network; firewall; system safety; port isolation; infrastructure protocol |
| HR Employee Disciplinary Action Policy | hr | hr_manager | disciplinary actions; employee violation; personnel warning; HR protocol |
| General Workspace Conduct Guideline | ops | public | public; welcoming environment; incoming personnel; workspace conduct |
| Acceptable Hardware Use Agreement | ops | public | hardware safety; computing equipment; acceptable use; disciplinary actions |
| PO Tax and Receipt Validation Practices | purchase | public | purchase order; vendor bill; tax receipt; PO validation |
| Sales Order Immediate Payment Follow-up Control | sales | public | sales order; payment follow-up; customer quotation |
| Timely Quotation Follow-up for High-Value Sales Orders | sales | public | quotation; high-value sales; customer follow-up |
| Early Purchase Confirmation for Premium Penthouse Products - P00030 | purchase | public | purchase confirmation; premium product; procurement |
| Bulk Purchasing Control for High-Demand Apartment Products | purchase | public | bulk purchase; demand control; procurement |

Runtime source-level access mapping:

| Source | Workspace Dimension | Access Role | Target Synonym List |
|---|---|---|---|
| kms.knowledge.article / blog.post | matrix-defined | matrix-defined | SOP; policy; onboarding; firewall; workspace conduct |
| sale.order | sales | internal | sales order; quotation; customer; payment; revenue; salesperson |
| purchase.order | purchase | internal | purchase order; RFQ; vendor; buyer; receipt; tax |
| cityrise.helpdesk.ticket | support | internal | ticket; helpdesk; urgent; SLA; customer support |
| hr.employee / res.users | hr | internal | employee; staff; admin; login; email; phone; department |
| product.template published on website | product | public | product; apartment; shop; public price; consultation |

Dimension-to-role rule:

| Workspace Dimension | Default Access Role |
|---|---|
| hr | hr_manager |
| it | it_staff |
| legal | public |
| ops | public |
| sales | internal |
| purchase | internal |
| support | internal |
| product | public |

Query-time security filters:

| Audience | Vector Filter |
|---|---|
| Customer / Public | `access_role == public` only |
| Employee / Admin | `access_role in public, internal, admin, it_staff, hr_manager, sales_staff, purchase_staff, support_staff` |

Security validation scenarios:

| Test | Query | Simulated Role Filter | Expected Outcome |
|---|---|---|---|
| Semantic match | How do we welcome a new developer into the team? | none | Returns onboarding/workspace conduct content |
| Access-controlled search | System safety and disciplinary actions protocol | it_staff OR public | Returns IT/public documents only |
| Leakage check | System safety and disciplinary actions protocol | it_staff OR public | Must not return `hr_manager` documents |
| Public customer isolation | purchase order P00030 ticket urgent employee login | public only | Returns public product/conduct information only, never internal/order/ticket/user chunks |
