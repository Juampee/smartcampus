# SmartCampus Solutions - Reserva de aulas

## Descripcion

API REST de gestion de aulas y reservas para la empresa ficticia SmartCampus Solutions
(Practica 1: Automatizacion y Despliegue con Git Hooks y GitHub Actions).

Reglas de negocio:

- No se puede reservar un aula inexistente (404).
- `hora_inicio` debe ser anterior a `hora_fin` (422).
- No puede haber solapamientos en la misma aula y fecha (409). Dos franjas solapan si
  `inicio_A < fin_B` y `inicio_B < fin_A`; las reservas contiguas (10:00-12:00 y 12:00-13:00) **no** son conflicto.
- La capacidad de un aula debe ser mayor que 0 (422).
- Borrar un aula o reserva inexistente devuelve 404.

| Metodo | Ruta | Codigos |
|---|---|---|
| GET | `/health` | 200 |
| GET / POST | `/rooms` | 200 / 201, 400, 422 |
| GET / DELETE | `/rooms/{id}` | 200 / 204, 404 |
| GET / POST | `/bookings` | 200 / 201, 400, 404, 409, 422 |
| DELETE | `/bookings/{id}` | 204, 404 |

## Arquitectura

```
 Cliente (curl / navegador)
          |
          v  HTTP
 +---------------------------+
 |  Docker: contenedor       |
 |  gunicorn -> Flask        |
 |  app/main.py (rutas)      |
 |       |                   |
 |  app/services.py (negocio)|
 |       |                   |
 |  app/db.py -> SQLite      |
 +-----------|---------------+
             v
     volumen /data (smartcampus.db)
```

- `app/main.py`: app factory `create_app()` y endpoints.
- `app/services.py`: logica de negocio, testeable sin HTTP.
- `app/models.py`, `app/db.py`, `app/config.py`: modelos, acceso a SQLite y configuracion por variables de entorno.

## Instalacion

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env          # ajusta los valores
```

## Ejecucion local

```bash
python -m app.main
curl http://localhost:5000/health
```

Variables (ver `.env.example`): `APP_ENV`, `HOST`, `PORT`, `HOST_PORT`, `DB_PATH`, `LOG_LEVEL`, `GUNICORN_WORKERS`, `SECRET_KEY`.

## Docker

```bash
docker build -t smartcampus .
docker run -d -p 5000:5000 -e SECRET_KEY=algo -v smartcampus-data:/data smartcampus
```

Imagen `python:3.12-slim`, usuario no root, gunicorn y `HEALTHCHECK` sobre `/health`.

## Docker Compose

```bash
cp .env.example .env     # define al menos SECRET_KEY
docker compose up --build -d
docker compose ps        # el servicio backend debe quedar "healthy"
```

Servicio `backend` con red propia (`smartcampus-net`), volumen `smartcampus-data` para SQLite,
puerto configurable (`HOST_PORT`) y `restart: unless-stopped`. No hay servicio de BD separado.

## Tests

```bash
pytest -m unit          # logica de servicios
pytest -m integration   # endpoints con el test client de Flask
pytest                  # todos
```

Los markers estan registrados en `pytest.ini`. Cada test usa una BD temporal.

## Git Hooks

Versionados en `hooks/` y activados con `core.hooksPath`:

```bash
sh scripts/install-hooks.sh      # o: make hooks / ./scripts/install-hooks.ps1
```

| Hook | Que hace |
|---|---|
| `pre-commit` | `ruff check`, `ruff format --check` y `pytest -m unit`. Si falla: "❌ Commit rechazado". |
| `post-commit` | Anade autor, fecha, hash corto y mensaje a `commit-log.txt` (ignorado por git). |
| `pre-push` | `pytest -m unit` y `pytest -m integration`. Si fallan: "❌ Push rechazado: existen tests fallidos"; si no: "✅ Todos los tests superados". |
| `post-push` | Muestra "🚀 Cambios enviados correctamente al repositorio remoto." y guarda `.push-info`. |

> **Nota sobre post-push:** Git **no tiene** un hook `post-push` nativo. `hooks/post-push` es un
> script que se lanza mediante el alias `git pushp`, que ejecuta `git push "$@"` y, solo si termina
> bien, invoca el script. Un `git push` normal ejecuta `pre-push` pero **no** `post-push`.

Evidencias del bloqueo y funcionamiento: `docs/evidencias/02-hooks.txt`.

## GitHub Actions

Workflow: `.github/workflows/ci-cd.yml`. Se ejecuta en cada **push** y **pull_request**.

| Etapa | Descripcion |
|---|---|
| `tests` | **Matrix** `python-version: [3.11, 3.12]`: checkout, setup-python (con cache de pip), instalar dependencias, ruff y pytest. |
| `build` | `needs: tests`. `docker build -t smartcampus .`, arranca el contenedor, espera al healthcheck, `curl /health` y lo para. |
| `deploy` | `needs: build`, solo en **push a main**, `runs-on: self-hosted`. Crea `.env` y ejecuta `docker compose up -d --build`; verifica `/health`. |

**Variables** (`env:` del workflow): `APP_ENV`, `PORT`, `HOST_PORT`, `LOG_LEVEL`, `GUNICORN_WORKERS`.

**Secrets:** `SECRET_KEY` (Settings > Secrets and variables > Actions). Se inyecta como variable de
entorno del job `deploy`, se escribe en `.env` sin `echo` y GitHub lo enmascara (`***`) en los logs.
El `.env` se borra del workspace al terminar. Nunca hay secretos en el codigo.

**Runner self-hosted:** el despliegue se ejecuta en el equipo del autor (`C:\actions-runner`, nombre
`smartcampus-local`). **El equipo debe estar encendido, con la sesion iniciada y Docker Desktop en
marcha** durante los despliegues; si no, el job `deploy` queda en cola.

**Seguridad:** el repo es publico y el runner es propio, por eso el job `deploy` solo corre en push a `main`
(nunca en PRs) y los workflows de colaboradores externos requieren aprobacion. `main` esta protegida:
exige que pasen los checks de `tests` y `build`.

**Flujo de Git:** ramas `feature/*` -> Pull Request -> CI en verde -> merge a `main` -> despliegue.

## Evidencias

Salidas de terminal en `docs/evidencias/`:

- `01-tests.txt`: tests unitarios e integracion.
- `02-hooks.txt`: hooks bloqueando y funcionando.
- `03-docker.txt`: build, arranque, healthcheck y pruebas con curl.
- `04-ci-deploy.txt`: ejecucion del pipeline, runner y despliegue.

Capturas de pantalla (a anadir manualmente en `docs/evidencias/capturas/`):

- [x] `pipeline-verde.png`: pestana Actions con el pipeline en verde.
- [x] `matrix.png`: jobs de la matrix (Python 3.11 y 3.12).
- [x] `secrets.png`: Settings > Secrets con `SECRET_KEY` (sin mostrar el valor).
- [x] `runner.png`: Settings > Actions > Runners con el runner online.
- [x] `app-desplegada.png`: `http://localhost:5000/health` en el navegador / `docker compose ps`.
