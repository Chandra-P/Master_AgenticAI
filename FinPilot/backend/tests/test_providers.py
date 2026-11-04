import json
from types import SimpleNamespace
from finpilot.providers import plan_with_openai, redact, publish_trace


def test_redaction():
    safe = redact(
        {"key": "sk-VERYSECRET123", "email": "alex@example.com", "account": "123456789012"}
    )
    assert "VERYSECRET" not in json.dumps(safe)
    assert "@" not in json.dumps(safe)
    assert "123456789012" not in json.dumps(safe)


def test_missing_key_falls_back(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    route, mode, error = plan_with_openai("How much did I spend?", "sql")
    assert route == "sql" and mode == "deterministic fallback" and error


def test_openai_structured_tool_contract(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-real")
    import openai

    observed = {}

    class Client:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=self)

        def create(self, **kwargs):
            observed.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            tool_calls=[
                                SimpleNamespace(
                                    function=SimpleNamespace(arguments='{"route":"rag"}')
                                )
                            ]
                        )
                    )
                ]
            )

    monkeypatch.setattr(openai, "OpenAI", Client)
    assert plan_with_openai("What APR is offered?", "rag")[:2] == ("rag", "OpenAI tool calling")
    assert observed["tools"][0]["function"]["strict"]
    assert observed["tool_choice"]["function"]["name"] == "select_route"
    # Even a model-selected route cannot resolve an unidentified purchase.
    assert plan_with_openai("Can I afford it?", "clarification")[0] == "clarification"


def test_langsmith_trace_excludes_private_data(monkeypatch):
    import langsmith

    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-only-not-real")
    captured = []

    class Client:
        def __init__(self, **kwargs):
            pass

        def create_run(self, **kwargs):
            captured.append(kwargs)

    monkeypatch.setattr(langsmith, "Client", Client)
    result = {
        "id": "9e535432-1093-4c41-a763-82c2a0b3b9e8",
        "question": "secret bank details",
        "route": "sql",
        "mode": "deterministic",
        "validation": {"passed": True, "errors": ["private proposed amount $12345"]},
        "completeness": "complete evidence",
        "tools": ["get_cash_position"],
        "latency_ms": 5,
        "events": [{"tool": "get_cash_position", "status": "complete"}],
    }
    assert publish_trace(result).startswith("sent")
    assert len(captured) == 2
    text = json.dumps(captured, default=str)
    assert "secret bank details" not in text
    assert "private proposed amount" not in text
    assert captured[1]["parent_run_id"] == captured[0]["id"]
