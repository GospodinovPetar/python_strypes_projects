from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "DevNewsScraper"}
LISTING_URL = "https://dev.bg/digest/category/it-news/"

# Bulgarian month lookup
BG_MONTHS = {
    "януари": 1,
    "февруари": 2,
    "март": 3,
    "април": 4,
    "май": 5,
    "юни": 6,
    "юли": 7,
    "август": 8,
    "септември": 9,
    "октомври": 10,
    "ноември": 11,
    "декември": 12,
}


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def fetch_first_recent_link(listing_url: str = LISTING_URL) -> str:
    selector = (
        "section.blogroll-section.digest-section" " .blogroll-main article a[href]"
    )
    link = get_soup(listing_url).select_one(selector)
    if not link:
        raise RuntimeError(f"No recent article link found using selector {selector!r}")
    return link["href"]


def scrape_devnews_article(url: str) -> dict:
    soup = get_soup(url)
    article = soup.find("article")
    if not article:
        raise RuntimeError("Article container not found on page")

    # Title
    title_tag = article.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Image URL
    img = article.find("img")
    image_url = img["src"] if img and img.has_attr("src") else None

    # Published date
    date_tag = soup.select_one("span.post-date")
    if date_tag:
        raw = date_tag.get_text(strip=True).replace("Публикувано на", "").strip()
        day_str, month_str, year_str, *_ = raw.split()
        date = (
            datetime(int(year_str), BG_MONTHS[month_str.lower()], int(day_str))
            .date()
            .isoformat()
        )  # devbg doesn't give out time of upload, just date
    else:
        date = None

    # Paragraphs
    paragraphs = [
        p.get_text(strip=True) for p in article.find_all("p") if p.get_text(strip=True)
    ]

    return {
        "title": title,
        "image_url": image_url,
        "date": date,
        "paragraphs": paragraphs,
    }


def fetch_and_scrape_latest_devnews() -> dict:
    url = fetch_first_recent_link()
    return scrape_devnews_article(url)
