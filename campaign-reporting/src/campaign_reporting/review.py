from .contracts import digest
from .repository import now


def save_draft(repo, actor, run_id, draft):
    if actor.role not in ("review", "compute"):
        raise PermissionError("draft write denied")
    if set(draft) != {"summary"} or not isinstance(draft["summary"], str) or len(draft["summary"]) > 4000:
        raise ValueError("invalid narrative schema")

    def change(run):
        if run["artifact"]:
            raise ValueError("published run is immutable; create a correction run")
        run.update(
            draft=draft,
            draft_hash=digest([run["identity_hash"], draft]),
            status="review",
            approval=None,
            revision=run["revision"] + 1,
        )
        return "draft_saved"

    return repo.mutate(actor, run_id, change)


def record_review_decision(repo, actor, run_id, draft_hash, approved, feedback=""):
    if actor.role != "review":
        raise PermissionError("review permission required")
    if type(approved) is not bool:
        raise ValueError("decision must be boolean")

    def change(run):
        if run["draft_hash"] != draft_hash or not run["draft"]:
            raise ValueError("stale or missing draft")
        if run["artifact"]:
            raise ValueError("published run is immutable")
        if run["status"] == "approved" and approved:
            return "approval_retry"
        run["status"] = "approved" if approved else "rejected"
        run["approval"] = {
            "actor_id": actor.actor_id,
            "draft_hash": draft_hash,
            "approved": approved,
            "at": now(),
        }
        # Restricted operational record only; never add free text to prompts or traces.
        run["feedback"] = feedback[:2000]
        return "approved" if approved else "rejected"

    return repo.mutate(actor, run_id, change)
