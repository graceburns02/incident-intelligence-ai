from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from src.schemas import FullAnalysisReport


def build_report(results, total_incidents: int) -> FullAnalysisReport:
    return FullAnalysisReport(
        generated_at=datetime.utcnow(),
        total_incidents=total_incidents,
        cluster_count=len(results),
        analysis_results=results,
    )


def cluster_results_to_dataframe(results) -> pd.DataFrame:
    rows = []
    for r in results:
        rows.append(
            {
                "cluster_id": r.cluster_id,
                "cluster_title": r.cluster_title,
                "issue_summary": r.issue_summary,
                "likely_root_cause": r.likely_root_cause,
                "confidence_score": r.confidence_score,
                "severity_assessment": r.severity_assessment,
                "review_status": r.review_status,
                "recommended_actions": "; ".join(r.recommended_actions),
            }
        )
    return pd.DataFrame(rows)


def to_markdown_report(report: FullAnalysisReport) -> str:
    lines = [
        "# Incident Intelligence AI Report",
        f"Generated at: {report.generated_at.isoformat()}",
        f"Total incidents: {report.total_incidents}",
        f"Cluster count: {report.cluster_count}",
        "",
    ]
    for r in report.analysis_results:
        lines += [
            f"## Cluster {r.cluster_id}: {r.cluster_title or 'Untitled'}",
            f"Summary: {r.issue_summary or 'N/A'}",
            f"Root cause: {r.likely_root_cause or 'N/A'}",
            f"Confidence: {r.confidence_score}",
            f"Status: {r.review_status}",
            "",
        ]
    return "\n".join(lines)


def to_json_report(report: FullAnalysisReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2)
