from fastapi import FastAPI
import models
from db import engine
from wired.router import router as wired_router
from technewsbg import router as technewsbg_router
from devbgnews import router as devbgnews_router

app = FastAPI(
    title="Tech News API",
    description="🛣️ Real‑time news articles from Bulgaria",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "Petar Gospodinov", "email": "petarjordanov2003@gmail.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

models.Base.metadata.create_all(bind=engine)

app.include_router(wired_router)
app.include_router(technewsbg_router.router)
app.include_router(devbgnews_router.router)
