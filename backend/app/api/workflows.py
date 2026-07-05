import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowUpdate

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/", response_model=list[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()))
    workflows = result.scalars().all()
    return [WorkflowResponse.model_validate(w) for w in workflows]


@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    body: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    import json as _json
    workflow = Workflow(
        name=body.name,
        description=body.description,
        trigger_type=body.trigger_type,
        trigger_config=_json.dumps(body.trigger_config) if body.trigger_config else None,
        steps=_json.dumps([s.model_dump() for s in body.steps]),
    )
    db.add(workflow)
    await db.flush()
    return WorkflowResponse.model_validate(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowResponse.model_validate(workflow)


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: uuid.UUID,
    body: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.is_active:
        raise HTTPException(status_code=400, detail="Deactivate workflow before editing")
    update_data = body.model_dump(exclude_unset=True)
    if "steps" in update_data and update_data["steps"] is not None:
        update_data["steps"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in update_data["steps"]]
    for field, value in update_data.items():
        setattr(workflow, field, value)
    await db.flush()
    return WorkflowResponse.model_validate(workflow)


@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.is_active = True
    await db.flush()
    return {"success": True, "message": "Workflow activated"}


@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.is_active = False
    await db.flush()
    return {"success": True, "message": "Workflow deactivated"}


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.run_count += 1
    workflow.last_run_at = datetime.now(timezone.utc)
    await db.flush()
    return {"success": True, "message": "Workflow triggered"}
