from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# 1) Общи константи
HEADERS = {"User-Agent": "NewsScraper"}
LISTING_URL = "https://news.bg"


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def fetch_first_recent_link(listing_url: str = LISTING_URL) -> str:
    """
    Fetches the first <li> under <ul id="recent-articles">
    and returns the href of its <h2><a> tag.
    """
    headers = {"User-Agent": "RecentArticlesScraper"}
    resp = requests.get(listing_url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    ul = soup.find("ul", id="recent-articles")
    if not ul:
        raise RuntimeError("Could not find <ul id='recent-articles'>")

    first_li = ul.find("li")
    if not first_li:
        raise RuntimeError("No <li> found inside <ul id='recent-articles'>")

    a_tag = first_li.find("h2").find("a", href=True)
    if not a_tag:
        raise RuntimeError("No <a> tag with href inside the first <li><h2>")

    return a_tag["href"]


def scrape_news(url: str) -> dict:
    soup = get_soup(url)
    # 0) Main article container
    article = soup.find("article", class_="article-inner")
    if not article:
        raise RuntimeError("Could not find the main <article> element")

    # 1) Заглавие
    title_tag = article.find("h1", itemprop="headline")
    title = title_tag.get_text(strip=True) if title_tag else None

    # 2) Картинка
    img_el = article.select_one("div.img-or-video img")
    image_url = urljoin(LISTING_URL, img_el["src"]) if img_el and img_el.get("src") else None

    # 3) Дата и час
    time_tag = article.select_one("div.article-info p.time")
    date = time_tag.get_text(strip=True) if time_tag else None

    # 4) Параграфи — все <p> без class (skip the time, author, etc.)
    paragraphs = []
    for p in article.find_all("p"):
        if not p.has_attr("class"):
            txt = p.get_text(strip=True)
            if txt:
                paragraphs.append(txt)

    return {
        "title": title,
        "image_url": image_url,
        "date": date,
        "paragraphs": paragraphs,
    }