from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from pydantic.v1 import ConfigDict
from sqlalchemy.orm import Session
from typing import List
from db import get_db
from models import Article as ArticleModel
from schemas import ArticleSchema
from scraper import scrape_trafficnews


app = FastAPI()
db_dependency: Session = Depends(get_db)


class ScrapeRequest(BaseModel):
    url: HttpUrl

    model_config = ConfigDict(
        url_allowed_hosts={"trafficnews.bg", "www.trafficnews.bg"},
        json_schema_extra={"example": {"url": "https://trafficnews.bg/...."}},
    )


@app.post("/scrape", response_model=ArticleSchema)
def scrape_and_store(req: ScrapeRequest, db: Session = db_dependency):
    try:
        data = scrape_trafficnews(str(req.url))
    except Exception:
        raise HTTPException(502, "Грешка при скрейпване на страницата")

    if not data['title']:
        raise HTTPException(404, "Няма намерени данни на тази страница")

    article = db.merge(ArticleModel(url=str(req.url), **data))

    db.commit()
    return article


@app.get("/read_all_news/", response_model=List[ArticleSchema])
def read_all_news(db: Session = db_dependency):
    return db.query(ArticleModel).all()


@app.get("/latest_news/", response_model=ArticleSchema)
def latest_news(db: Session = db_dependency):
    article = db.query(ArticleModel).order_by(ArticleModel.id.desc()).first()

    if not article:
        raise HTTPException(404, detail="Няма новини")
    return article
