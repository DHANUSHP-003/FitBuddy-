from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


Goal = Literal[
    "weight loss",
    "muscle gain",
    "general wellness",
    "flexibility",
    "endurance",
]


Intensity = Literal[
    "low",
    "medium",
    "high",
]


class UserInput(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    name: str = Field(
        min_length=2,
        max_length=120,
    )

    age: int = Field(
        ge=13,
        le=100,
    )

    weight_kg: float = Field(
        gt=25,
        le=400,
    )

    goal: Goal

    intensity: Intensity

    @field_validator("name")
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:

        return " ".join(
            value.strip().split()
        )


class FeedbackRequest(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=64,
    )

    feedback: str = Field(
        min_length=3,
        max_length=2000,
    )


class PlanResponse(BaseModel):

    user_id: str
    name: str
    age: int
    weight_kg: float
    goal: str
    intensity: str
    workout_plan: str
    nutrition_tip: str
    is_updated: bool = False


class UserSummary(BaseModel):

    user_id: str
    name: str
    age: int
    weight_kg: float
    goal: str
    intensity: str
    original_plan: str
    updated_plan: str | None = None
    latest_feedback: str | None = None
    nutrition_tip: str
    created_at: datetime