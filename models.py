"""Pydantic models aligned with Hevy OpenAPI (PostRoutinesRequest*, ExerciseTemplate, YAML sources)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RoutineSetType = Literal["warmup", "normal", "failure", "dropset"]


class RepRange(BaseModel):
    start: float | None = None
    end: float | None = None


class PostRoutinesRequestSet(BaseModel):
    type: RoutineSetType = "normal"
    weight_kg: float | None = None
    reps: int | None = None
    distance_meters: int | None = None
    duration_seconds: int | None = None
    custom_metric: float | None = None
    rep_range: RepRange | None = None


class PostRoutinesRequestExercise(BaseModel):
    exercise_template_id: str
    superset_id: int | None = None
    rest_seconds: int | None = None
    notes: str | None = None
    sets: list[PostRoutinesRequestSet] = Field(default_factory=list)


class RoutinePayload(BaseModel):
    title: str
    folder_id: int | None = None
    notes: str | None = None
    exercises: list[PostRoutinesRequestExercise] = Field(default_factory=list)


class PostRoutinesRequestBody(BaseModel):
    routine: RoutinePayload


class ExerciseTemplate(BaseModel):
    id: str
    title: str
    type: str | None = None
    primary_muscle_group: str | None = None
    secondary_muscle_groups: list[str] | None = None
    is_custom: bool | None = None


class RoutineCreated(BaseModel):
    """Subset of Routine returned by POST /v1/routines (201)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str | None = None


# --- YAML definitions (exercise identified by name, resolved to template id later) ---


class YamlRoutineSet(BaseModel):
    type: RoutineSetType = "normal"
    weight_kg: float | None = None
    reps: int | None = None
    distance_meters: int | None = None
    duration_seconds: int | None = None
    custom_metric: float | None = None
    rep_range: RepRange | None = None


class YamlRoutineExercise(BaseModel):
    name: str
    superset_id: int | None = None
    rest_seconds: int | None = None
    notes: str | None = None
    sets: list[YamlRoutineSet] = Field(default_factory=list)


class YamlRoutineDefinition(BaseModel):
    title: str
    folder_id: int | None = None
    notes: str | None = None
    exercises: list[YamlRoutineExercise] = Field(default_factory=list)
