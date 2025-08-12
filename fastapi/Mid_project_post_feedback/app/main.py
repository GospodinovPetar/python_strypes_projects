from fastapi import FastAPI
from app.routers import articles

app = FastAPI(
    title="Tech News API (Post-feedback)",
    description="Scrape all news on a page into a single `articles` table",
    version="2.0.0",
)

app.include_router(articles.router)


@app.get("/", include_in_schema=False)
def root():
    return {"ok": True, "docs": "/docs"}
