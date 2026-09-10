from urllib.parse import urlparse


SOURCE_RULES = [
    (
        "realmadrid.com",
        "Real Madrid",
        100,
    ),
    (
        "atleticodemadrid.com",
        "Atlético de Madrid",
        100,
    ),
    (
        "rayovallecano.es",
        "Rayo Vallecano",
        100,
    ),
    (
        "getafecf.com",
        "Getafe CF",
        100,
    ),
    (
        "cdleganes.com",
        "CD Leganés",
        100,
    ),
    (
        "movistararena.es",
        "Movistar Arena",
        100,
    ),
    (
        "laliga.com",
        "LaLiga",
        95,
    ),
    (
        "acb.com",
        "ACB",
        95,
    ),
    (
        "rfef.es",
        "RFEF",
        90,
    ),
    (
        "marca.com",
        "Marca",
        70,
    ),
    (
        "mundodeportivo.com",
        "Mundo Deportivo",
        65,
    ),
    (
        "palaciovistalegre.com",
        "Palacio Vistalegre",
        100,
    ),
    (
        "salariviera.com",
        "La Riviera",
        100,
    ),
    (
        "livenation.es",
        "Live Nation",
        90,
    ),
    (
        "ticketmaster.es",
        "Ticketmaster",
        85,
    ),
    (
        "songkick.com",
        "Songkick",
        60,
    ),
]


def get_domain(
    url: str
) -> str:
    try:
        return (
            urlparse(url)
            .netloc
            .lower()
            .replace("www.", "")
        )
    except Exception:
        return ""


def get_source_info(
    url: str
) -> tuple[str, int]:

    domain = get_domain(url)

    for source_domain, name, priority in SOURCE_RULES:
        if source_domain in domain:
            return name, priority

    return domain, 40
