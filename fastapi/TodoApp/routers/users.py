from typing import Annotated
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, HTTPException, Path, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.testing.pickleable import User

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

@router.get("/")
async def get_user(user_first_name : str, db: db_dependency):
    return db.query(Users).filter(user_first_name == Users.first_name).first()
