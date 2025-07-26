from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://www.wired.com"
HEADERS = {"User-Agent": "NewsScraper"}


def get_page_html(source: str) -> str:
    """
    Given a URL or file path, return the HTML as text.
    If source starts with 'http', fetch via HTTP;
    otherwise, read from local file.
    """
    response = requests.get(source, headers=HEADERS)
    response.raise_for_status()
    return response.text


def fetch_first_recent_link() -> str:
    """
    Load Wired's homepage and return the first article URL found.
    """
    html = get_page_html(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")

    # find the first <a> whose href contains '/story/'
    for a in soup.find_all("a", href=True):
        if "/story/" in a["href"]:
            return urljoin(BASE_URL, a["href"])

    raise RuntimeError("Could not find any article links on the homepage.")


def scrape_news(source: str) -> dict:
    """
    Given an article URL or file, return a dict with title, date, images, and paragraphs.
    """
    html = get_page_html(source)
    soup = BeautifulSoup(html, "html.parser")

    # Title
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)

    # Date
    time_tag = soup.find("time")
    if time_tag:
        if time_tag.has_attr("datetime"):
            date = time_tag["datetime"]
        else:
            date = time_tag.get_text(strip=True)

    # Article body
    body = soup.find("div", itemprop="articleBody") or soup.find("article")

    # Images
    images = []
    if body:
        for img in body.find_all("img", src=True):
            images.append(img["src"])

    # Paragraphs
    paragraphs = []
    if body:
        for p in body.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

    return {
        "title": title,
        "date": date,
        "image_url": images,
        "paragraphs": paragraphs,
    }
