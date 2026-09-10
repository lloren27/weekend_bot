from ddgs import DDGS


def search_web(
    query: str,
    max_results: int = 5
):
    with DDGS() as ddgs:
        results = ddgs.text(
            query,
            region="es-es",
            max_results=max_results
        )

        return list(results)