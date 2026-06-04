import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.core.carbon import (
    calculate_carbon_saving,
    calculate_panel_carbon,
    calculate_traditional_carbon,
)
from backend.core.optimiser.genetic import run_optimisation
from backend.core.optimiser.models import OptimiserInput
from backend.db.database import get_db
from backend.db.models import OptimisationRun, PanelType, Project, User

router = APIRouter(prefix="/optimiser", tags=["optimiser"])
projects_router = APIRouter(prefix="/projects", tags=["optimiser"])


class OptimiserRunRequest(BaseModel):
    project_id: int
    panel_type_id: int
    wall_width_mm: int
    wall_height_mm: int

    @field_validator("wall_width_mm", "wall_height_mm")
    @classmethod
    def validate_wall_dimension(cls, v: int) -> int:
        if v < 500 or v > 50000:
            raise ValueError("Wall dimensions must be between 500mm and 50000mm")
        return v


class OptimiserRunOut(BaseModel):
    id: int
    project_id: int
    panel_type_id: int
    wall_width_mm: int
    wall_height_mm: int
    status: str
    waste_percentage: Optional[float]
    result_json: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/run", response_model=OptimiserRunOut, status_code=201)
async def run_optimiser(
    payload: OptimiserRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_owned_project(payload.project_id, current_user.id, db)

    result = await db.execute(select(PanelType).where(PanelType.id == payload.panel_type_id))
    panel_type = result.scalar_one_or_none()
    if not panel_type:
        raise HTTPException(status_code=404, detail="Panel type not found")

    opt_input = OptimiserInput(
        wall_width_mm=payload.wall_width_mm,
        wall_height_mm=payload.wall_height_mm,
        panel_width_mm=panel_type.width_mm,
        panel_height_mm=panel_type.height_mm,
    )
    opt_result = run_optimisation(opt_input)

    run = OptimisationRun(
        project_id=payload.project_id,
        panel_type_id=payload.panel_type_id,
        wall_width_mm=payload.wall_width_mm,
        wall_height_mm=payload.wall_height_mm,
        status="complete",
        result_json=opt_result.model_dump_json(),
        waste_percentage=opt_result.waste_percentage,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


@router.get("/{run_id}", response_model=OptimiserRunOut)
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(OptimisationRun).where(OptimisationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Optimisation run not found")

    await _get_owned_project(run.project_id, current_user.id, db)
    return run


@projects_router.get("/{project_id}/optimisations", response_model=list[OptimiserRunOut])
async def list_project_optimisations(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(project_id, current_user.id, db)

    result = await db.execute(
        select(OptimisationRun)
        .where(OptimisationRun.project_id == project_id)
        .order_by(OptimisationRun.created_at.desc())
    )
    return result.scalars().all()


class CarbonResult(BaseModel):
    sip_carbon: dict
    traditional_carbon: dict
    saving: dict
    panel_type_name: str


@router.get("/{run_id}/carbon", response_model=CarbonResult)
async def get_carbon_estimate(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(OptimisationRun).where(OptimisationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Optimisation run not found")

    await _get_owned_project(run.project_id, current_user.id, db)

    pt_result = await db.execute(select(PanelType).where(PanelType.id == run.panel_type_id))
    panel_type = pt_result.scalar_one_or_none()
    if not panel_type:
        raise HTTPException(status_code=404, detail="Panel type not found")

    run_data = json.loads(run.result_json or "{}")
    total_panels = run_data.get("total_panels", 0)
    cut_panels = run_data.get("cut_panels", 0)

    sip = calculate_panel_carbon(panel_type.material, total_panels, cut_panels)
    traditional = calculate_traditional_carbon(run.wall_width_mm, run.wall_height_mm)
    saving = calculate_carbon_saving(sip, traditional)

    return CarbonResult(
        sip_carbon=sip,
        traditional_carbon=traditional,
        saving=saving,
        panel_type_name=panel_type.name,
    )


class CompareRequest(BaseModel):
    project_id: int
    wall_width_mm: int
    wall_height_mm: int
    panel_type_ids: list[int]

    @field_validator("panel_type_ids")
    @classmethod
    def validate_panel_count(cls, v: list[int]) -> list[int]:
        if len(v) < 2 or len(v) > 4:
            raise ValueError("Select between 2 and 4 panel types to compare")
        return v

    @field_validator("wall_width_mm", "wall_height_mm")
    @classmethod
    def validate_compare_dimension(cls, v: int) -> int:
        if v < 500 or v > 50000:
            raise ValueError("Wall dimensions must be between 500mm and 50000mm")
        return v


class CompareResult(BaseModel):
    runs: list[OptimiserRunOut]
    best_panel_type_id: int
    summary: str


@router.post("/compare", response_model=CompareResult, status_code=201)
async def compare_panels(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(payload.project_id, current_user.id, db)

    run_records: list[tuple[OptimisationRun, PanelType]] = []
    for panel_type_id in payload.panel_type_ids:
        pt_result = await db.execute(select(PanelType).where(PanelType.id == panel_type_id))
        panel_type = pt_result.scalar_one_or_none()
        if not panel_type:
            raise HTTPException(status_code=404, detail=f"Panel type {panel_type_id} not found")

        opt_result = run_optimisation(
            OptimiserInput(
                wall_width_mm=payload.wall_width_mm,
                wall_height_mm=payload.wall_height_mm,
                panel_width_mm=panel_type.width_mm,
                panel_height_mm=panel_type.height_mm,
            )
        )
        run = OptimisationRun(
            project_id=payload.project_id,
            panel_type_id=panel_type_id,
            wall_width_mm=payload.wall_width_mm,
            wall_height_mm=payload.wall_height_mm,
            status="complete",
            result_json=opt_result.model_dump_json(),
            waste_percentage=opt_result.waste_percentage,
        )
        db.add(run)
        run_records.append((run, panel_type))

    await db.commit()
    for run, _ in run_records:
        await db.refresh(run)

    best_run, best_panel = min(run_records, key=lambda x: x[0].waste_percentage or 0.0)
    summary = f"{best_panel.name} achieves lowest waste at {best_run.waste_percentage:.1f}%"

    return CompareResult(
        runs=[OptimiserRunOut.model_validate(run) for run, _ in run_records],
        best_panel_type_id=best_run.panel_type_id,
        summary=summary,
    )


async def _get_owned_project(project_id: int, user_id: int, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
