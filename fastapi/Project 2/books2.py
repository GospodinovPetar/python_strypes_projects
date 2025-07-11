from typing import Optional
from fastapi import FastAPI, Path, Query, HTTPException, Body
from pydantic import BaseModel, Field
from starlette import status

app = FastAPI()


class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: int

    def __init__(self, id, title, author, description, rating, published_date):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date


class BookRequest(BaseModel):
    id : Optional[int] = Field(description="ID is not needed on create", default= None)
    title: str = Field(min_legth = 3)
    author: str = Field(min_length = 1)
    description: str = Field(min_length = 1, max_length = 100)
    rating: int = Field(gt = 0, lt = 6)
    published_date: int

    model_config = {
        "json_schema_extra":{
            "example": {
                "title": "New Book",
                "author": "Petar G",
                "description": "A book description",
                "rating": 5
            }
        }
    }


BOOKS = [
    Book(1, 'Computer Science Pro', 'codingwithroby', 'A very nice book!', 5, 2030),
    Book(2, 'Be Fast with FastAPI', 'codingwithroby', 'A great book!', 5, 2030),
    Book(3, 'Master Endpoints', 'codingwithroby', 'A awesome book!', 5, 2029),
    Book(4, 'HP1', 'Author 1', 'Book Description', 2, 2028),
    Book(5, 'HP2', 'Author 2', 'Book Description', 3, 2027),
    Book(6, 'HP3', 'Author 3', 'Book Description', 1, 2026)
]

@app.get("/books")
async def read_all_books():
    return BOOKS

@app.get("/books/by_date/{published_date}")
async def read_all_books_by_published_date(published_date: int):
    books_to_return = []
    for book in BOOKS:
        if book.published_date == published_date:
            books_to_return.append(book)

    return books_to_return


@app.get("/books/{book_id}")
async def read_book(book_id: int):
    for book in BOOKS:
        if book.id == book_id:
            return book

@app.get("/books/")
async def read_book_by_rating(book_rating:int):
    books_to_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            books_to_return.append(book)

    return books_to_return

@app.post("/create_book")
async def create_book(book_request : BookRequest):
    new_book = Book(**book_request.model_dump()) # transforming it into a Book type
    BOOKS.append(new_book)

def find_book_by_id(book):
    if len(BOOKS) > 0:
        book.id = BOOKS[-1].id + 1
    else:
        book.id = 1

    return book

@app.put("/books/update_book")
async def update_book(book_request : BookRequest):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_request.id:
            BOOKS[i] = book_request

@app.delete("/books/{book_id}")
async def delete_book(book_id: int):
    for book in BOOKS:
        if book.id == book_id:
            BOOKS.remove(book)
            break