from fastapi import FastAPI
import models
from db import engine
from routers import trafficnews


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(trafficnews.router)
