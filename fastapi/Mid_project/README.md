# TrafficNews Scraper API

A FastAPI service that scrapes news articles from `trafficnews.bg/bulgaria/`, stores them in PostgreSQL, and provides RESTful endpoints to manage and retrieve the data. The application and database are spun up together using Docker Compose.

## Endpoints

| Method | Path                          | Description                                                                           |
| ------ |-------------------------------| ------------------------------------------------------------------------------------- |
| **GET**    | `trafficnews/items`           | Retrieve all stored articles.                                                        |
| **GET**    | `trafficnews/items/{item_id}` | Retrieve a single article by its numeric `id`.                                       |
| **GET**    | `trafficnews/latest_news_from_db/`       | Fetch the most recently inserted article (by `id`) from the database.     ___________|
| **DELETE** | `trafficnews/items/{item_id}`            | Delete an article by its numeric `id`.                                               |
| **POST**   | `trafficnews/scrape/latest`              | Scrape the latest article from the listing page and upsert it into the database.     |
| **POST**   | `trafficnews/scrape`                     | Scrape a given article URL and upsert it into the database.                          |

### Request / Response Models

- **`ScrapeRequest`** (used by `/scrape`):
  ```json
  {
    "url": "https://trafficnews.bg/..."
  }
  ```
- **`ArticleSchema`** includes:
  - `id`: integer
  - `url`: string
  - `title`: string
  - `image_url`: string | null
  - `date`: string (original scraped date)
  - `paragraphs`: string[]
  - `created_at`: datetime

## Installation & Running

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/trafficnews-scraper.git
   cd trafficnews-scraper
   ```

2. **Create an environment file**:
   - Copy `.env.example` to `.env`
   - Fill in your database credentials:
     ```dotenv
     DATABASE_URL=postgresql+psycopg2://<DB_USER>:<DB_PASS>@<DB_HOST>:<DB_PORT>/<DB_NAME>
     ```

3. **Start the application with Docker Compose** (it will build and run both the FastAPI app and Postgres):
   ```bash
   docker-compose up --build
   ```

4. **Access the API**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc:       `http://localhost:8000/redoc`

## Project Structure

```
.
├── app/
│   ├── main.py           # FastAPI application & endpoints
│   ├── db.py             # SQLAlchemy engine, Base, session factory
│   ├── models.py         # ORM model `Article`
│   ├── schemas.py        # Pydantic model `ArticleSchema`
│   ├── scraper.py        # `scrape_trafficnews()`, `fetch_latest_news()`, etc.
│   └── tasks.py          # Optional helper functions
├── docker-compose.yml    # Defines app + database services
├── Dockerfile            # Builds the FastAPI application image
├── .env.example          # Example environment variables
└── README.md             # This file
```

## TODOs

- [ ] Create and document `.env.example` (database credentials, other settings).
- [ ] Add integration tests for all endpoints.
- [ ] Enhance error handling.

> _Created by Petar Gospodinov_  
