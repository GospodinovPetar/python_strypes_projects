# 📰 Mid Project News Scraper

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

> **A unified scraping & API service** for aggregating news from multiple Bulgarian sites into a single mobile-friendly
> feed.

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

By aggregating these disparate sources, you can power a **mobile app** to deliver all headlines & articles in one
cohesive experience.

---

## 🔧 Architecture & Data Flow

| Component         | Location / Modules                                                         | Responsibility                                                                                                                                                                                 |
|-------------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
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

### 2. Configure Environment Configure Environment

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
    * `admin panel` (pgAdmin for Postgres)

> *Tip: Use a cron or scheduler to `POST /{site}/scrape` periodically.*

---

## 📡 Example API Calls

Use the `{site}` placeholder for any of: `trafficnews`, `devnews`, `newsbg`.

* **Read Latest Article**

  ```bash
  curl http://localhost:8000/{site}/latest
  ```

  Retrieves the most recently stored article from the database.

* **Read All Articles**

  ```bash
  curl http://localhost:8000/{site}/items
  ```

  Retrieves all stored articles. Supports optional filtering via query parameters:

    * `date_from=YYYY-MM-DD`
    * `date_to=YYYY-MM-DD`
    * `keyword=search_term`

* **Read Article by ID**

  ```bash
  curl http://localhost:8000/{site}/items/{id}
  ```

  Retrieves a single article by its database ID.

* **Scrape Latest Article**

  ```bash
  curl -X POST http://localhost:8000/{site}/scrape/latest
  ```

  Scrapes the newest article from the site feed and stores it in the database.

* **Delete an Article**

  ```bash
  curl -X DELETE http://localhost:8000/{site}/items/{id}
  ```

  Deletes the specified article by its database ID.

## 📸 Screenshots

---

## 🛠 Logging


---

## 🤝 Contributing

1. Fork & branch
2. Make your changes
3. Submit a pull request

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 📄 License

Distributed under the MIT License.

> _Created by Petar Gospodinov_  
