"""Archivage des éditions dans docs/ (GitHub Pages)."""
import os
import re
from pathlib import Path
from datetime import datetime

from renderer import render_archive_index, format_date


PROJECT_ROOT = Path(__file__).parent.parent
EDITIONS_DIR = PROJECT_ROOT / "docs" / "editions"
INDEX_FILE = PROJECT_ROOT / "docs" / "index.html"


def save_to_archive(html, date, issue_number):
    """Sauvegarde le HTML de l'édition dans docs/editions/."""
    EDITIONS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{date.strftime('%Y-%m-%d')}-edition-{issue_number:03d}.html"
    filepath = EDITIONS_DIR / filename
    filepath.write_text(html, encoding="utf-8")
    print(f"  ✓ Édition archivée : docs/editions/{filename}")
    return filepath


def update_archive_index():
    """Reconstruit la page d'index des archives."""
    if not EDITIONS_DIR.exists():
        return

    editions = []
    for f in sorted(EDITIONS_DIR.glob("*.html"), reverse=True):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-edition-(\d+)\.html", f.name)
        if not m:
            continue
        date_str, num = m.groups()
        date = datetime.strptime(date_str, "%Y-%m-%d")
        editions.append({
            "filename": f.name,
            "date_label": format_date(date),
            "number": int(num),
            "number_padded": f"{int(num):03d}",
            "url": f"editions/{f.name}",
        })

    gh_pages_url = os.environ.get("GH_PAGES_URL", "").rstrip("/")
    html = render_archive_index(editions, gh_pages_url)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(html, encoding="utf-8")
    print(f"  ✓ Index d'archive mis à jour ({len(editions)} édition(s))")


def get_next_issue_number():
    """Calcule le numéro de la prochaine édition (nombre d'éditions + 1)."""
    if not EDITIONS_DIR.exists():
        return 1
    existing = list(EDITIONS_DIR.glob("*-edition-*.html"))
    return len(existing) + 1
