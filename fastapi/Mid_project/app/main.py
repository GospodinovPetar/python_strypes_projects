import fastapi

from app.routers import devbgnews
from app.routers import technewsbg
from app.routers import wired

app = fastapi.FastAPI()
app.include_router(wired.router)
app.include_router(technewsbg.router)
# app.include_router(devbgnews.router)
