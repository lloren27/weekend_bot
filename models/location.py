from dataclasses import dataclass, field


@dataclass
class TargetLocation:
    name: str

    country: str = "España"

    regions: set[str] = field(
        default_factory=set
    )

    municipalities: set[str] = field(
        default_factory=set
    )

    postal_prefixes: set[str] = field(
        default_factory=set
    )