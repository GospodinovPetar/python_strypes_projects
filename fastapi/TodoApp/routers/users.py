from typing import Annotated

from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from models import *
from database import SessionLocal
from starlette import status
from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserVerification(BaseModel):
    password: str
    new_password: str


@router.get("/")
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db.query(Users).filter(Users.id == user["id"]).first()


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependency, db: db_dependency, user_verification: UserVerification
):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_model = db.query(Users).filter(Users.id == user["id"]).first()
    if not bcrypt_context.verify(
        user_verification.password, user_model.hashed_password
    ):
        raise HTTPException(status_code=404, detail="Incorrect password")
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()

@router.put('/phone_number', status_code=status.HTTP_204_NO_CONTENT)
async def change_phone_number(user: user_dependency, db: db_dependency, new_phone_number: str):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_model = db.query(Users).filter(Users.id == user["id"]).first()

    user_model.phone_number = new_phone_number
    db.add(user_model)
    db.commit()