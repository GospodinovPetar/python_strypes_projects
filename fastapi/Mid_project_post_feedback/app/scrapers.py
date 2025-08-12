from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; MidProject/2.0; +https://example.invalid)"
)


@dataclass(frozen=True)
class ArticleData:
    source: str
    url: str
    title: str
    date: Optional[str]
    image_urls: List[str]
    paragraphs: List[str]


# Config-driven sites (add more below)
SITE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "techcrunch": {
        "base_url": "https://techcrunch.com",
        "listing_url": "https://techcrunch.com/",
        "listing_page_format": "/page/{page}/",

        # article links on listing pages
        "listing_link_selector": "a.post-block__title__link[href]",
        "listing_link_exclude_contains": ["/video/"],

        # where article content lives
        "article_root_selectors": ["article", ".article-content"],

        # title/date
        "title_selector": "h1",
        "date_selector": "time[datetime]",

        # images (inside the article only)
        "header_image_selectors": ["figure img[src]", "header img[src]"],
        "body_image_selectors": [".article-content img[src]"],
    },

    "technewsbg": {
        "base_url": "https://technews.bg",
        "listing_url": "https://technews.bg/",
        "listing_page_format": "/page/{page}/",

        "listing_link_selector": "article .entry-title a[href], .entry-title a[href]",
        "listing_link_exclude_contains": [
            "/article-category/", "/category/", "/tag/", "/author/", "/search/", "/page/",
        ],

        "article_root_selectors": ["article", ".entry-content"],
        "title_selector": "h1.entry-title",
        "date_selector": "time.entry-date, span.posted-on time, .entry-meta time",

        "header_image_selectors": [
            "header img[src]", ".post-header img[src]", ".entry-header img[src]"
        ],
        "body_image_selectors": [
            "div.wp-block-image img[src]", ".entry-content img[src]"
        ],
    },

    "wired": {
        "base_url": "https://www.wired.com",
        "listing_url": "https://www.wired.com/most-recent/",
        "listing_page_format": "/page/{page}/",

        "listing_link_selector": ".archive-item-component a[href], a[href^='/story/']",
        "listing_link_exclude_contains": [],

        "article_root_selectors": ["article"],
        "title_selector": "h1",
        "date_selector": "time[datetime]",

        "header_image_selectors": ["header img[src]", ".article-header img[src]"],
        "body_image_selectors": ["figure img[src]", ".body__inner-container img[src]", ".content img[src]"],
    },
}


def download_html(url: str) -> str:
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def build_listing_url(listing_url: str, page_format: str, page_number: int) -> str:
    if page_number <= 1:
        return listing_url
    return listing_url.rstrip("/") + page_format.format(page=page_number)


def get_text_or_default(
    soup: BeautifulSoup, css_selector: str, default_value: str = ""
) -> str:
    element = soup.select_one(css_selector)
    if element:
        text_value = element.get_text(strip=True)
        if text_value:
            return text_value
    return default_value


def parse_title(soup: BeautifulSoup, site_config: Dict[str, Any]) -> str:
    selector = site_config.get("title_selector", "")
    if selector:
        title_text = get_text_or_default(soup, selector, "")
        if title_text:
            return title_text

    title_text = get_text_or_default(soup, "h1", "")
    if title_text:
        return title_text

    meta_tag = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
    if meta_tag:
        content = meta_tag.get("content")
        if content:
            return content.strip()

    return ""


def parse_date(soup: BeautifulSoup, site_config: Dict[str, Any]) -> Optional[str]:
    """
    Prefer machine-readable <time datetime="..."> and return YYYY-MM-DD.
    (No regex, no locale-specific parsing.)
    """
    time_selector = site_config.get("date_selector") or "time[datetime]"
    time_tag = soup.select_one(time_selector)
    if time_tag is None or not time_tag.has_attr("datetime"):
        return None

    raw = (time_tag.get("datetime") or "").strip()
    if not raw:
        return None

    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return None


def collect_image_urls(
    article_url: str, container: Tag | BeautifulSoup, css_selectors: List[str]
) -> List[str]:
    image_urls: List[str] = []
    seen: set = set()

    for selector in css_selectors:
        matching_images = container.select(selector)
        for img in matching_images:
            src_value = img.get("src")
            if not src_value:
                continue
            absolute_url = urljoin(article_url, src_value.strip())
            if absolute_url.startswith("//"):
                absolute_url = "https:" + absolute_url
            if absolute_url not in seen:
                seen.add(absolute_url)
                image_urls.append(absolute_url)

    return image_urls


def parse_paragraphs(container: Tag | BeautifulSoup) -> List[str]:
    paragraphs: List[str] = []
    paragraph_nodes = container.select("p")
    for p in paragraph_nodes:
        text_value = p.get_text(strip=True)
        if text_value:
            paragraphs.append(text_value)
    return paragraphs


def find_article_root(
    soup: BeautifulSoup, site_config: Dict[str, Any]
) -> Tag | BeautifulSoup:
    selectors = site_config.get("article_root_selectors", [])
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            return node
    return soup


def extract_links_from_listing(
    listing_html: str, site_config: Dict[str, Any]
) -> List[str]:
    soup = BeautifulSoup(listing_html, "html.parser")

    article_links: List[str] = []
    seen: set = set()

    link_selector = site_config["listing_link_selector"]
    link_elements = soup.select(link_selector)

    for a in link_elements:
        href_value = a.get("href")
        if not href_value:
            continue

        absolute_url = urljoin(site_config["base_url"], href_value)
        should_skip = False

        exclude_fragments = site_config.get("listing_link_exclude_contains", [])
        for bad in exclude_fragments:
            if bad in absolute_url:
                should_skip = True
                break

        if should_skip:
            continue

        if absolute_url not in seen:
            seen.add(absolute_url)
            article_links.append(absolute_url)

    return article_links


def parse_article(
    article_url: str, article_html: str, site_name: str, site_config: Dict[str, Any]
) -> ArticleData:
    soup = BeautifulSoup(article_html, "html.parser")
    article_root = find_article_root(soup, site_config)

    title_text = parse_title(soup, site_config)
    date_text = parse_date(soup, site_config)

    header_image_urls: List[str] = []
    header_selectors = site_config.get("header_image_selectors", [])
    for selector in header_selectors:
        node = article_root.select_one(selector)
        if node and node.get("src"):
            absolute_url = urljoin(article_url, node.get("src").strip())
            if absolute_url.startswith("//"):
                absolute_url = "https:" + absolute_url
            header_image_urls.append(absolute_url)
            break  # one header image max

    body_image_urls = collect_image_urls(
        article_url=article_url,
        container=article_root,
        css_selectors=site_config.get("body_image_selectors", []),
    )

    all_image_urls: List[str] = []
    for u in header_image_urls:
        all_image_urls.append(u)
    for u in body_image_urls:
        if u not in all_image_urls:
            all_image_urls.append(u)

    paragraphs = parse_paragraphs(article_root)

    return ArticleData(
        source=site_name,
        url=article_url,
        title=title_text,
        date=date_text,
        image_urls=all_image_urls,
        paragraphs=paragraphs,
    )


def scrape_site(site_name: str, page_number: int = 1) -> List[ArticleData]:
    site_key = site_name.lower()
    site_config = SITE_CONFIGS[site_key]

    listing_url = build_listing_url(
        listing_url=site_config["listing_url"],
        page_format=site_config.get("listing_page_format", "/page/{page}/"),
        page_number=page_number,
    )

    listing_html = download_html(listing_url)
    article_links = extract_links_from_listing(listing_html, site_config)

    scraped_articles: List[ArticleData] = []
    for link in article_links:
        article_html = download_html(link)
        article = parse_article(link, article_html, site_key, site_config)
        if len(article.title) > 1:
            scraped_articles.append(article)

    return scraped_articles


def scrape_pages(
    site_name: str, start_page: int = 1, number_of_pages: int = 1
) -> List[ArticleData]:
    if number_of_pages < 1:
        number_of_pages = 1

    all_articles: List[ArticleData] = []

    last_page = start_page + number_of_pages - 1
    current_page = start_page
    while current_page <= last_page:
        page_articles = scrape_site(site_name, current_page)
        for article in page_articles:
            all_articles.append(article)
        current_page += 1

    return all_articles
