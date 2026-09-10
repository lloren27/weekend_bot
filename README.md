# Weekend Bot

Weekend Bot es un bot de Telegram para descubrir planes de fin de semana. El proyecto está preparado para crecer hacia varias ciudades, aunque ahora la ubicación principal está configurada para la Comunidad de Madrid.

El bot busca eventos del siguiente viernes, sábado y domingo, extrae información estructurada de páginas con JSON-LD/schema.org, filtra por ubicación, deduplica resultados y genera mensajes listos para Telegram.

## Comandos

- `/start`: muestra la ayuda inicial.
- `/help`: lista todos los comandos disponibles.
- `/planes`: digest general de planes del fin de semana.
- `/conciertos`: conciertos y música en directo.
- `/exposiciones`: exposiciones y museos.
- `/ferias`: ferias, mercados y mercadillos.
- `/fiestas_regionales`: fiestas populares y regionales.
- `/deporte_profesional`: partidos y competiciones profesionales.
- `/running`: carreras populares, trail y running.
- `/ciclismo`: marchas y pruebas de carretera, gravel, XCM y BTT.
- `/id`: muestra el `chat_id` de Telegram.

## Configuración

Variables de entorno:

- `TELEGRAM_BOT_TOKEN`: token del bot creado en BotFather. Obligatoria.
- `APP_NAME`: nombre visible que usa el bot en mensajes de ayuda. Opcional; por defecto `Weekend Bot`.

Para desarrollo local puedes crear un `.env` a partir de `.env.example`:

```bash
cp .env.example .env
```

## Desarrollo Local

Requisitos:

- Python 3.12
- Entorno virtual

Instalación:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Pruebas:

```bash
.venv/bin/python -m unittest discover
```

## Despliegue en Railway

El proyecto incluye un `Dockerfile` para que Railway construya el servicio con la imagen oficial `python:3.12-slim`. Esto evita el fallo observado en Nixpacks/mise al descargar Python durante el build.

En Railway añade al menos esta variable:

```text
TELEGRAM_BOT_TOKEN=<token de BotFather>
```

El servicio no necesita exponer puerto HTTP, porque el bot funciona con polling de Telegram. El comando de arranque del contenedor es:

```bash
python bot.py
```

También se incluye un `Procfile` como pista de ejecución para plataformas compatibles con procesos worker.

## Arquitectura

La aplicación está organizada por capas pequeñas:

- `bot.py`: entrada principal de Telegram. Registra comandos, envía mensajes de estado y delega la generación de digests.
- `config.py`: configuración global y variables de entorno.
- `config_locations.py`: ubicación activa. Ahora apunta a Comunidad de Madrid, pero está separada para facilitar futuras ciudades.
- `models/`: dataclasses de dominio, como `Event` y `TargetLocation`.
- `services/event_categories.py`: registro de categorías, queries, filtrado semántico y pipeline común de búsqueda.
- `services/digest.py`: formatea los eventos y resultados para Telegram.
- `sources/jsonld.py`: descarga páginas y extrae eventos desde JSON-LD/schema.org.
- `services/deduplicator.py`: fusiona eventos repetidos. Incluye lógica especial para conciertos y deporte profesional.
- `services/location_filter.py`: comprueba si un evento pertenece a la ubicación activa.
- `services/normalizer.py`: normalización de texto, horas y alias de recintos.
- `services/ranking.py`: ordena eventos por calidad de datos y prioridad de fuente.
- `services/source_registry.py`: asigna nombre y prioridad a fuentes conocidas.
- `tests/`: pruebas unitarias del pipeline, deduplicación, ayuda, digest, ubicación y parser JSON-LD.

## Flujo de una Categoría

1. El usuario ejecuta un comando, por ejemplo `/conciertos`.
2. `bot.py` llama a `build_category_digest()`.
3. `event_categories.py` genera queries para el fin de semana y la ubicación activa.
4. `web_search.py` descubre URLs.
5. `jsonld.py` intenta extraer eventos con fecha verificable.
6. Se filtra por categoría y por ubicación.
7. `deduplicator.py` fusiona duplicados.
8. `ranking.py` selecciona los mejores eventos por día.
9. `digest.py` devuelve el texto final para Telegram.

## Notas de Diseño

- Las categorías nuevas deben añadirse preferentemente en `services/event_categories.py`.
- La futura selección de ciudad debería evolucionar desde `config_locations.py` hacia un registro de ubicaciones.
- `.env`, `.venv`, cachés y logs están excluidos del repositorio con `.gitignore` y `.dockerignore`.
