"""A deliberately small FastAPI app: one resource, every HTTP method.

Swagger UI is automatic at /docs (ReDoc at /redoc) - nothing extra to
configure. Point Postman at the same routes to see each method's request
and response.
"""

import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

load_dotenv()
API_KEY = os.getenv("API_KEY")

Base.metadata.create_all(bind=engine)

api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

app = FastAPI(
    title="Students API",
    description="A minimal CRUD API for demonstrating GET, POST, PUT, PATCH and DELETE in Postman.",
    version="1.0.0",
)


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}


@app.get("/students", response_model=list[schemas.StudentOut], tags=["students"])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()


@app.get("/grades", response_model=list[str], tags=["students"])
def list_grades(db: Session = Depends(get_db)):
    """Just the distinct grades in use, e.g. ["A", "B"] - no student details."""
    rows = db.query(models.Student.grade).distinct().all()
    return [row[0] for row in rows]


@app.get("/students/{student_id}", response_model=schemas.StudentOut, tags=["students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.post(
    "/students",
    response_model=schemas.StudentOut,
    status_code=201,
    tags=["students"],
    dependencies=[Depends(verify_api_key)],
)
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    student = models.Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.put(
    "/students/{student_id}",
    response_model=schemas.StudentOut,
    tags=["students"],
    dependencies=[Depends(verify_api_key)],
)
def replace_student(student_id: int, payload: schemas.StudentUpdate, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in payload.model_dump().items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@app.patch(
    "/students/{student_id}",
    response_model=schemas.StudentOut,
    tags=["students"],
    dependencies=[Depends(verify_api_key)],
)
def update_student(student_id: int, payload: schemas.StudentPatch, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@app.delete(
    "/students/{student_id}",
    status_code=204,
    tags=["students"],
    dependencies=[Depends(verify_api_key)],
)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return None
