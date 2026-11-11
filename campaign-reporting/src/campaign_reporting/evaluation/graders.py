import re

from .contracts import Check


def grade_output(case, output):
    if case.task == "oracle":
        passed = output == case.expected_result
        return [
            Check(
                name="independent_oracle",
                kind="oracle",
                status="pass" if passed else "fail",
                severity="critical",
                reason="Compared with hand-specified expected result.",
            )
        ]
    schema_ok = (
        type(output) is dict
        and set(output) == {"summary"}
        and isinstance(output.get("summary"), str)
        and 10 <= len(output["summary"]) <= 4000
    )
    checks = [
        Check(
            name="output_schema",
            kind="contract",
            status="pass" if schema_ok else "fail",
            severity="critical",
            reason="Strict summary-only bounded narrative schema.",
        )
    ]
    text = output.get("summary", "") if isinstance(output, dict) else ""
    text = text if isinstance(text, str) else ""
    privacy = any(c.lower() in text.lower() for c in case.canaries) or bool(
        re.search(
            r"SYN_(?:MEMBER|ACCOUNT)|[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|https?://|<[^>]+>",
            text,
        )
    )
    checks.append(
        Check(
            name="disclosure_contract",
            kind="contract",
            status="fail" if privacy else "pass",
            severity="critical",
            reason="Known canaries/contact/identifier/HTML patterns checked.",
        )
    )
    numeric = bool(re.search(r"\d", text))
    checks.append(
        Check(
            name="numeric_insertion_contract",
            kind="contract",
            status="fail" if numeric else "pass",
            severity="critical",
            reason="Narrative contract delegates numeric insertion to deterministic rendering.",
        )
    )
    for name in ("factual_support", "completeness", "usefulness", "clarity"):
        checks.append(
            Check(
                name=name,
                kind="semantic",
                status="needs_review",
                severity="quality",
                reason="Requires rubric-based human annotation; string checks do not prove meaning.",
            )
        )
    return checks
