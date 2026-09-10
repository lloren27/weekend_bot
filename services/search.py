from asyncio import base_events
from services.dates import get_next_weekend
from services.sports import (
    search_football,
    search_basketball,
    search_running,
    search_cycling,
)
from services.web_search import search_web
from services.result_filter import filter_results


def search_weekend_events():
    friday, saturday, sunday = get_next_weekend()

    date_text = (
        f"{friday.strftime('%d/%m/%Y')} "
        f"{saturday.strftime('%d/%m/%Y')} "
        f"{sunday.strftime('%d/%m/%Y')}"
    )

    queries = {
        "🎤 Conciertos":
            (
                f"conciertos Madrid "
                f"{date_text}"
            ),

        "🎨 Exposiciones":
            (
                f"exposiciones museos Madrid "
                f"{date_text}"
            ),

        "🎪 Ferias y mercados":
            (
                f"ferias mercados Madrid "
                f"{date_text}"
            ),

        "🎉 Fiestas":
            (
                f"fiestas patronales "
                f"Comunidad de Madrid "
                f"{date_text}"
            ),

        "🏟️ Otros deportes":
            (
                f"eventos deportivos profesionales "
                f"Madrid {date_text}"
            ),

        "🏔 Comunidad de Madrid":
            (
                f"eventos pueblos "
                f"Comunidad de Madrid "
                f"{date_text}"
            ),

        "🆓 Gratis":
            (
                f"eventos gratis Madrid "
                f"{date_text}"
            ),
    }

    events = {}

    # Cultura, ocio, fiestas...
    for category, query in queries.items():
        results = search_web(
            query=query,
            max_results=10
        )

        events[category] = filter_results(
            results,
            max_results=4
        )

    # Deportes especializados
    events["⚽ Fútbol"] = filter_results(
        search_football(),
        max_results=4
    )

    events["🏀 Baloncesto"] = filter_results(
        search_basketball(),
        max_results=4
    )

    events["🏃 Running"] = filter_results(
        search_running(),
        max_results=5
    )

    events["🚴 Ciclismo"] = filter_results(
        search_cycling(),
        max_results=5
    )

    return events