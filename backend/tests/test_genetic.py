import pytest

from backend.core.optimiser.genetic import (
    evaluate_fitness,
    generate_individual,
    get_grid_layout,
    run_optimisation,
)
from backend.core.optimiser.models import OptimiserInput


def test_grid_layout_fills_wall():
    positions = get_grid_layout(wall_w=6000, wall_h=2400, panel_w=1200, panel_h=2400)
    assert len(positions) == 5
    x_values = [p[0] for p in positions]
    assert all(x % 1200 == 0 for x in x_values)


def test_individual_within_bounds():
    individual = generate_individual(6000, 2400, 1200, 2400)
    assert all(x >= 0 for x, _ in individual)
    assert all(y >= 0 for _, y in individual)


def test_fitness_perfect_layout():
    positions = get_grid_layout(6000, 2400, 1200, 2400)
    fitness = evaluate_fitness(positions, 6000, 2400, 1200, 2400)
    assert fitness >= 95.0


def test_optimisation_reduces_waste():
    result = run_optimisation(
        OptimiserInput(
            wall_width_mm=6000,
            wall_height_mm=2400,
            panel_width_mm=1200,
            panel_height_mm=2400,
            generations=50,
        )
    )
    assert result.waste_percentage < 10.0
    assert result.total_panels == 5


def test_fitness_improves_over_generations():
    inp_base = dict(wall_width_mm=6000, wall_height_mm=2400, panel_width_mm=1200, panel_height_mm=2400)
    result_10 = run_optimisation(OptimiserInput(**inp_base, generations=10))
    result_50 = run_optimisation(OptimiserInput(**inp_base, generations=50))
    assert result_50.fitness_history[-1] >= result_10.fitness_history[-1]


def test_wall_smaller_than_panel():
    result = run_optimisation(
        OptimiserInput(
            wall_width_mm=800,
            wall_height_mm=800,
            panel_width_mm=1200,
            panel_height_mm=2400,
        )
    )
    assert result.total_panels == 0
    assert result.cut_panels >= 0
