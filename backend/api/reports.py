from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.core.ai.claude_client import generate_report
from backend.db.database import get_db
from backend.db.models import OptimisationRun, Project, Quote, Report, User

router = APIRouter(prefix="/reports", tags=["reports"])
projects_router = APIRouter(prefix="/projects", tags=["reports"])


class ReportGenerateRequest(BaseModel):
    project_id: int


class ReportOut(BaseModel):
    id: int
    project_id: int
    content_markdown: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/generate", response_model=ReportOut, status_code=201)
async def generate_report_endpoint(
    payload: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_owned_project(payload.project_id, current_user.id, db)

    runs_result = await db.execute(
        select(OptimisationRun).where(
            OptimisationRun.project_id == payload.project_id,
            OptimisationRun.status == "complete",
        )
    )
    runs = runs_result.scalars().all()
    if not runs:
        raise HTTPException(
            status_code=400,
            detail="Run at least one optimisation before generating a report",
        )

    quotes_result = await db.execute(
        select(Quote).where(Quote.project_id == payload.project_id)
    )
    quotes = quotes_result.scalars().all()

    runs_summary = [
        {
            "wall_width_mm": r.wall_width_mm,
            "wall_height_mm": r.wall_height_mm,
            "waste_percentage": r.waste_percentage or 0.0,
            "total_panels": _extract_field(r.result_json, "total_panels", 0),
            "cut_panels": _extract_field(r.result_json, "cut_panels", 0),
            "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else "N/A",
        }
        for r in runs
    ]

    quotes_summary = [
        {
            "total_cost": q.total_cost,
            "created_at": q.created_at.strftime("%Y-%m-%d") if q.created_at else "N/A",
        }
        for q in quotes
    ]

    try:
        content = await generate_report(
            project_name=project.name,
            project_location=project.location or "Not specified",
            project_status=project.status,
            project_description=project.description or "",
            optimisation_runs=runs_summary,
            quotes=quotes_summary,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="AI service unavailable")

    report = Report(project_id=payload.project_id, content_markdown=content)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@projects_router.get("/{project_id}/reports", response_model=list[ReportOut])
async def list_project_reports(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(project_id, current_user.id, db)

    result = await db.execute(
        select(Report)
        .where(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
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


def _extract_field(result_json: Optional[str], field: str, default):
    if not result_json:
        return default
    try:
        import json
        return json.loads(result_json).get(field, default)
    except (ValueError, KeyError):
        return default
