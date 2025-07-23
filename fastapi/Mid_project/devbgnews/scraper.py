from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "DevNewsScraper"}
LISTING_URL = "https://dev.bg/digest/category/it-news/"


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def fetch_first_recent_link(listing_url: str = LISTING_URL) -> str:
    soup = get_soup(listing_url)
    section = soup.find("section", class_="blogroll-section digest-section")
    if not section:
        raise RuntimeError(
            "Section 'blogroll-section digest-section' not found on listing page"
        )

    main_div = section.find("div", class_="blogroll-main")
    if not main_div:
        raise RuntimeError("Div 'blogroll-main' not found in section")

    first_article = main_div.find("article")
    if not first_article:
        raise RuntimeError("No <article> tag found in blogroll-main")

    link_tag = first_article.find("a", href=True)
    if not link_tag:
        raise RuntimeError("No <a> tag with href inside the first <article>")

    return link_tag["href"]


def scrape_devnews_article(url: str) -> dict:
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    article_tag = soup.find("article")
    if not article_tag:
        raise RuntimeError("Article container not found on page")

    # 1) Title
    title_tag = article_tag.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # 2) Image
    img_tag = article_tag.find("img")
    image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

    # 3) Published date
    date_tag = soup.find("span", class_="post-date")
    if date_tag:
        raw = date_tag.get_text(strip=True)
        # strip off the Bulgarian prefix
        raw = raw.replace("Публикувано на", "").strip()
        # parse Bulgarian month names
        bg_months = {
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
        parts = raw.split()  # e.g. ["21", "юли", "2025", "г."]
        day = int(parts[0])
        month = bg_months[parts[1].lower()]
        year = int(parts[2])
        date = datetime(year, month, day).isoformat()
    else:
        date = None

    # 4) Paragraphs
    paragraphs = []
    for p in article_tag.find_all("p"):
        txt = p.get_text(strip=True)
        if txt:
            paragraphs.append(txt)

    return {
        "title": title,
        "image_url": image_url,
        "date": date,
        "paragraphs": paragraphs,
    }


def fetch_and_scrape_latest_devnews() -> dict:
    article_url = fetch_first_recent_link(LISTING_URL)
    return scrape_devnews_article(article_url)
