import random

from .models import OptimiserInput, OptimiserResult, PanelPlacement


def get_grid_layout(
    wall_w: int, wall_h: int, panel_w: int, panel_h: int
) -> list[tuple[int, int]]:
    """Generate ideal grid layout of panels on a wall.

    Panels placed left-to-right, bottom-to-top. Includes partial panels at the
    right and top edges so every part of the wall is addressed.
    """
    positions: list[tuple[int, int]] = []
    x = 0
    while x < wall_w:
        y = 0
        while y < wall_h:
            positions.append((x, y))
            y += panel_h
        x += panel_w
    return positions


def evaluate_fitness(
    positions: list[tuple[int, int]],
    wall_w: int,
    wall_h: int,
    panel_w: int,
    panel_h: int,
) -> float:
    """Score a panel layout — higher is better.

    Fitness = coverage_area / wall_area * 100 minus overlap and out-of-bounds
    penalties. Max possible score is 100.0 (perfect coverage, no issues).
    """
    wall_area = wall_w * wall_h
    covered_area = 0
    out_of_bounds_penalty = 0
    overlap_penalty = 0
    valid_rects: list[tuple[int, int, int, int]] = []

    for x, y in positions:
        if x >= wall_w or y >= wall_h or x + panel_w <= 0 or y + panel_h <= 0:
            out_of_bounds_penalty += 50
            continue
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(wall_w, x + panel_w), min(wall_h, y + panel_h)
        if x2 > x1 and y2 > y1:
            covered_area += (x2 - x1) * (y2 - y1)
            valid_rects.append((x1, y1, x2, y2))

    for i in range(len(valid_rects)):
        for j in range(i + 1, len(valid_rects)):
            r1, r2 = valid_rects[i], valid_rects[j]
            if max(r1[0], r2[0]) < min(r1[2], r2[2]) and max(r1[1], r2[1]) < min(r1[3], r2[3]):
                overlap_penalty += 10

    coverage = min(covered_area / wall_area * 100, 100.0)
    return coverage - out_of_bounds_penalty - overlap_penalty


def generate_individual(
    wall_w: int, wall_h: int, panel_w: int, panel_h: int
) -> list[tuple[int, int]]:
    """Generate one candidate layout by applying small random offsets to the grid.

    Offsets are ±100mm in both axes, creating variation while staying close to
    the optimal grid arrangement.
    """
    base = get_grid_layout(wall_w, wall_h, panel_w, panel_h)
    return [
        (max(0, x + random.randint(-100, 100)), max(0, y + random.randint(-100, 100)))
        for x, y in base
    ]


def generate_population(
    size: int, wall_w: int, wall_h: int, panel_w: int, panel_h: int
) -> list[list[tuple[int, int]]]:
    """Generate the initial population of `size` candidate layouts.

    Half start as the pure grid layout for elitism; the other half use random
    offsets to seed diversity in the search space.
    """
    grid = get_grid_layout(wall_w, wall_h, panel_w, panel_h)
    half = size // 2
    population = [list(grid) for _ in range(half)]
    population += [
        generate_individual(wall_w, wall_h, panel_w, panel_h)
        for _ in range(size - half)
    ]
    return population


def tournament_select(
    population: list, fitnesses: list[float], k: int = 3
) -> list[tuple[int, int]]:
    """Tournament selection: pick k random individuals, return the fittest."""
    candidates = random.sample(range(len(population)), min(k, len(population)))
    best = max(candidates, key=lambda i: fitnesses[i])
    return list(population[best])


def crossover(
    parent1: list, parent2: list
) -> tuple[list, list]:
    """Single-point crossover: split at a random point and swap the tails.

    Returns two child individuals. Length is bounded by the shorter parent.
    """
    n = min(len(parent1), len(parent2))
    if n <= 1:
        return list(parent1), list(parent2)
    point = random.randint(1, n - 1)
    child1 = parent1[:point] + parent2[point:n]
    child2 = parent2[:point] + parent1[point:n]
    return child1, child2


def mutate(
    individual: list,
    wall_w: int,
    wall_h: int,
    panel_w: int,
    panel_h: int,
    rate: float = 0.05,
) -> list[tuple[int, int]]:
    """Randomly shift panel positions by ±100mm, clamped to wall bounds.

    Each panel is mutated independently with probability `rate`.
    """
    result = []
    for x, y in individual:
        if random.random() < rate:
            x = max(0, min(wall_w, x + random.randint(-100, 100)))
            y = max(0, min(wall_h, y + random.randint(-100, 100)))
        result.append((x, y))
    return result


def positions_to_placements(
    positions: list[tuple[int, int]],
    wall_w: int,
    wall_h: int,
    panel_w: int,
    panel_h: int,
) -> list[PanelPlacement]:
    """Convert raw (x, y) positions into PanelPlacement objects.

    A panel is marked is_full=False if any part of it extends beyond the wall.
    Panels are numbered starting from 1.
    """
    return [
        PanelPlacement(
            panel_number=i,
            x=x,
            y=y,
            is_full=(
                x >= 0
                and y >= 0
                and x + panel_w <= wall_w
                and y + panel_h <= wall_h
            ),
        )
        for i, (x, y) in enumerate(positions, start=1)
    ]


def calculate_waste(
    positions: list[tuple[int, int]],
    wall_w: int,
    wall_h: int,
    panel_w: int,
    panel_h: int,
) -> float:
    """Calculate the percentage of the wall not covered by any panel.

    Only the within-wall portion of each panel counts toward coverage.
    """
    wall_area = wall_w * wall_h
    covered_area = sum(
        (min(wall_w, x + panel_w) - max(0, x)) * (min(wall_h, y + panel_h) - max(0, y))
        for x, y in positions
        if max(0, x) < min(wall_w, x + panel_w) and max(0, y) < min(wall_h, y + panel_h)
    )
    return max(0.0, (wall_area - covered_area) / wall_area * 100)


def run_optimisation(input: OptimiserInput) -> OptimiserResult:
    """Run the genetic algorithm to find the best panel layout for a given wall.

    Steps: generate population → evaluate → select → crossover → mutate → repeat.
    Elitism keeps the top 2 individuals each generation. Early exit at fitness ≥ 99.
    """
    wall_w, wall_h = input.wall_width_mm, input.wall_height_mm
    panel_w, panel_h = input.panel_width_mm, input.panel_height_mm

    try:
        population = generate_population(input.population_size, wall_w, wall_h, panel_w, panel_h)
        fitness_history: list[float] = []
        best_individual = get_grid_layout(wall_w, wall_h, panel_w, panel_h)
        best_fitness = -float("inf")
        best_generation = 0

        for gen in range(input.generations):
            fitnesses = [
                evaluate_fitness(ind, wall_w, wall_h, panel_w, panel_h)
                for ind in population
            ]

            top_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
            gen_best = fitnesses[top_idx]
            fitness_history.append(round(gen_best, 4))

            if gen_best > best_fitness:
                best_fitness = gen_best
                best_individual = list(population[top_idx])
                best_generation = gen

            if best_fitness >= 99.0:
                break

            sorted_idx = sorted(range(len(population)), key=lambda i: fitnesses[i], reverse=True)
            new_pop: list = [list(population[sorted_idx[0]]), list(population[sorted_idx[1]])]

            while len(new_pop) < input.population_size:
                p1 = tournament_select(population, fitnesses)
                p2 = tournament_select(population, fitnesses)
                c1, c2 = crossover(p1, p2)
                new_pop.append(mutate(c1, wall_w, wall_h, panel_w, panel_h))
                if len(new_pop) < input.population_size:
                    new_pop.append(mutate(c2, wall_w, wall_h, panel_w, panel_h))

            population = new_pop

        placements = positions_to_placements(best_individual, wall_w, wall_h, panel_w, panel_h)
        waste = calculate_waste(best_individual, wall_w, wall_h, panel_w, panel_h)
        wall_area = wall_w * wall_h
        covered = sum(
            (min(wall_w, x + panel_w) - max(0, x)) * (min(wall_h, y + panel_h) - max(0, y))
            for x, y in best_individual
            if max(0, x) < min(wall_w, x + panel_w) and max(0, y) < min(wall_h, y + panel_h)
        )
        coverage = min(covered / wall_area * 100, 100.0)

        return OptimiserResult(
            placements=placements,
            total_panels=sum(1 for p in placements if p.is_full),
            cut_panels=sum(1 for p in placements if not p.is_full),
            waste_percentage=round(waste, 2),
            coverage_percentage=round(coverage, 2),
            fitness_history=fitness_history,
            best_generation=best_generation,
        )

    except Exception:
        fallback = get_grid_layout(wall_w, wall_h, panel_w, panel_h)
        placements = positions_to_placements(fallback, wall_w, wall_h, panel_w, panel_h)
        waste = calculate_waste(fallback, wall_w, wall_h, panel_w, panel_h)
        wall_area = wall_w * wall_h
        covered = sum(
            (min(wall_w, x + panel_w) - max(0, x)) * (min(wall_h, y + panel_h) - max(0, y))
            for x, y in fallback
            if max(0, x) < min(wall_w, x + panel_w) and max(0, y) < min(wall_h, y + panel_h)
        )
        coverage = min(covered / wall_area * 100, 100.0) if wall_area > 0 else 0.0
        return OptimiserResult(
            placements=placements,
            total_panels=sum(1 for p in placements if p.is_full),
            cut_panels=sum(1 for p in placements if not p.is_full),
            waste_percentage=round(waste, 2),
            coverage_percentage=round(coverage, 2),
            fitness_history=[],
            best_generation=0,
        )
