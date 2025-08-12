# Universal News Scraper API

A small, a FastAPI app that scrapes tech news articles from multiple sites using a **single, config‑driven scraper**. It stores results in a database and exposes clean REST endpoints to list, fetch, and delete articles.

---

## Features

* **One scraper for many sites** via `SITE_CONFIGS` (CSS selectors per site)

---

## Project structure

```
app/
  ├─ routers/
  │   └─ articles.py            # FastAPI router (endpoints)
  ├─ scrapers.py                # Universal, config‑driven scraper
  ├─ schemas.py                 # Response schemas
  ├─ main.py                    # FastAPI app

database/
  ├─ session.py                 # SQLAlchemy SessionLocal + engine
  └─ models.py                  # Article model

README.md                       # this file

setup/
  ├─ docker-compose.yml         # Local dev stack (API + DB)
  ├─ Dockerfile                 # Container image for the API
  ├─ env.example                # Example environment variables
  ├─ requirements.txt           # Python dependencies
  └─ servers.json               # Server process config
```

---
# Setup


1. **Environment variables**
   Copy the example env file and adjust values as needed (e.g., `DATABASE_URL`).

```bash
cp setup/env.example .env
```

> Everything is set up in the default .env, you only need to uncomment DATABASE_URL

2. **Build and start the stack**
   (You have to be in the setup directory)

```bash
docker compose up --build -d
```

## The universal scraper (how it works)

The scraper lives in `scraper.py`:

* `SITE_CONFIGS`: a dict keyed by site (e.g., `"devbg"`, `"technewsbg"`, `"wired"`)

**What it extracts**

* `title`: via site `title_selector`, or `<h1>`, or fallback `og:title`
* `date`: prefers `<time datetime>`, else parses text (supports BG month names & `dd.mm.yyyy`)
* `image_urls`: only images **inside the article root** (header first, then body)
* `paragraphs`: all non‑empty `<p>` texts inside the article root

**Pagination**

* Uses `listing_page_format`, default `"/page/{page}/"` → page 1 returns `listing_url` as‑is

---

## Supported sites (out of the box)

* `devbg` – [https://dev.bg](https://dev.bg)
* `technewsbg` – [https://technews.bg](https://technews.bg)
* `wired` – [https://www.wired.com](https://www.wired.com)

List them at runtime:

```
GET /articles/sites
```

---

## API

### List supported sites

```
GET /articles/sites
```

Response: `["devbg", "technewsbg", "wired"]`

### Scrape & store

```
POST /articles/scrape?site=devbg&page=1&pages=1
```

* `site` – one of `/articles/sites`
* `page` – listing page to start from (default 1)
* `pages` – how many pages to scrape starting at `page` (default 1)

**Example (curl):**

```bash
curl -X POST "http://localhost:8000/articles/scrape?site=devbg&page=1&pages=1" \
     -H "accept: application/json"
```

### List stored articles

```
GET /articles?source=devbg&limit=50
```

**Query params**

* `source` (optional): filter by site key
* `limit` (1–200): max rows to return (default 50)

### Get article by ID

```
GET /articles/{article_id}
```

### Delete article by ID

```
DELETE /articles/{article_id}
```

**Response model** (`ArticleOut`):

```json
{
  "id": 1,
  "source": "devbg",
  "url": "https://dev.bg/...",
  "title": "...",
  "image_urls": ["https://.../img.jpg"],
  "paragraphs": ["para1", "para2"],
  "date": "2025-08-12",
  "created_at": "2025-08-12T09:30:00"
}
```

---

## Adding a new site

Open `scraper.py` and add a block in `SITE_CONFIGS`:

```python
SITE_CONFIGS["example"] = {
    "base_url": "https://example.com",
    "listing_url": "https://example.com/news/",
    "listing_page_format": "/page/{page}/",     # or "?page={page}"

    # Find article links on listing pages
    "listing_link_selector": "article .title a[href]",
    "listing_link_exclude_contains": ["/tag/", "/author/"],

    # Where the article lives
    "article_root_selectors": ["article", ".entry-content"],

    # Title & date
    "title_selector": "h1",
    "date_selector": "span.post-date, time[datetime]",
    "date_prefixes_to_strip": ["Published on", "г.", "Публикувано на"],
    "months": {  # only if you need non‑English months
        "януари":1, "февруари":2, "март":3, "април":4, "май":5, "юни":6,
        "юли":7, "август":8, "септември":9, "октомври":10, "ноември":11, "декември":12
    },

    # Images (inside the article only)
    "header_image_selectors": ["header img[src]"],
    "body_image_selectors": [".content img[src]"],
}
```

Tips:

* Keep selectors **specific** to avoid sidebars/ads.
* If dates come back `None`, confirm `date_selector` matches the actual element and (if needed) supply a `months` map.
* If images are missing/too many, tweak `header_image_selectors` and `body_image_selectors`.

---

## Implementation notes

* **Dates**: the parser first tries `<time datetime>`. If missing, it parses text and supports BG month names and numeric `dd.mm.yyyy`.
* **Pagination**: page 1 is the listing URL as‑is; page ≥2 uses `listing_page_format`.



