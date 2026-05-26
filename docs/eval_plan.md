# Evaluation Plan — Incident Intelligence AI

## Clustering Quality Metrics
- Silhouette score (offline)
- Theme coherence spot checks
- Incident duplicate-collapse ratio

## Root Cause Quality Review
- Reviewer scorecard (accuracy, actionability, evidence quality)
- % clusters requiring substantial rewrite

## Remediation Acceptance Rate
- accepted / (accepted + rejected + needs investigation)

## Human Correction Rate
- % clusters where root cause/remediation edited by reviewer

## Latency and Cost Tracking
- End-to-end batch analysis time
- Tokens and embedding cost per 100 incidents

## Benchmark Dataset Approach
- Synthetic seeded datasets with known themes
- Incrementally noisier datasets to test robustness
