import hashlib
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .contracts import canonical


def render_report(run):
    # Input is restricted to reviewed aggregate data; omit identities, feedback and internal source rows.
    payload = {
        "config": run["config"],
        "periods": run["facts"],
        "version": run["version"],
        "correction": run["correction"],
        "summary": run["draft"]["summary"],
    }
    root = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(root / "templates"), autoescape=select_autoescape(["html"]))
    text = canonical(payload).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return (
        env.get_template("report.html")
        .render(
            brand=run["config"]["brand"],
            version=run["version"],
            data=text,
            css=(root / "static/report.css").read_text(encoding="utf-8"),
            js=(root / "static/report.js").read_text(encoding="utf-8"),
        )
        .encode("utf-8")
    )


def publish_report(repo, actor, run_id, destination):
    if actor.role not in ("review", "delivery"):
        raise PermissionError("delivery denied")
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    def publish(run):
        approval = run.get("approval")
        if run["artifact"]:
            artifact = run["artifact"]
            path = Path(artifact["path"])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
                raise ValueError("published artifact integrity failure")
            return "delivery_retry"
        if run["status"] != "approved" or not approval or not approval["approved"]:
            raise ValueError("review approval required")
        if approval["draft_hash"] != run["draft_hash"]:
            raise ValueError("stale approval")
        content = render_report(run)
        checksum = hashlib.sha256(content).hexdigest()
        # Opaque UUID avoids untrusted filenames and cross-client name collisions.
        if not re.fullmatch(r"[a-f0-9-]{36}", run_id):
            raise ValueError("invalid run identifier")
        path = destination / f"{run_id}-v{run['version']}.html"
        try:
            with path.open("xb") as stream:
                stream.write(content)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError("immutable artifact conflict")
        run["artifact"] = {"path": str(path), "sha256": checksum, "version": run["version"]}
        run["status"] = "delivered"
        return "report_delivered"

    updated = repo.mutate(actor, run_id, publish)
    return updated["artifact"]
