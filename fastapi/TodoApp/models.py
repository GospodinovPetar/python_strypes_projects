from database import Base
from sqlalchemy import Integer, String, Boolean, Column


class Todos(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, unique=True)
    description = Column(String(1000), nullable=False)
    priority = Column(Integer, nullable=False)
    complete = Column(Boolean, nullable=False)
