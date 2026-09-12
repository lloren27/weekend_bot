import re
import unicodedata
from typing import Any


VENUE_ALIAS_GROUPS = (
    (
        "cide segovia",
        "cide",
        "recinto del cide",
        "centro de innovacion desarrollo empresarial cide",
        "centro de innovacion y desarrollo empresarial cide",
        "cide centro de innovacion y desarrollo empresarial",
        "centro de innovacion y desarrollo empresarial",
    ),
    (
        "movistar arena",
        "wizink center",
        "palacio de deportes",
        "palacio de deportes de la comunidad de madrid",
        "palacio de los deportes",
        "palacio de los deportes de madrid",
    ),
    (
        "santiago bernabeu",
        "bernabeu",
        "estadio santiago bernabeu",
        "estadio bernabeu",
    ),
    (
        "riyadh air metropolitano",
        "civitas metropolitano",
        "wanda metropolitano",
        "estadio metropolitano",
        "metropolitano",
    ),
    (
        "estadio de vallecas",
        "campo de futbol de vallecas",
        "campo de futbol de vallecas estadio de vallecas",
        "vallecas",
    ),
    (
        "coliseum",
        "coliseum alfonso perez",
        "estadio coliseum",
        "estadio coliseum alfonso perez",
    ),
    (
        "estadio municipal de butarque",
        "butarque",
        "estadio butarque",
    ),
    (
        "estadio fernando torres",
        "fernando torres",
    ),
    (
        "la riviera",
        "sala la riviera",
    ),
    (
        "palacio vistalegre",
        "palacio vistalegre arena",
        "vistalegre arena",
    ),
    (
        "teatro eslava",
        "joy eslava",
        "sala joy eslava",
    ),
    (
        "teatro barcelo",
        "sala barcelo",
        "pacha madrid",
    ),
    (
        "real jardin botanico alfonso xiii",
        "jardin botanico alfonso xiii",
        "botanico complutense",
    ),
)


VENUE_ALIASES = {
    alias: aliases[0]
    for aliases in VENUE_ALIAS_GROUPS
    for alias in aliases
}


def to_text(
    value: Any
) -> str:
    """
    Convierte valores procedentes de JSON/JSON-LD
    en texto de forma segura.

    Soporta:
    - str
    - list
    - tuple
    - set
    - dict con name / @value
    - números y otros valores simples
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(
        value,
        (list, tuple, set)
    ):
        parts = []

        for item in value:
            text = to_text(item)

            if text:
                parts.append(text)

        return ", ".join(parts)

    if isinstance(value, dict):
        # Casos habituales en JSON-LD.
        for key in (
            "name",
            "@value",
            "value",
        ):
            if key in value:
                return to_text(
                    value[key]
                )

        return ""

    return str(value).strip()


def normalize_text(
    value: Any
) -> str:
    text = to_text(value)

    if not text:
        return ""

    text = text.lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = re.sub(
        r"[^a-z0-9 ]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_venue_name(
    value: Any
) -> str:
    """
    Normaliza recintos conocidos.

    Algunas fuentes publican el nombre
    comercial y otras el nombre popular
    o histórico. Para deduplicar nos
    interesa el identificador estable
    del recinto, no la marca visible.
    """

    normalized = normalize_text(
        value
    )

    if not normalized:
        return ""

    return VENUE_ALIASES.get(
        normalized,
        normalized,
    )


def normalize_time(
    value: Any
) -> str | None:
    text = to_text(value)

    if not text:
        return None

    match = re.search(
        r"(?<![\d:])([01]?\d|2[0-3])[:.h]([0-5]\d)(?!\d)",
        text
    )

    if not match:
        return None

    return (
        f"{int(match.group(1)):02d}:"
        f"{int(match.group(2)):02d}"
    )
