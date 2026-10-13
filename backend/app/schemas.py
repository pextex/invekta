from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)

class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    sector: str = Field(min_length=2, max_length=100)
    stage: Literal["Kontakt", "Ponuda", "Pregovori"] = "Kontakt"
    potential_value: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)

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
    city: str
    sector: str
    stage: str
    potential_value: Decimal
    is_demo: bool
