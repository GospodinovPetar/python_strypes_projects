from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from app.site_configs import SITE_CONFIGS
from app.schemas import ArticleData
from app.logger.logger import logger

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; MidProject/2.0; +https://example.invalid)"
)


def download_html(url: str) -> str:
    """
    Fetch a URL and return HTML text.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    logger.info(f"[HTTP] GET {url}")
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        logger.info(f"[HTTP] {response.status_code} {url} ({len(response.text)} bytes)")
        return response.text
    except requests.RequestException as exc:
        logger.info(f"[HTTP] ERROR fetching {url}: {exc}")
        raise


def build_listing_url(listing_url: str, page_format: str, page_number: int) -> str:
    """
    Build the listing URL for a given page.
    """
    if page_number <= 1:
        final_url = listing_url
    else:
        final_url = listing_url.rstrip("/") + page_format.format(page=page_number)
    logger.info(f"[LISTING] page={page_number} -> {final_url}")
    return final_url


def get_text_or_default(
    soup: BeautifulSoup, css_selector: str, default_value: str = ""
) -> str:
    """
    Return the stripped text of the first element matching a selector.
    """
    element = soup.select_one(css_selector)
    if element:
        text_value = element.get_text(strip=True)
        if text_value:
            return text_value
    return default_value


def parse_title(soup: BeautifulSoup, site_config: Dict[str, Any]) -> str:
    """
    Extract a title with simple fallbacks.
    """
    selector = site_config.get("title_selector", "")
    if selector:
        title_text = get_text_or_default(soup, selector, "")
        if title_text:
            return title_text

    title_text = get_text_or_default(soup, "h1", "")
    if title_text:
        return title_text

    meta_tag = soup.find("meta", property="og:title") or soup.find(
        "meta", attrs={"name": "og:title"}
    )
    if meta_tag:
        content = meta_tag.get("content")
        if content:
            return content.strip()

    return ""


def _normalize_isoish(value: str) -> Optional[str]:
    """Make timestamps friendlier to `fromisoformat()` (Z → +00:00, ±HHMM → ±HH:MM)."""
    if not value:
        return None
    string = value.strip()
    if not string:
        return None
    if string.endswith("Z"):
        string = string[:-1] + "+00:00"
    if len(string) >= 5 and (string[-5] in "+-") and string[-3] != ":" and string[-2:].isdigit():
        string = string[:-2] + ":" + string[-2:]
    return string


def _take_date_only(ts: str) -> Optional[str]:
    """Parse a timestamp to date-only ISO; fallback if already like 'YYYY-MM-DD'."""
    normal = _normalize_isoish(ts)
    if not normal:
        return None
    try:
        return datetime.fromisoformat(normal).date().isoformat()
    except Exception:
        if len(normal) >= 10 and normal[4] == "-" and normal[7] == "-":
            return normal[:10]
        return None


def parse_date(soup: BeautifulSoup, site_config: Dict[str, Any]) -> Optional[str]:
    """
    Return a date ('YYYY-MM-DD') using selector, <time>, or common meta tags.
    """
    selector = site_config.get("date_selector")
    if selector:
        node = soup.select_one(selector)
        if node:
            val = (node.get("datetime") or node.get_text(strip=True) or "").strip()
            date = _take_date_only(val)
            if date:
                return date

    time_tag = soup.find("time")
    if time_tag:
        val = (time_tag.get("datetime") or time_tag.get_text(strip=True) or "").strip()
        date = _take_date_only(val)
        if date:
            return date

    for key in ("article:published_time", "og:updated_time", "datePublished", "publish-date"):
        tag = (
            soup.find("meta", property=key)
            or soup.find("meta", attrs={"name": key})
            or soup.find("meta", itemprop=key)
        )
        val = tag.get("content").strip() if tag and tag.get("content") else None
        if val:
            date = _take_date_only(val)
            if date:
                return date

    return None


def collect_image_urls(
    article_url: str, container: Tag | BeautifulSoup, css_selectors: List[str]
) -> List[str]:
    """
    Collect unique, absolute `<img src=...>` URLs from an article container.
    """
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
    """
    Extract all non-empty `<p>` texts in order.
    """
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
    """
    Find the main article container using configured selectors.
    """
    selectors = site_config.get("article_root_selectors", [])
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            return node
    return soup


def extract_links_from_listing(
    listing_html: str, site_config: Dict[str, Any]
) -> List[str]:
    """
    Extract article links from a listing page; absolutize, filter, dedupe.
    """
    soup = BeautifulSoup(listing_html, "html.parser")

    article_links: List[str] = []
    seen: set = set()

    link_selector = site_config["listing_link_selector"]
    link_elements = soup.select(link_selector)
    logger.info(f"[LISTING] selector='{link_selector}' matched {len(link_elements)} links (raw)")

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

    logger.info(f"[LISTING] usable article links: {len(article_links)}")
    return article_links


def parse_article(
    article_url: str, article_html: str, site_name: str, site_config: Dict[str, Any]
) -> ArticleData:
    """
    Parse an article page into `ArticleData`.
    """
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

    logger.info(
        f"[PARSE] site={site_name} "
        f"title_len={len(title_text)} date={date_text or 'None'} "
        f"images={len(all_image_urls)} paragraphs={len(paragraphs)} "
        f"url={article_url}"
    )

    return ArticleData(
        source=site_name,
        url=article_url,
        title=title_text,
        date=date_text,
        image_urls=all_image_urls,
        paragraphs=paragraphs,
    )


def scrape_site(site_name: str, page_number: int = 1) -> List[ArticleData]:
    """
    Scrape a single listing page and parse each article.
    """
    site_key = site_name.lower()
    site_config = SITE_CONFIGS[site_key]

    listing_url = build_listing_url(
        listing_url=site_config["listing_url"],
        page_format=site_config.get("listing_page_format", "/page/{page}/"),
        page_number=page_number,
    )

    logger.info(f"[SCRAPE] site={site_key} page={page_number} listing={listing_url}")

    listing_html = download_html(listing_url)
    article_links = extract_links_from_listing(listing_html, site_config)

    scraped_articles: List[ArticleData] = []
    for link in article_links:
        logger.info(f"[SCRAPE] fetching article {link}")
        article_html = download_html(link)
        article = parse_article(link, article_html, site_key, site_config)
        if len(article.paragraphs) > 2:
            logger.info(f"[SCRAPE] accepted (paragraphs={len(article.paragraphs)}) {link}")
            scraped_articles.append(article)
        else:
            logger.info(f"[SCRAPE] skipped (too short: {len(article.paragraphs)} paragraphs) {link}")

    logger.info(f"[SCRAPE] page done. kept={len(scraped_articles)} of {len(article_links)}")
    return scraped_articles


def scrape_pages(
    site_name: str, start_page: int = 1, number_of_pages: int = 1
) -> List[ArticleData]:
    """
    Scrape multiple consecutive listing pages and combine results.
    """
    if number_of_pages < 1:
        number_of_pages = 1

    logger.info(f"[SCRAPE:MULTI] site={site_name} pages={start_page}..{start_page + number_of_pages - 1}")

    all_articles: List[ArticleData] = []

    last_page = start_page + number_of_pages - 1
    current_page = start_page
    while current_page <= last_page:
        page_articles = scrape_site(site_name, current_page)
        for article in page_articles:
            all_articles.append(article)
        current_page += 1

    logger.info(f"[SCRAPE:MULTI] total articles collected: {len(all_articles)}")
    return all_articles
