from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PolicyFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(default=1, ge=1, le=10000)
    page_size: int = Field(default=20, ge=1, le=100)


class ResolutionDate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_of: date


class PolicyIdentity(BaseModel):
    id: UUID
    policy_key: str
    name: str


class PolicyPage(BaseModel):
    items: list[PolicyIdentity]
    page: int
    page_size: int
    has_more: bool


class Rule(BaseModel):
    id: UUID
    control_definition_id: UUID
    control_key: str
    control_name: str
    control_active: bool
    frequency_months: int
    due_soon_days: int
    mandatory: bool
    evidence_requirement: str | None


class Version(BaseModel):
    id: UUID
    version_number: int
    effective_from: date
    effective_to: date | None
    gxp_classification: str
    criticality: str
    change_reason: str
    rules: list[Rule]


class PolicyHistory(PolicyIdentity):
    versions: list[Version]


class ResolvedVersion(BaseModel):
    policy_id: UUID
    policy_key: str
    policy_name: str
    policy_version_id: UUID
    version_number: int
    effective_from: date
    effective_to: date | None


class PolicyResolution(BaseModel):
    application_id: UUID
    as_of: date
    timezone: str
    configuration: Literal["Resolved", "Missing Configuration", "Conflicting Configuration"]
    explanation: str
    candidates: list[ResolvedVersion]
    rules: list[Rule]
