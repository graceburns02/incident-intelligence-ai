from __future__ import annotations

import json
from collections import defaultdict

from openai import OpenAI
from pydantic import ValidationError

from src.schemas import ClusterAnalysisResult
from src.utils import safe_json_loads


def group_incidents_by_cluster(df, labels):
    grouped = defaultdict(list)
    for idx, (_, row) in enumerate(df.iterrows()):
        grouped[int(labels[idx])].append(row.to_dict())
    return dict(grouped)


def _schema_dict():
    schema = ClusterAnalysisResult.model_json_schema()
    schema["additionalProperties"] = False
    if "$defs" in schema:
        for v in schema["$defs"].values():
            if isinstance(v, dict) and v.get("type") == "object":
                v["additionalProperties"] = False
    return schema


def analyze_cluster_with_llm(client: OpenAI, cluster_id: int, incidents: list[dict], model: str):
    prompt = (
        "You are an incident intelligence assistant for operations teams. "
        "Provide decision support with evidence and uncertainty. "
        f"Cluster ID: {cluster_id}\nIncidents:\n{json.dumps(incidents, indent=2)}"
    )
    raw_output = ""
    try:
        resp = client.responses.create(
            model=model,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "cluster_analysis_result",
                    "schema": _schema_dict(),
                    "strict": True,
                }
            },
        )
        raw_output = resp.output_text
        data = safe_json_loads(raw_output)
    except Exception:
        resp = client.responses.create(
            model=model,
            input=prompt + "\nReturn JSON only matching ClusterAnalysisResult schema.",
            response_format={"type": "json_object"},
        )
        raw_output = resp.output_text
        data = safe_json_loads(raw_output)
    try:
        parsed = ClusterAnalysisResult.model_validate(data)
    except ValidationError:
        parsed = ClusterAnalysisResult(cluster_id=cluster_id, issue_summary="Manual review required due to parsing failure.")
    return parsed, raw_output


def analyze_clusters(df, labels, api_key: str, model: str = "gpt-4.1-mini"):
    client = OpenAI(api_key=api_key)
    grouped = group_incidents_by_cluster(df, labels)
    results = []
    raw = {}
    for cid, incidents in grouped.items():
        parsed, raw_output = analyze_cluster_with_llm(client, cid, incidents, model)
        if parsed.cluster_id != cid:
            parsed.cluster_id = cid
        results.append(parsed)
        raw[cid] = raw_output
    return results, grouped, raw
