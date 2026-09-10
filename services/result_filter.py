import re
from urllib.parse import urlparse


GENERIC_TITLE_WORDS = [
    "agenda",
    "guía de madrid",
    "qué hacer en madrid",
    "eventos en madrid",
    "actividades y eventos",
    "calendario",
    "conciertos en madrid",
    "conciertos en españa",
    "musicales en madrid",
    "exposiciones en madrid",
]


def normalize_title(title: str) -> str:
    title = title.lower()

    title = re.sub(
        r"[^a-záéíóúüñ0-9 ]",
        " ",
        title
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


def is_generic_result(result: dict) -> bool:
    title = result.get(
        "title",
        ""
    ).lower()

    for word in GENERIC_TITLE_WORDS:
        if word in title:
            return True

    return False


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace(
            "www.",
            ""
        )
    except Exception:
        return ""


def deduplicate_results(
    results: list[dict]
) -> list[dict]:

    seen_titles = set()
    seen_urls = set()

    unique = []

    for result in results:
        title = result.get(
            "title",
            ""
        )

        url = result.get(
            "href",
            ""
        )

        normalized = normalize_title(
            title
        )

        if not normalized:
            continue

        if url in seen_urls:
            continue

        if normalized in seen_titles:
            continue

        seen_titles.add(
            normalized
        )

        seen_urls.add(
            url
        )

        unique.append(
            result
        )

    return unique


def filter_results(
    results: list[dict],
    max_results: int = 4
) -> list[dict]:

    results = deduplicate_results(
        results
    )

    results = [
        result
        for result in results
        if not is_generic_result(result)
    ]

    return results[:max_results]