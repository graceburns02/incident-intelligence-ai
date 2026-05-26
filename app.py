from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from openai import APIError, AuthenticationError, RateLimitError

from src.analysis import analyze_clusters
from src.clustering import cluster_embeddings
from src.data_loader import load_incidents_csv, load_sample_dataset
from src.embeddings import build_embedding_texts, generate_embeddings
from src.export import build_report, cluster_results_to_dataframe, to_json_report, to_markdown_report
from src.validation import REQUIRED_COLUMNS, apply_column_mapping, normalize_dataframe, validate_incident_dataframe

st.set_page_config(page_title="Incident Intelligence AI", layout="wide")
st.title("Incident Intelligence AI")
st.caption("AI-assisted decision support for operational incident triage, root cause analysis, and remediation planning.")

with st.sidebar:
    st.header("Workflow")
    st.markdown("""
1. Upload CSV or use sample data.
2. Validate + map columns.
3. Generate embeddings and clusters.
4. Review AI recommendations with evidence.
5. Edit/approve outputs.
6. Export reports.
""")

api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

st.header("1) Upload / Sample Data")
use_sample = st.toggle("Use sample dataset", value=True)
uploaded = st.file_uploader("Upload incidents CSV", type=["csv"])

try:
    df = load_sample_dataset() if use_sample else (load_incidents_csv(uploaded) if uploaded else None)
except Exception as e:
    st.error(f"Invalid CSV: {e}")
    st.stop()

if df is None:
    st.info("Upload a CSV or enable sample dataset.")
    st.stop()

st.write(df.head(5))

if "mapped_df" not in st.session_state:
    st.session_state.mapped_df = df.copy()

st.header("2) Data Validation Summary")
missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing_cols:
    st.warning("Some required columns are missing. Map your columns below.")
    mapping = {}
    cols = [""] + list(df.columns)
    for req in REQUIRED_COLUMNS:
        mapping_choice = st.selectbox(f"Map source column to `{req}`", cols, index=0)
        if mapping_choice:
            mapping[mapping_choice] = req
    mapped = apply_column_mapping(df, mapping)
else:
    mapped = df.copy()

mapped = normalize_dataframe(mapped)
st.session_state.mapped_df = mapped
val = validate_incident_dataframe(mapped)
if not val.valid:
    st.error("; ".join(val.errors))
    with st.expander("Validation errors (debug)"):
        st.json({"errors": val.errors, "warnings": val.warnings})
    st.stop()
if val.warnings:
    st.warning("; ".join(val.warnings))
st.success("Validation passed.")

st.header("3) Incident Overview Metrics")
c1, c2, c3 = st.columns(3)
c1.metric("Incident Count", len(mapped))
c2.metric("System Areas", mapped["system_area"].nunique())
c3.metric("Severities", mapped["severity"].nunique())

fig1 = px.histogram(mapped, x="severity", title="Severity distribution")
fig2 = px.histogram(mapped, x="system_area", title="Incidents by system area")
col1, col2 = st.columns(2)
col1.plotly_chart(fig1, use_container_width=True)
col2.plotly_chart(fig2, use_container_width=True)

st.header("4) Cluster Analysis")
default_clusters = min(6, max(2, len(mapped) // 8))
n_clusters = st.slider("Number of clusters", min_value=2, max_value=min(12, len(mapped)), value=default_clusters)
run = st.button("Run incident intelligence workflow", type="primary")

if run:
    if not api_key:
        st.error("Missing API key. Set OPENAI_API_KEY in Streamlit secrets or environment variables.")
        st.stop()
    texts = build_embedding_texts(mapped.to_dict(orient="records"))
    try:
        embeds = generate_embeddings(texts, api_key=api_key, model=embedding_model)
        labels = cluster_embeddings(embeds, n_clusters=n_clusters)
    except Exception as e:
        st.error(f"Embedding or clustering failure: {e}")
        st.stop()

    mapped["cluster_id"] = labels
    st.session_state.clustered_df = mapped

    st.plotly_chart(px.histogram(mapped, x="cluster_id", title="Cluster sizes"), use_container_width=True)

    try:
        results, grouped, raw_outputs = analyze_clusters(mapped, labels, api_key=api_key, model=model)
    except (AuthenticationError, RateLimitError, APIError) as e:
        st.error(f"OpenAI API error: {e}")
        st.info("Fallback mode enabled: you can still review clusters manually.")
        results, grouped, raw_outputs = [], {}, {}

    st.session_state.analysis_results = results
    st.session_state.grouped = grouped
    st.session_state.raw_outputs = raw_outputs

if "analysis_results" in st.session_state:
    st.header("5) Root Cause Recommendations")
    for r in st.session_state.analysis_results:
        with st.container(border=True):
            st.subheader(f"Cluster {r.cluster_id}: {r.cluster_title or 'Untitled cluster'}")
            st.write(r.issue_summary)
            st.write(f"**AI Root cause (editable):**")
            r.root_cause.likely_root_cause = st.text_area(f"Root cause c{r.cluster_id}", value=r.root_cause.likely_root_cause or "", key=f"rc_{r.cluster_id}")
            rem_text = "\n".join([a.action for a in r.remediation_actions])
            edited_rem = st.text_area(f"Remediation c{r.cluster_id}", value=rem_text, key=f"rem_{r.cluster_id}")
            r.remediation_actions = [{"action": line.strip()} for line in edited_rem.split("\n") if line.strip()]
            r.recommendation_status = st.selectbox(
                f"Decision c{r.cluster_id}",
                ["accepted", "rejected", "needs investigation"],
                index=["accepted", "rejected", "needs investigation"].index(r.recommendation_status),
                key=f"status_{r.cluster_id}",
            )
            st.write("**Evidence**")
            for ev in r.root_cause.supporting_evidence:
                st.markdown(f"- {ev}")
            st.caption(f"Confidence: {r.root_cause.confidence_score}")
            with st.expander(f"Raw cluster inputs (debug) c{r.cluster_id}"):
                st.json(st.session_state.grouped.get(r.cluster_id, []))
            with st.expander(f"Raw model output (debug) c{r.cluster_id}"):
                st.code(st.session_state.raw_outputs.get(r.cluster_id, ""))

    st.header("6) Human Review")
    pending = [r for r in st.session_state.analysis_results if r.recommendation_status == "needs investigation"]
    if pending:
        st.warning(f"{len(pending)} clusters still marked as needs investigation.")
    else:
        st.success("All clusters reviewed.")

    st.header("7) Export Report")
    report = build_report(st.session_state.analysis_results, total_incidents=len(st.session_state.mapped_df))
    export_df = cluster_results_to_dataframe(report.analysis_results)
    md = to_markdown_report(report)
    js = to_json_report(report)

    st.download_button("Download cluster analysis CSV", data=export_df.to_csv(index=False), file_name="cluster_analysis.csv")
    st.download_button("Download markdown report", data=md, file_name="incident_report.md")
    st.download_button("Download structured JSON report", data=js, file_name="incident_report.json")
