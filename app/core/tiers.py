from dataclasses import dataclass


@dataclass(frozen=True)
class TierInfo:
    number: int
    name: str
    definition: str
    marker: str | None  # shown beside the name wherever the tier appears


TIERS: dict[int, TierInfo] = {
    1: TierInfo(
        1,
        "Direct statement of intent",
        "The company's own press release, earnings call or investor material "
        "states expansion into the EU or Ireland specifically.",
        None,
    ),
    2: TierInfo(
        2,
        "Regulatory / structural indicator",
        "EU subsidiary registration, CE marking application, or trade mission "
        "delegation membership.",
        None,
    ),
    3: TierInfo(
        3,
        "Behavioural proxy",
        "Hiring for EU, Dublin or European roles. Inference, not confirmation.",
        "inference",
    ),
    4: TierInfo(
        4,
        "Sector / policy tailwind",
        "General EU-Canada dialogue or CETA developments. Never a company "
        "signal on its own.",
        "context only",
    ),
    0: TierInfo(
        0,
        "Not a signal",
        "Matched a tracked company but carries no expansion evidence. Stored, "
        "hidden by default, never in the digest.",
        None,
    ),
}

SECTORS: dict[str, str] = {
    "ai_cloud": "AI / cloud infrastructure",
    "life_sciences": "Life sciences / biopharma",
    "fintech": "Fintech",
}


def tier_info(tier: int) -> TierInfo:
    """Unknown tier numbers get an explicit label rather than a crash."""
    return TIERS.get(tier, TierInfo(tier, f"Unrecognised tier {tier}", "", None))


def sector_label(sector: str) -> str:
    return SECTORS.get(sector, sector)
