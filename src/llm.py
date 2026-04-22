"""Analyse des articles via l'API Gemini (tier gratuit)."""
import os
import json
import re

from google import genai
from google.genai import types


MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = """Tu es HUGINN, agent de veille OSINT pour ARQUUS (constructeur français de véhicules blindés terrestres).

Mission : analyser une liste d'articles bruts issus de flux RSS de défense, et produire une newsletter hebdomadaire en français pour ARQUUS.

ÉTAPES :
1. Filtrer les articles selon les critères (inclusion stricte + exclusions absolues)
2. Pour les articles retenus : traduire et reformuler en FRANÇAIS (titres et résumés)
3. Classer chaque article dans un thème parmi la liste fournie
4. Générer une synthèse globale, un baromètre hebdomadaire, et une analyse "ARQUUS" pour les articles les plus pertinents

RÈGLES STRICTES :
- Minimum 2 articles, maximum 10 (prioriser les plus pertinents pour ARQUUS)
- Traduire INTÉGRALEMENT en français (titres, résumés, analyses, synthèse, baromètre)
- Ne JAMAIS inventer d'information : tout doit être basé sur le contenu fourni
- Les "quote" doivent être des phrases-signatures COURTES (< 15 mots) en français, paraphrasant l'idée centrale de l'article — PAS de citation verbatim
- Les "arquus_angle" : 1-2 phrases concrètes expliquant l'enjeu pour ARQUUS. Mettre null si pas d'angle ARQUUS évident
- Ordonner les articles du plus pertinent au moins pertinent à l'intérieur de chaque thème
- Retourner UNIQUEMENT du JSON valide, sans balises markdown, sans commentaires

THÈMES À UTILISER (exactement ces libellés, casse comprise) :
- "Contrats & Industrie"
- "Front ukrainien"
- "Innovation & Technologie"
- "Géopolitique"
- "Conflits & Zones chaudes"

BAROMÈTRE (niveau 1 à 5) :
1 = semaine calme (peu d'actualité significative)
2 = activité modérée
3 = activité soutenue (comportement "normal")
4 = semaine dense (plusieurs annonces majeures)
5 = semaine exceptionnelle (rupture, contrat majeur, escalade)

SCHÉMA DE SORTIE (JSON STRICT — aucun texte en dehors) :
{
  "synthesis": "2-3 lignes en français résumant les dynamiques de la semaine",
  "barometer_text": "1-2 lignes décrivant l'intensité de la semaine",
  "barometer_level": 3,
  "articles": [
    {
      "title_fr": "titre reformulé en français",
      "summary_fr": "résumé de 2-3 phrases en français",
      "quote": "phrase-signature < 15 mots en français (paraphrase)",
      "theme": "un des 5 thèmes listés",
      "arquus_angle": "1-2 phrases ou null",
      "source": "nom de la source (tel que fourni)",
      "date": "date ISO telle que fournie",
      "link": "URL originale",
      "image_url": "URL image ou null"
    }
  ]
}
"""


def analyze_articles(raw_articles, criteria):
    """Envoie tous les articles à Gemini et récupère la newsletter structurée.

    Args:
        raw_articles: liste de dicts issus de fetch_articles
        criteria: contenu du fichier criteria.md

    Returns:
        dict {synthesis, barometer_text, barometer_level, articles} ou None
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquant dans les variables d'environnement.")

    client = genai.Client(api_key=api_key)

    # Compactage des articles pour limiter la taille du prompt
    compact = []
    for a in raw_articles:
        compact.append({
            "title": a["title"][:300],
            "summary": _strip_html(a.get("summary", ""))[:800],
            "link": a["link"],
            "source": a["source"],
            "date": a["date"],
            "image_url": a.get("image_url"),
        })

    user_prompt = (
        "# CRITÈRES DE FILTRAGE\n\n"
        f"{criteria}\n\n"
        "# ARTICLES BRUTS À ANALYSER\n\n"
        f"{json.dumps(compact, ensure_ascii=False, indent=2)}\n\n"
        "Produis le JSON final (schéma défini dans les instructions système)."
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.3,
            max_output_tokens=8192,
        ),
    )

    raw_text = response.text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        # Tentative de récupération : retirer d'éventuelles balises markdown
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print("⚠ LLM : JSON invalide.")
            print(f"Raw output (500 chars) : {raw_text[:500]}")
            raise e


def _strip_html(text):
    """Nettoie le HTML des résumés RSS."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
