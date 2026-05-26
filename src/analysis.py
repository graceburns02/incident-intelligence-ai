from __future__ import annotations

import json
import logging
import re
from collections import defaultdict

from openai import OpenAI
from pydantic import ValidationError

from src.schemas import ClusterAnalysisResult
from src.utils import safe_json_loads

logger = logging.getLogger(__name__)


def group_incidents_by_cluster(df, labels):
    grouped = defaultdict(list)
    for idx, (_, row) in enumerate(df.iterrows()):
        grouped[int(labels[idx])].append(row.to_dict())
    return dict(grouped)


def _extract_json_text(raw_text: str) -> str:
    text = (raw_text or "").strip()
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


def _status_from_confidence(confidence_score: float) -> str:
    return "accepted" if confidence_score >= 0.75 else "needs_investigation"


def _normalize_parsed_data(cluster_id: int, parsed_data: dict | None) -> dict:
    parsed_data = dict(parsed_data or {})
    parsed_data["cluster_id"] = cluster_id
    parsed_data.setdefault("cluster_title", "Untitled cluster")
    parsed_data.setdefault("issue_summary", "")
    parsed_data.setdefault("likely_root_cause", "")
    parsed_data.setdefault("severity_assessment", "unknown")
    parsed_data.setdefault("supporting_evidence", [])
    parsed_data.setdefault("recommended_actions", [])
    parsed_data.setdefault("confidence_score", 0.5)

    if not isinstance(parsed_data["supporting_evidence"], list):
        parsed_data["supporting_evidence"] = [str(parsed_data["supporting_evidence"])]
    if not isinstance(parsed_data["recommended_actions"], list):
        parsed_data["recommended_actions"] = [str(parsed_data["recommended_actions"])]

    try:
        parsed_data["confidence_score"] = float(parsed_data["confidence_score"])
    except Exception:
        parsed_data["confidence_score"] = 0.5

    parsed_data["review_status"] = _status_from_confidence(parsed_data["confidence_score"])
    return parsed_data


def _chat_completion(client: OpenAI, model: str, prompt: str, method_label: str = "analysis") -> str:
    logger.info("cluster_analysis request model=%s method=chat.completions purpose=%s", model, method_label)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an operations analyst. Return only valid JSON. No markdown. No commentary."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    raw_output = (response.choices[0].message.content or "").strip()
    logger.info("cluster_analysis raw_response purpose=%s: %s", method_label, raw_output)
    return raw_output


def analyze_cluster_with_llm(client: OpenAI, cluster_id: int, incidents: list[dict], model: str):
    schema_example = {
        "cluster_id": cluster_id,
        "cluster_title": "Authentication timeouts in checkout",
        "issue_summary": "Checkout API is timing out for a subset of users during peak windows.",
        "likely_root_cause": "Connection pool exhaustion after recent config change.",
        "supporting_evidence": ["Spike in timeout errors after 14:00 UTC", "DB connections saturated at 100%"],
        "recommended_actions": ["Roll back pool size config", "Add alert for pool saturation"],
        "severity_assessment": "high",
        "confidence_score": 0.82,
        "review_status": "accepted",
    }
    prompt = (
        "Analyze the incident cluster and return JSON matching this exact schema and field names only:\n"
        f"{json.dumps(schema_example, indent=2)}\n\n"
        f"Cluster ID: {cluster_id}\nIncidents:\n{json.dumps(incidents, indent=2)}"
    )

    raw_output = ""
    parse_errors: list[str] = []
    used_repair = False
    try:
        raw_output = _chat_completion(client, model, prompt)
    except Exception as e:
        logger.exception("cluster_analysis exception during primary request")
        parse_errors.append(f"OpenAI request failed: {e}")
        fallback = ClusterAnalysisResult(cluster_id=cluster_id, issue_summary="Manual review required due to model request failure.")
        return fallback, {"raw_response": raw_output, "parse_errors": parse_errors, "used_repair": used_repair, "used_fallback": True}

    parsed_data = None
    try:
        parsed_data = safe_json_loads(_extract_json_text(raw_output))
    except Exception as e:
        logger.exception("cluster_analysis parse failure")
        parse_errors.append(f"Initial JSON parse failed: {e}")

    if parsed_data is None:
        used_repair = True
        repair_prompt = (
            "Convert the following text into valid JSON matching this schema exactly.\n"
            f"{json.dumps(schema_example, indent=2)}\n\n"
            f"Text:\n{raw_output}"
        )
        try:
            repair_raw = _chat_completion(client, model, repair_prompt, method_label="repair")
            raw_output = raw_output + "\n\n--- JSON_REPAIR_ATTEMPT ---\n" + repair_raw
            parsed_data = safe_json_loads(_extract_json_text(repair_raw))
        except Exception as e:
            logger.exception("cluster_analysis repair failure")
            parse_errors.append(f"Repair attempt failed: {e}")

    try:
        normalized = _normalize_parsed_data(cluster_id, parsed_data)
        parsed = ClusterAnalysisResult.model_validate(normalized)
    except ValidationError as e:
        logger.exception("cluster_analysis validation failure")
        parse_errors.append(f"Schema validation failed: {e}")
        fallback = ClusterAnalysisResult(cluster_id=cluster_id, issue_summary="Manual review required due to parsing failure.")
        return fallback, {"raw_response": raw_output, "parse_errors": parse_errors, "used_repair": used_repair, "used_fallback": True}

    logger.info("cluster_analysis validation passed cluster_id=%s", cluster_id)
    return parsed, {"raw_response": raw_output, "parse_errors": parse_errors, "used_repair": used_repair, "used_fallback": False}


def analyze_clusters(df, labels, api_key: str, model: str = "gpt-4.1-mini"):
    client = OpenAI(api_key=api_key)
    grouped = group_incidents_by_cluster(df, labels)
    results = []
    raw = {}
    for cid, incidents in grouped.items():
        parsed, raw_output = analyze_cluster_with_llm(client, cid, incidents, model)
        results.append(parsed)
        raw[cid] = raw_output
    return results, grouped, raw
