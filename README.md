# Incident Intelligence AI

**One-line description:** AI-assisted incident intelligence workspace that clusters operational incidents and supports evidence-based root cause decisions with human review.

## Live Demo
- Streamlit Community Cloud: _[Add deployment URL]_

## Problem Statement
Operational teams receive fragmented incidents/tickets across systems. Signal gets buried in noise, causing slower triage and inconsistent remediation decisions.

## Target Users
- SRE / DevOps teams
- Incident commanders
- Support operations leads
- AI platform/product managers driving reliability outcomes

## Product Workflow
1. Upload CSV or start with sample incidents.
2. Validate schema and map columns.
3. Generate semantic embeddings.
4. Cluster related incidents.
5. Produce AI recommendations (root cause + remediation + confidence + evidence).
6. Human reviewer edits/approves/rejects.
7. Export CSV, Markdown, and JSON reports.

## Features
- Column mapping for non-standard CSV headers
- Severity normalization
- Embedding-based clustering with adjustable cluster count
- Cluster-level LLM analysis using structured outputs with fallback JSON parsing
- Human-in-the-loop review controls
- Debug expanders for raw inputs/outputs/errors
- Multi-format exports

## Screenshots
See `screenshots/README.md` for placeholder guidance.

## Architecture Diagram
```text
CSV Upload/Sample -> Validation/Mapping -> Embeddings -> Clustering -> LLM Analysis
                                      -> Human Review -> Export (CSV/MD/JSON)
```

## Setup Instructions
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Streamlit Deployment Instructions
1. Push repo to GitHub.
2. Create Streamlit Community Cloud app pointing to `app.py`.
3. Add `OPENAI_API_KEY` in Streamlit Secrets.
4. Optionally set `OPENAI_MODEL` and `OPENAI_EMBEDDING_MODEL`.

## Environment Variables
- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional, default `gpt-4.1-mini`)
- `OPENAI_EMBEDDING_MODEL` (optional, default `text-embedding-3-small`)

## Example CSV Schema
`incident_id, created_at, title, description, severity, status, system_area, customer_impact`

## Example Output
- Cluster title and issue summary
- Likely root cause with evidence bullets
- Remediation actions and recommendation status
- Confidence score and human-review state

## AI Product Tradeoffs
- **Clustering quality:** Depends on textual consistency and embedding signal quality.
- **Root cause uncertainty:** LLM outputs are probabilistic and should be reviewed.
- **Hallucination risk:** Mitigated by explicit evidence requirements and review.
- **Evidence-based recommendations:** Every cluster includes supporting incident evidence.
- **Human-in-the-loop:** Export should happen after reviewer verification.
- **Cost/latency:** Embeddings + LLM calls scale with incident volume and cluster count.

## Evaluation Plan
See `docs/eval_plan.md` for metric definitions and benchmark methodology.

## Roadmap
- Integrations (Jira/ServiceNow/PagerDuty)
- Feedback loops for recommendation quality
- Trend analysis across recurring incident families
