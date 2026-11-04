"""Reviewed payroll facts; documents never activate themselves as tax inputs."""

import json
import re
import sqlite3
import uuid
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator
from .db import AS_OF
from .money import decimal, fmt
from .rag import ingest, INJECTION

MONEY_LABELS = {
    "gross": "Gross pay",
    "federal_taxable": "Federal taxable wages",
    "federal_withholding": "Federal withholding",
    "social_security_wages": "Social Security wages",
    "medicare_wages": "Medicare wages",
    "social_security_withholding": "Social Security withholding",
    "medicare_withholding": "Medicare withholding",
    "additional_medicare_withholding": "Additional Medicare withholding",
    "traditional_401k": "Traditional 401k",
    "roth_401k": "Roth 401k",
    "hsa": "HSA",
    "employer_hsa": "Employer HSA",
    "other_deductions": "Other deductions",
    "net_pay": "Net pay",
}
META_LABELS = {
    "employment_key": "Employment ID",
    "employee_key": "Employee ID",
    "employee_name": "Employee name",
    "employer_name": "Employer name",
    "age": "Age",
    "pay_frequency": "Pay frequency",
    "pay_type": "Pay type",
    "pay_date": "Pay date",
    "next_pay_date": "Next pay date",
    "pay_period_start": "Pay period start",
    "pay_period_end": "Pay period end",
    "annual_periods": "Annual pay periods",
    "completed_periods": "Completed pay periods",
    "remaining_periods": "Remaining pay periods",
}
MONEY_FIELDS = {
    f"{key}_{period}": f"{label} {period.upper() if period == 'ytd' else period}"
    for key, label in MONEY_LABELS.items()
    for period in ["current", "ytd"]
}
PERIODS = {"weekly": {52, 53}, "biweekly": {26, 27}, "semimonthly": {24}, "monthly": {12}}


class PayrollMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employment_key: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    employee_key: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    employee_name: str = Field(min_length=1, max_length=100)
    employer_name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=49)
    pay_frequency: Literal["weekly", "biweekly", "semimonthly", "monthly"]
    pay_type: Literal["regular"]
    pay_date: date
    next_pay_date: date | None = None
    pay_period_start: date
    pay_period_end: date
    annual_periods: int = Field(ge=12, le=53)
    completed_periods: int = Field(ge=1, le=53)
    remaining_periods: int = Field(ge=0, le=52)

    @model_validator(mode="after")
    def reconcile(self):
        if (
            self.pay_date.year != 2026
            or self.pay_period_start.year != 2026
            or self.pay_period_end.year != 2026
        ):
            raise ValueError("Only tax year 2026 is supported")
        if not self.pay_period_start <= self.pay_period_end <= self.pay_date:
            raise ValueError("Pay-period dates must be ordered and not after pay date")
        if (
            self.annual_periods not in PERIODS[self.pay_frequency]
            or self.completed_periods + self.remaining_periods != self.annual_periods
        ):
            raise ValueError(
                "Completed plus remaining pay periods must match the reviewed annual schedule"
            )
        if self.remaining_periods and (
            self.next_pay_date is None
            or self.next_pay_date <= self.pay_date
            or self.next_pay_date.year != 2026
        ):
            raise ValueError(
                "Review a future next pay date in 2026 before modeling remaining checks"
            )
        for key in MONEY_LABELS:
            if getattr(self, key + "_ytd") < getattr(self, key + "_current"):
                raise ValueError(f"{key} YTD cannot be below the current amount")
        for period in ["current", "ytd"]:
            gross = getattr(self, "gross_" + period)
            deductions = sum(
                (
                    getattr(self, key + "_" + period)
                    for key in [
                        "traditional_401k",
                        "roth_401k",
                        "hsa",
                        "other_deductions",
                        "federal_withholding",
                        "social_security_withholding",
                        "medicare_withholding",
                        "additional_medicare_withholding",
                    ]
                ),
                Decimal(0),
            )
            if abs(gross - deductions - getattr(self, "net_pay_" + period)) > Decimal(".02"):
                raise ValueError(
                    f"Net pay does not reconcile with gross minus deductions ({period})"
                )
            if any(
                getattr(self, key + "_" + period) > gross
                for key in ["federal_taxable", "social_security_wages", "medicare_wages"]
            ):
                raise ValueError(
                    "Taxable wage bases cannot exceed gross in this supported paystub format"
                )
        return self


PaystubFacts = create_model(
    "PaystubFacts",
    __base__=PayrollMeta,
    **{key: (Decimal, Field(ge=0, le=100000000, decimal_places=2)) for key in MONEY_FIELDS},
)


class TaxProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tax_year: Literal[2026] = 2026
    state: Literal["TX"] = "TX"
    filing_status: Literal["single", "married_filing_jointly"] = "married_filing_jointly"
    as_of: date = date.fromisoformat(AS_OF)
    employee_keys: list[str] = Field(
        default_factory=lambda: ["alex", "jordan"], min_length=1, max_length=2
    )
    hsa_coverage: Literal["none", "self_only", "family"] = "family"
    hsa_eligible_months: int = Field(default=12, ge=0, le=12)
    hsa_eligibility_confirmed: bool = False
    hsa_payroll_cafeteria_plan_confirmed: bool = False
    other_ordinary_income: Decimal = Field(default=Decimal(0), ge=0, le=10000000, decimal_places=2)
    nonrefundable_credits: Decimal = Field(default=Decimal(0), ge=0, le=1000000, decimal_places=2)
    estimated_payments: Decimal = Field(default=Decimal(0), ge=0, le=1000000, decimal_places=2)
    prior_year_total_tax: Decimal | None = Field(default=None, ge=0, le=1000000, decimal_places=2)
    prior_year_agi: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    prior_year_full_year_return: bool = False
    supported_scope_confirmed: bool = False
    confirmed: bool = False
    revision: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def scope(self):
        if self.as_of.year != 2026:
            raise ValueError("Projection date must be in tax year 2026")
        if len(set(self.employee_keys)) != len(self.employee_keys):
            raise ValueError("Select each worker only once")
        if self.filing_status == "single" and len(self.employee_keys) != 1:
            raise ValueError("Single filing requires exactly one worker in this scope")
        if (self.prior_year_total_tax is None) != (self.prior_year_agi is None):
            raise ValueError("Provide both prior-year tax and AGI, or leave both unknown")
        return self


def extract_paystub(text):
    lines = [line.strip() for line in text.splitlines() if not INJECTION.search(line)]
    fields, evidence = {}, {}
    for key, label in {**META_LABELS, **MONEY_FIELDS}.items():
        matches = []
        for line in lines:
            match = re.fullmatch(re.escape(label) + r"\s*:\s*(.+)", line, re.I)
            if match:
                raw = match.group(1).strip()
                if key in MONEY_FIELDS:
                    if not re.fullmatch(r"\$?\s*\d[\d,]*(?:\.\d{1,2})?", raw):
                        continue
                    raw = fmt(decimal(raw.replace("$", "").replace(",", "").strip()))
                elif key == "next_pay_date" and raw.lower() in {"none", "n/a", "unknown"}:
                    raw = None
                elif key in ["age", "annual_periods", "completed_periods", "remaining_periods"]:
                    if not raw.isdigit():
                        continue
                    raw = int(raw)
                matches.append((raw, line))
        if matches and len({str(v) for v, _ in matches}) == 1:
            fields[key] = matches[0][0]
            evidence[key] = {"label": label, "passage": matches[0][1]}
    missing = [
        key
        for key in {**META_LABELS, **MONEY_FIELDS}
        if key not in fields
        or (key == "next_pay_date" and fields[key] is None and fields.get("remaining_periods") != 0)
    ]
    return {
        "fields": fields,
        "evidence": evidence,
        "missing_fields": missing,
        "requires_confirmation": True,
        "note": "Untrusted extraction. Review every amount, wage basis, date, and remaining-paycheck count before confirmation.",
    }


def preview_paystub(conn, filename, data, user_id="demo", synthetic=False):
    doc = ingest(
        conn,
        filename,
        data,
        user_id=user_id,
        family="paystub",
        embedding_provider="local",
        synthetic=synthetic,
    )
    chunks = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM document_chunks WHERE document_id=? AND quarantined=0 ORDER BY rowid",
            (doc["id"],),
        )
    ]
    extraction = extract_paystub("\n".join(c["content"] for c in chunks))
    for evidence in extraction["evidence"].values():
        chunk = next((c for c in chunks if evidence["passage"] in c["content"]), None)
        if chunk:
            evidence.update(page=chunk["page"], section=chunk["section"], chunk_id=chunk["id"])
    uid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO paystub_uploads(id,user_id,document_id,extraction) VALUES(?,?,?,?)",
        (uid, user_id, doc["id"], json.dumps(extraction)),
    )
    return {"upload_id": uid, "document_id": doc["id"], **extraction}


def confirm_paystub(conn, upload_id, facts, confirmed=False, user_id="demo", supersedes=None):
    if not confirmed:
        raise ValueError("Explicit confirmation is required for payroll facts")
    data = PaystubFacts.model_validate(facts).model_dump(mode="json")
    upload = conn.execute(
        "SELECT * FROM paystub_uploads WHERE id=? AND user_id=?", (upload_id, user_id)
    ).fetchone()
    if not upload or upload["state"] != "needs_review":
        raise ValueError("Accessible unconfirmed paystub upload not found")
    profile = tax_profile(conn, user_id)
    if data["pay_date"] > profile["as_of"]:
        raise ValueError("Pay date is after the reviewed projection date")
    old = None
    if supersedes:
        old = conn.execute(
            "SELECT * FROM paystubs WHERE id=? AND user_id=? AND status='confirmed'",
            (supersedes, user_id),
        ).fetchone()
        if (
            not old
            or old["employment_key"] != data["employment_key"]
            or old["pay_date"] != data["pay_date"]
        ):
            raise ValueError(
                "A correction must explicitly replace the same owned employment/pay date"
            )
    duplicate = conn.execute(
        "SELECT id FROM paystubs WHERE user_id=? AND employment_key=? AND pay_date=? AND status='confirmed'",
        (user_id, data["employment_key"], data["pay_date"]),
    ).fetchone()
    if duplicate and (not old or duplicate["id"] != old["id"]):
        raise ValueError("Duplicate pay date; explicitly select the existing paystub to correct")
    pid = str(uuid.uuid4())
    conn.execute("SAVEPOINT confirm_paystub")
    try:
        if old:
            conn.execute("UPDATE paystubs SET status='superseded' WHERE id=?", (old["id"],))
        conn.execute(
            "INSERT INTO paystubs(id,user_id,document_id,upload_id,employment_key,employee_key,pay_date,tax_year,payload,supersedes) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                pid,
                user_id,
                upload["document_id"],
                upload_id,
                data["employment_key"],
                data["employee_key"],
                data["pay_date"],
                2026,
                json.dumps(data),
                supersedes,
            ),
        )
        conn.execute(
            "UPDATE paystub_uploads SET state='confirmed' WHERE id=? AND state='needs_review'",
            (upload_id,),
        )
        conn.execute(
            "INSERT INTO tax_audit(id,user_id,action,previous_value,new_value) VALUES(?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                user_id,
                "confirm_paystub",
                old["payload"] if old else upload["extraction"],
                json.dumps(data),
            ),
        )
        conn.execute("RELEASE SAVEPOINT confirm_paystub")
    except sqlite3.Error:
        conn.execute("ROLLBACK TO SAVEPOINT confirm_paystub")
        conn.execute("RELEASE SAVEPOINT confirm_paystub")
        raise
    return {"id": pid, "document_id": upload["document_id"], "status": "confirmed", "facts": data}


def tax_profile(conn, user_id="demo"):
    row = conn.execute("SELECT * FROM tax_profiles WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        raise ValueError("Review and confirm a household tax profile first")
    return {
        **TaxProfile.model_validate(json.loads(row["payload"])).model_dump(mode="json"),
        "revision": row["revision"],
        "confirmed": bool(row["confirmed"]),
    }


def save_tax_profile(conn, body, user_id="demo"):
    profile = TaxProfile.model_validate(body)
    if not profile.confirmed or not profile.supported_scope_confirmed:
        raise ValueError("Explicitly confirm household facts and the supported tax scope")
    previous = tax_profile(conn, user_id)
    if profile.revision != previous["revision"]:
        raise ValueError("Tax profile changed; reload before confirming")
    new = profile.model_dump(mode="json")
    cursor = conn.execute(
        "UPDATE tax_profiles SET payload=?,revision=revision+1,confirmed=1,updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND revision=?",
        (json.dumps(new), user_id, profile.revision),
    )
    if cursor.rowcount != 1:
        raise ValueError("Tax profile changed; reload before confirming")
    conn.execute(
        "INSERT INTO tax_audit(id,user_id,action,previous_value,new_value) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()), user_id, "confirm_tax_profile", json.dumps(previous), json.dumps(new)),
    )
    return tax_profile(conn, user_id)


def list_paystubs(conn, user_id="demo"):
    rows = conn.execute(
        "SELECT p.*,d.title FROM paystubs p JOIN documents d ON p.document_id=d.id WHERE p.user_id=? ORDER BY pay_date DESC,created_at DESC",
        (user_id,),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "document_id": r["document_id"],
            "title": r["title"],
            "status": r["status"],
            "facts": json.loads(r["payload"]),
        }
        for r in rows
    ]


def latest_paystubs(conn, profile, user_id="demo"):
    selected = {}
    for row in list_paystubs(conn, user_id):
        facts = row["facts"]
        if (
            row["status"] != "confirmed"
            or facts["pay_date"] > profile["as_of"]
            or facts["employee_key"] not in profile["employee_keys"]
        ):
            continue
        selected.setdefault(facts["employment_key"], row)
    if set(profile["employee_keys"]) != {r["facts"]["employee_key"] for r in selected.values()}:
        raise ValueError("Missing confirmed current paystubs for selected household workers")
    keys = [r["facts"]["employee_key"] for r in selected.values()]
    if len(keys) != len(set(keys)):
        raise ValueError(
            "Multiple employers for one worker require an expanded payroll model; no estimate generated"
        )
    for row in selected.values():
        PaystubFacts.model_validate(row["facts"])
        if row["facts"]["remaining_periods"] and profile["as_of"] >= row["facts"]["next_pay_date"]:
            raise ValueError(
                "The reviewed next pay date has passed; upload a current paystub before modeling future changes"
            )
        days = (
            date.fromisoformat(profile["as_of"]) - date.fromisoformat(row["facts"]["pay_date"])
        ).days
        max_age = {"weekly": 14, "biweekly": 28, "semimonthly": 32, "monthly": 62}[
            row["facts"]["pay_frequency"]
        ]
        if days > max_age:
            raise ValueError("Latest confirmed paystub is stale; upload a current regular paycheck")
    return list(selected.values())


def seed_tax_demo(conn):
    if conn.execute("SELECT 1 FROM tax_profiles WHERE user_id='demo'").fetchone():
        return
    profile = TaxProfile(
        confirmed=True,
        supported_scope_confirmed=True,
        hsa_eligibility_confirmed=True,
        hsa_payroll_cafeteria_plan_confirmed=True,
        prior_year_total_tax=Decimal("13600"),
        prior_year_agi=Decimal("145000"),
        prior_year_full_year_return=True,
    ).model_dump(mode="json")
    conn.execute(
        "INSERT INTO tax_profiles(user_id,tax_year,payload,confirmed) VALUES(?,?,?,1)",
        ("demo", 2026, json.dumps(profile)),
    )
    for key, name, employer, gross, trad, hsa, ss, med, fit, net in [
        ("acme-alex", "Alex Morgan", "Acme", 4000, 400, 100, "241.80", "56.55", "201.65", 3000),
        (
            "studio-jordan",
            "Jordan Morgan",
            "Studio Works",
            2700,
            200,
            0,
            "167.40",
            "39.15",
            "293.45",
            2000,
        ),
    ]:
        employee = "alex" if key == "acme-alex" else "jordan"
        for completed, paydate, start, end in [
            (19, "2026-10-15", "2026-10-01", "2026-10-15"),
            (20, "2026-10-31", "2026-10-16", "2026-10-31"),
        ]:
            meta = {
                "employment_key": key,
                "employee_key": employee,
                "employee_name": name,
                "employer_name": employer,
                "age": 35 if employee == "alex" else 33,
                "pay_frequency": "semimonthly",
                "pay_type": "regular",
                "pay_date": paydate,
                "next_pay_date": "2026-10-31" if completed == 19 else "2026-11-15",
                "pay_period_start": start,
                "pay_period_end": end,
                "annual_periods": 24,
                "completed_periods": completed,
                "remaining_periods": 24 - completed,
            }
            amounts = {
                "gross": gross,
                "federal_taxable": gross - trad - hsa,
                "federal_withholding": fit,
                "social_security_wages": gross - hsa,
                "medicare_wages": gross - hsa,
                "social_security_withholding": ss,
                "medicare_withholding": med,
                "additional_medicare_withholding": 0,
                "traditional_401k": trad,
                "roth_401k": 0,
                "hsa": hsa,
                "employer_hsa": 0,
                "other_deductions": 0,
                "net_pay": net,
            }
            lines = ["SYNTHETIC — Reviewed demo paystub"] + [
                f"{label}: {meta[field]}" for field, label in META_LABELS.items()
            ]
            for field, label in MONEY_FIELDS.items():
                base, period = field.rsplit("_", 1)
                lines.append(
                    f"{label}: ${fmt(decimal(amounts[base]) * (completed if period == 'ytd' else 1))}"
                )
            preview = preview_paystub(
                conn, f"{key}-{paydate}-paystub.txt", "\n".join(lines).encode()
            )
            confirm_paystub(conn, preview["upload_id"], preview["fields"], True)
