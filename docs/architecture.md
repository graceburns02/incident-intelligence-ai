# Architecture — Incident Intelligence AI

## System Diagram
```text
CSV Upload/Sample -> Validation & Mapping -> Embeddings -> Clustering -> LLM Cluster Analysis
      -> Human Review Edits/Decisions -> Export (CSV/MD/JSON)
```

## Module Responsibilities
- `app.py`: UI orchestration and workflow control
- `src/data_loader.py`: CSV/sample loading
- `src/validation.py`: required columns, mapping, normalization checks
- `src/embeddings.py`: OpenAI embeddings generation
- `src/clustering.py`: KMeans cluster assignment
- `src/analysis.py`: LLM cluster analysis with structured output + fallback
- `src/schemas.py`: strict Pydantic domain models
- `src/export.py`: report serialization
- `src/utils.py`: shared helpers

## Data Flow
Records are normalized, embedded, clustered, then passed cluster-by-cluster to LLM for structured analysis. Human reviewers can override root cause/remediation/status prior to export.

## Failure Modes
- Missing API key
- Invalid CSV/missing columns
- Embedding API failures or quota limits
- LLM schema mismatch/parsing errors

## Dependency Overview
Streamlit UI, OpenAI API, pandas manipulation, scikit-learn clustering, Pydantic validation, Plotly charts, pytest coverage.
