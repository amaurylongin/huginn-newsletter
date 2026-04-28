"""Récupération d'articles depuis les flux RSS avec extraction d'images og:image."""
import feedparser
import urllib.request
import ssl
import re
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

HEADERS_HTML = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
}


def _fetch_raw(url, headers, timeout=15):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def _fetch_feed(url):
    try:
        raw = _fetch_raw(url, HEADERS)
        return feedparser.parse(raw)
    except Exception:
        return feedparser.parse(url, agent=HEADERS["User-Agent"])


def _fetch_og_image(url):
    """Tente de récupérer l'og:image d'une page d'article."""
    try:
        raw = _fetch_raw(url, HEADERS_HTML, timeout=8)
        html = raw.decode("utf-8", errors="ignore")
        # og:image
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            return m.group(1).strip()
        # twitter:image
        m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            return m.group(1).strip()
        # content= avant property= (ordre inversé)
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None


def fetch_articles(sources, start_date, end_date):
    articles = []

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    extended_start = start_date - timedelta(days=3)

    for source_url in sources:
        try:
            print(f"  → {source_url}")
            feed = _fetch_feed(source_url)

            if not feed.entries:
                print(f"     ⚠ Flux vide ou inaccessible")
                continue

            source_name = feed.feed.get("title", source_url)
            count = 0

            for entry in feed.entries:
                pub_date = _parse_date(entry)

                if pub_date is None:
                    date_val = end_date.isoformat()
                else:
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                    if not (extended_start <= pub_date <= end_date):
                        continue
                    date_val = pub_date.isoformat()

                link = entry.get("link", "")
                # Image : d'abord dans le flux, sinon on essaie de la récupérer
                image_url = _extract_image(entry)
                if not image_url and link:
                    image_url = _fetch_og_image(link)

                articles.append({
                    "title": (entry.get("title") or "").strip(),
                    "summary": _extract_summary(entry),
                    "link": link,
                    "source": source_name,
                    "date": date_val,
                    "image_url": image_url,
                })
                count += 1

            print(f"     {count} article(s) récupéré(s)")
        except Exception as e:
            print(f"     ⚠ erreur : {e}")
            continue

    return articles


def _parse_date(entry):
    for field in ("published", "updated", "created", "date"):
        raw = entry.get(field)
        if not raw:
            continue
        try:
            return date_parser.parse(str(raw), fuzzy=True)
        except Exception:
            continue
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _extract_summary(entry):
    content = entry.get("content")
    if isinstance(content, list) and content:
        return content[0].get("value", "")
    return entry.get("summary") or entry.get("description") or ""


def _extract_image(entry):
    for media in (entry.get("media_content") or []):
        if isinstance(media, dict) and media.get("url"):
            return media["url"]
    for thumb in (entry.get("media_thumbnail") or []):
        if isinstance(thumb, dict) and thumb.get("url"):
            return thumb["url"]
    for enc in (entry.get("enclosures") or []):
        if isinstance(enc, dict) and str(enc.get("type", "")).startswith("image/"):
            return enc.get("href") or enc.get("url")
    for link in (entry.get("links") or []):
        if isinstance(link, dict) and str(link.get("type", "")).startswith("image/"):
            return link.get("href")
    return None
