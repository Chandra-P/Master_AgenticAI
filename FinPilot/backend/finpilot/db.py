"""SQLite adapter. Money is integer cents; connections are request-scoped."""

import json
import os
import sqlite3
from pathlib import Path

AS_OF = "2026-11-02"
DB_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).parents[1] / "finpilot.db"))


def connect(path=DB_PATH):
    conn = sqlite3.connect(path, timeout=20, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def migrate(conn):
    for migration in sorted((Path(__file__).parents[1] / "migrations").glob("*.sql")):
        conn.executescript(migration.read_text())
    conn.commit()


def seed(conn):
    if conn.execute("SELECT 1 FROM users WHERE id='demo'").fetchone():
        from .payroll import seed_tax_demo

        seed_tax_demo(conn)
        conn.commit()
        return
    conn.execute("INSERT INTO users VALUES('demo','Alex Morgan')")
    for args in [
        ("checking", "demo", "Northstar Bank", "Everyday checking", "checking", 1200000, 1200000),
        ("savings", "demo", "Northstar Bank", "High-yield savings", "savings", 4800000, 4800000),
        (
            "retirement",
            "demo",
            "Horizon Investments",
            "Retirement portfolio",
            "investment",
            9500000,
            9500000,
        ),
    ]:
        conn.execute(
            "INSERT INTO accounts(id,user_id,institution_name,account_name,account_type,current_balance,available_balance) VALUES(?,?,?,?,?,?,?)",
            args,
        )
    categories = [
        "Housing",
        "Groceries",
        "Restaurants",
        "Utilities",
        "Subscriptions",
        "Travel",
        "Shopping",
        "Transport",
        "Income",
        "Transfer",
    ]
    conn.executemany(
        "INSERT INTO transaction_categories VALUES(?,?)", [(x.lower(), x) for x in categories]
    )
    conn.executemany(
        "INSERT INTO merchant_aliases VALUES(?,?)",
        [("COSTCO WHSE #102", "Costco"), ("COSTCO.COM", "Costco"), ("COSTCO GAS #102", "Costco")],
    )
    subscriptions = [
        ("stream", "StreamBox", 8000, "monthly"),
        ("gym", "Pulse Fitness", 7000, "monthly"),
        ("cloud", "Cloud Studio", 5000, "monthly"),
        ("music", "Soundwave", 2000, "monthly"),
        ("news", "Daily Journal", 3000, "monthly"),
    ]
    for sid, name, amount, freq in subscriptions:
        conn.execute(
            "INSERT INTO recurring_transactions VALUES(?,?,?,?,?,?,?)",
            (
                sid,
                "demo",
                name,
                amount,
                freq,
                1,
                "Repeated posted charges, May–October 2026; annual plan from synthetic billing schedule.",
            ),
        )
    conn.execute(
        "INSERT INTO financial_goals VALUES('house','demo','House down payment',5000000,2000000,'2027-06-01',1,'active')"
    )
    conn.execute(
        "INSERT INTO user_preferences(user_id,emergency_fund_minimum,preferred_currency,risk_preference,rules) VALUES(?,?,?,?,?)",
        (
            "demo",
            2500000,
            "USD",
            "balanced",
            json.dumps(
                {
                    "max_goal_delay_months": 2,
                    "house_monthly_allocation": "4000.00",
                    "assumption_status": "demo default; confirm before relying on advice",
                }
            ),
        ),
    )
    conn.execute("INSERT INTO budgets VALUES('monthly','demo','Monthly spending',600000)")

    def tx(tid, month, day, merchant, amount, category, **kw):
        date = f"2026-{month:02d}-{day:02d}"
        normalized = "Costco" if merchant.startswith("COSTCO") else merchant
        conn.execute(
            "INSERT INTO transactions(id,account_id,external_id,posted_date,transaction_date,merchant_raw,merchant_normalized,description,amount,category,transaction_type,is_pending,is_internal_transfer,is_refund,duplicate_group_id,is_reversed) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                tid,
                "checking",
                tid,
                date,
                date,
                merchant,
                normalized,
                "Synthetic " + merchant,
                amount,
                category,
                "income"
                if category == "Income"
                else "transfer"
                if category == "Transfer"
                else "expense",
                kw.get("pending", 0),
                kw.get("transfer", 0),
                int(amount < 0 and category not in ["Income", "Transfer"]),
                kw.get("duplicate"),
                kw.get("reversed", 0),
            ),
        )

    for m in range(5, 11):
        prefix = f"{m}-"
        tx(prefix + "pay1", m, 1, "Acme Payroll", -500000, "Income")
        tx(prefix + "pay2", m, 15, "Acme Payroll", -500000, "Income")
        tx(prefix + "house", m, 2, "Northstar Mortgage", 280000, "Housing")
        grocery = 80000 if m == 9 else 90000
        for n, merchant in enumerate(["COSTCO WHSE #102", "COSTCO.COM", "Green Market"]):
            tx(
                prefix + "grocery" + str(n),
                m,
                5 + n,
                merchant,
                [25000, 15000, grocery - 40000][n],
                "Groceries",
            )
        restaurant = 55000 if m == 9 else 65000
        for n, (name, amt) in enumerate(
            [
                ("Juniper Kitchen", 30000),
                ("Little Olive", 20000),
                ("Neighborhood Cafe", restaurant - 50000),
            ]
        ):
            tx(prefix + "food" + str(n), m, 9 + n, name, amt, "Restaurants")
        tx(prefix + "utility", m, 12, "City Utilities", 35000, "Utilities")
        for sid, name, amount, freq in subscriptions:
            if freq == "monthly":
                tx(prefix + sid, m, 13, name, amount, "Subscriptions")
        # Annual subscriptions, when present, are normalized only in the subscription tool.
        tx(prefix + "hotel", m, 18, "Harbor Hotel", 60000 if m != 9 else 0, "Travel")
        if m != 9:
            tx(prefix + "refund", m, 22, "Harbor Hotel", -30000, "Travel")
        tx(prefix + "shop", m, 20, "Home & Field", 75000 if m == 9 else 45000, "Shopping")
        tx(prefix + "transport", m, 25, "Metro & Fuel", 30000, "Transport")
        tx(prefix + "transfer", m, 23, "Checking to savings", 100000, "Transfer", transfer=1)
        tx(
            prefix + "transfer-in",
            m,
            23,
            "Savings transfer received",
            -100000,
            "Transfer",
            transfer=1,
        )
    tx("10-duplicate", 10, 9, "Juniper Kitchen", 30000, "Restaurants", duplicate="10-food0")
    tx("pending", 10, 31, "Pending electronics", 95000, "Shopping", pending=1)
    tx("future", 12, 20, "Future holiday booking", 200000, "Travel")
    tx("reversed", 10, 26, "Reversed charge", 50000, "Shopping", reversed=1)
    tx("nov-pay", 11, 1, "Acme Payroll", -500000, "Income")
    tx("nov-house", 11, 2, "Northstar Mortgage", 280000, "Housing")
    tx("nov-transfer", 11, 2, "Checking to savings", 100000, "Transfer", transfer=1)
    from .rag import seed_documents

    seed_documents(conn)
    from .payroll import seed_tax_demo

    seed_tax_demo(conn)
    conn.commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["migrate", "seed", "reset"])
    args = parser.parse_args()
    if args.command == "reset" and Path(DB_PATH).exists():
        Path(DB_PATH).unlink()
    with connect() as c:
        migrate(c)
        if args.command != "migrate":
            seed(c)
    print(f"{args.command}: complete (synthetic demo)")
