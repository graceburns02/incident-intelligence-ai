from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IncidentRecord(StrictBaseModel):
    incident_id: str
    created_at: Optional[datetime] = None
    title: str
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    system_area: Optional[str] = None
    customer_impact: Optional[str] = None


class IncidentCluster(StrictBaseModel):
    cluster_id: int
    incident_ids: list[str] = Field(default_factory=list)
    representative_theme: Optional[str] = None


class ClusterAnalysisResult(StrictBaseModel):
    cluster_id: int
    cluster_title: str = "Untitled cluster"
    issue_summary: str = ""
    likely_root_cause: str = ""
    supporting_evidence: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    severity_assessment: str = "unknown"
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    review_status: Literal["accepted", "needs_investigation", "rejected"] = "needs_investigation"


class FullAnalysisReport(StrictBaseModel):
    generated_at: datetime
    total_incidents: int
    cluster_count: int
    analysis_results: list[ClusterAnalysisResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
