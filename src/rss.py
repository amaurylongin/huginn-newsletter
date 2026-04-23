"""Récupération d'articles depuis les flux RSS avec User-Agent navigateur."""
import feedparser
import urllib.request
import ssl
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser

# User-Agent d'un navigateur réel — évite d'être bloqué par les serveurs
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
}


def _fetch_feed(url):
    """Télécharge le contenu d'un flux RSS avec des en-têtes navigateur."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        raw = resp.read()
    return feedparser.parse(raw)


def fetch_articles(sources, start_date, end_date):
    """Récupère tous les articles publiés entre start_date et end_date."""
    articles = []

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    # Fenêtre élargie de 3 jours pour absorber les décalages de timezone
    extended_start = start_date - timedelta(days=3)

    for source_url in sources:
        try:
            print(f"  → {source_url}")
            feed = _fetch_feed(source_url)

            if not feed.entries:
                # Fallback : laisser feedparser gérer lui-même (certains sites
                # acceptent feedparser mais pas urllib)
                feed = feedparser.parse(
                    source_url,
                    agent=HEADERS["User-Agent"],
                )

            if not feed.entries:
                print(f"     ⚠ Flux vide ou inaccessible")
                continue

            source_name = feed.feed.get("title", source_url)
            count = 0

            for entry in feed.entries:
                pub_date = _parse_date(entry)

                if pub_date is None:
                    # Date illisible → on inclut avec date fictive
                    articles.append({
                        "title": (entry.get("title") or "").strip(),
                        "summary": _extract_summary(entry),
                        "link": entry.get("link", ""),
                        "source": source_name,
                        "date": end_date.isoformat(),
                        "image_url": _extract_image(entry),
                    })
                    count += 1
                    continue

                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)

                if not (extended_start <= pub_date <= end_date):
                    continue

                articles.append({
                    "title": (entry.get("title") or "").strip(),
                    "summary": _extract_summary(entry),
                    "link": entry.get("link", ""),
                    "source": source_name,
                    "date": pub_date.isoformat(),
                    "image_url": _extract_image(entry),
                })
                count += 1

            print(f"     {count} article(s) récupéré(s)")

        except Exception as e:
            print(f"     ⚠ erreur : {e}")
            continue

    return articles


def _parse_date(entry):
    """Tente d'extraire une date depuis différents champs RSS."""
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
    """Récupère le résumé disponible."""
    content = entry.get("content")
    if isinstance(content, list) and content:
        return content[0].get("value", "")
    return entry.get("summary") or entry.get("description") or ""


def _extract_image(entry):
    """Cherche une image hero dans les différents champs."""
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
