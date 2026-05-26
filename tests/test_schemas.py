from datetime import datetime

from src.export import build_report, to_markdown_report
from src.schemas import ClusterAnalysisResult, FullAnalysisReport


def test_schema_creation():
    item = ClusterAnalysisResult(cluster_id=1, issue_summary="x")
    report = FullAnalysisReport(generated_at=datetime.utcnow(), total_incidents=2, cluster_count=1, analysis_results=[item])
    assert report.analysis_results[0].cluster_id == 1


def test_export_markdown_formatting():
    item = ClusterAnalysisResult(cluster_id=2, cluster_title="Auth")
    report = build_report([item], total_incidents=10)
    md = to_markdown_report(report)
    assert "Incident Intelligence AI Report" in md
    assert "Cluster 2" in md
