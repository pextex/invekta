from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator


class WorkInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    company_id: int = Field(gt=0)
    opportunity_id: int | None = Field(None, gt=0)
    assignee_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=200)
    notes: str | None = Field(None, max_length=4000)


class TaskInput(WorkInput):
    status: Literal["open", "doing", "done", "cancelled"] = "open"
    priority: Literal["low", "normal", "high"] = "normal"
    due_at: AwareDatetime
    remind_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def valid_reminder(self):
        if self.remind_at and self.remind_at > self.due_at:
            raise ValueError("Podsetnik mora biti najkasnije u vreme roka.")
        return self


class TaskUpdate(TaskInput):
    version: int = Field(ge=1)


class ActivityInput(WorkInput):
    kind: Literal["call", "meeting", "note"]
    status: Literal["planned", "done", "cancelled"] = "planned"
    scheduled_at: AwareDatetime | None = None
    occurred_at: AwareDatetime | None = None
    remind_at: AwareDatetime | None = None
    outcome: str | None = Field(None, max_length=4000)

    @model_validator(mode="after")
    def valid_dates(self):
        if self.remind_at and self.scheduled_at and self.remind_at > self.scheduled_at:
            raise ValueError("Podsetnik mora biti pre aktivnosti.")
        if self.status == "planned" and not self.scheduled_at:
            raise ValueError("Planirana aktivnost zahteva vreme.")
        if self.status != "done" and self.occurred_at:
            raise ValueError("Vreme izvršenja je samo za završene aktivnosti.")
        return self


class ActivityUpdate(ActivityInput):
    version: int = Field(ge=1)


class WorkOutput(WorkInput):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: int
    business_unit_id: int
    creator_id: int
    company_name: str
    assignee_name: str
    opportunity_title: str | None
    version: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class TaskOutput(WorkOutput):
    status: str
    priority: str
    due_at: datetime
    remind_at: datetime | None
    completed_at: datetime | None


class ActivityOutput(WorkOutput):
    kind: str
    status: str
    scheduled_at: datetime | None
    occurred_at: datetime | None
    remind_at: datetime | None
    outcome: str | None
