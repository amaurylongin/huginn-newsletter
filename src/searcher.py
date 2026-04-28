"""Recherche autonome d'articles via Gemini + Google Search intégré.

Alternative au module rss.py : Gemini cherche lui-même les articles pertinents
sur le web dans toutes les langues, sans flux RSS prédéfinis.
"""
import os
import json
import re
import time
from datetime import datetime, timezone

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

MODEL_NAME = "gemini-2.0-flash"  # supporte mieux Google Search que flash-lite


SEARCH_PROMPT = """Tu es HUGINN, agent de veille OSINT pour ARQUUS (constructeur français de véhicules militaires terrestres : Griffon, Serval, Jaguar, VBCI, VAB...).

Ta mission : rechercher sur le web les actualités défense les plus importantes de la semaine écoulée, dans TOUTES LES LANGUES (français, anglais, allemand, espagnol, polonais, ukrainien, hébreu, arabe, coréen, etc.). La veille est internationale.

DOMAINES À SURVEILLER (liés au métier d'ARQUUS) :
- Véhicules blindés et de combat (MBT, IFV, APC, MRAP, blindés légers)
- Nouvelles technologies véhicules militaires : hybridation, électromobilité, IHM, IA embarquée, autonomie, survivabilité, furtivité, chenilles, propulsion
- Drones terrestres (UGV) et drones impactant les blindés (FPV, loitering munitions)
- Artillerie, missiles antichar
- Contrats et commandes de véhicules militaires dans le monde
- Conflits en cours sous l'angle terrestre/blindé (Ukraine, Proche-Orient, Sahel, Asie)
- Industrie défense terrestre : KNDS, Rheinmetall, Hanwha, BAE Systems Land, Nexter, Arquus, GDLS, Oshkosh, Milrem...

À EXCLURE : aviation pure, marine, espace, cybersécurité pure, nucléaire stratégique, RH militaire.

CONSIGNES :
1. Recherche les actualités des 7 derniers jours uniquement
2. Cherche dans toutes les langues — ne te limite pas au français ou à l'anglais
3. Pour chaque article trouvé, récupère une URL d'image si possible
4. Génère un titre en français de 6 mots maximum
5. Sélectionne entre 6 et 10 articles pertinents pour ARQUUS
6. Retourne UNIQUEMENT du JSON valide, sans balises markdown

SCHÉMA JSON STRICT :
{
  "articles": [
    {
      "title_fr": "titre 6 mots max en français",
      "source": "nom du média source",
      "date": "date ISO YYYY-MM-DD",
      "link": "URL de l'article",
      "image_url": "URL d'une image illustrant l'article, ou null si aucune trouvée"
    }
  ]
}
"""


def search_articles(criteria, start_date, end_date):
    """Utilise Gemini + Google Search pour trouver les articles de la semaine.

    Args:
        criteria: contenu du fichier criteria.md (contexte ARQUUS)
        start_date: datetime début de fenêtre
        end_date: datetime fin de fenêtre

    Returns:
        Liste de dicts compatibles avec le format attendu par renderer/mailer
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquant.")

    client = genai.Client(api_key=api_key)

    # Période en clair pour aider Gemini à cibler
    period = f"du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"

    user_prompt = (
        f"Recherche les actualités défense terrestre importantes pour ARQUUS "
        f"parues {period}, dans toutes les langues.\n\n"
        f"Contexte ARQUUS pour t'aider à évaluer la pertinence :\n{criteria}\n\n"
        "Produis le JSON final avec les articles trouvés."
    )

    delays = [20, 40, 80]
    response = None
    last_error = None

    for attempt in range(len(delays)):
        try:
            print(f"  ▸ Recherche web autonome (tentative {attempt+1}/{len(delays)})...")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SEARCH_PROMPT,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.2,
                    max_output_tokens=8192,
                ),
            )
            print("  ✓ Réponse reçue")
            break
        except genai_errors.ServerError as e:
            last_error = e
            if attempt < len(delays) - 1:
                wait = delays[attempt]
                print(f"    ⚠ Indisponible — retry dans {wait}s")
                time.sleep(wait)
            else:
                raise
        except genai_errors.ClientError as e:
            last_error = e
            code = str(getattr(e, "code", ""))
            if code == "429" and attempt < len(delays) - 1:
                wait = delays[attempt]
                print(f"    ⚠ Rate limit — retry dans {wait}s")
                time.sleep(wait)
            else:
                raise

    if response is None:
        raise RuntimeError(f"Impossible d'obtenir une réponse. Dernière erreur : {last_error}")

    # Extraire le JSON de la réponse (Gemini avec search peut mélanger texte + JSON)
    raw_text = response.text.strip() if response.text else ""

    # Chercher un bloc JSON dans la réponse
    json_match = re.search(r'\{[\s\S]*"articles"[\s\S]*\}', raw_text)
    if json_match:
        raw_json = json_match.group(0)
    else:
        raw_json = raw_text

    # Nettoyer les balises markdown éventuelles
    raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_json, flags=re.MULTILINE).strip()

    try:
        result = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON invalide : {e}")
        print(f"  Raw (300 chars) : {raw_text[:300]}")
        return []

    articles = result.get("articles", [])

    # Normaliser le format pour compatibilité avec renderer.py
    normalized = []
    for a in articles:
        normalized.append({
            "title_fr":  (a.get("title_fr") or a.get("title") or "").strip(),
            "source":    a.get("source", ""),
            "date":      _normalize_date(a.get("date", ""), end_date),
            "link":      a.get("link", ""),
            "image_url": a.get("image_url") or None,
        })

    print(f"  → {len(normalized)} article(s) trouvé(s) par recherche autonome")
    print(f"  → {sum(1 for a in normalized if a['image_url'])} avec image")
    return normalized


def _normalize_date(date_str, fallback):
    """Normalise une date ISO ou partielle."""
    if not date_str:
        return fallback.isoformat()
    try:
        # Accepte YYYY-MM-DD ou datetime ISO complet
        if len(date_str) == 10:
            return date_str + "T00:00:00+00:00"
        return date_str
    except Exception:
        return fallback.isoformat()
