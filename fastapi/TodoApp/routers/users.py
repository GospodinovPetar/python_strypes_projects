from typing import Annotated

from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy.orm import Session

from models import Users
from database import SessionLocal
from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Users, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserVerification(BaseModel):
    password: str
    new_password: str


@router.get("/")
async def get_user(
    user: user_dependency,
    db: db_dependency,
):
    db_user = db.query(Users).filter(Users.id == user.id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    return db_user


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependency,
    db: db_dependency,
    user_verification: UserVerification,
):
    db_user = db.query(Users).filter(Users.id == user.id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    if not bcrypt_context.verify(user_verification.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password."
        )

    db_user.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(db_user)
    db.commit()


@router.put("/phone_number", status_code=status.HTTP_204_NO_CONTENT)
async def change_phone_number(
    user: user_dependency,
    db: db_dependency,
    new_phone_number: str,
):
    db_user = db.query(Users).filter(Users.id == user.id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    db_user.phone_number = new_phone_number
    db.add(db_user)
    db.commit()
