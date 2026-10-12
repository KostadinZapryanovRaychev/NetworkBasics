"""Pydantic schemas: what the API accepts (In) and returns (Out)."""

from pydantic import BaseModel, ConfigDict, EmailStr


class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    grade: str


class StudentUpdate(BaseModel):
    """Used for PUT: the client must send the full resource."""

    name: str
    email: EmailStr
    grade: str


class StudentPatch(BaseModel):
    """Used for PATCH: every field is optional, only sent fields are changed."""

    name: str | None = None
    email: EmailStr | None = None
    grade: str | None = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    grade: str
