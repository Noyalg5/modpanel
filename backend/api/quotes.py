import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.core.ai.claude_client import generate_quote
from backend.db.database import get_db
from backend.db.models import OptimisationRun, PanelType, Project, Quote, User

router = APIRouter(prefix="/quotes", tags=["quotes"])
projects_router = APIRouter(prefix="/projects", tags=["quotes"])


class QuoteGenerateRequest(BaseModel):
    project_id: int
    optimisation_run_id: int


class QuoteOut(BaseModel):
    id: int
    project_id: int
    optimisation_run_id: Optional[int]
    ai_summary: str
    total_cost: float
    breakdown_json: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/generate", response_model=QuoteOut, status_code=201)
async def generate_quote_endpoint(
    payload: QuoteGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_owned_project(payload.project_id, current_user.id, db)

    run_result = await db.execute(
        select(OptimisationRun).where(
            OptimisationRun.id == payload.optimisation_run_id,
            OptimisationRun.project_id == payload.project_id,
        )
    )
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Optimisation run not found for this project")
    if run.status != "complete":
        raise HTTPException(status_code=400, detail="Optimisation run is not complete")

    panel_result = await db.execute(select(PanelType).where(PanelType.id == run.panel_type_id))
    panel_type = panel_result.scalar_one_or_none()
    if not panel_type:
        raise HTTPException(status_code=404, detail="Panel type not found")

    run_data = json.loads(run.result_json or "{}")
    total_panels = run_data.get("total_panels", 0)
    cut_panels = run_data.get("cut_panels", 0)
    waste_pct = run_data.get("waste_percentage", 0.0)

    try:
        quote_data = await generate_quote(
            project_name=project.name,
            project_location=project.location or "Not specified",
            wall_width_mm=run.wall_width_mm,
            wall_height_mm=run.wall_height_mm,
            panel_name=panel_type.name,
            panel_thickness_mm=panel_type.thickness_mm,
            cost_per_unit=panel_type.cost_per_unit,
            total_panels=total_panels,
            cut_panels=cut_panels,
            waste_percentage=waste_pct,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=str(e))

    quote = Quote(
        project_id=payload.project_id,
        optimisation_run_id=payload.optimisation_run_id,
        ai_summary=quote_data["ai_summary"],
        total_cost=quote_data["total_cost"],
        breakdown_json=quote_data["breakdown_json"],
    )
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    return quote


@projects_router.get("/{project_id}/quotes", response_model=list[QuoteOut])
async def list_project_quotes(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(project_id, current_user.id, db)

    result = await db.execute(
        select(Quote)
        .where(Quote.project_id == project_id)
        .order_by(Quote.created_at.desc())
    )
    return result.scalars().all()


async def _get_owned_project(project_id: int, user_id: int, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
