from ddgs import DDGS

from config import CACHE_TTL_SECONDS
from services.cache import TTLCache


_SEARCH_CACHE = TTLCache(
    CACHE_TTL_SECONDS
)


def copy_results(
    results: list[dict],
) -> list[dict]:
    return [
        dict(result)
        for result in results
    ]


def search_web(
    query: str,
    max_results: int = 5
):
    cache_key = (
        "ddgs_text",
        "es-es",
        query,
        max_results,
    )

    cached_results = _SEARCH_CACHE.get(
        cache_key
    )

    if cached_results is not None:
        return copy_results(
            cached_results
        )

    with DDGS() as ddgs:
        results = ddgs.text(
            query,
            region="es-es",
            max_results=max_results
        )

        results = list(
            results
        )

    _SEARCH_CACHE.set(
        cache_key,
        copy_results(
            results
        ),
    )

    return copy_results(
        results
    )


def clear_search_cache() -> None:
    _SEARCH_CACHE.clear()
