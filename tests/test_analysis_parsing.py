from src.analysis import _extract_json_text, _normalize_parsed_data, _status_from_confidence, analyze_cluster_with_llm


class DummyChoice:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})


class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]


class DummyClient:
    def __init__(self, contents):
        self._contents = list(contents)
        self.chat = type("Chat", (), {"completions": self})

    def create(self, **kwargs):
        return DummyResponse(self._contents.pop(0))


def test_successful_raw_json_parse():
    text = '{"cluster_id":1,"cluster_title":"t"}'
    assert _extract_json_text(text).startswith("{")


def test_markdown_wrapped_json_parse():
    text = "```json\n{\"cluster_id\":1,\"cluster_title\":\"t\"}\n```"
    assert _extract_json_text(text) == '{"cluster_id":1,"cluster_title":"t"}'


def test_missing_optional_fields_are_filled():
    normalized = _normalize_parsed_data(2, {"issue_summary": "x"})
    assert normalized["supporting_evidence"] == []
    assert normalized["recommended_actions"] == []


def test_fallback_only_after_failed_retry():
    client = DummyClient(["not json", "still not json"])
    parsed, raw = analyze_cluster_with_llm(client, 3, [{"a": 1}], "gpt-4.1-mini")
    assert raw["used_repair"] is True
    assert raw["used_fallback"] is True
    assert "Manual review required" in parsed.issue_summary


def test_review_status_assignment_based_on_confidence():
    assert _status_from_confidence(0.9) == "accepted"
    assert _status_from_confidence(0.7) == "needs_investigation"
    assert _status_from_confidence(0.2) == "needs_investigation"
