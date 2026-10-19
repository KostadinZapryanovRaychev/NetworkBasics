# Students API (Java)

The same app as `fastapi-demo/`, same routes, same architecture, written in
Java with Spring Boot instead of Python with FastAPI. For comparing how two
languages solve the same problem.

| Python (fastapi-demo) | Java (this folder) |
|---|---|
| FastAPI routes in `main.py` | `StudentController.java` |
| SQLAlchemy model in `models.py` | JPA `@Entity` in `Student.java` |
| Pydantic schemas in `schemas.py` | Java records: `StudentCreate`, `StudentUpdate`, `StudentPatch`, `StudentOut` |
| `database.py` (engine/session) | Spring Data JPA `StudentRepository` + `application.properties` |
| SQLite fallback, Postgres in prod | H2 file fallback, Postgres in prod |
| Swagger automatic at `/docs` | Swagger automatic at `/docs` (via springdoc) |

No auth here either — same routes as the Python version:
`GET /students`, `GET /students/{id}`, `POST /students`, `PUT /students/{id}`,
`PATCH /students/{id}`, `DELETE /students/{id}`, `GET /grades`.

## Run it

Requires Java 17+ and Maven.

```bash
cd java-server
mvn spring-boot:run
```

Open **http://127.0.0.1:8080/docs** for Swagger UI.

No database setup needed to try it — it uses a local H2 file (`students-db.mv.db`) by default.

## Use Postgres (Neon) instead

Set three environment variables before running (note: Java needs a `jdbc:`
URL, not the `postgresql://` string the Python version uses directly):

```bash
export DATABASE_URL="jdbc:postgresql://<your-neon-host>/neondb?sslmode=require&channel_binding=require"
export DATABASE_USERNAME="neondb_owner"
export DATABASE_PASSWORD="<your-neon-password>"
mvn spring-boot:run
```
