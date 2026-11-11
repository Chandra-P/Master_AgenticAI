from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .review import record_review_decision, save_draft
from .tools import ReportTools


class ReviewState(TypedDict):
    run_id: str
    status: str


def offline_narrative(metrics, flags):
    lead = "This version reflects corrected synthetic source data. " if flags["correction"] else ""
    return {
        "summary": lead + "Review the measured Checking and new-member results against their separate goals. "
        "Use the historical scenario range to assess the remaining uncertainty. Channel overlap describes "
        "matched exposure and does not establish incremental lift. No budget or delivery changes are executed "
        "by this report. This interpretation was produced by the offline narrative adapter."
    }


@contextmanager
def review_graph(repo, actor, checkpoint_path, adapter=None):
    tools = ReportTools(repo, actor)

    def draft(state):
        run = repo.get_run(actor, state["run_id"])
        if run["status"] in ("approved", "delivered"):
            return {"status": run["status"]}
        if run["revision"] >= 5:
            raise ValueError("draft regeneration limit reached")
        metrics = tools.get_metrics(state["run_id"])
        flags = tools.get_flag_status(state["run_id"])
        tools.get_rules_context(state["run_id"])
        tools.get_prior_version(state["run_id"])
        draft_text = (adapter or offline_narrative)(metrics, flags)
        save_draft(repo, actor, state["run_id"], draft_text)
        return {"status": "review"}

    def human_review(state):
        run = repo.get_run(actor, state["run_id"])
        if run["status"] in ("approved", "delivered"):
            return {"status": run["status"]}
        decision = interrupt({"run_id": state["run_id"], "draft_hash": run["draft_hash"]})
        # A graph resume payload is not authority; the authenticated service validates the exact draft.
        approved = record_review_decision(
            repo, actor, state["run_id"], decision["draft_hash"], decision["approved"]
        )
        return {"status": approved["status"]}

    builder = StateGraph(ReviewState)
    builder.add_node("draft", draft)
    builder.add_node("human_review", human_review)
    builder.add_edge(START, "draft")
    builder.add_edge("draft", "human_review")
    builder.add_conditional_edges("human_review", lambda s: "draft" if s["status"] == "rejected" else END)
    path = Path(checkpoint_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(path)) as saver:
        yield builder.compile(checkpointer=saver)


def start_review(repo, actor, run_id, checkpoint_path, adapter=None):
    repo.get_run(actor, run_id)  # authorize before using a thread/checkpoint
    with review_graph(repo, actor, checkpoint_path, adapter) as graph:
        config = {"configurable": {"thread_id": run_id}}
        existing = graph.get_state(config)
        if existing.values and existing.next:
            return existing.values
        return graph.invoke({"run_id": run_id, "status": "computed"}, config)


def resume_review(repo, actor, run_id, checkpoint_path, draft_hash, approved):
    if actor.role != "review":
        raise PermissionError("review role required")
    run = repo.get_run(actor, run_id)
    if run["draft_hash"] != draft_hash:
        raise ValueError("stale draft")
    with review_graph(repo, actor, checkpoint_path) as graph:
        return graph.invoke(
            Command(resume={"draft_hash": draft_hash, "approved": approved}),
            {"configurable": {"thread_id": run_id}},
        )
