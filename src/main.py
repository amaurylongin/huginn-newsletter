"""HUGINN — point d'entrée principal.

Deux modes disponibles, contrôlés par la variable GH_MODE :
  - GH_MODE=rss    (défaut) : collecte via flux RSS dans config/sources.txt
  - GH_MODE=search : Gemini cherche lui-même sur le web dans toutes les langues

Pour basculer en mode search :
  GitHub → Settings → Variables → Ajouter GH_MODE = search
"""
import sys
import os"""HUGINN — point d'entrée principal.

Deux modes disponibles, contrôlés par la variable GH_MODE :
  - GH_MODE=rss    (défaut) : collecte via flux RSS dans config/sources.txt
  - GH_MODE=search : Gemini cherche lui-même sur le web dans toutes les langues

Pour basculer en mode search :
  GitHub → Settings → Variables → Ajouter GH_MODE = search
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

from renderer import render_newsletter
from mailer import send_newsletter
from archiver import save_to_archive, update_archive_index, get_next_issue_number

PROJECT_ROOT = Path(__file__).parent.parent


def _load_lines(filepath):
    return [l.strip() for l in filepath.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")]


def main():
    print("=" * 60)
    print("HUGINN — Génération de la revue hebdomadaire")
    print("=" * 60)

    criteria       = (PROJECT_ROOT / "config" / "criteria.md").read_text(encoding="utf-8")
    mode           = os.environ.get("GH_MODE", "rss").strip().lower()

    print(f"\n▸ Mode : {mode.upper()}")
    print(f"▸ Destinataires : gérés par Brevo")

    end_date   = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    print(f"▸ Fenêtre : {start_date.date()} → {end_date.date()}")

    articles = []

    # ── MODE RSS ──────────────────────────────────────────────
    if mode == "rss":
        from rss import fetch_articles
        from llm import analyze_articles

        sources = _load_lines(PROJECT_ROOT / "config" / "sources.txt")
        print(f"▸ {len(sources)} source(s) RSS")
        print("\n▸ Collecte des flux RSS...")
        raw_articles = fetch_articles(sources, start_date, end_date)
        print(f"\n▸ {len(raw_articles)} article(s) brut(s) récupéré(s)")

        if not raw_articles:
            print("❌ Aucun article. Arrêt.")
            sys.exit(0)

        print("\n▸ Analyse et filtrage via Gemini...")
        result   = analyze_articles(raw_articles, criteria)
        articles = result.get("articles", [])

    # ── MODE SEARCH ───────────────────────────────────────────
    elif mode == "search":
        from searcher import search_articles

        print("\n▸ Recherche autonome via Gemini + Google Search...")
        articles = search_articles(criteria, start_date, end_date)

    else:
        print(f"❌ Mode inconnu : '{mode}'. Utilisez 'rss' ou 'search'.")
        sys.exit(1)

    # ── SUITE COMMUNE ─────────────────────────────────────────
    print(f"\n▸ {len(articles)} article(s) retenu(s)")

    if len(articles) < 2:
        print("ℹ Moins de 2 articles. Newsletter non envoyée.")
        sys.exit(0)

    issue_number = get_next_issue_number()
    print(f"▸ Édition N°{issue_number:03d}")

    print("\n▸ Rendu de la newsletter...")
    html = render_newsletter(
        articles=articles,
        synthesis="",
        barometer_text="",
        barometer_level=3,
        issue_number=issue_number,
        start_date=start_date,
        end_date=end_date,
    )

    print("\n▸ Archivage...")
    save_to_archive(html, end_date, issue_number)
    update_archive_index()

    print("\n▸ Envoi via Brevo...")
    send_newsletter([], html, issue_number, start_date, end_date)

    print("\n" + "=" * 60)
    print(f"✓ HUGINN N°{issue_number:03d} diffusée ({mode.upper()} mode).")
    print("=" * 60)


if __name__ == "__main__":
    main()
from pathlib import Path
from datetime import datetime, timedelta, timezone

from renderer import render_newsletter
from mailer import send_newsletter
from archiver import save_to_archive, update_archive_index, get_next_issue_number

PROJECT_ROOT = Path(__file__).parent.parent


def _load_lines(filepath):
    return [l.strip() for l in filepath.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")]


def main():
    print("=" * 60)
    print("HUGINN — Génération de la revue hebdomadaire")
    print("=" * 60)

    criteria       = (PROJECT_ROOT / "config" / "criteria.md").read_text(encoding="utf-8")
    recipients_env = os.environ.get("RECIPIENTS", "")
    recipients     = [r.strip() for r in recipients_env.split(",") if r.strip()]
    mode           = os.environ.get("GH_MODE", "search").strip().lower()

    print(f"\n▸ Mode : {mode.upper()}")
    print(f"▸ {len(recipients)} destinataire(s)")

    if not recipients:
        print("❌ Aucun destinataire. Arrêt.")
        sys.exit(1)

    end_date   = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    print(f"▸ Fenêtre : {start_date.date()} → {end_date.date()}")

    articles = []

    # ── MODE RSS ──────────────────────────────────────────────
    if mode == "rss":
        from rss import fetch_articles
        from llm import analyze_articles

        sources = _load_lines(PROJECT_ROOT / "config" / "sources.txt")
        print(f"▸ {len(sources)} source(s) RSS")
        print("\n▸ Collecte des flux RSS...")
        raw_articles = fetch_articles(sources, start_date, end_date)
        print(f"\n▸ {len(raw_articles)} article(s) brut(s) récupéré(s)")

        if not raw_articles:
            print("❌ Aucun article. Arrêt.")
            sys.exit(0)

        print("\n▸ Analyse et filtrage via Gemini...")
        result   = analyze_articles(raw_articles, criteria)
        articles = result.get("articles", [])

    # ── MODE SEARCH ───────────────────────────────────────────
    elif mode == "search":
        from searcher import search_articles

        print("\n▸ Recherche autonome via Gemini + Google Search...")
        articles = search_articles(criteria, start_date, end_date)

    else:
        print(f"❌ Mode inconnu : '{mode}'. Utilisez 'rss' ou 'search'.")
        sys.exit(1)

    # ── SUITE COMMUNE ─────────────────────────────────────────
    print(f"\n▸ {len(articles)} article(s) retenu(s)")

    if len(articles) < 2:
        print("ℹ Moins de 2 articles. Newsletter non envoyée.")
        sys.exit(0)

    issue_number = get_next_issue_number()
    print(f"▸ Édition N°{issue_number:03d}")

    print("\n▸ Rendu de la newsletter...")
    html = render_newsletter(
        articles=articles,
        synthesis="",
        barometer_text="",
        barometer_level=3,
        issue_number=issue_number,
        start_date=start_date,
        end_date=end_date,
    )

    print("\n▸ Archivage...")
    save_to_archive(html, end_date, issue_number)
    update_archive_index()

    print(f"\n▸ Envoi à {len(recipients)} destinataire(s)...")
    send_newsletter(recipients, html, issue_number, start_date, end_date)

    print("\n" + "=" * 60)
    print(f"✓ HUGINN N°{issue_number:03d} diffusée ({mode.upper()} mode).")
    print("=" * 60)


if __name__ == "__main__":
    main()
