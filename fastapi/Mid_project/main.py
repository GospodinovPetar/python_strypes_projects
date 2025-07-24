from fastapi import FastAPI

import models
from db import engine
from news_bg.router import router as newsbg_router
from trafficnews import router as trafficnews_router
from devbgnews import router as devbgnews_router

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(newsbg_router)
app.include_router(trafficnews_router.router)
app.include_router(devbgnews_router.router)
