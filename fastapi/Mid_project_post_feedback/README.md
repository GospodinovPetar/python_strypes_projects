# 📰 News Scraper

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

> **A unified scraping & API service** that aggregates tech news from multiple sites into one simple, mobile‑friendly feed.

---

## 📖 Table of Contents

1. [🚀 Project Summary](#-project-summary)
2. [🔧 Architecture & Data Flow](#-architecture--data-flow)
3. [⚙️ Setup](#setup)
4. [📡 Example API Calls](#-example-api-calls)
5. [🤝 Contributing](#-contributing)
6. [📄 License](#-license)

---

## 🚀 Project Summary

This repo implements a **single, config‑driven scraper** and a **FastAPI** service.

Supported sources (out of the box):

* **TechCrunch** (`techcrunch.com`)
* **TechNews BG** (`technews.bg`)
* **WIRED** (`wired.com`)

Each scrape cycle:

1. **Fetches** listing pages and discovers article links.
2. **Parses** title, URL, ISO publication date, images (header + body), and paragraphs.
3. **Upserts** into a **single `articles` table** (index on `source` recommended).

The API then exposes clean endpoints to scrape, list, fetch, and delete articles.

---

## 🔧 Architecture & Data Flow

| Component       | Location / Modules                          | Responsibility                                                                                               |
| --------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Scraper**     | `app/scrapers.py`                           | Config‑driven selectors per site (`SITE_CONFIGS`), pagination, parsing (title/date/images/paragraphs).       |
| **Database**    | `database/models.py`, `database/session.py` | SQLAlchemy + Postgres (or SQLite). **Single** `articles` table; JSON arrays for `image_urls` & `paragraphs`. |
| **API Service** | `app/main.py`, `app/routers/articles.py`    | REST endpoints: `/articles/sites`, `/articles/scrape`, `/articles`, `/articles/{id}` (GET/DELETE).           |

**Flow**

```
Listing page → extract article links → download articles → parse fields → upsert rows → API returns JSON
```

**Conventions**

* Empty lists return **200** with `[]` (not 404).
* Only article‑scoped images (header + body), no site‑wide OG image fallbacks.
* Pagination: page 1 uses `listing_url`; page ≥2 uses `listing_page_format`.

---

## ⚙️ Setup

### Project structure

```
app/
  ├─ routers/
  │   └─ articles.py            # FastAPI router (endpoints)
  ├─ scrapers.py                # Universal, config‑driven scraper
  ├─ schemas.py                 # Pydantic schemas (ORM‑compatible)
  ├─ main.py                    # FastAPI app

database/
  ├─ session.py                 # SQLAlchemy engine + SessionLocal
  └─ models.py                  # Article model

setup/
  ├─ docker-compose.yml         # Local dev stack (API + DB)
  ├─ Dockerfile                 # API image
  ├─ env.example                # Sample env vars
  ├─ requirements.txt           # Python deps
  └─ servers.json               # Procfile‑style server config
```

### 1) Environment

```bash
cd setup
cp env.example .env
# uncomment this for postgres database to work
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/news
```

### 2) Launch with Docker Compose

```bash
docker compose up --build -d
```

API: [http://localhost:8000](http://localhost:8000)  ·  Docs: [http://localhost:8000/docs](http://localhost:8000/docs)


---

## 📡 Example API Calls

Site keys are discovered at runtime.

```bash
# Supported sites
curl -s http://localhost:8000/articles/sites
```

```bash
# Scrape page 1 from TechCrunch
curl -X POST "http://localhost:8000/articles/scrape?site=techcrunch&page=1" \
     -H "accept: application/json"
```

```bash
# Scrape multiple pages (first 3 pages of WIRED)
curl -X POST "http://localhost:8000/articles/scrape?site=wired&page=1&pages=3"
```

```bash
# List stored (latest 20 from TechNews BG)
curl -s "http://localhost:8000/articles?source=technewsbg&limit=20" | jq '.[0]'
```

```bash
# Get one by ID
curl -s http://localhost:8000/articles/123
```

```bash
# Delete one by ID
curl -X DELETE http://localhost:8000/articles/123
```

**Response model** (`ArticleOut`)

```json
{
  "id": 1,
  "source": "wired",
  "url": "https://www.wired.com/story/...",
  "title": "...",
  "image_urls": ["https://.../hero.jpg"],
  "paragraphs": ["para1", "para2"],
  "date": "2025-08-12",
  "created_at": "2025-08-12T09:30:00"
}
```
---


## 🤝 Contributing

1. Fork & branch
2. Make your changes
3. Open a PR with a clear description and screenshots (if UI‑relevant)

---

## 📄 License

MIT. © Petar Gospodinov
