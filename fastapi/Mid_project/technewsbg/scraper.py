from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# Configuration
USER_AGENT = "TechNewsScraper"
BASE_URL = "https://technews.bg"
HEADERS = {"User-Agent": USER_AGENT}


def get_soup(url: str) -> BeautifulSoup:
    """Fetch and parse HTML for a given URL."""
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def fetch_first_recent_link() -> str:
    """Return the URL of the latest TechNews.bg article from the homepage."""
    soup = get_soup(BASE_URL)
    link_el = soup.select_one("article.hentry a[href]")
    if not link_el:
        raise RuntimeError(
            "Could not find the latest article link on TechNews.bg homepage"
        )
    return urljoin(BASE_URL, link_el["href"])


def scrape_news(url: str) -> dict:
    """Scrape a TechNews.bg article given its URL."""
    page_url = str(url)
    soup = get_soup(page_url)

    # Title
    title = soup.select_one("h1.entry-title")
    title = title.get_text(strip=True) if title else None

    # Publish date
    time = soup.select_one("time.entry-date.published")
    date = time.get("datetime") or time.get_text(strip=True) if time else None

    # Article body
    body = soup.select_one("div.entry-content") or soup.select_one("article")

    # Images: list of img src/data-src
    images = []
    for img in body.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if src and not src.startswith("data:"):
            images.append(urljoin(page_url, src))

    # Paragraphs: all non-empty text from p tags
    paragraphs = [
        p.get_text(strip=True) for p in body.find_all("p") if p.get_text(strip=True)
    ]

    return {
        "url": page_url,
        "title": title,
        "image_url": images,
        "date": date,
        "paragraphs": paragraphs,
    }


def fetch_latest_news() -> dict:
    """Fetch and scrap the latest TechNews.bg article from homepage."""
    latest_url = fetch_first_recent_link()
    data = scrape_news(latest_url)
    return data
