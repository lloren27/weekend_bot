# Weekend Bot

Weekend Bot es un bot de Telegram para descubrir planes de fin de semana en ciudades españolas. Por defecto usa la Comunidad de Madrid, y cada chat puede elegir su ciudad con `/ciudad`.

El bot busca eventos del siguiente viernes, sábado y domingo, extrae información estructurada de páginas con JSON-LD/schema.org, filtra por ubicación, deduplica resultados y genera mensajes listos para Telegram.

## Comandos

- `/start`: muestra la ayuda inicial.
- `/help`: lista todos los comandos disponibles.
- `/ciudad`: muestra la ciudad actual o permite cambiarla. Ejemplo: `/ciudad Barcelona`.
- `/ciudades`: lista las ciudades disponibles.
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
- `LOG_LEVEL`: nivel de logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Opcional; por defecto `INFO`.
- `CACHE_TTL_SECONDS`: segundos que se cachean búsquedas web y páginas descargadas en memoria. Opcional; por defecto `1800`. Usa `0` para desactivar la caché.

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
- `config_locations.py`: registro de ciudades disponibles, alias y ubicación por defecto.
- `models/`: dataclasses de dominio, como `Event` y `TargetLocation`.
- `services/event_categories.py`: registro de categorías, queries, filtrado semántico y pipeline común de búsqueda.
- `services/cache.py`: caché TTL en memoria para reducir llamadas repetidas a buscadores y páginas.
- `services/digest.py`: formatea los eventos y resultados para Telegram.
- `sources/jsonld.py`: descarga páginas, reutiliza HTML cacheado y extrae eventos desde JSON-LD/schema.org.
- `services/deduplicator.py`: fusiona eventos repetidos. Incluye lógica especial para conciertos y deporte profesional.
- `services/location_filter.py`: comprueba si un evento pertenece a la ubicación seleccionada.
- `services/normalizer.py`: normalización de texto, horas y alias de recintos.
- `services/ranking.py`: ordena eventos por calidad de datos y prioridad de fuente.
- `services/source_registry.py`: asigna nombre y prioridad a fuentes conocidas.
- `tests/`: pruebas unitarias del pipeline, deduplicación, ayuda, digest, ubicación y parser JSON-LD.

## Flujo de una Categoría

1. El usuario ejecuta un comando, por ejemplo `/conciertos`.
2. `bot.py` llama a `build_category_digest()`.
3. `event_categories.py` genera queries para el fin de semana y la ubicación seleccionada.
4. `web_search.py` descubre URLs.
5. `jsonld.py` intenta extraer eventos con fecha verificable.
6. Se filtra por categoría y por ubicación.
7. `deduplicator.py` fusiona duplicados.
8. `ranking.py` selecciona los mejores eventos por día.
9. `digest.py` devuelve el texto final para Telegram.

## Notas de Diseño

- Las categorías nuevas deben añadirse preferentemente en `services/event_categories.py`.
- La ciudad seleccionada se guarda en memoria por chat de Telegram. Si el proceso se reinicia, el chat vuelve a la ubicación por defecto.
- `.env`, `.venv`, cachés y logs están excluidos del repositorio con `.gitignore` y `.dockerignore`.

## Identidad y deduplicación de eventos

`services/event_identity.py` compara fecha, rango de fechas, recinto, ciudad,
participantes, tipo y hora, además del título normalizado. Reconoce variantes
como «Vibra Mahou Fest» / «Vibra Mahou Festival Segovia 2026» y los nombres
abreviado y completo del CIDE. La normalización solo se usa para comparar.

- `MATCH`: permite fusionar las fuentes. Cada miembro del grupo debe coincidir
  con todos los demás para evitar unir sesiones distintas a través de una ficha incompleta.
- `POSSIBLE_MATCH`: conserva entradas separadas y registra la referencia,
  puntuación y motivos en `possible_matches` para revisión.
- `DIFFERENT`: impide fusionar identidades con datos incompatibles.

Cada resultado incluye `canonical_id`, `sources` (valores originales y JSON-LD),
`field_sources` (procedencia de los datos consolidados), `conflicts`,
`match_level` y `match_confidence`. Una ficha sin coincidencias confirmadas
conserva estos dos últimos valores como desconocidos. Se elige la fuente con
mayor prioridad, se completan sus datos ausentes y se conservan las discrepancias
de precio; un precio inferior por sí solo no decide la selección.
Los identificadores son deterministas para la misma identidad normalizada y
el mismo conjunto de fuentes, independientemente del orden de búsqueda. No hay
un registro persistente de identidad entre búsquedas: datos nuevos de ubicación,
fecha u hora pueden cambiar el identificador.

Los festivales se muestran con su título, aunque una fuente indique un único
artista como `performer`. Una actuación puede aparecer dentro de `related_events`
y bajo «Incluye» en el mensaje cuando coinciden fecha y recinto y hay evidencia
explícita: `superEvent`/`subEvent`, participantes del cartel o un enlace compartido
al festival. La actuación conserva sus propios datos y fuentes. Compartir fecha
y recinto no basta, y no se absorben jornadas o actuaciones de eventos de varios días.

Se mantiene la tolerancia previa de hasta dos horas para fuentes de deporte
profesional con los mismos equipos y ubicación, registrando la discrepancia.
En conciertos, dos horas distintas dejan la coincidencia pendiente de revisión.
