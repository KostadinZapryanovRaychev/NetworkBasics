# Students API

A tiny FastAPI app: one `students` resource, one route per HTTP method
(GET, POST, PUT, PATCH, DELETE). Reads (GET) are open; writes (POST, PUT,
PATCH, DELETE) require an API key — see [Authentication](#authentication) below.

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

## Your first Postman request

1. Open Postman, click **New → HTTP Request**.
2. Set the method to **POST**.
3. URL:
   ```
   https://networkbasics.onrender.com/students
   ```
4. Go to the **Headers** tab and add:
   | Key | Value |
   |---|---|
   | `X-API-Key` | *(see [Authentication](#authentication) below for where to get this)* |
5. Go to the **Body** tab, select **raw**, and change the type dropdown (right side) from `Text` to **JSON**.
6. Paste:
   ```json
   {
     "name": "Koce",
     "email": "koce@example.com",
     "grade": "A"
   }
   ```
7. Click **Send**. You should get back **201 Created** with the same object, now including an `id`:
   ```json
   {
     "id": 1,
     "name": "Koce",
     "email": "koce@example.com",
     "grade": "A"
   }
   ```

Then try **GET** `https://networkbasics.onrender.com/students` (no headers or body needed) to see it in the list.

Skip step 4 (no `X-API-Key` header) and this POST comes back as **401 Unauthorized** instead.

## Authentication

`GET` requests (`/students`, `/students/{id}`, `/grades`) need nothing. Every
write (`POST`, `PUT`, `PATCH`, `DELETE`) requires an `X-API-Key` header
matching the server's `API_KEY` environment variable.

**Generate a key** (or just make one up for a class demo):

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Set it** in `fastapi-demo/.env`:

```
API_KEY=paste-the-generated-value-here
```

(and as an environment variable on Render too, the same way `DATABASE_URL` is set there.)

**Use it in Postman:** on any write request, open the **Headers** tab and add:

| Key         | Value                           |
| ----------- | ------------------------------- |
| `X-API-Key` | _(the same value as `API_KEY`)_ |

**Use it in Swagger (`/docs`):** click the **Authorize** button (top right,
padlock icon), paste the key, click **Authorize**. Every write request sent
from Swagger after that includes the header automatically.

**Use it with curl:**

```bash
curl -X POST https://networkbasics.onrender.com/students \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"name": "Koce", "email": "koce@example.com", "grade": "A"}'
```

Missing or wrong key → `401 Unauthorized`.
