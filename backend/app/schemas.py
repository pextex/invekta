from decimal import Decimal
from datetime import date, datetime, time
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    business_unit_code: Literal["LUU", "INVEKTA", "CENOBOTS"] | None = None
    email: EmailStr | None = Field(default=None, max_length=254)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def one_identifier(self):
        if (self.email is None) == (self.username is None):
            raise ValueError("Unesite email adresu.")
        return self


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=200)
    address: str | None = Field(default=None, min_length=2, max_length=300)
    pib: str | None = Field(default=None, pattern=r"^[0-9]{9}$")
    city: str = Field(min_length=2, max_length=100)
    sector: str = Field(min_length=2, max_length=100)
    stage: Literal["Kontakt", "Ponuda", "Pregovori"] = "Kontakt"
    potential_value: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=14, decimal_places=2
    )

    @field_validator("name", "city", "sector")
    @classmethod
    def no_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Polje ne sme biti prazno.")
        return value


class CompanyOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    business_unit_id: int
    owner_id: int
    name: str
    address: str | None
    pib: str | None
    city: str
    sector: str
    stage: str
    potential_value: Decimal
    is_demo: bool


class ContactInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=150)
    position: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("position", "email", "phone", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class CompanyCreate(CompanyInput):
    contacts: list[ContactInput] = Field(default_factory=list, max_length=50)


class ContactOutput(ContactInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    business_unit_id: int
    is_demo: bool


OpportunityStage = Literal[
    "Novi lead",
    "Kontaktiran",
    "Sastanak",
    "Ponuda",
    "Pregovori",
    "Dobijeno",
    "Izgubljeno",
]


class OpportunityFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    business_type: Literal["sale", "contracted", "leasing", "rental"] | None = None
    title: str = Field(min_length=2, max_length=200)
    amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    stage: OpportunityStage = "Novi lead"
    expected_close_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class OpportunityCreate(OpportunityFields):
    company_id: int = Field(gt=0)


class OpportunityUpdate(OpportunityFields):
    version: int = Field(ge=1)


class OpportunityStageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage: OpportunityStage
    version: int = Field(ge=1)


class OpportunityOutput(OpportunityFields):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: int
    company_id: int
    company_name: str
    business_unit_id: int
    owner_name: str
    is_demo: bool
    version: int
    updated_at: datetime


class OpportunityPage(BaseModel):
    items: list[OpportunityOutput]
    total: int


class StageChangeOutput(BaseModel):
    id: int
    from_stage: str | None
    to_stage: str
    actor_name: str
    changed_at: datetime


class UnitSummary(BaseModel):
    company_count: int
    contact_count: int
    opportunity_count: int
    open_count: int
    open_value: Decimal
    won_count: int
    won_value: Decimal
    stages: dict[str, int]


class ReportPerson(BaseModel):
    id: int
    name: str


class ReportOwner(BaseModel):
    user_id: int
    user_name: str
    total: int
    created_count: int
    stage_change_count: int
    edit_count: int
    realized_count: int
    unrealized_count: int


class ReportChange(BaseModel):
    owner_id: int
    owner_name: str
    id: int
    changed_at: datetime
    company_name: str
    opportunity_id: int
    title: str
    amount: Decimal | None
    from_stage: str | None
    to_stage: str
    actor_name: str
    changes: dict | None


class SalesReport(BaseModel):
    people: list[ReportPerson]
    owners: list[ReportOwner]
    total: int
    opportunity_count: int
    created_count: int
    stage_change_count: int
    edit_count: int
    realized_count: int
    unrealized_count: int
    stage_counts: dict[str, int]
    items: list[ReportChange]


class TaskFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=200)
    due_date: date
    due_time: time | None = None
    notes: str | None = Field(default=None, max_length=2000)
    company_id: int | None = Field(default=None, gt=0)

    @field_validator("due_time")
    @classmethod
    def local_time(cls, value: time | None):
        if value is not None and value.tzinfo is not None:
            raise ValueError("Unesite lokalno vreme u Beogradu bez vremenske zone.")
        return value


class TaskUpdate(TaskFields):
    version: int = Field(ge=1)


class TaskStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["planned", "done"]
    version: int = Field(ge=1)


class TaskOutput(TaskFields):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: int
    owner_id: int
    owner_name: str
    company_name: str | None
    business_unit_id: int
    status: Literal["planned", "done"]
    version: int


class TaskPage(BaseModel):
    items: list[TaskOutput]
    total: int


class TargetEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal["sale", "contracted", "leasing", "rental"]
    target_amount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    version: int | None = Field(default=None, ge=1)


class TargetsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int = Field(gt=0)
    month: str = Field(pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$")
    targets: list[TargetEntry] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def unique_categories(self):
        if len({entry.category for entry in self.targets}) != len(self.targets):
            raise ValueError("Vrsta targeta može biti navedena samo jednom.")
        return self


class TargetProgress(BaseModel):
    category: str
    target_amount: Decimal | None
    achieved_amount: Decimal
    achieved_count: int
    version: int | None


class TargetSalesperson(BaseModel):
    user_id: int
    user_name: str
    targets: list[TargetProgress]


class TargetsOutput(BaseModel):
    month: str
    categories: list[str]
    can_manage: bool
    salespeople: list[TargetSalesperson]


class TeamBonusInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    month: str = Field(pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$")
    target_amount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    reward_note: str | None = Field(default=None, max_length=1000)
    version: int | None = Field(default=None, ge=1)


class TeamBonusOutput(BaseModel):
    month: str
    target_amount: Decimal | None
    reward_note: str | None
    version: int | None
    can_manage: bool
    individual_targets_total: Decimal
    achieved_amount: Decimal
    my_achieved_amount: Decimal
    salespeople_count: int
    achieved_count: int
    unlocked: bool
