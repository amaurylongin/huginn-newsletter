"""Rendu HTML de la newsletter et de la page d'archive via Jinja2."""
import os
from pathlib import Path
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


THEMES_ORDER = [
    "Contrats & Industrie",
    "Front ukrainien",
    "Innovation & Technologie",
    "Géopolitique",
    "Conflits & Zones chaudes",
]


FRENCH_MONTHS = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def format_date(d):
    return f"{d.day} {FRENCH_MONTHS[d.month]} {d.year}"


def format_date_short(d):
    return f"{d.day} {FRENCH_MONTHS[d.month][:4]}."


def render_newsletter(articles, synthesis, barometer_text, barometer_level,
                      issue_number, start_date, end_date):
    """Rend le HTML de la newsletter."""
    grouped = defaultdict(list)
    for article in articles:
        theme = article.get("theme", "Géopolitique")
        grouped[theme].append(article)

    themed_sections = []
    theme_num = 1
    for theme in THEMES_ORDER:
        if theme in grouped:
            themed_sections.append({
                "number": theme_num,
                "title": theme,
                "articles": grouped[theme],
                "count": len(grouped[theme]),
            })
            theme_num += 1
    # Thèmes hors liste officielle (au cas où le LLM en invente un)
    for theme, arts in grouped.items():
        if theme not in THEMES_ORDER:
            themed_sections.append({
                "number": theme_num,
                "title": theme,
                "articles": arts,
                "count": len(arts),
            })
            theme_num += 1

    gh_pages_url = os.environ.get("GH_PAGES_URL", "").rstrip("/")
    feedback_email = os.environ.get("SMTP_USER", "arquus.osint@gmail.com")
    # URL d'archive pour cette édition (GitHub Pages)
    archive_filename = f"{end_date.strftime('%Y-%m-%d')}-edition-{issue_number:03d}.html"
    archive_url = (
        f"{gh_pages_url}/editions/{archive_filename}" if gh_pages_url else "#"
    )
    archive_index_url = f"{gh_pages_url}/" if gh_pages_url else "#"

    template = env.get_template("newsletter.html")
    return template.render(
        issue_number=issue_number,
        issue_number_padded=f"{issue_number:03d}",
        start_date_label=format_date(start_date),
        end_date_label=format_date(end_date),
        start_date_short=format_date_short(start_date),
        end_date_short=format_date_short(end_date),
        synthesis=synthesis,
        barometer_text=barometer_text,
        barometer_level=barometer_level,
        barometer_bars=[i < barometer_level for i in range(5)],
        barometer_label=_barometer_label(barometer_level),
        total_articles=len(articles),
        themed_sections=themed_sections,
        gh_pages_url=gh_pages_url,
        feedback_email=feedback_email,
        archive_url=archive_url,
        archive_index_url=archive_index_url,
    )


def render_archive_index(editions, gh_pages_url=""):
    """Rend la page index de l'archive web."""
    template = env.get_template("archive_index.html")
    return template.render(
        editions=editions,
        gh_pages_url=gh_pages_url.rstrip("/"),
    )


def _barometer_label(level):
    return {
        1: "SEMAINE CALME",
        2: "ACTIVITÉ MODÉRÉE",
        3: "ACTIVITÉ SOUTENUE",
        4: "SEMAINE DENSE",
        5: "SEMAINE EXCEPTIONNELLE",
    }.get(level, "ACTIVITÉ SOUTENUE")
