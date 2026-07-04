from typing import Any

from pydantic import BaseModel, ConfigDict


class WorkflowStep(BaseModel):
    step_type: str
    config: dict


class WorkflowBase(BaseModel):
    name: str
    description: str | None = None
    trigger_type: str
    trigger_config: dict | None = None
    steps: list[WorkflowStep]


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    steps: list[WorkflowStep] | None = None
    trigger_config: dict | None = None


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    trigger_type: str
    trigger_config: Any | None = None
    steps: Any
    is_active: bool
    run_count: int
    last_run_at: str | None = None
    created_at: str
    updated_at: str | None = None
