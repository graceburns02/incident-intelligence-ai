import pandas as pd

from src.validation import normalize_dataframe, validate_incident_dataframe


def base_df():
    return pd.DataFrame([
        {
            "incident_id": "1",
            "created_at": "2026-01-01",
            "title": "x",
            "description": "y",
            "severity": "SEV1",
            "status": "open",
            "system_area": "auth",
            "customer_impact": "login broken",
        }
    ])


def test_validation_passes_for_required_columns():
    result = validate_incident_dataframe(base_df())
    assert result.valid


def test_validation_fails_on_missing_required_columns():
    df = base_df().drop(columns=["title"])
    result = validate_incident_dataframe(df)
    assert not result.valid


def test_severity_normalization():
    out = normalize_dataframe(base_df())
    assert out.loc[0, "severity"] == "high"
