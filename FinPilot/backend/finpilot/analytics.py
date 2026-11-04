"""Approved parameterized SQL tools. All date ranges are [start, end)."""

import json
from datetime import date
from decimal import Decimal
from .db import AS_OF
from .money import dollars, fmt

EXCLUSIONS = [
    "internal transfers",
    "pending",
    "duplicate copies",
    "reversed",
    "future-dated beyond as-of date",
    "excluded accounts",
]


def month_bounds(offset=-1):
    anchor = date.fromisoformat(AS_OF)
    n = anchor.year * 12 + anchor.month - 1 + offset
    y, m = divmod(n, 12)
    start = date(y, m + 1, 1)
    end = date(y + 1, 1, 1) if m == 11 else date(y, m + 2, 1)
    return start.isoformat(), end.isoformat()


class Analytics:
    def __init__(self, conn, user_id="demo"):
        self.conn, self.user_id = conn, user_id

    def memory(self):
        row = self.conn.execute(
            "SELECT * FROM user_preferences WHERE user_id=?", (self.user_id,)
        ).fetchone()
        if not row:
            raise ValueError("User preferences unavailable")
        r = dict(row)
        r["emergency_fund_minimum"] = dollars(r["emergency_fund_minimum"])
        r["rules"] = json.loads(r["rules"])
        r["excluded_accounts"] = json.loads(r["excluded_accounts"])
        goal = self.conn.execute(
            "SELECT target_amount,current_amount FROM financial_goals WHERE user_id=? AND id=?",
            (self.user_id, "house"),
        ).fetchone()
        r["house_goal"] = (
            {
                "target_amount": dollars(goal["target_amount"]),
                "current_amount": dollars(goal["current_amount"]),
            }
            if goal
            else None
        )
        r["source"] = "User-approved structured memory (demo defaults until confirmed)"
        return r

    def _rows(self, start, end, category=None, merchant=None):
        date.fromisoformat(start)
        date.fromisoformat(end)
        if start >= end:
            raise ValueError("Start must precede end")
        excluded = self.memory()["excluded_accounts"]
        sql = """SELECT t.* FROM transactions t JOIN accounts a ON a.id=t.account_id
        WHERE a.user_id=? AND t.posted_date>=? AND t.posted_date<? AND t.posted_date<=?
        AND t.is_pending=0 AND t.is_internal_transfer=0 AND t.is_reversed=0
        AND t.duplicate_group_id IS NULL AND a.is_active=1"""
        params = [self.user_id, start, end, AS_OF]
        if category:
            sql += " AND lower(t.category)=lower(?)"
            params.append(category)
        if merchant:
            alias = self.conn.execute(
                "SELECT normalized FROM merchant_aliases WHERE lower(alias)=lower(?)", (merchant,)
            ).fetchone()
            sql += " AND lower(t.merchant_normalized)=lower(?)"
            params.append(alias["normalized"] if alias else merchant)
        return [
            dict(r)
            for r in self.conn.execute(sql, params).fetchall()
            if r["account_id"] not in excluded
        ]

    def _result(self, value, rows, start=None, end=None, definition="", **extra):
        return {
            "value": value,
            "currency": "USD",
            "period": {"start": start, "end_exclusive": end},
            "included_record_count": len(rows),
            "exclusion_rules": EXCLUSIONS,
            "calculation_definition": definition,
            "data_as_of": AS_OF,
            "completeness": "no matching data" if not rows else "complete evidence",
            "filters": {},
            **extra,
        }

    def get_spending_by_category(self, start, end, category=None):
        rows = [r for r in self._rows(start, end, category) if r["transaction_type"] == "expense"]
        groups = {}
        for row in rows:
            groups[row["category"]] = groups.get(row["category"], 0) + row["amount"]
        return self._result(
            dollars(sum(r["amount"] for r in rows)) if rows else None,
            rows,
            start,
            end,
            "SUM(posted expense cents), refunds reduce expense",
            items=[
                {"category": k, "amount": dollars(v)}
                for k, v in sorted(groups.items(), key=lambda x: -x[1])
            ],
            filters={"category": category},
        )

    def compare_category_spending(self, start_a, end_a, start_b, end_b, category):
        a = self.get_spending_by_category(start_a, end_a, category)
        b = self.get_spending_by_category(start_b, end_b, category)
        av, bv = a["value"], b["value"]
        diff = Decimal(bv) - Decimal(av) if av is not None and bv is not None else None
        return {
            "previous": a,
            "current": b,
            "difference": fmt(diff) if diff is not None else None,
            "percent_change": fmt(diff / Decimal(av) * 100)
            if diff is not None and Decimal(av) != 0
            else None,
            "currency": "USD",
            "calculation_definition": "(current - previous) / previous * 100; undefined for zero or missing baseline",
        }

    def get_spending_by_merchant(self, merchant, start, end):
        rows = [
            r
            for r in self._rows(start, end, merchant=merchant)
            if r["transaction_type"] == "expense"
        ]
        return self._result(
            dollars(sum(r["amount"] for r in rows)) if rows else None,
            rows,
            start,
            end,
            "Normalized merchant expense less refunds",
            filters={"merchant": merchant},
        )

    def get_largest_purchases(self, start, end, limit=5):
        rows = sorted(
            [
                r
                for r in self._rows(start, end)
                if r["transaction_type"] == "expense" and r["amount"] > 0
            ],
            key=lambda r: (-r["amount"], r["id"]),
        )[: max(1, min(limit, 20))]
        return self._result(
            None,
            rows,
            start,
            end,
            "Positive posted purchases ordered by amount descending; refunds shown separately",
            items=[{**r, "amount": dollars(r["amount"])} for r in rows],
        )

    def get_total_income(self, start, end):
        rows = [r for r in self._rows(start, end) if r["transaction_type"] == "income"]
        return self._result(
            dollars(-sum(r["amount"] for r in rows)) if rows else None,
            rows,
            start,
            end,
            "Negative-signed posted income converted to positive inflow",
        )

    def get_monthly_cash_flow(self, start=None, end=None):
        start, end = (start, end) if start and end else month_bounds()
        income = self.get_total_income(start, end)
        expense = self.get_spending_by_category(start, end)
        i, e = income["value"], expense["value"]
        return {
            "income": i,
            "expenses": e,
            "surplus": fmt(Decimal(i) - Decimal(e)) if i is not None and e is not None else None,
            "currency": "USD",
            "period": income["period"],
            "income_metadata": income,
            "expense_metadata": expense,
            "calculation_definition": "income - net posted expenses",
            "data_as_of": AS_OF,
        }

    def calculate_savings_rate(self, start, end):
        cf = self.get_monthly_cash_flow(start, end)
        i = cf["income"]
        value = (
            fmt(Decimal(cf["surplus"]) / Decimal(i) * 100)
            if i is not None and Decimal(i) > 0 and cf["surplus"] is not None
            else None
        )
        return {
            **cf,
            "value": value,
            "unit": "percent",
            "calculation_definition": "(income - expenses) / income * 100",
            "reason": None if value is not None else "Income is zero or required data is missing",
        }

    def get_account_balances(self):
        excluded = self.memory()["excluded_accounts"]
        rows = [
            dict(r)
            for r in self.conn.execute(
                "SELECT * FROM accounts WHERE user_id=? AND is_active=1", (self.user_id,)
            )
            if r["id"] not in excluded
        ]
        return self._result(
            None,
            rows,
            definition="Current account snapshot, not reconstructed from transaction history",
            items=[
                {
                    **r,
                    "current_balance": dollars(r["current_balance"]),
                    "available_balance": dollars(r["available_balance"]),
                }
                for r in rows
            ],
        )

    def get_cash_position(self):
        rows = [
            r
            for r in self.get_account_balances()["items"]
            if r["account_type"] in ["checking", "savings"]
        ]
        return self._result(
            fmt(sum((Decimal(r["available_balance"]) for r in rows), Decimal(0))) if rows else None,
            rows,
            definition="Sum available balances in eligible checking/savings; investment accounts excluded",
        )

    def get_goal_status(self):
        rows = [
            dict(r)
            for r in self.conn.execute(
                "SELECT * FROM financial_goals WHERE user_id=?", (self.user_id,)
            )
        ]
        return self._result(
            None,
            rows,
            definition="Structured goal records; earmarked savings are included in cash",
            items=[
                {
                    **r,
                    "target_amount": dollars(r["target_amount"]),
                    "current_amount": dollars(r["current_amount"]),
                }
                for r in rows
            ],
        )

    def find_recurring_subscriptions(self):
        rows = [
            dict(r)
            for r in self.conn.execute(
                "SELECT * FROM recurring_transactions WHERE user_id=? AND active=1", (self.user_id,)
            )
        ]
        history = self._rows(month_bounds(-6)[0], month_bounds(-1)[1], category="Subscriptions")
        for r in rows:
            months = {
                t["posted_date"][:7]
                for t in history
                if t["merchant_normalized"] == r["merchant"]
                and t["amount"] == r["amount"]
                and t["amount"] > 0
            }
            r["observed_months"] = len(months)
            r["detection_method"] = (
                "Matched posted monthly charges in at least three complete months"
                if r["frequency"] == "monthly"
                else "Explicit annual billing schedule; not inferred from monthly charges"
            )
        rows = [r for r in rows if r["frequency"] == "annual" or r["observed_months"] >= 3]
        for r in rows:
            r["monthly_equivalent"] = fmt(
                Decimal(r["amount"]) / 100 / (12 if r["frequency"] == "annual" else 1)
            )
            r["amount"] = dollars(r["amount"])
        return self._result(
            fmt(sum((Decimal(r["monthly_equivalent"]) for r in rows), Decimal(0)))
            if rows
            else None,
            rows,
            definition="Active monthly schedules verified against at least three complete months of matching posted charges; explicit annual schedules / 12. Monthly equivalents are not posted cash expenses.",
            items=rows,
        )

    def identify_spending_anomalies(self, start=None, end=None):
        start, end = (start, end) if start and end else month_bounds()
        current = self.get_spending_by_category(start, end)
        dt = date.fromisoformat(start)
        prev = (
            date(dt.year - 1, 12, 1) if dt.month == 1 else date(dt.year, dt.month - 1, 1)
        ).isoformat()
        old = self.get_spending_by_category(prev, start)
        baseline = {r["category"]: Decimal(r["amount"]) for r in old["items"]}
        items = []
        for row in current["items"]:
            before = baseline.get(row["category"])
            now = Decimal(row["amount"])
            if before is not None and now > before:
                items.append(
                    {
                        "category": row["category"],
                        "previous": fmt(before),
                        "current": fmt(now),
                        "difference": fmt(now - before),
                        "percent_change": fmt((now - before) / before * 100) if before else None,
                    }
                )
        return {
            **current,
            "items": items,
            "comparison_period": {"start": prev, "end_exclusive": start},
            "calculation_definition": "Category increases versus preceding calendar month; descriptive, not proof of cause",
        }

    def get_debt_payments(self):
        start, end = month_bounds()
        rows = [
            r for r in self._rows(start, end, "Housing") if "Mortgage" in r["merchant_normalized"]
        ]
        return self._result(
            dollars(sum(r["amount"] for r in rows)) if rows else None,
            rows,
            start,
            end,
            "Observed mortgage cash outflow already included in baseline expenses; not added again",
        )

    def get_spending_by_merchants(self, start, end):
        rows = [r for r in self._rows(start, end) if r["transaction_type"] == "expense"]
        groups = {}
        for r in rows:
            groups[r["merchant_normalized"]] = groups.get(r["merchant_normalized"], 0) + r["amount"]
        return self._result(
            None,
            rows,
            start,
            end,
            "Net expense grouped by normalized merchant",
            items=[
                {"merchant": k, "amount": dollars(v)}
                for k, v in sorted(groups.items(), key=lambda x: -x[1])
            ],
        )
