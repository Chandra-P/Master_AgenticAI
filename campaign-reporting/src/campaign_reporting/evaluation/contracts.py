from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Split = Literal["development", "validation", "test"]
Status = Literal["pass", "fail", "needs_review"]
SEMANTIC_DIMENSIONS = ("factual_support", "completeness", "usefulness", "clarity")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Evidence(StrictModel):
    checking_accounts: int = Field(ge=0)
    new_members: int = Field(ge=0)
    checking_goal: int = Field(gt=0)
    member_goal: int = Field(gt=0)
    forecast: int = Field(ge=0)
    forecast_low: int = Field(ge=0)
    forecast_high: int = Field(ge=0)
    cpa: str | None = Field(default=None, pattern=r"^[0-9]+(?:\.[0-9]{1,2})?$")
    correction: bool = False

    @model_validator(mode="after")
    def valid_range(self):
        if not self.forecast_low <= self.forecast <= self.forecast_high:
            raise ValueError("invalid forecast range")
        return self


class Case(StrictModel):
    case_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    client_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    split: Split
    task: Literal["narrative", "oracle"] = "narrative"
    period: Literal["30", "60", "90", "120", "F"]
    year: Literal[2024, 2025]
    tags: tuple[str, ...] = ()
    facts: Evidence
    required_findings: tuple[str, ...]
    prohibited_claims: tuple[str, ...] = ("exposure_proves_incrementality", "invented_deposit_dates")
    canaries: tuple[str, ...] = ("EVAL_PRIVATE_CANARY",)
    untrusted_context: str = Field(default="", max_length=500)
    reference_status: Literal["proposed", "hand_checked"] = "proposed"
    oracle_scenario: str | None = None
    expected_result: dict | None = None

    @model_validator(mode="after")
    def oracle_contract(self):
        if self.task == "oracle" and (not self.oracle_scenario or self.expected_result is None):
            raise ValueError("oracle reference required")
        if self.task == "narrative" and (self.oracle_scenario or self.expected_result is not None):
            raise ValueError("narrative cannot carry executable oracle parameters")
        return self


class Check(StrictModel):
    name: str
    kind: Literal["contract", "semantic", "oracle"]
    status: Status
    severity: Literal["critical", "important", "quality"]
    reason: str


class Annotation(StrictModel):
    factual_support: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    usefulness: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)
    accepted: bool
    critical_violation: bool = False
    notes: str = Field(default="", max_length=1500)
