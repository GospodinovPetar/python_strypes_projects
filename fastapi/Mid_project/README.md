# 📰 Mid Project News Scraper Suite

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

> **A unified scraping & API service** for aggregating news from multiple Bulgarian sites into a single mobile-friendly feed.

---

## 📖 Table of Contents

1. [🚀 Project Summary](#-project-summary)
2. [🔧 Architecture & Data Flow](#-architecture--data-flow)
3. [⚙️ Setup & Running](#️-setup--running)
4. [📡 Example API Calls](#-example-api-calls)
5. [📸 Screenshots](#-screenshots)
6. [🛠 Logging](#-logging)
7. [🤝 Contributing](#-contributing)
8. [📄 License](#-license)

---

## 🚀 Project Summary

This repository hosts individual scrapers for three Bulgarian news websites:

* **TrafficNews** (`trafficnews.bg`)
* **Dev BG News** (`dev.bg`)
* **News.bg** (`news.bg`)

Each scraper:

1. **Fetches** the latest articles using HTTP requests.
2. **Parses** relevant fields: title, URL, publication date, image, and content.
3. **Stores** articles in PostgreSQL tables named per site:

   * `trafficnews_articles`
   * `devnews_articles`
   * `newsbg_articles`

By aggregating these disparate sources, you can power a **mobile app** to deliver all headlines & articles in one cohesive experience.

---

## 🔧 Architecture & Data Flow

| Component         | Location / Modules                                                         | Responsibility                                                                                                                                                                                 |
| ----------------- |----------------------------------------------------------------------------| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Scraper**       | `trafficnews/scraper.py`<br>`devbgnews/scraper.py`<br>`news_bg/scraper.py` | • HTTP GET with custom `User-Agent`<br>• Identify latest article links<br>• Extract fields: title, url, image\_url, date, paragraphs                                                           |
| **Database**      | `db.py`, `models.py`                                                       | • SQLAlchemy ORM with PostgreSQL<br>• Per-site tables with `url` uniqueness & timestamping                                                                                                     |
| **API Service**   | `main.py` + `routers/{trafficnews, devnews, newsbg}.py`                    | • FastAPI endpoints for each site:<br>  - `GET /{site}/latest`<br>  - `POST /{site}/scrape`<br>  - `GET /{site}/items`<br>  - `DELETE /{site}/items/{id}`<br>• Supports pagination & filtering |
| **Mobile Client** | *TBD*                                                                      | • Consume unified API<br>• Display combined news feed with filtering                                                                                                                           |

---

## ⚙️ Setup & Running

### 1. Clone Repository

```bash
git clone https://github.com/GospodinovPetar/python_strypes_projects.git
cd fastapi/Mid_project
```

### 2. Configure Environment

```bash
cp env.example .env
# Edit .env:
# POSTGRES_USER=
# POSTGRES_PASSWORD=
# POSTGRES_DB=
# POSTGRES_HOST=
```

### 3. Launch with Docker Compose

```bash
docker-compose up --build
```

* **Services started:**

  * `db` (PostgreSQL)
  * `app` (FastAPI server at [http://localhost:8000](http://localhost:8000))
  * `Admin panel` (pgAdmin for Postgres) 

> *Tip: Use a cron or scheduler to `POST /{site}/scrape` periodically.*

---

## 📡 Example API Calls

### Fetch Latest Article

```bash
curl http://localhost:8000/trafficnews/latest
```

### List Articles (Paginated)

```bash
curl "http://localhost:8000/newsbg/items?limit=10&page=1"
```

#### Common Query Parameters

* `limit` (int): number of articles
* `page` (int): page number
* `date_from`, `date_to` (YYYY-MM-DD)
* `keyword` (string)

---

## 📸 Screenshots



---

## 🛠 Logging

All scrapers log to console via Python `logging`:

```text
2025-07-23 12:00:00 INFO  TrafficNewsScraper: Starting crawl
2025-07-23 12:00:02 INFO  TrafficNewsScraper: Found 1 new article
2025-07-23 12:00:03 ERROR TrafficNewsScraper: Failed to parse https://.../page
```

* **INFO**: crawl start, items found
* **ERROR**: HTTP failures, parse errors, DB issues

---

## 🤝 Contributing

1. Fork & branch
2. Make your changes
3. Submit a pull request

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

> _Created by Petar Gospodinov_  


