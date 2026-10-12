from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Classification = Literal["GxP", "Non-GxP"]
Criticality = Literal["High", "Medium", "Low"]
Lifecycle = Literal["Implementation", "Operational", "Retirement", "Retired"]
Validation = Literal["Not Assessed", "Validation Required", "In Validation", "Validated", "Remediation Required"]


class ApplicationFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    search: str = Field(default="", max_length=100)
    classification: Classification | None = None
    criticality: Criticality | None = None
    lifecycle_state: Lifecycle | None = None
    validation_state: Validation | None = None
    page: int = Field(default=1, ge=1, le=10000)
    page_size: int = Field(default=20, ge=1, le=100)


class Application(BaseModel):
    id: UUID
    organization_id: UUID
    ci_id: str
    name: str
    system_type: str
    description: str | None
    gxp_classification: Classification
    criticality: Criticality
    lifecycle_state: Lifecycle
    validation_state: Validation
    supplier: str | None
    platform: str | None
    created_at: datetime
    updated_at: datetime
    # Identity/assignment tables arrive later; null means ownership is not recorded.
    business_owner_id: UUID | None = None
    technical_owner_id: UUID | None = None
    quality_owner_id: UUID | None = None


class ApplicationPage(BaseModel):
    items: list[Application]
    total: int
    page: int
    page_size: int
