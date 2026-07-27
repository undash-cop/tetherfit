from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExerciseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    muscle_group: str | None = None
    equipment: str | None = None
    instructions: str | None = None


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    muscle_group: str | None
    equipment: str | None
    instructions: str | None


class WorkoutItem(BaseModel):
    exercise_id: UUID | None = None
    name: str
    sets: int = 3
    reps: str = "10"
    weight: str | None = None
    rest_seconds: int = 60
    notes: str | None = None
    order: int = 0


class WorkoutPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_template: bool = True
    items: list[WorkoutItem] = Field(default_factory=list)


class WorkoutPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    is_template: bool
    items: list
    created_at: datetime


class AssignmentCreate(BaseModel):
    client_id: UUID
    workout_plan_id: UUID
    notes: str | None = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    client_id: UUID
    workout_plan_id: UUID
    assigned_at: datetime
    notes: str | None
    plan_name: str | None = None
