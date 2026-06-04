from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.models import PanelType

router = APIRouter(prefix="/panels", tags=["panels"])

_SEED_PANELS = [
    {
        "name": "Standard SIP 100mm",
        "width_mm": 1200,
        "height_mm": 2400,
        "thickness_mm": 100,
        "material": "OSB/Expanded Polystyrene",
        "cost_per_unit": 85.0,
    },
    {
        "name": "Insulated SIP 150mm",
        "width_mm": 1200,
        "height_mm": 2400,
        "thickness_mm": 150,
        "material": "OSB/Expanded Polystyrene",
        "cost_per_unit": 110.0,
    },
    {
        "name": "Structural SIP 200mm",
        "width_mm": 1200,
        "height_mm": 2700,
        "thickness_mm": 200,
        "material": "OSB/Polyurethane Foam",
        "cost_per_unit": 145.0,
    },
]


class PanelTypeCreate(BaseModel):
    name: str
    width_mm: int
    height_mm: int
    thickness_mm: int
    material: str
    cost_per_unit: float


class PanelTypeOut(BaseModel):
    id: int
    name: str
    width_mm: int
    height_mm: int
    thickness_mm: int
    material: str
    cost_per_unit: float

    model_config = {"from_attributes": True}


@router.get("", response_model=list[PanelTypeOut])
async def list_panels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PanelType))
    return result.scalars().all()


@router.post("", response_model=PanelTypeOut, status_code=201)
async def create_panel(payload: PanelTypeCreate, db: AsyncSession = Depends(get_db)):
    panel = PanelType(**payload.model_dump())
    db.add(panel)
    await db.commit()
    await db.refresh(panel)
    return panel


async def seed_panels(db: AsyncSession) -> None:
    result = await db.execute(select(PanelType).limit(1))
    if result.scalar_one_or_none():
        return
    for data in _SEED_PANELS:
        db.add(PanelType(**data))
    await db.commit()
