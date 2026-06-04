CARBON_FACTORS: dict[str, float] = {
    "OSB/Expanded Polystyrene": 3.2,
    "OSB/Polyurethane Foam": 4.1,
    "default": 3.5,
}
BRICK_MORTAR_CARBON_PER_M2 = 85.0
TRANSPORT_CARBON_PER_PANEL = 0.8


def calculate_panel_carbon(material: str, total_panels: int, cut_panels: int) -> dict:
    """Calculate embodied carbon for SIP construction."""
    factor = CARBON_FACTORS.get(material, CARBON_FACTORS["default"])
    all_panels = total_panels + cut_panels
    embodied = all_panels * factor
    transport = all_panels * TRANSPORT_CARBON_PER_PANEL
    total_sip = embodied + transport
    carbon_per_panel = total_sip / all_panels if all_panels else 0.0
    return {
        "embodied_kgco2e": round(embodied, 2),
        "transport_kgco2e": round(transport, 2),
        "total_kgco2e": round(total_sip, 2),
        "carbon_per_panel": round(carbon_per_panel, 3),
    }


def calculate_traditional_carbon(wall_width_mm: int, wall_height_mm: int) -> dict:
    """Calculate embodied carbon for equivalent traditional brick construction."""
    wall_area_m2 = (wall_width_mm / 1000) * (wall_height_mm / 1000)
    total = wall_area_m2 * BRICK_MORTAR_CARBON_PER_M2
    return {
        "wall_area_m2": round(wall_area_m2, 4),
        "total_kgco2e": round(total, 2),
        "carbon_per_m2": BRICK_MORTAR_CARBON_PER_M2,
    }


def calculate_carbon_saving(sip_result: dict, traditional_result: dict) -> dict:
    """Compare SIP vs traditional construction carbon impact."""
    saving_kgco2e = traditional_result["total_kgco2e"] - sip_result["total_kgco2e"]
    saving_pct = (saving_kgco2e / traditional_result["total_kgco2e"]) * 100 if traditional_result["total_kgco2e"] else 0.0
    trees_equivalent = saving_kgco2e / 21.0
    return {
        "saving_kgco2e": round(saving_kgco2e, 2),
        "saving_percentage": round(saving_pct, 2),
        "trees_equivalent": round(trees_equivalent, 2),
        "is_lower_carbon": saving_kgco2e > 0,
    }
