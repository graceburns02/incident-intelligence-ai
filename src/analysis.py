from __future__ import annotations

import json
import re
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


def _extract_json_text(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()

    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            _, end = decoder.raw_decode(text[i:])
            return text[i : i + end]
        except Exception:
            continue
    return text


def _request_cluster_analysis(client: OpenAI, model: str, prompt: str):
    """
    Compatibility note:
    - Chat Completions historically used response_format/json schema options differently.
    - Responses API currently supports structured outputs through text.format json_schema,
      while older or mismatched SDK/server combinations may reject those params.
    """
    try:
        return client.responses.create(
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
    except TypeError:
        # SDK/version incompatibility fallback: prompt-only JSON generation.
        return client.responses.create(
            model=model,
            input=prompt + "\nReturn JSON only that matches ClusterAnalysisResult schema.",
        )


def analyze_cluster_with_llm(client: OpenAI, cluster_id: int, incidents: list[dict], model: str):
    prompt = (
        "You are an incident intelligence assistant for operations teams. "
        "Provide decision support with evidence and uncertainty. "
        "Output strict JSON only, no markdown fences, no prose. "
        f"Cluster ID: {cluster_id}\nIncidents:\n{json.dumps(incidents, indent=2)}"
    )

    raw_output = ""
    parse_errors: list[str] = []
    used_repair = False
    try:
        resp = _request_cluster_analysis(client, model, prompt)
        raw_output = getattr(resp, "output_text", "") or ""
    except Exception as e:
        parse_errors.append(f"OpenAI request failed: {e}")
        fallback = ClusterAnalysisResult(cluster_id=cluster_id, issue_summary="Manual review required due to model request failure.")
        return fallback, {"raw_response": raw_output, "parse_errors": parse_errors, "used_repair": used_repair}

    parsed_data = None
    json_text = _extract_json_text(raw_output)
    try:
        parsed_data = safe_json_loads(json_text)
    except Exception as e:
        parse_errors.append(f"Initial JSON parse failed: {e}")

    if parsed_data is None:
        used_repair = True
        repair_prompt = (
            "Repair the following content into valid JSON only that matches the ClusterAnalysisResult schema. "
            "Do not include markdown or explanation.\n\n"
            f"Original content:\n{raw_output}"
        )
        try:
            repair_resp = client.responses.create(model=model, input=repair_prompt)
            repair_raw = getattr(repair_resp, "output_text", "") or ""
            raw_output = raw_output + "\n\n--- JSON_REPAIR_ATTEMPT ---\n" + repair_raw
            parsed_data = safe_json_loads(_extract_json_text(repair_raw))
        except Exception as e:
            parse_errors.append(f"Repair attempt failed: {e}")

    try:
        parsed = ClusterAnalysisResult.model_validate(parsed_data or {})
    except ValidationError as e:
        parse_errors.append(f"Schema validation failed: {e}")
        parsed = ClusterAnalysisResult(cluster_id=cluster_id, issue_summary="Manual review required due to parsing failure.")

    return parsed, {"raw_response": raw_output, "parse_errors": parse_errors, "used_repair": used_repair}


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
