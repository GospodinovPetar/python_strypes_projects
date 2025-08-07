from datetime import datetime

import requests
from bs4 import BeautifulSoup

LISTING_URL = "https://dev.bg/digest/category/it-news/"
DEVBG_HEADERS = {"User-Agent": "DevNewsScraper"}
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


def _get_page_html(url: str, headers: dict) -> str:
    """Fetches the page HTML using the given headers."""
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def get_soup(url: str) -> BeautifulSoup:
    """Fetches and parses HTML from Dev.bg."""
    html = _get_page_html(url, DEVBG_HEADERS)
    return BeautifulSoup(html, "html.parser")


def fetch_first_recent_link(listing_url: str = LISTING_URL) -> str:
    soup = get_soup(listing_url)
    selector = "section.blogroll-section.digest-section .blogroll-main article a[href]"
    link = soup.select_one(selector)
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
    image_urls = []

    header_image = article.select_one("section.article-head img.wp-post-image[src]")
    if header_image:
        src = header_image["src"].strip()
        if src:
            image_urls.append(src)

    body_images = [
        img["src"].strip()
        for block in article.select("div.wp-block-image")
        for img in block.find_all("img", src=True)
        if img["src"].strip()
    ]
    image_urls.extend(body_images)

    # Published date
    date_tag = soup.select_one("span.post-date")
    if date_tag:
        raw = date_tag.get_text(strip=True).replace("Публикувано на", "").strip()
        day_str, month_str, year_str, *_ = raw.split()
        date = (
            datetime(int(year_str), BG_MONTHS[month_str.lower()], int(day_str))
            .date()
            .isoformat()
        )
    else:
        date = None

    # Paragraphs
    paragraphs = [
        p.get_text(strip=True) for p in article.find_all("p") if p.get_text(strip=True)
    ]

    return {
        "url": url,
        "title": title,
        "date": date,
        "image_url": image_urls,
        "paragraphs": paragraphs,
    }


def fetch_and_scrape_latest_devnews() -> dict:
    url = fetch_first_recent_link()
    return scrape_devnews_article(url)
