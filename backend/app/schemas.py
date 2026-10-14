from decimal import Decimal
from datetime import date, datetime
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
