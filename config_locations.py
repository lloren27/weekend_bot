import unicodedata

from models.location import TargetLocation


def normalize_location_name(
    value: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    ascii_text = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )

    return " ".join(
        ascii_text
        .lower()
        .replace("-", " ")
        .split()
    )


LOCATION_REGISTRY = {
    "comunidad_madrid": TargetLocation(
        name="Comunidad de Madrid",
        country="España",
        regions={
            "Comunidad de Madrid",
            "Madrid",
        },
        municipalities={
            "Madrid",
        },
        postal_prefixes={
            "28",
        },
    ),
    "madrid": TargetLocation(
        name="Madrid",
        country="España",
        regions={
            "Comunidad de Madrid",
            "Madrid",
        },
        municipalities={
            "Madrid",
        },
        postal_prefixes={
            "28",
        },
    ),
    "barcelona": TargetLocation(
        name="Barcelona",
        country="España",
        regions={
            "Cataluña",
            "Catalunya",
            "Barcelona",
        },
        municipalities={
            "Barcelona",
        },
        postal_prefixes={
            "08",
        },
    ),
    "valencia": TargetLocation(
        name="Valencia",
        country="España",
        regions={
            "Comunidad Valenciana",
            "Comunitat Valenciana",
            "Valencia",
        },
        municipalities={
            "Valencia",
        },
        postal_prefixes={
            "46",
        },
    ),
    "sevilla": TargetLocation(
        name="Sevilla",
        country="España",
        regions={
            "Andalucía",
            "Sevilla",
        },
        municipalities={
            "Sevilla",
        },
        postal_prefixes={
            "41",
        },
    ),
    "zaragoza": TargetLocation(
        name="Zaragoza",
        country="España",
        regions={
            "Aragón",
            "Zaragoza",
        },
        municipalities={
            "Zaragoza",
        },
        postal_prefixes={
            "50",
        },
    ),
    "malaga": TargetLocation(
        name="Málaga",
        country="España",
        regions={
            "Andalucía",
            "Málaga",
            "Malaga",
        },
        municipalities={
            "Málaga",
            "Malaga",
        },
        postal_prefixes={
            "29",
        },
    ),
    "bilbao": TargetLocation(
        name="Bilbao",
        country="España",
        regions={
            "País Vasco",
            "Euskadi",
            "Bizkaia",
            "Vizcaya",
        },
        municipalities={
            "Bilbao",
        },
        postal_prefixes={
            "48",
        },
    ),
    "alicante": TargetLocation(
        name="Alicante",
        country="España",
        regions={
            "Comunidad Valenciana",
            "Comunitat Valenciana",
            "Alicante",
            "Alacant",
        },
        municipalities={
            "Alicante",
            "Alacant",
        },
        postal_prefixes={
            "03",
        },
    ),
    "murcia": TargetLocation(
        name="Murcia",
        country="España",
        regions={
            "Región de Murcia",
            "Murcia",
        },
        municipalities={
            "Murcia",
        },
        postal_prefixes={
            "30",
        },
    ),
    "granada": TargetLocation(
        name="Granada",
        country="España",
        regions={
            "Andalucía",
            "Granada",
        },
        municipalities={
            "Granada",
        },
        postal_prefixes={
            "18",
        },
    ),
    "cordoba": TargetLocation(
        name="Córdoba",
        country="España",
        regions={
            "Andalucía",
            "Córdoba",
            "Cordoba",
        },
        municipalities={
            "Córdoba",
            "Cordoba",
        },
        postal_prefixes={
            "14",
        },
    ),
    "segovia": TargetLocation(
        name="Segovia",
        country="España",
        regions={
            "Castilla y León",
            "Segovia",
        },
        municipalities={
            "Segovia",
        },
        postal_prefixes={
            "40",
        },
    ),
    "valladolid": TargetLocation(
        name="Valladolid",
        country="España",
        regions={
            "Castilla y León",
            "Valladolid",
        },
        municipalities={
            "Valladolid",
        },
        postal_prefixes={
            "47",
        },
    ),
    "vigo": TargetLocation(
        name="Vigo",
        country="España",
        regions={
            "Galicia",
            "Pontevedra",
        },
        municipalities={
            "Vigo",
        },
        postal_prefixes={
            "36",
        },
    ),
    "a_coruna": TargetLocation(
        name="A Coruña",
        country="España",
        regions={
            "Galicia",
            "A Coruña",
            "La Coruña",
        },
        municipalities={
            "A Coruña",
            "La Coruña",
        },
        postal_prefixes={
            "15",
        },
    ),
    "gijon": TargetLocation(
        name="Gijón",
        country="España",
        regions={
            "Asturias",
            "Principado de Asturias",
        },
        municipalities={
            "Gijón",
            "Gijon",
        },
        postal_prefixes={
            "33",
        },
    ),
    "palma": TargetLocation(
        name="Palma",
        country="España",
        regions={
            "Islas Baleares",
            "Illes Balears",
            "Mallorca",
        },
        municipalities={
            "Palma",
            "Palma de Mallorca",
        },
        postal_prefixes={
            "07",
        },
    ),
    "las_palmas": TargetLocation(
        name="Las Palmas de Gran Canaria",
        country="España",
        regions={
            "Canarias",
            "Las Palmas",
            "Gran Canaria",
        },
        municipalities={
            "Las Palmas de Gran Canaria",
        },
        postal_prefixes={
            "35",
        },
    ),
    "santa_cruz_tenerife": TargetLocation(
        name="Santa Cruz de Tenerife",
        country="España",
        regions={
            "Canarias",
            "Santa Cruz de Tenerife",
            "Tenerife",
        },
        municipalities={
            "Santa Cruz de Tenerife",
        },
        postal_prefixes={
            "38",
        },
    ),
}


LOCATION_ALIASES = {
    "comunidad de madrid": "comunidad_madrid",
    "madrid comunidad": "comunidad_madrid",
    "madrid": "madrid",
    "barcelona": "barcelona",
    "bcn": "barcelona",
    "valencia": "valencia",
    "valència": "valencia",
    "sevilla": "sevilla",
    "seville": "sevilla",
    "zaragoza": "zaragoza",
    "malaga": "malaga",
    "málaga": "malaga",
    "bilbao": "bilbao",
    "alicante": "alicante",
    "alacant": "alicante",
    "murcia": "murcia",
    "granada": "granada",
    "cordoba": "cordoba",
    "córdoba": "cordoba",
    "valladolid": "valladolid",
    "vigo": "vigo",
    "a coruna": "a_coruna",
    "a Coruña": "a_coruna",
    "la coruna": "a_coruna",
    "la Coruña": "a_coruna",
    "coruna": "a_coruna",
    "coruña": "a_coruna",
    "gijon": "gijon",
    "gijón": "gijon",
    "palma": "palma",
    "palma de mallorca": "palma",
    "las palmas": "las_palmas",
    "las palmas de gran canaria": "las_palmas",
    "santa cruz": "santa_cruz_tenerife",
    "santa cruz de tenerife": "santa_cruz_tenerife",
    "tenerife": "santa_cruz_tenerife",
}

DEFAULT_LOCATION_KEY = "comunidad_madrid"
CURRENT_LOCATION = LOCATION_REGISTRY[
    DEFAULT_LOCATION_KEY
]


def get_location(
    key: str,
) -> TargetLocation:
    return LOCATION_REGISTRY[
        key
    ]


def get_default_location() -> TargetLocation:
    return CURRENT_LOCATION


def find_location_key(
    value: str,
) -> str | None:
    normalized = normalize_location_name(
        value
    )

    for alias, key in LOCATION_ALIASES.items():
        if normalize_location_name(alias) == normalized:
            return key

    if normalized in LOCATION_REGISTRY:
        return normalized

    return None


def find_location(
    value: str,
) -> TargetLocation | None:
    key = find_location_key(
        value
    )

    if key is None:
        return None

    return get_location(
        key
    )


def get_location_options() -> list[tuple[str, TargetLocation]]:
    return list(
        LOCATION_REGISTRY.items()
    )
