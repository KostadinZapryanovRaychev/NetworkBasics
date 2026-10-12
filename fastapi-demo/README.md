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

## Your first Postman request

1. Open Postman, click **New → HTTP Request**.
2. Set the method to **POST**.
3. URL:
   ```
   https://networkbasics.onrender.com/students
   ```
4. Go to the **Body** tab, select **raw**, and change the type dropdown (right side) from `Text` to **JSON**.
5. Paste:
   ```json
   {
     "name": "Koce",
     "email": "koce@example.com",
     "grade": "A"
   }
   ```
6. Click **Send**. You should get back **201 Created** with the same object, now including an `id`:
   ```json
   {
     "id": 1,
     "name": "Koce",
     "email": "koce@example.com",
     "grade": "A"
   }
   ```

Then try **GET** `https://networkbasics.onrender.com/students` (no body needed) to see it in the list.
