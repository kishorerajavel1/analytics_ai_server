# Analytics AI Server

Backend service for Analytics AI. This repository contains a FastAPI application that:

- Authenticates requests via Supabase JWTs (except the demo login endpoint)
- Manages user datasource connections backed by Supabase
- Uses MindsDB to introspect/query connected datasources
- Uses Google Gemini (via LangChain) to:
  - Generate SQL for analytical questions
  - Summarize query results
  - Generate dashboard panel configurations from database schemas

## Tech stack

- **API framework**: FastAPI
- **Server**: Uvicorn
- **Auth & persistence**: Supabase (Python client)
- **Datasource/query engine**: MindsDB (`mindsdb_sdk`)
- **LLM orchestration**: LangChain
- **LLM provider**: Google Gemini (`langchain-google-genai`, `google-generativeai`)
- **Logging**: Loguru

## Project structure

```
analytics_ai_server/
  run.py                   # Uvicorn entrypoint
  requirements.txt
  app/
    main.py                # FastAPI app, middleware, routers
    config.py              # Settings (Pydantic BaseSettings, loads .env)
    deps.py                # App “managers” lifecycle (Supabase, MindsDB)
    middleware/
      auth.py              # Supabase Bearer token validation
    routes/
      auth.py              # Demo login
      datasources.py       # Datasource CRUD + schema/semantics/relationships
      chat.py              # SQL generation + analytics panel generation + SSE
    managers/
      db.py                # Supabase client wrapper
      mindsdb.py           # MindsDB SDK wrapper
    services/
      db_chat.py           # LLM routing + SQL generation + execution + summary
      analytics_generation.py
      db_relationships_analyzer.py
      db_semantics_analyzer.py
      mindsdb_service.py
    prompts/               # LangChain prompt templates
    schemas/               # Pydantic request schemas
    models/                # SQLModel models (reference)
```

## Requirements

- **Python** 3.10+ recommended
- A reachable **MindsDB** instance (the code calls `mindsdb_sdk.connect()` using default connection settings)
- A **Supabase** project (URL + keys)
- A **Google Gemini API key**

## Configuration (.env)

Configuration is loaded by `app/config.py` using `pydantic-settings` with `env_file = ".env"`.

Create a `.env` file in the repository root (same folder as `run.py`).

Required environment variables:

```bash
# mindsdb
MINDSDB_URL=...

# Supabase
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# Google Gemini
GEMINI_API_KEY=...

# Demo account used by /auth/demo-login
DEMO_ACCOUNT_EMAIL=...
DEMO_ACCOUNT_PASSWORD=...

# Optional server settings
# HOST=0.0.0.0
# PORT=8000
# DEBUG=false

# Optional CORS
# ORIGINS=["http://localhost:3000"]
```

Notes:

- The app uses `SUPABASE_SERVICE_ROLE_KEY` for the backend Supabase client in `app/deps.py`.
- All non-demo endpoints require an `Authorization: Bearer <access_token>` header.

## Install

Using a virtual environment is recommended.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS/Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

The app is started via `run.py`, which runs Uvicorn with:

- `app.main:app`
- `host=settings.host` (default `0.0.0.0`)
- `port=settings.port` (default `8000`)
- `reload=settings.debug`

```bash
python run.py
```

Open:

- `GET http://localhost:8000/` (root)
- `GET http://localhost:8000/health` (health check)
- `GET http://localhost:8000/docs` (Swagger UI)

## Authentication

Middleware: `app/middleware/auth.py`

- Requests to `POST /auth/demo-login` are **not** protected.
- All other endpoints require:

```http
Authorization: Bearer <SUPABASE_ACCESS_TOKEN>
```

The token is validated by calling `supabase_client.auth.get_user(token)`.

The middleware sets:

- `request.state.user`
- `request.state.user_id`

## API

Base URL: `http://localhost:8000`

### Auth

#### `POST /auth/demo-login`

Logs in using the configured demo account and returns Supabase session tokens.

Example:

```bash
curl -X POST http://localhost:8000/auth/demo-login
```

Response (shape):

- `access_token`
- `refresh_token`
- `expires_in`
- `user`

### Datasources

All `/datasources/*` endpoints require `Authorization: Bearer ...`.

#### `POST /datasources/create`

Creates a datasource in MindsDB and stores metadata in Supabase table `user_datasource_connections`.

Request body (`DataSourceCreateSchema`):

```json
{
  "connection_data": {"host": "...", "port": 5432, "user": "...", "password": "...", "database": "..."},
  "metadata": {
    "name": "my_datasource",
    "label": "My Datasource",
    "engine": "postgres",
    "description": "Primary analytics DB",
    "integration_id": "<uuid>"
  }
}
```

#### `DELETE /datasources/{id}`

Deletes the datasource connection row in Supabase and drops the corresponding MindsDB database.

#### `GET /datasources/`

Returns datasource connections (selects fields from `user_datasource_connections` and joins `master_datasource_connections`).

#### `GET /datasources/schemas/{name}`

Fetch tables and schemas for a datasource from MindsDB.

#### `POST /datasources/schemas`

Fetches schemas from MindsDB and persists them into Supabase under `user_datasource_connections.schemas`.

Request:

```json
{ "name": "my_datasource" }
```

#### `POST /datasources/generate-relationships`

Loads stored schemas from Supabase, generates relationships via Gemini, and persists them to `user_datasource_connections.relationships`.

Request:

```json
{ "name": "my_datasource" }
```

#### `POST /datasources/generate-semantics`

Loads stored schemas from Supabase, generates semantics via Gemini, and persists them to `user_datasource_connections.semantics`.

Request:

```json
{ "name": "my_datasource" }
```

#### `POST /datasources/query`

Executes a SQL query against a named MindsDB database and returns tabular results.

Request:

```json
{
  "name": "my_datasource",
  "query": "SELECT * FROM my_table LIMIT 10"
}
```

### Chat / LLM

All `/chat/*` endpoints require `Authorization: Bearer ...`.

#### `POST /chat/classify`

Classifies a user message.

Request:

```json
{ "user_message": "Show me revenue trend" }
```

Note: In current implementation `DBChatService.classify()` returns the **generic reply chain output** (not the classifier label). Use `/chat/generateSQL` or `/chat/stream` for end-to-end behavior.

#### `POST /chat/generateSQL`

Runs the LLM pipeline (intent routing, SQL generation, execution, summary) and returns a structured response.

Request (`ChatInput` in `app/services/db_chat.py`):

```json
{
  "user_message": "Total orders by month",
  "db_type": "postgres",
  "tables": {"orders": {"id": "int", "created_at": "timestamp"}},
  "relationships": [],
  "semantics": [],
  "db_name": "my_datasource"
}
```

Response:

- `type`: `generic_reply` or `data_response`
- When `data_response`:
  - `sql`
  - `data`
  - `summary`

#### `POST /chat/stream`

Streams the pipeline as **Server-Sent Events** (SSE) with incremental events like intent, SQL chunks, data, and summary chunks.

Example:

```bash
curl -N \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8000/chat/stream \
  -d '{
    "user_message": "Total orders by month",
    "db_type": "postgres",
    "tables": {"orders": {"id": "int", "created_at": "timestamp"}},
    "relationships": [],
    "semantics": [],
    "db_name": "my_datasource"
  }'
```

Each SSE message is sent as a JSON line (not the classic `event:` / `data:` format), e.g.:

```json
{"event":"status","data":{"content":"Classifying query..."}}
```

#### `POST /chat/analytics`

Generates dashboard panel configuration via Gemini and stores the resulting list into Supabase table `dashboard_panels`.

Request:

```json
{
  "db_info": {
    "schemas": {},
    "relationships": [],
    "semantics": [],
    "db_type": "postgres"
  },
  "dashboard_id": "<string>"
}
```

## Supabase tables expected

This backend reads/writes these tables (at minimum):

- `public.user_datasource_connections`
  - `schemas` (JSON)
  - `relationships` (JSON)
  - `semantics` (JSON)
  - `user_id`
  - `integration_id`
- `public.dashboard_panels` (used by `POST /chat/analytics`)
- `public.master_datasource_connections` (joined in `GET /datasources/`)

## Troubleshooting

- **401 Unauthorized**
  - Ensure you pass `Authorization: Bearer <token>` for all endpoints except `POST /auth/demo-login`.

- **MindsDB connection errors**
  - `MindsDBManager` calls `mindsdb_sdk.connect()` with default settings. Ensure MindsDB is running and configured to accept connections.

- **Gemini errors / empty outputs**
  - Verify `GEMINI_API_KEY` is set.
  - Some services parse JSON from model output; invalid JSON will raise errors.

- **CORS issues**
  - Set `origins` via env (see `.env` section). The app uses `allow_headers=["*", "Authorization"]`.

## Development

Formatting tools are included in `requirements.txt`:

- `black`
- `isort`
- `pytest`, `pytest-asyncio`

## License

Proprietary / internal (add a license if you intend to distribute).
