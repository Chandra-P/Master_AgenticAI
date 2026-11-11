"""Metadata-only events. Payloads and arbitrary exception text never enter exporters."""

import json
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from time import perf_counter

from opentelemetry import trace

SAFE = {"item_count", "attempt", "input_tokens", "output_tokens", "prompt_version", "model", "adapter"}
_LOCK = Lock()


class Telemetry:
    def __init__(self, path, exporter=None):
        self.path, self.exporter = Path(path), exporter
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def span(self, name, run_id, origin="application", attributes=None):
        start = perf_counter()
        event = {
            "name": name,
            "run_id": run_id,
            "origin": origin,
            "span_id": str(uuid.uuid4()),
            "started_at": datetime.now(UTC).isoformat(),
            "status": "ok",
            "attributes": {
                k: v for k, v in (attributes or {}).items() if k in SAFE and isinstance(v, (str, int, float))
            },
        }
        # Auto tracing integrations are intentionally not used: they may capture bodies.
        with trace.get_tracer("campaign-reporting").start_as_current_span(name, record_exception=False):
            try:
                yield event
            except BaseException as exc:
                event["status"] = "error"
                event["error_category"] = type(exc).__name__
                raise
            finally:
                event["duration_ms"] = round((perf_counter() - start) * 1000, 3)
                with _LOCK, self.path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(event) + "\n")
                if self.exporter:
                    try:
                        self.exporter(dict(event))
                    except Exception:  # noqa: BLE001 -- exporter errors may contain sensitive payloads
                        # Record a fixed category, never the provider's exception message.
                        with _LOCK, self.path.open("a", encoding="utf-8") as stream:
                            stream.write(
                                json.dumps(
                                    {"name": "telemetry_export_failed", "run_id": run_id, "status": "error"}
                                )
                                + "\n"
                            )


def langsmith_exporter(project):
    from langsmith import Client

    client = Client(hide_inputs=True, hide_outputs=True, hide_metadata=True)

    def export(event):
        client.create_run(
            name=event["name"],
            run_type="tool",
            inputs={},
            outputs={},
            project_name=project,
            id=uuid.UUID(event["span_id"]),
            start_time=datetime.fromisoformat(event["started_at"]),
            end_time=datetime.now(UTC),
            error=event.get("error_category"),
        )

    return export
