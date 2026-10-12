# Students API

A tiny FastAPI app: one `students` resource, one route per HTTP method
(GET, POST, PUT, PATCH, DELETE). No auth — just hit it from Postman.

Swagger UI is automatic, no setup needed.

## Run it

```bash
cd fastapi-demo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs**.

No database setup needed to try it — it uses a local SQLite file by default.

## Database

For the real demo, free Postgres: **[neon.tech](https://neon.tech)** — sign up,
create a project, copy the connection string it gives you.

Once you have it, send me the URL and I'll wire it up — set it as
`DATABASE_URL` and the app uses Postgres instead of SQLite, no code changes.
