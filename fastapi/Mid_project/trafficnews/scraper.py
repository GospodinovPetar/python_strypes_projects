from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "TrafficNewsScraper"}
LISTING_URL = "https://trafficnews.bg/bulgaria/"


def get_soup(url: str, headers: dict = HEADERS) -> BeautifulSoup:
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def fetch_latest_article_url(listing_url: str = LISTING_URL) -> str:
    link = get_soup(listing_url).select_one("article a[href]")
    if not link:
        raise RuntimeError("Не намерих <article> или <a href> на listing страницата")
    return urljoin(listing_url, link["href"])


def scrape_trafficnews(url: str) -> dict:
    soup = get_soup(url)

    title = soup.select_one(".new-title")
    title = title.get_text(strip=True) if title else None

    img = soup.select_one(".article-img img[src]")
    image_url = img["src"] if img else None

    time_el = soup.select_one("div.single-infos.mb10 > span.time")
    date = time_el.get_text(strip=True) if time_el else None

    paragraphs = [
        p.get_text(strip=True)
        for p in soup.select("div.article-text.single-content p")
        if p.get_text(strip=True)
    ]

    return {
        "title": title,
        "image_url": image_url,
        "date": date,
        "paragraphs": paragraphs,
    }


def fetch_latest_news(listing_url: str = LISTING_URL) -> dict:
    url = fetch_latest_article_url(listing_url)
    data = scrape_trafficnews(url)
    data["url"] = url
    return data
