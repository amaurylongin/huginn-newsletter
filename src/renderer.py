"""Rendu HTML de la newsletter via Jinja2 — liste plate sans thèmes."""
import os
import base64
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
ASSETS_DIR    = Path(__file__).parent.parent / "docs" / "assets"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

FRENCH_MONTHS = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

def format_date(d):
    return f"{d.day} {FRENCH_MONTHS[d.month]} {d.year}"

def format_date_short(d):
    return f"{d.day} {FRENCH_MONTHS[d.month][:4]}."

def _load_logo_b64(filename):
    path = ASSETS_DIR / filename
    if not path.exists():
        print(f"  ⚠ Logo introuvable : {path}")
        return ""
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def render_newsletter(articles, synthesis, barometer_text, barometer_level,
                      issue_number, start_date, end_date):

    gh_pages_url      = os.environ.get("GH_PAGES_URL", "").rstrip("/")
    feedback_email    = os.environ.get("SMTP_USER", "")
    archive_filename  = f"{end_date.strftime('%Y-%m-%d')}-edition-{issue_number:03d}.html"
    archive_url       = f"{gh_pages_url}/editions/{archive_filename}" if gh_pages_url else "#"
    archive_index_url = f"{gh_pages_url}/" if gh_pages_url else "#"

    huginn_b64       = _load_logo_b64("huginn-logo.png")
    arquus_dark_b64  = _load_logo_b64("arquus-logo-dark.png")
    arquus_white_b64 = _load_logo_b64("arquus-logo-white.png")

    template = env.get_template("newsletter.html")
    return template.render(
        issue_number=issue_number,
        issue_number_padded=f"{issue_number:03d}",
        start_date_label=format_date(start_date),
        end_date_label=format_date(end_date),
        start_date_short=format_date_short(start_date),
        end_date_short=format_date_short(end_date),
        articles=articles,          # liste plate, plus de themed_sections
        total_articles=len(articles),
        gh_pages_url=gh_pages_url,
        feedback_email=feedback_email,
        archive_url=archive_url,
        archive_index_url=archive_index_url,
        huginn_b64=huginn_b64,
        arquus_dark_b64=arquus_dark_b64,
        arquus_white_b64=arquus_white_b64,
    )


def render_archive_index(editions, gh_pages_url=""):
    template = env.get_template("archive_index.html")
    return template.render(editions=editions, gh_pages_url=gh_pages_url.rstrip("/"))
