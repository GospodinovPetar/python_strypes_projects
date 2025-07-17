from typing import Annotated, List
from pydantic import BaseModel, Field
from fastapi import Depends, HTTPException, Path, APIRouter
from sqlalchemy.orm import Session
from starlette import status

from models import Todos, Users
from database import SessionLocal
from .auth import get_current_user

router = APIRouter(prefix="/todos", tags=["todos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Users, Depends(get_current_user)]


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: int
    complete: bool
    owner_id: int

    class Config:
        orm_mode = True


@router.get("/", response_model=List[TodoResponse], status_code=status.HTTP_200_OK)
async def read_all(
    user: user_dependency,
    db: db_dependency,
):
    return db.query(Todos).filter(Todos.owner_id == user.id).all()


@router.get(
    "/todo/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK
)
async def read_todo(
    user: user_dependency,
    db: db_dependency,
    todo_id: int = Path(..., gt=0),
):
    todo = (
        db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.id).first()
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found."
        )
    return todo


@router.post("/todo", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    user: user_dependency,
    db: db_dependency,
    todo_request: TodoRequest,
):
    todo = Todos(**todo_request.model_dump(), owner_id=user.id)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.put(
    "/todo/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK
)
async def update_todo(
    todo_request: TodoRequest,
    user: user_dependency,
    db: db_dependency,
    todo_id: int = Path(..., gt=0),
):
    todo = (
        db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.id).first()
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found."
        )
    for k, v in todo_request.model_dump().items():
        setattr(todo, k, v)
    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency,
    db: db_dependency,
    todo_id: int = Path(..., gt=0),
):
    deleted = (
        db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.id).delete()
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found."
        )
    db.commit()
