import json
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

from .db import connect, migrate, seed, AS_OF
from .analytics import Analytics, month_bounds
from .money import dollars
from .scenario import Changes, simulate
from .agents import run
from .rag import ingest, MAX_SIZE
from .evaluation import evaluate

from .payroll import (
    TaxProfile,
    tax_profile,
    save_tax_profile,
    preview_paystub,
    confirm_paystub,
    list_paystubs,
)
from .tax_engine import TaxChanges, project_tax, tax_strategy, RULES
import sqlite3

logger = logging.getLogger("finpilot")
logging.basicConfig(level=logging.INFO, format="%(message)s")


@asynccontextmanager
async def lifespan(app):
    with connect() as conn:
        migrate(conn)
        seed(conn)
    yield


app = FastAPI(title="FinPilot", version="1.0.0", lifespan=lifespan)
requests = defaultdict(deque)


@app.middleware("http")
async def boundary(request: Request, call_next):
    # Demo identity is fixed server-side; never accept a caller-supplied user id.
    token = os.getenv("FINPILOT_ACCESS_TOKEN")
    if (
        request.url.path != "/api/health"
        and token
        and request.headers.get("authorization") != f"Bearer {token}"
    ):
        return JSONResponse({"detail": "Authentication required"}, status_code=401)
    host = request.client.host if request.client else "local"
    now = time.monotonic()
    bucket = requests[host]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= 120:
        return JSONResponse({"detail": "Too many requests. Try again shortly."}, status_code=429)
    bucket.append(now)
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    logger.info(
        json.dumps(
            {
                "event": "http",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": round((time.perf_counter() - started) * 1000),
            }
        )
    )
    return response


def connection():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[object, Depends(connection)]


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "demo": True,
        "as_of": AS_OF,
        "model_mode": os.getenv("MODEL_MODE", "deterministic"),
        "council_mode": os.getenv("COUNCIL_MODE", "off"),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "langsmith_configured": bool(os.getenv("LANGSMITH_API_KEY")),
        "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "local"),
    }


@app.get("/api/dashboard")
def dashboard(conn: Conn):
    a = Analytics(conn)
    cf = a.get_monthly_cash_flow()
    projection, projection_error = None, None
    try:
        projection = simulate(a, {})
    except ValueError as exc:
        projection_error = str(exc)
    trend = []
    for offset in range(-6, 0):
        start, end = month_bounds(offset)
        trend.append({"month": start, **a.get_monthly_cash_flow(start, end)})
    return {
        "user": "Alex Morgan",
        "as_of": AS_OF,
        "cash": a.get_cash_position(),
        "cash_flow": cf,
        "savings_rate": a.calculate_savings_rate(*month_bounds()),
        "categories": a.get_spending_by_category(*month_bounds()),
        "trend": trend,
        "goals": a.get_goal_status(),
        "memory": a.memory(),
        "anomalies": a.identify_spending_anomalies(),
        "subscriptions": a.find_recurring_subscriptions(),
        "baseline_projection": projection,
        "projection_unavailable_reason": projection_error,
    }


@app.get("/api/accounts")
def accounts(conn: Conn):
    return Analytics(conn).get_account_balances()


@app.get("/api/transactions")
def transactions(conn: Conn, search: str = "", category: str = ""):
    sql = "SELECT t.*,a.account_name FROM transactions t JOIN accounts a ON a.id=t.account_id WHERE a.user_id=? AND (t.merchant_normalized LIKE ? OR t.merchant_raw LIKE ?)"
    params = ["demo", "%" + search[:100] + "%", "%" + search[:100] + "%"]
    if category:
        sql += " AND t.category=?"
        params.append(category)
    rows = [
        dict(r) for r in conn.execute(sql + " ORDER BY t.posted_date DESC,t.id LIMIT 500", params)
    ]
    for r in rows:
        r["amount"] = dollars(r["amount"])
    return {
        "items": rows,
        "as_of": AS_OF,
        "note": "Ledger includes diagnostic entries; analytics exclude flagged transactions.",
    }


@app.get("/api/subscriptions")
def subscriptions(conn: Conn):
    return Analytics(conn).find_recurring_subscriptions()


@app.get("/api/goals")
def goals(conn: Conn):
    return Analytics(conn).get_goal_status()


@app.get("/api/memory")
def memory(conn: Conn):
    return Analytics(conn).memory()


class MemoryEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    house_target_amount: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    emergency_fund_minimum: Decimal = Field(ge=0, le=10000000, decimal_places=2)
    max_goal_delay_months: int = Field(ge=0, le=120)
    house_monthly_allocation: Decimal = Field(ge=0, le=100000, decimal_places=2)
    risk_preference: str = Field(pattern="^(conservative|balanced|growth)$")
    confirmed: bool = False
    revision: int = Field(ge=1)


@app.put("/api/memory")
def edit_memory(body: MemoryEdit, conn: Conn):
    if not body.confirmed:
        raise HTTPException(
            409, "Explicit confirmation is required before replacing financial constraints"
        )
    old = Analytics(conn).memory()
    if old["revision"] != body.revision:
        raise HTTPException(409, "Preferences changed. Reload before confirming")
    rules = {
        **old["rules"],
        "max_goal_delay_months": body.max_goal_delay_months,
        "house_monthly_allocation": str(body.house_monthly_allocation),
        "assumption_status": "Explicitly confirmed by user",
    }
    cursor = conn.execute(
        "UPDATE user_preferences SET emergency_fund_minimum=?,risk_preference=?,rules=?,revision=revision+1 WHERE user_id=? AND revision=?",
        (
            int(body.emergency_fund_minimum * 100),
            body.risk_preference,
            json.dumps(rules),
            "demo",
            body.revision,
        ),
    )
    if cursor.rowcount != 1:
        conn.rollback()
        raise HTTPException(409, "Concurrent memory edit; reload and confirm")
    if body.house_target_amount is not None:
        conn.execute(
            "UPDATE financial_goals SET target_amount=? WHERE user_id=? AND id=?",
            (int(body.house_target_amount * 100), "demo", "house"),
        )
    conn.execute(
        "INSERT INTO memory_audit(id,user_id,previous_value,new_value,confirmed) VALUES(?,?,?,?,1)",
        (str(uuid.uuid4()), "demo", json.dumps(old), body.model_dump_json()),
    )
    conn.commit()
    return Analytics(conn).memory()


@app.get("/api/memory/audit")
def memory_audit(conn: Conn):
    return {
        "items": [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM memory_audit WHERE user_id=? ORDER BY created_at DESC", ("demo",)
            )
        ]
    }


@app.get("/api/documents")
def documents(conn: Conn):
    return {
        "items": [
            {**dict(r), "metadata": json.loads(r["metadata"])}
            for r in conn.execute(
                "SELECT * FROM documents WHERE user_id=? ORDER BY effective_date DESC", ("demo",)
            )
        ]
    }


@app.get("/api/documents/{doc_id}")
def document(doc_id: str, conn: Conn):
    row = conn.execute(
        "SELECT * FROM documents WHERE user_id=? AND id=?", ("demo", doc_id)
    ).fetchone()
    if not row:
        raise HTTPException(404, "Document not found")
    return {
        **dict(row),
        "chunks": [
            dict(r)
            for r in conn.execute(
                "SELECT section,page,content,quarantined FROM document_chunks WHERE document_id=? AND quarantined=0",
                (doc_id,),
            )
        ],
    }


@app.post("/api/documents")
async def upload(
    conn: Conn,
    file: UploadFile = File(...),
    supersedes: str = Form(""),
    effective_date: str = Form(AS_OF),
):
    data = await file.read(MAX_SIZE + 1)
    try:
        result = ingest(
            conn,
            file.filename or "upload.txt",
            data,
            supersedes=supersedes or None,
            effective_date=effective_date,
        )
        conn.commit()
        return result
    except ValueError as exc:
        conn.rollback()
        raise HTTPException(400, str(exc)) from exc
    finally:
        await file.close()


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    selected_subscription_ids: list[str] | None = None


@app.post("/api/copilot")
def copilot(body: Question, conn: Conn):
    if not body.question.strip():
        raise HTTPException(422, "Enter a financial question")
    return run(conn, body.question, selected_subscription_ids=body.selected_subscription_ids)


@app.post("/api/scenarios")
def scenario(body: Changes, conn: Conn):
    try:
        result = simulate(Analytics(conn), body.model_dump(mode="json"))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    rid = str(uuid.uuid4())
    conn.execute("INSERT INTO scenario_runs(id,user_id) VALUES(?,?)", (rid, "demo"))
    conn.execute("INSERT INTO scenario_inputs VALUES(?,?)", (rid, body.model_dump_json()))
    conn.execute("INSERT INTO scenario_results VALUES(?,?)", (rid, json.dumps(result)))
    conn.commit()
    return {"id": rid, **result}


@app.get("/api/traces")
def traces(conn: Conn):
    return {
        "items": [
            json.loads(r["answer"])
            for r in conn.execute(
                "SELECT answer FROM agent_runs WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
                ("demo",),
            )
        ]
    }


@app.get("/api/evaluations")
def latest_evaluation(conn: Conn):
    row = conn.execute("SELECT * FROM evaluation_runs ORDER BY created_at DESC LIMIT 1").fetchone()
    if not row:
        return {"metrics": None, "results": []}
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "metrics": json.loads(row["metrics"]),
        "results": [
            json.loads(r["payload"])
            for r in conn.execute(
                "SELECT payload FROM evaluation_results WHERE run_id=? ORDER BY test_id",
                (row["id"],),
            )
        ],
    }


@app.post("/api/evaluations")
def run_evaluation(conn: Conn):
    return evaluate(conn)


# Payroll and tax planning use the same server-derived demo identity and connection boundary.


@app.get("/api/tax/profile")
def get_tax_profile(conn: Conn):
    return tax_profile(conn)


@app.put("/api/tax/profile")
def update_tax_profile(body: TaxProfile, conn: Conn):
    missing = set(TaxProfile.model_fields) - body.model_fields_set
    if missing:
        raise HTTPException(
            422,
            "Submit the complete reviewed tax profile; omitted fields cannot be defaulted: "
            + ", ".join(sorted(missing)),
        )
    try:
        result = save_tax_profile(conn, body.model_dump(mode="json"))
        conn.commit()
        return result
    except ValueError as exc:
        conn.rollback()
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/tax/rules")
def get_tax_rules():
    return RULES


@app.get("/api/tax/projection")
def get_tax_projection(conn: Conn):
    try:
        return project_tax(conn)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/tax/paystubs")
def get_paystubs(conn: Conn):
    return {"items": list_paystubs(conn)}


@app.post("/api/tax/paystubs/preview")
async def preview_paystub_upload(conn: Conn, file: UploadFile = File(...)):
    try:
        data = await file.read(MAX_SIZE + 1)
        result = preview_paystub(conn, file.filename or "paystub.txt", data)
        conn.commit()
        return result
    except ValueError as exc:
        conn.rollback()
        raise HTTPException(400, str(exc)) from exc
    finally:
        await file.close()


class PaystubConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    upload_id: str = Field(min_length=1, max_length=64)
    confirmed: bool = False
    facts: dict
    supersedes_paystub_id: str | None = None


@app.post("/api/tax/paystubs/confirm")
def confirm_paystub_upload(body: PaystubConfirmation, conn: Conn):
    if not body.confirmed:
        raise HTTPException(409, "Explicitly confirm the reviewed payroll facts")
    try:
        result = confirm_paystub(
            conn, body.upload_id, body.facts, True, supersedes=body.supersedes_paystub_id
        )
        conn.commit()
        return result
    except ValueError as exc:
        conn.rollback()
        raise HTTPException(422, str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise HTTPException(
            409, "Duplicate or concurrent paystub confirmation; reload and review"
        ) from exc


@app.post("/api/tax/strategy")
def run_tax_strategy(body: TaxChanges, conn: Conn):
    try:
        result = tax_strategy(conn, body.model_dump(mode="json"))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    rid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO tax_runs(id,user_id,inputs,result) VALUES(?,?,?,?)",
        (rid, "demo", body.model_dump_json(), json.dumps(result)),
    )
    conn.commit()
    return {"id": rid, **result}


@app.get("/api/tax/audit")
def get_tax_audit(conn: Conn):
    return {
        "items": [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM tax_audit WHERE user_id=? ORDER BY rowid DESC LIMIT 100", ("demo",)
            )
        ]
    }
