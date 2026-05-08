# backend/app/ — description

The FastAPI application package. Holds the entry point (`main.py`), global config (`config.py`), and three subfolders that each own one architectural layer.

## Subfolders

- **`routers/`** — HTTP-facing endpoint handlers; one file per resource.
- **`schemas/`** — Pydantic request/response models that define the JSON contract.
- **`services/`** — pure business logic (URL parsing, transcript fetching/formatting, ZIP building). Routers stay thin and call into services.

## Files

### `__init__.py`

Empty package marker — no exports.

### `config.py`

A single module-level constant:

- `CORS_ORIGINS: list[str] = ["http://localhost:5173"]` — origins allowed to call the API. Currently hardcoded for local dev. Imported by `main.py`. **Update this when deploying or when the frontend port changes.**

No functions.

### `main.py`

FastAPI app entry point. Configures logging, instantiates the `FastAPI` object, attaches CORS middleware (with `Content-Disposition` exposed so the frontend can read filenames), and registers the transcript router. Defines one trivial liveness endpoint.

#### Module-level objects

- `app: FastAPI` — the application object. Imported by `uvicorn` (`uvicorn app.main:app`) and by `tests/conftest.py` for the `TestClient`. Inherits FastAPI's full route/middleware/dependency machinery.

#### Functions

**`health_check() -> dict[str, str]`** *(async, decorated with `@app.get("/health")`)*

- Purpose: simple liveness probe.
- Inherits / called by: registered as a route on `app`. Called by HTTP clients (load balancers, uptime monitors) hitting `GET /health`.
- Effect: returns `{"status": "ok"}` with HTTP 200.
- Use case: container health check, deployment smoke test.
- Limitations: doesn't verify dependencies (e.g. `youtube-transcript-api` reachability). It only proves the process is up.
