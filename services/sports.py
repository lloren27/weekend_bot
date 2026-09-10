from services.dates import get_next_weekend
from services.web_search import search_web


def get_date_text():
    friday, saturday, sunday = get_next_weekend()

    return (
        f"{friday.strftime('%d/%m/%Y')} "
        f"{saturday.strftime('%d/%m/%Y')} "
        f"{sunday.strftime('%d/%m/%Y')}"
    )


def search_football():
    dates = get_date_text()

    teams = [
        "Real Madrid",
        "Atlético de Madrid",
        "Rayo Vallecano",
        "Getafe CF",
        "CD Leganés",
    ]

    results = []

    for team in teams:
        query = (
            f"{team} partido Madrid "
            f"{dates}"
        )

        results.extend(
            search_web(
                query,
                max_results=2
            )
        )

    return results


def search_basketball():
    dates = get_date_text()

    queries = [
        (
            f"Real Madrid baloncesto partido "
            f"Madrid {dates}"
        ),
        (
            f"Movistar Estudiantes partido "
            f"Madrid {dates}"
        ),
        (
            f"baloncesto Liga Endesa Madrid "
            f"{dates}"
        ),
    ]

    results = []

    for query in queries:
        results.extend(
            search_web(
                query,
                max_results=3
            )
        )

    return results


def search_running():
    dates = get_date_text()

    queries = [
        f"carrera popular Madrid {dates}",
        f"10K Madrid {dates}",
        f"media maratón Madrid {dates}",
        f"trail Madrid sierra {dates}",
        (
            f"carrera running Comunidad "
            f"de Madrid {dates}"
        ),
    ]

    results = []

    for query in queries:
        results.extend(
            search_web(
                query,
                max_results=3
            )
        )

    return results


def search_cycling():
    dates = get_date_text()

    queries = [
        (
            f"marcha cicloturista Madrid "
            f"{dates}"
        ),
        (
            f"carrera ciclismo carretera "
            f"Madrid {dates}"
        ),
        (
            f"MTB Madrid carrera "
            f"{dates}"
        ),
        (
            f"gravel Madrid evento "
            f"{dates}"
        ),
        (
            f"ciclismo Comunidad de Madrid "
            f"{dates}"
        ),
    ]

    results = []

    for query in queries:
        results.extend(
            search_web(
                query,
                max_results=3
            )
        )

    return results