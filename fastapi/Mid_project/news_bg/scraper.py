from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "NewsScraper"}
LISTING_URL = "https://news.bg"


def get_soup(url: str, headers: dict = HEADERS) -> BeautifulSoup:
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def fetch_first_recent_link(listing_url: str = LISTING_URL) -> str:
    link = get_soup(
        listing_url, headers={"User-Agent": "RecentArticlesScraper"}
    ).select_one("ul#recent-articles li h2 a[href]")
    if not link:
        raise RuntimeError("Could not find recent article link")
    return link["href"]


def scrape_news(url: str) -> dict:
    soup = get_soup(url)
    article = soup.select_one("article.article-inner")
    if not article:
        raise RuntimeError("Could not find the main <article> element")

    # 1) Заглавие
    title_el = article.select_one("h1[itemprop='headline']")
    title = title_el.get_text(strip=True) if title_el else None

    # 2) Картинка
    img_el = article.select_one("div.img-or-video img")
    image_url = (
        urljoin(LISTING_URL, img_el["src"])
        if img_el and img_el.has_attr("src")
        else None
    )

    # 3) Дата и час
    time_el = article.select_one("div.article-info p.time")
    date = time_el.get_text(strip=True) if time_el else None

    # 4) Параграфи — все <p> без class
    paragraphs = [
        p.get_text(strip=True)
        for p in article.select("p:not([class])")
        if p.get_text(strip=True)
    ]

    return {
        "title": title,
        "image_url": image_url,
        "date": date,
        "paragraphs": paragraphs,
    }
