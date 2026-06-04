from pydantic import BaseModel


class OptimiserInput(BaseModel):
    wall_width_mm: int
    wall_height_mm: int
    panel_width_mm: int
    panel_height_mm: int
    population_size: int = 50
    generations: int = 100


class PanelPlacement(BaseModel):
    panel_number: int
    x: int
    y: int
    is_full: bool


class OptimiserResult(BaseModel):
    placements: list[PanelPlacement]
    total_panels: int
    cut_panels: int
    waste_percentage: float
    coverage_percentage: float
    fitness_history: list[float]
    best_generation: int
