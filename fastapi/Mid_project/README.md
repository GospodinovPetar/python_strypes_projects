# Project Summary

This project provides a web service that scrapes the latest news articles from **DEV.BG**, **NEWS.BG** and **TRAFFICNEWS.BG** and stores them in a **PostgreSQL** database. It uses **FastAPI** to expose RESTful endpoints for:

* **Listing all scraped articles**
* **Retrieving a single article by ID**
* **Retrieving the most recent article from the database**
* **Scraping and returning the latest live article**
* **Scraping and storing a user‑provided article URL**
* **Deleting an article**

Under the hood, the scraper fetches a listing page, finds the first `<article>`, scrapes its content (title, image URL, date, paragraphs), and commits it to the corresponding table via **SQLAlchemy**.

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/GospodinovPetar/python_strypes_projects.git
   cd fastapi/Mid_project
   ```

2. **Configure environment variables**

   Create a `.env` file in the project root with the following content:

   ```ini
   DB_USER=admin
   DB_PASS=admin
   DB_NAME=news
   DB_HOST=localhost
   DB_PORT=5432

   PGADMIN_DEFAULT_EMAIL=admin@admin.com
   PGADMIN_DEFAULT_PASSWORD=admin
   PGADMIN_PORT=8080
   ```

3. **Start services with Docker Compose**

   ```bash
   docker-compose up --build
   ```

## Example API Calls

* **List all articles**

  ```bash
  http://localhost:8000/devnews/items
  ```

* **Get an article by ID**

  ```bash
  http://localhost:8000/devnews/items/1
  ```

* **Get the most recent article from DB**

  ```bash
  http://localhost:8000/devnews/latest_news_from_db/
  ```

* **Scrape & return the latest live article**

  ```bash
  
  ```

* **Scrape & store a specific URL**

  ```bash
  
  ```

* **Delete an article**

  ```bash
  
  ```

## Logging

The scraper and API log key events to the console. You should see lines indicating:

* **INFO** when items are found or operations succeed
* **ERROR** if scraping fails or the HTML structure changes

Example log output:

```text
INFO    Scraper      Found article link: https://dev.bg/it-news/example
INFO    Scraper      Scraped 5 paragraphs
ERROR   Scraper      Could not find `<article>` tag on page
```

Be sure to run the FastAPI server in a terminal to observe these logs in real time.
