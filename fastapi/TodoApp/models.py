from database import Base
from sqlalchemy import Integer, String, Boolean, Column, ForeignKey


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)
    phone_number = Column(String)


class Todos(Base):
    __tablename__ = "todosapp"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, unique=True)
    description = Column(String(1000), nullable=False)
    priority = Column(Integer, nullable=False)
    complete = Column(Boolean, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
