from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from app.schemas import ArticleData

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; MidProject/2.0; +https://example.invalid)"
)

# Config-driven sites (add more below)
SITE_CONFIGS: Dict[str, Dict[str, Any]] = {
    # TechCrunch homepage / recent pages (loop-card layout).
    "techcrunch": {
        "base_url": "https://techcrunch.com",
        "listing_url": "https://techcrunch.com/",
        "listing_page_format": "/page/{page}/",
        # Article links on listing pages (new TC theme uses loop-card*)
        "listing_link_selector": "a.loop-card__title-link[href], .loop-card__title a[href]",
        "listing_link_exclude_contains": [
            "/video/",
            "/videos/",
            "/podcasts/",
            "/events/",
            "/sponsored/",
            "/brand-studio/",
            "/category/",
            "/tag/",
        ],
        # Where article content lives
        "article_root_selectors": [
            "article",
            ".wp-block-post-content",
            ".entry-content",
            ".article-content",
        ],
        # Title / date
        "title_selector": "h1",
        "date_selector": "time[datetime]",
        # Images (inside the article only)
        "header_image_selectors": [
            "header img[src]",
            "figure img.wp-post-image[src]",
            "figure.wp-block-image img[src]",
        ],
        "body_image_selectors": [
            ".wp-block-post-content img[src]",
            ".article-content img[src]",
            ".entry-content img[src]",
        ],
    },
    # TechNews.bg (WordPress-based).
    "technewsbg": {
        "base_url": "https://technews.bg",
        "listing_url": "https://technews.bg/",
        "listing_page_format": "/page/{page}/",
        "listing_link_selector": "article .entry-title a[href], .entry-title a[href]",
        "listing_link_exclude_contains": [
            "/article-category/",
            "/category/",
            "/tag/",
            "/author/",
            "/search/",
            "/page/",
        ],
        "article_root_selectors": ["article", ".entry-content"],
        "title_selector": "h1.entry-title",
        "date_selector": "time.entry-date, span.posted-on time, .entry-meta time",
        "header_image_selectors": [
            "header img[src]",
            ".post-header img[src]",
            ".entry-header img[src]",
        ],
        "body_image_selectors": [
            "div.wp-block-image img[src]",
            ".entry-content img[src]",
        ],
    },
    # WIRED "Most Recent".
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
        "body_image_selectors": [
            "figure img[src]",
            ".body__inner-container img[src]",
            ".content img[src]",
        ],
    },
}


def download_html(url: str) -> str:
    """
    Fetch a URL and return its HTML as text.

    Parameters
    ----------
    url : str
        Absolute URL to download.

    Returns
    -------
    str
        Response body as text.

    Raises
    ------
    requests.HTTPError
        If the response status is not 2xx.
    requests.RequestException
        For other network issues (timeouts, DNS, etc.).
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def _first_meta(soup: BeautifulSoup, key: str) -> Optional[str]:
    tag = (
        soup.find("meta", property=key)
        or soup.find("meta", attrs={"name": key})
        or soup.find("meta", itemprop=key)
    )
    return tag.get("content").strip() if tag and tag.get("content") else None


def build_listing_url(listing_url: str, page_format: str, page_number: int) -> str:
    """
    Build a listing page URL for the requested page number.

    Page 1 returns `listing_url` unchanged; for page >= 2 the `page_format`
    is appended to the stripped `listing_url`, with `{page}` replaced.

    Parameters
    ----------
    listing_url : str
        Base listing URL (page 1).
    page_format : str
        Format pattern such as "/page/{page}/" or "?page={page}".
    page_number : int
        Desired page number (1-based).

    Returns
    -------
    str
        Fully formed listing URL for the page.
    """
    if page_number <= 1:
        return listing_url
    return listing_url.rstrip("/") + page_format.format(page=page_number)


def get_text_or_default(
    soup: BeautifulSoup, css_selector: str, default_value: str = ""
) -> str:
    """
    Get the stripped text content of the first node matching a CSS selector.

    Parameters
    ----------
    soup : BeautifulSoup
        Document or element to search within.
    css_selector : str
        CSS selector to match a single element.
    default_value : str, optional
        Value to return if no element or no text is found, by default "".

    Returns
    -------
    str
        Extracted text or the provided default.
    """
    element = soup.select_one(css_selector)
    if element:
        text_value = element.get_text(strip=True)
        if text_value:
            return text_value
    return default_value


def parse_title(soup: BeautifulSoup, site_config: Dict[str, Any]) -> str:
    """
    Extract an article title using site config, with simple fallbacks.

    Order:
      1) site_config["title_selector"]
      2) <h1>
      3) <meta property='og:title'> (or name='og:title')

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed article document.
    site_config : Dict[str, Any]
        Configuration block for the target site.

    Returns
    -------
    str
        Title string (may be empty if none found).
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
    """Make common ISO-ish timestamps acceptable to fromisoformat()."""
    if not value:
        return None
    str = value.strip()
    if not str:
        return None
    # 'Z' -> UTC
    if str.endswith("Z"):
        str = str[:-1] + "+00:00"
    # Fix zone like -0700 or +0530 -> -07:00 / +05:30
    if len(str) >= 5 and (str[-5] in "+-") and str[-3] != ":" and str[-2:].isdigit():
        str = str[:-2] + ":" + str[-2:]
    return str


def _take_date_only(ts: str) -> Optional[str]:
    """Return YYYY-MM-DD if ts parses, else None."""
    normal = _normalize_isoish(ts)
    if not normal:
        return None
    try:
        return datetime.fromisoformat(normal).date().isoformat()
    except Exception:
        # last chance: if it already looks like YYYY-MM-DD, take first 10
        if len(normal) >= 10 and normal[4] == "-" and normal[7] == "-":
            return normal[:10]
        return None


def parse_date(soup: BeautifulSoup, site_config: Dict[str, Any]) -> Optional[str]:
    """
    Simple date extraction:
      1) site-configured selector (node.text or node['datetime'])
      2) first <time> tag (datetime attr or text)
      3) a couple of common meta fallbacks
    """
    # 1) Configured selector
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

    # 3) Meta fallbacks
    for key in (
        "article:published_time",
        "og:updated_time",
        "datePublished",
        "publish-date",
    ):
        val = _first_meta(soup, key)
        if val:
            date = _take_date_only(val)
            if date:
                return date

    return None


def collect_image_urls(
    article_url: str, container: Tag | BeautifulSoup, css_selectors: List[str]
) -> List[str]:
    """
    Collect unique absolute image URLs (<img src=...>) matched by given selectors.

    Parameters
    ----------
    article_url : str
        The current article URL; used to absolutize relative image sources.
    container : Tag | BeautifulSoup
        Root element to scope the search to (usually the article root).
    css_selectors : List[str]
        One or more CSS selectors for images within the article.

    Returns
    -------
    List[str]
        Ordered list of unique absolute image URLs.
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
    Extract all non-empty paragraph texts (<p>) from a container in order.

    Parameters
    ----------
    container : Tag | BeautifulSoup
        Article root (or any element) to search for <p> nodes.

    Returns
    -------
    List[str]
        Ordered list of paragraph strings (empty texts are skipped).
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
    Locate the main article container using configured selectors.

    The first selector in `article_root_selectors` that matches is returned.
    If none match, the entire document is returned as a safe fallback.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed article document.
    site_config : Dict[str, Any]
        Configuration block for the target site.

    Returns
    -------
    Tag | BeautifulSoup
        The article root element or the full document.
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
    Extract absolute article links from a listing page.

    The function:
      1) Parses the listing HTML.
      2) Selects link elements using `listing_link_selector`.
      3) Absolutizes hrefs against `base_url`.
      4) Filters out links containing any fragment from `listing_link_exclude_contains`.
      5) Deduplicates while preserving order.

    Parameters
    ----------
    listing_html : str
        The listing page HTML.
    site_config : Dict[str, Any]
        Configuration block for the target site.

    Returns
    -------
    List[str]
        Ordered list of absolute article URLs.
    """
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
    """
    Parse one article page into an `ArticleData` record.

    Steps:
      - Find the article root using `article_root_selectors`.
      - Extract title and date (prefers <time datetime> → ISO).
      - Collect at most one header image (first match across header selectors).
      - Collect all unique body images (across body selectors).
      - Extract ordered non-empty paragraph texts.

    Parameters
    ----------
    article_url : str
        Absolute URL of the article.
    article_html : str
        Raw HTML of the article page.
    site_name : str
        Site key (as in `SITE_CONFIGS`), stored into `ArticleData.source`.
    site_config : Dict[str, Any]
        Configuration block for the target site.

    Returns
    -------
    ArticleData
        Structured representation of the parsed article.
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
    Scrape a single listing page for a configured site and parse each article.

    Parameters
    ----------
    site_name : str
        Key present in `SITE_CONFIGS`.
    page_number : int, optional
        Listing page number (1-based), by default 1.

    Returns
    -------
    List[ArticleData]
        Parsed articles for the given listing page.
    """
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
        if len(article.paragraphs) > 2:
            scraped_articles.append(article)

    return scraped_articles


def scrape_pages(
    site_name: str, start_page: int = 1, number_of_pages: int = 1
) -> List[ArticleData]:
    """
    Scrape multiple consecutive listing pages and return all parsed articles.

    Parameters
    ----------
    site_name : str
        Key present in `SITE_CONFIGS`.
    start_page : int, optional
        First listing page (1-based), by default 1.
    number_of_pages : int, optional
        How many pages to scrape (>= 1), by default 1.

    Returns
    -------
    List[ArticleData]
        Combined list of parsed articles from all requested pages.
    """
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
