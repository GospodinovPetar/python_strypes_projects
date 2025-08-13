from typing import Dict, Any

SITE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "techcrunch": {
        "base_url": "https://techcrunch.com",
        "listing_url": "https://techcrunch.com/",
        "listing_page_format": "/page/{page}/",
        "listing_link_selector": "a.loop-card__title-link[href], .loop-card__title a[href]",
        "listing_link_exclude_contains": [
            "/video/", "/videos/", "/podcasts/", "/events/",
            "/sponsored/", "/brand-studio/", "/category/", "/tag/",
        ],
        "article_root_selectors": [
            "article", ".wp-block-post-content", ".entry-content", ".article-content"
        ],
        "title_selector": "h1",
        "date_selector": "time[datetime]",
        "header_image_selectors": [
            "header img[src]", "figure img.wp-post-image[src]", "figure.wp-block-image img[src]"
        ],
        "body_image_selectors": [
            ".wp-block-post-content img[src]", ".article-content img[src]", ".entry-content img[src]"
        ],
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
        "header_image_selectors": ["header img[src]", ".post-header img[src]", ".entry-header img[src]"],
        "body_image_selectors": ["div.wp-block-image img[src]", ".entry-content img[src]"],
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

__all__ = ["SITE_CONFIGS"]
