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


class RootCauseAnalysis(StrictBaseModel):
    likely_root_cause: Optional[str] = None
    supporting_evidence: list[str] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class RemediationAction(StrictBaseModel):
    action: str
    owner_team: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None


class ClusterAnalysisResult(StrictBaseModel):
    cluster_id: int
    cluster_title: Optional[str] = None
    issue_summary: Optional[str] = None
    severity_assessment: Optional[str] = None
    root_cause: RootCauseAnalysis = Field(default_factory=RootCauseAnalysis)
    remediation_actions: list[RemediationAction] = Field(default_factory=list)
    recommendation_status: Literal["accepted", "rejected", "needs investigation"] = "needs investigation"


class FullAnalysisReport(StrictBaseModel):
    generated_at: datetime
    total_incidents: int
    cluster_count: int
    analysis_results: list[ClusterAnalysisResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
