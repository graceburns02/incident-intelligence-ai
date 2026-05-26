from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.utils import normalize_severity

REQUIRED_COLUMNS = [
    "incident_id",
    "created_at",
    "title",
    "description",
    "severity",
    "status",
    "system_area",
    "customer_impact",
]


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def apply_column_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    rename_dict = {src: dst for src, dst in mapping.items() if src in df.columns and dst}
    return df.rename(columns=rename_dict)


def validate_incident_dataframe(df: pd.DataFrame) -> ValidationResult:
    result = ValidationResult(valid=True)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        result.valid = False
        result.errors.append(f"Missing required columns: {', '.join(missing)}")
    if "incident_id" in df.columns and df["incident_id"].duplicated().any():
        result.warnings.append("Duplicate incident_id values detected.")
    return result


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "severity" in out.columns:
        out["severity"] = out["severity"].apply(normalize_severity)
    return out
