"""Récupération d'articles depuis les flux RSS."""
import feedparser
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser


def fetch_articles(sources, start_date, end_date):
    """Récupère tous les articles publiés entre start_date et end_date.

    La fenêtre est légèrement élargie côté passé pour compenser les flux RSS
    qui publient des dates avec des timezones incorrectes ou du retard d'indexation.
    """
    articles = []

    # Normalisation timezone
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    # On élargit la fenêtre de 3 jours en arrière pour rattraper les flux
    # dont les dates sont mal formatées ou publiées avec du retard
    extended_start = start_date - timedelta(days=3)

    for source_url in sources:
        try:
            print(f"  → {source_url}")
            feed = feedparser.parse(source_url)

            if not feed.entries:
                print(f"     ⚠ Flux vide ou inaccessible")
                continue

            source_name = feed.feed.get("title", source_url)
            count_for_source = 0

            for entry in feed.entries:
                pub_date = _parse_date(entry)

                # Si on ne peut pas lire la date → on inclut quand même l'article
                # (c'est l'IA qui triera selon la pertinence)
                if pub_date is None:
                    articles.append({
                        "title": (entry.get("title") or "").strip(),
                        "summary": _extract_summary(entry),
                        "link": entry.get("link", ""),
                        "source": source_name,
                        "date": end_date.isoformat(),  # date fictive = aujourd'hui
                        "image_url": _extract_image(entry),
                        "date_uncertain": True,
                    })
                    count_for_source += 1
                    continue

                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)

                # Fenêtre élargie
                if not (extended_start <= pub_date <= end_date):
                    continue

                articles.append({
                    "title": (entry.get("title") or "").strip(),
                    "summary": _extract_summary(entry),
                    "link": entry.get("link", ""),
                    "source": source_name,
                    "date": pub_date.isoformat(),
                    "image_url": _extract_image(entry),
                    "date_uncertain": False,
                })
                count_for_source += 1

            print(f"     {count_for_source} article(s) récupéré(s)")
        except Exception as e:
            print(f"     ⚠ erreur : {e}")
            continue

    return articles


def _parse_date(entry):
    """Tente d'extraire une date de publication depuis différents champs."""
    # Champs texte
    for field in ("published", "updated", "created", "date"):
        raw = entry.get(field)
        if not raw:
            continue
        try:
            return date_parser.parse(str(raw), fuzzy=True)
        except Exception:
            continue

    # Champ struct_time parsé par feedparser
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                continue

    return None


def _extract_summary(entry):
    """Récupère le résumé / description disponible."""
    content = entry.get("content")
    if isinstance(content, list) and content:
        return content[0].get("value", "")
    return (
        entry.get("summary")
        or entry.get("description")
        or ""
    )


def _extract_image(entry):
    """Cherche une image hero dans les différents champs possibles."""
    media = entry.get("media_content") or []
    if media and isinstance(media, list):
        url = media[0].get("url")
        if url:
            return url
    thumb = entry.get("media_thumbnail") or []
    if thumb and isinstance(thumb, list):
        url = thumb[0].get("url")
        if url:
            return url
    for enc in entry.get("enclosures", []) or []:
        if isinstance(enc, dict) and str(enc.get("type", "")).startswith("image/"):
            return enc.get("href") or enc.get("url")
    for link in entry.get("links", []) or []:
        if isinstance(link, dict) and str(link.get("type", "")).startswith("image/"):
            return link.get("href")
    return None
