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

Main url

https://networkbasics.onrender.com/

Swagger

https://networkbasics.onrender.com/docs
