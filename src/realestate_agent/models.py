"""Typed contracts shared by workflows, tools, calculations, and reports."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator


class Command(StrEnum):
    ANALYZE = "analyze"
    QUICK = "quick"
    COMPS = "comps"
    RENTAL = "rental"
    LISTING = "listing"
    INVEST = "invest"
    NEIGHBORHOOD = "neighborhood"
    FLIP = "flip"
    COMMERCIAL = "commercial"
    MORTGAGE = "mortgage"
    MARKET = "market"
    COMPARE = "compare"
    SCREEN = "screen"
    REPORT_PDF = "report-pdf"


class FinancialAssumptions(BaseModel):
    down_payment_percent: float = Field(default=20, ge=0, le=100)
    annual_interest_rate: float = Field(default=6.5, ge=0, le=30)
    loan_term_years: int = Field(default=30, gt=0, le=50)
    vacancy_percent: float = Field(default=8, ge=0, le=100)
    management_percent: float = Field(default=10, ge=0, le=100)
    maintenance_percent: float = Field(default=10, ge=0, le=100)
    capex_percent: float = Field(default=5, ge=0, le=100)


class PropertyProfile(BaseModel):
    address: str = Field(min_length=3)
    price: float = Field(gt=0)
    bedrooms: float | None = Field(default=None, ge=0)
    bathrooms: float | None = Field(default=None, ge=0)
    square_feet: float | None = Field(default=None, gt=0)
    lot_size: str | None = None
    year_built: int | None = Field(default=None, ge=1600, le=2200)
    property_type: str = "Unknown"
    annual_property_tax: float = Field(default=0, ge=0)
    annual_insurance: float = Field(default=0, ge=0)
    monthly_hoa: float = Field(default=0, ge=0)


class EvidenceItem(BaseModel):
    key: str
    value: Any
    source_url: HttpUrl | None = None
    provider: str
    source_tier: Literal["official", "community", "unofficial", "user"]
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    observed_at: datetime | None = None
    confidence: float = Field(ge=0, le=1)
    units: str | None = None
    warning: str | None = None


class EvidenceBundle(BaseModel):
    property: PropertyProfile
    evidence: list[EvidenceItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SpecialistResult(BaseModel):
    specialist: Literal["comps", "rental", "neighborhood", "investment", "market"]
    score: float = Field(ge=0, le=100)
    findings: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evidence_keys: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class AnalysisRequest(BaseModel):
    command: Command = Command.ANALYZE
    address: str | None = None
    comparison_address: str | None = None
    property: PropertyProfile | None = None
    assumptions: FinancialAssumptions = Field(default_factory=FinancialAssumptions)
    model_profile_id: str | None = None

    @model_validator(mode="after")
    def require_property_input(self) -> "AnalysisRequest":
        if self.command != Command.REPORT_PDF and not (self.address or self.property):
            raise ValueError("address or property is required")
        if self.command == Command.COMPARE and not self.comparison_address:
            raise ValueError("comparison_address is required for compare")
        return self


class AnalysisResult(BaseModel):
    analysis_id: str
    command: Command
    property: PropertyProfile
    specialists: list[SpecialistResult] = Field(default_factory=list)
    overall_score: float = Field(ge=0, le=100)
    grade: str
    signal: str
    confidence: float = Field(ge=0, le=1)
    summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    model_profile_id: str
    agent_version: str = "local"
    toolbox_version: str | None = None
    skill_versions: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
