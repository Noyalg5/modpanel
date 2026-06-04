import asyncio
import json

import anthropic

from backend.core.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

_QUOTE_SYSTEM = (
    "You are an expert quantity surveyor and construction cost estimator specialising "
    "in Modern Methods of Construction (MMC) and Structural Insulated Panel (SIP) systems. "
    "You produce accurate, professional itemised quotes."
)

_REPORT_SYSTEM = (
    "You are a technical writer producing formal progress reports for a KTP (Knowledge Transfer "
    "Partnership) project between a university and an advanced manufacturing company in the modern "
    "construction sector. Reports must be professional, evidence-based, and suitable for review "
    "by both academic supervisors and company directors."
)


async def generate_quote(
    project_name: str,
    project_location: str,
    wall_width_mm: int,
    wall_height_mm: int,
    panel_name: str,
    panel_thickness_mm: int,
    cost_per_unit: float,
    total_panels: int,
    cut_panels: int,
    waste_percentage: float,
) -> dict:
    """Use AI model to generate a detailed construction cost quote in markdown format.

    Returns dict with keys: ai_summary (str), total_cost (float), breakdown_json (str).
    """
    wall_area_m2 = (wall_width_mm * wall_height_mm) / 1_000_000

    user_prompt = f"""Generate a detailed itemised cost quote in markdown for the following SIP construction project:

**Project Details:**
- Project Name: {project_name}
- Location: {project_location}
- Wall Dimensions: {wall_width_mm}mm wide × {wall_height_mm}mm high ({wall_area_m2:.2f} m²)

**Panel Specification:**
- Panel Type: {panel_name} ({panel_thickness_mm}mm thick)
- Cost per panel: £{cost_per_unit:.2f}
- Full panels required: {total_panels}
- Cut panels required: {cut_panels}
- Material waste: {waste_percentage:.1f}%

**Cost Breakdown (use these rates):**
- Material cost: panels × cost per unit + 10% waste allowance
- Labour: £48/hour, assume 1.5 hours per full panel, 0.75 hours per cut panel
- Plant & equipment hire: £150/day, assume 1 day per 20 panels (minimum 1 day)
- Delivery & logistics: £275 flat fee
- Subtotal
- Contingency: 5% of subtotal
- Grand subtotal
- VAT: 20%
- **Total**

Format the quote as a proper markdown table for the cost breakdown. Add a brief Executive Summary at the top (2 sentences). End with a Recommendations section (3 bullet points about this specific panel configuration).

After the markdown, on a new line, output ONLY this JSON (nothing else after it):
COST_JSON:{{"total_cost": <number>, "material": <number>, "labour": <number>, "plant": <number>, "delivery": <number>, "contingency": <number>, "vat": <number>}}"""

    def _call() -> str:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=_QUOTE_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    text = await asyncio.to_thread(_call)

    if "COST_JSON:" in text:
        parts = text.split("COST_JSON:", 1)
        markdown_part = parts[0].strip()
        json_str = parts[1].strip()
        try:
            cost_data = json.loads(json_str)
            total_cost = float(cost_data.get("total_cost", 0.0))
            breakdown_json = json_str
        except (json.JSONDecodeError, ValueError, KeyError):
            total_cost = 0.0
            breakdown_json = "{}"
    else:
        markdown_part = text.strip()
        total_cost = 0.0
        breakdown_json = "{}"

    return {
        "ai_summary": markdown_part,
        "total_cost": total_cost,
        "breakdown_json": breakdown_json,
    }


async def generate_report(
    project_name: str,
    project_location: str,
    project_status: str,
    project_description: str,
    optimisation_runs: list[dict],
    quotes: list[dict],
) -> str:
    """Use AI model to generate a formal KTP project progress report in markdown.

    Returns the full markdown string.
    """
    runs_table = _format_runs_table(optimisation_runs)
    quotes_table = _format_quotes_table(quotes)
    avg_cost = _average_cost(quotes)

    user_prompt = f"""Generate a formal KTP project progress report for the following project:

**Project:** {project_name}
**Location:** {project_location}
**Status:** {project_status}
**Description:** {project_description or "No description provided."}

**Optimisation Runs ({len(optimisation_runs)} runs completed):**
{runs_table}

**Quotes Generated ({len(quotes)} quotes, average cost: £{avg_cost:,.2f}):**
{quotes_table}

Write a formal technical report with these sections:
1. Executive Summary
2. Project Overview (name, location, status, description)
3. Technical Progress — describe the AI-assisted panel layout optimisation work, referencing the actual runs data above
4. Optimisation Results — include a markdown table of all runs with wall dimensions, panels used, and waste percentage
5. Financial Analysis — include a markdown table of all quotes with dates and totals, plus the average cost
6. Key Achievements This Period
7. Challenges & Mitigations
8. Next Steps & Milestones
9. Conclusion

Use formal academic and industry language appropriate for a KTP report reviewed by both university supervisors and company directors."""

    def _call() -> str:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            system=_REPORT_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    return await asyncio.to_thread(_call)


def _format_runs_table(runs: list[dict]) -> str:
    if not runs:
        return "No optimisation runs recorded."
    header = "| # | Wall Width (mm) | Wall Height (mm) | Full Panels | Cut Panels | Waste % | Date |"
    sep = "|---|---|---|---|---|---|---|"
    rows = [
        f"| {i + 1} | {r['wall_width_mm']} | {r['wall_height_mm']} "
        f"| {r.get('total_panels', 'N/A')} | {r.get('cut_panels', 'N/A')} "
        f"| {r['waste_percentage']:.1f}% | {r['created_at']} |"
        for i, r in enumerate(runs)
    ]
    return "\n".join([header, sep] + rows)


def _format_quotes_table(quotes: list[dict]) -> str:
    if not quotes:
        return "No quotes generated."
    header = "| # | Total Cost | Date |"
    sep = "|---|---|---|"
    rows = [
        f"| {i + 1} | £{q['total_cost']:,.2f} | {q['created_at']} |"
        for i, q in enumerate(quotes)
    ]
    return "\n".join([header, sep] + rows)


def _average_cost(quotes: list[dict]) -> float:
    if not quotes:
        return 0.0
    return sum(q["total_cost"] for q in quotes) / len(quotes)
