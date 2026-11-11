import os
from datetime import date

from ..budget import BudgetExceeded
from ..contracts import digest
from ..openai_adapter import SYSTEM, OpenAINarrative
from .runner import EvaluationBlocked


class LiveTarget:
    """Explicit opt-in; no provider client or API request before preflight checks."""

    prompt_hash = digest(SYSTEM)

    def __init__(self, runtime):
        self.runtime = runtime
        self.run_id = "eval"
        self.last_usage = {}

    def __call__(self, case):
        self.last_usage = {}
        required = (
            "OPENAI_API_KEY",
            "OPENAI_MODEL",
            "OPENAI_INPUT_USD_PER_MILLION",
            "OPENAI_OUTPUT_USD_PER_MILLION",
            "OPENAI_PRICING_REVIEWED",
        )
        if os.environ.get("ENABLE_OPENAI") != "1" or not all(os.environ.get(k) for k in required):
            raise EvaluationBlocked("secure live configuration unavailable")
        try:
            age = (date.today() - date.fromisoformat(os.environ["OPENAI_PRICING_REVIEWED"])).days
        except ValueError:
            raise EvaluationBlocked("pricing review required") from None
        if not 0 <= age <= 30:
            raise EvaluationBlocked("pricing review expired")
        adapter = OpenAINarrative(self.runtime, self.run_id, allow_untrusted_context=True)
        facts = case.facts.model_dump()
        metrics = {
            "periods": {case.period: facts},
            "goals": {"checking": facts["checking_goal"], "members": facts["member_goal"]},
            "untrusted_context": case.untrusted_context,
        }
        try:
            return adapter(metrics, {"correction": facts["correction"]})
        except BudgetExceeded:
            raise EvaluationBlocked("shared POC budget exhausted") from None
        finally:
            self.last_usage = dict(adapter.last_usage)
