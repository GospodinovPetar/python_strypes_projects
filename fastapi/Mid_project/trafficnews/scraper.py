from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# 1) Общи константи
HEADERS = {"User-Agent": "TrafficNewsScraper"}
LISTING_URL = "https://trafficnews.bg/bulgaria/"


# 2) Утилитна функция: прави GET + raise_for_status + връща soup
def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


# 3) Връща абсолютния URL на първата <article> от listing-а
def fetch_latest_article_url(listing_url: str = LISTING_URL) -> str:
    soup = get_soup(listing_url)
    first = soup.find("article")
    if not first:
        raise RuntimeError("Не намерих <article> на listing страницата")
    a = first.find("a", href=True)
    if not a:
        raise RuntimeError("Първият <article> няма <a href>")
    return urljoin(listing_url, a["href"])


# 4) Скрапва една статия — използва get_soup вместо повторен код
def scrape_trafficnews(url: str) -> dict:
    soup = get_soup(url)

    # 1) Заглавие
    title_tag = soup.find(class_="new-title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # 2) Картинка
    img_url = None
    img_container = soup.find(class_="article-img")
    if img_container:
        img = img_container.find("img")
        if img and img.get("src"):
            img_url = img["src"]

    # 3) Дата и час
    time_tag = soup.select_one("div.single-infos.mb10 > span.time")
    date = time_tag.text.strip() if time_tag else None

    # 4) Параграфи
    paragraphs = []
    content_div = soup.find("div", class_="article-text single-content")
    if content_div:
        for p in content_div.find_all("p"):
            txt = p.get_text(strip=True)
            if txt:
                paragraphs.append(txt)

    return {
        "title": title,
        "image_url": img_url,
        "date": date,
        "paragraphs": paragraphs,
    }


def fetch_latest_news(listing_url: str = LISTING_URL) -> dict:
    url = fetch_latest_article_url(listing_url)
    data = scrape_trafficnews(url)
    data["url"] = url
    return data
