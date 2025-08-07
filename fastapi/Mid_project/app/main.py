from fastapi import FastAPI

from app.routers import devbgnews
from app.routers import technewsbg
from app.routers import wired

app = FastAPI(
    title="Tech News API",
    description="🛣️ Scrape real-time news articles from tech websites",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "Petar Gospodinov", "email": "petarjordanov2003@gmail.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

app.include_router(wired.router)
app.include_router(technewsbg.router)
app.include_router(devbgnews.router)
