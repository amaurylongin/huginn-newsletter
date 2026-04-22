"""Récupération d'articles depuis les flux RSS."""
import feedparser
from datetime import datetime, timezone
from dateutil import parser as date_parser


def fetch_articles(sources, start_date, end_date):
    """Récupère tous les articles publiés entre start_date et end_date.

    Args:
        sources: liste d'URLs de flux RSS
        start_date: datetime (inclusive)
        end_date: datetime (inclusive)

    Returns:
        Liste de dicts : {title, summary, link, source, date, image_url}
    """
    articles = []

    # Normalisation timezone
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    for source_url in sources:
        try:
            print(f"  → {source_url}")
            feed = feedparser.parse(source_url)
            source_name = feed.feed.get("title", source_url)
            count_for_source = 0

            for entry in feed.entries:
                pub_date = _parse_date(entry)
                if pub_date is None:
                    continue
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                if not (start_date <= pub_date <= end_date):
                    continue

                articles.append({
                    "title": (entry.get("title") or "").strip(),
                    "summary": _extract_summary(entry),
                    "link": entry.get("link", ""),
                    "source": source_name,
                    "date": pub_date.isoformat(),
                    "image_url": _extract_image(entry),
                })
                count_for_source += 1

            print(f"     {count_for_source} article(s) dans la fenêtre")
        except Exception as e:
            print(f"     ⚠ erreur : {e}")
            continue

    return articles


def _parse_date(entry):
    """Tente d'extraire une date de publication depuis différents champs."""
    for field in ("published", "updated", "created"):
        raw = entry.get(field)
        if not raw:
            continue
        try:
            return date_parser.parse(raw)
        except Exception:
            continue
    # Fallback : champ parsed par feedparser
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return None


def _extract_summary(entry):
    """Récupère le résumé / description disponible."""
    return (
        entry.get("summary")
        or entry.get("description")
        or entry.get("content", [{}])[0].get("value", "")
        if isinstance(entry.get("content"), list)
        else entry.get("summary", "")
    )


def _extract_image(entry):
    """Cherche une image hero dans les différents champs possibles."""
    # media_content
    media = entry.get("media_content") or []
    if media and isinstance(media, list):
        url = media[0].get("url")
        if url:
            return url
    # media_thumbnail
    thumb = entry.get("media_thumbnail") or []
    if thumb and isinstance(thumb, list):
        url = thumb[0].get("url")
        if url:
            return url
    # enclosures
    for enc in entry.get("enclosures", []) or []:
        if isinstance(enc, dict) and str(enc.get("type", "")).startswith("image/"):
            return enc.get("href") or enc.get("url")
    # links avec type image
    for link in entry.get("links", []) or []:
        if isinstance(link, dict) and str(link.get("type", "")).startswith("image/"):
            return link.get("href")
    return None
