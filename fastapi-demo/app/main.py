"""A deliberately small FastAPI app: one resource, every HTTP method.

Swagger UI is automatic at /docs (ReDoc at /redoc) - nothing extra to
configure. Point Postman at the same routes to see each method's request
and response.
"""

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

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


@app.get("/students/{student_id}", response_model=schemas.StudentOut, tags=["students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.post("/students", response_model=schemas.StudentOut, status_code=201, tags=["students"])
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    student = models.Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

#wrong arthitecture style
@app.post("/students-create", response_model=schemas.StudentOut, status_code=201, tags=["students"])
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    student = models.Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.put("/students/{student_id}", response_model=schemas.StudentOut, tags=["students"])
def replace_student(student_id: int, payload: schemas.StudentUpdate, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in payload.model_dump().items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@app.patch("/students/{student_id}", response_model=schemas.StudentOut, tags=["students"])
def update_student(student_id: int, payload: schemas.StudentPatch, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@app.delete("/students/{student_id}", status_code=204, tags=["students"])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return None
