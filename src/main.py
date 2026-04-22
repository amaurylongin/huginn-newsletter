"""HUGINN — point d'entrée principal.

Enchaîne : récupération RSS → analyse LLM → rendu HTML → envoi email → archivage.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Imports locaux
from rss import fetch_articles
from llm import analyze_articles
from renderer import render_newsletter
from mailer import send_newsletter
from archiver import save_to_archive, update_archive_index, get_next_issue_number


PROJECT_ROOT = Path(__file__).parent.parent


def _load_lines(filepath):
    """Charge un fichier texte ligne par ligne, ignore vides et commentaires."""
    content = filepath.read_text(encoding="utf-8")
    return [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def main():
    print("=" * 60)
    print("HUGINN — Génération de la revue hebdomadaire")
    print("=" * 60)

    # 1. Configuration
    sources = _load_lines(PROJECT_ROOT / "config" / "sources.txt")
    recipients = _load_lines(PROJECT_ROOT / "config" / "recipients.txt")
    criteria = (PROJECT_ROOT / "config" / "criteria.md").read_text(encoding="utf-8")

    print(f"\n▸ {len(sources)} source(s) RSS configurée(s)")
    print(f"▸ {len(recipients)} destinataire(s)")

    if not recipients:
        print("❌ Aucun destinataire. Arrêt.")
        sys.exit(1)

    # 2. Fenêtre temporelle = 7 jours précédents
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    print(f"\n▸ Fenêtre : {start_date.date()} → {end_date.date()}")

    # 3. Collecte RSS
    print("\n▸ Collecte des flux RSS...")
    raw_articles = fetch_articles(sources, start_date, end_date)
    print(f"\n▸ {len(raw_articles)} article(s) brut(s) récupéré(s)")

    if not raw_articles:
        print("❌ Aucun article dans la fenêtre. Arrêt sans envoi.")
        sys.exit(0)

    # 4. Analyse LLM (filtrage + traduction + enrichissement)
    print("\n▸ Analyse et filtrage via Gemini...")
    result = analyze_articles(raw_articles, criteria)

    if not result or not result.get("articles"):
        print("❌ Aucun article retenu par le filtre LLM.")
        sys.exit(0)

    articles = result["articles"]
    print(f"\n▸ {len(articles)} article(s) retenu(s) après filtrage")

    if len(articles) < 2:
        print(f"ℹ Moins de 2 articles retenus ({len(articles)}). Newsletter non envoyée.")
        sys.exit(0)

    # 5. Numéro d'édition
    issue_number = get_next_issue_number()
    print(f"▸ Édition N°{issue_number:03d}")

    # 6. Rendu HTML
    print("\n▸ Rendu de la newsletter...")
    html = render_newsletter(
        articles=articles,
        synthesis=result.get("synthesis", ""),
        barometer_text=result.get("barometer_text", ""),
        barometer_level=result.get("barometer_level", 3),
        issue_number=issue_number,
        start_date=start_date,
        end_date=end_date,
    )

    # 7. Archivage (avant envoi, pour que le lien d'archive dans le mail soit valide
    #    une fois la branche poussée par GitHub Actions)
    print("\n▸ Archivage...")
    save_to_archive(html, end_date, issue_number)
    update_archive_index()

    # 8. Envoi
    print(f"\n▸ Envoi à {len(recipients)} destinataire(s)...")
    send_newsletter(recipients, html, issue_number, start_date, end_date)

    print("\n" + "=" * 60)
    print("✓ HUGINN : édition diffusée avec succès.")
    print("=" * 60)


if __name__ == "__main__":
    main()
