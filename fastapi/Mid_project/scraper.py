import requests
from bs4 import BeautifulSoup


def scrape_trafficnews(url: str) -> dict:
    headers = {
        "User-Agent": "TrafficNewsScraper"
    } # Never stay anonymous
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

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
    if time_tag:
        date = time_tag.text.strip()
    else:
        date = None

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
