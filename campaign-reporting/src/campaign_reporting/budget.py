import sqlite3
import uuid
from decimal import ROUND_CEILING, Decimal
from pathlib import Path


class BudgetExceeded(ValueError):
    """The shared POC ledger cannot cover a new maximum-cost reservation."""


class BudgetLedger:
    """One persistent POC-wide ledger; unresolved requests keep their maximum reservation."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS reservations (id TEXT PRIMARY KEY, micros INTEGER, settled INTEGER)"
            )

    def _connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def remaining(self):
        with self._connect() as conn:
            used = conn.execute("SELECT COALESCE(SUM(micros),0) FROM reservations").fetchone()[0]
        return Decimal(5000000 - used) / 1000000

    def reserve(self, dollars):
        dollars = Decimal(dollars)
        if not dollars.is_finite() or dollars <= 0:
            raise ValueError("invalid budget reservation")
        amount = int((dollars * 1000000).to_integral_value(rounding=ROUND_CEILING))
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            used = conn.execute("SELECT COALESCE(SUM(micros),0) FROM reservations").fetchone()[0]
            if used + amount > 5000000:
                raise BudgetExceeded("POC budget exhausted")
            identity = str(uuid.uuid4())
            conn.execute("INSERT INTO reservations VALUES (?,?,0)", (identity, amount))
        return identity

    def settle(self, identity, dollars):
        dollars = Decimal(dollars)
        if not dollars.is_finite() or dollars < 0:
            raise ValueError("invalid actual cost")
        amount = int((dollars * 1000000).to_integral_value(rounding=ROUND_CEILING))
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT micros,settled FROM reservations WHERE id=?", (identity,)).fetchone()
            if not row or amount > row[0] or row[1]:
                raise ValueError("invalid settlement; reservation retained")
            conn.execute("UPDATE reservations SET micros=?,settled=1 WHERE id=?", (amount, identity))
