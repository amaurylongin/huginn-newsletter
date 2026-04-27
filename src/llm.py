"""Analyse des articles via l'API Gemini (tier gratuit) — avec retry automatique."""
import os
import json
import re
import time

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

MODEL_NAME = "gemini-3.1-flash-lite-preview"

SYSTEM_PROMPT = """Tu es HUGINN, agent de veille OSINT pour ARQUUS (constructeur français de véhicules blindés terrestres).

Mission : analyser une liste d'articles bruts issus de flux RSS de défense, et produire une newsletter hebdomadaire ultra-concise en français pour ARQUUS.

ÉTAPES :
1. Filtrer les articles selon les critères (inclusion stricte + exclusions absolues)
2. Pour les articles retenus : générer un TITRE COURT en français (6 mots maximum, percutant, factuel)
3. Classer chaque article dans un thème parmi la liste fournie
4. Générer une synthèse globale et un baromètre

RÈGLES STRICTES :
- Minimum 2 articles, maximum 10
- Le titre doit faire 6 MOTS MAXIMUM — c'est la seule description de l'article
- Traduire INTÉGRALEMENT en français
- Ne JAMAIS inventer d'information
- Retourner UNIQUEMENT du JSON valide, sans balises markdown

THÈMES (exactement ces libellés) :
- "Contrats & Industrie"
- "Front ukrainien"
- "Innovation & Technologie"
- "Géopolitique"
- "Conflits & Zones chaudes"

BAROMÈTRE (niveau 1 à 5) :
1 = semaine calme / 2 = modérée / 3 = soutenue / 4 = dense / 5 = exceptionnelle

SCHÉMA JSON STRICT :
{
  "articles": [
    {
      "title_fr": "titre 6 mots max en français",
      "theme": "un des 5 thèmes listés",
      "source": "nom de la source",
      "date": "date ISO",
      "link": "URL originale",
      "image_url": "URL image ou null"
    }
  ]
}
  ]
}
"""


def analyze_articles(raw_articles, criteria):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquant.")

    client = genai.Client(api_key=api_key)

    compact = []
    for a in raw_articles:
        compact.append({
            "title": a["title"][:200],
            "summary": _strip_html(a.get("summary", ""))[:400],
            "link": a["link"],
            "source": a["source"],
            "date": a["date"],
            "image_url": a.get("image_url"),
        })

    user_prompt = (
        f"# CRITÈRES\n\n{criteria}\n\n"
        f"# ARTICLES\n\n{json.dumps(compact, ensure_ascii=False, indent=2)}\n\n"
        "Produis le JSON final."
    )

    models_to_try = [MODEL_NAME, "gemini-2.0-flash", "gemini-2.5-pro"]
    delays = [15, 30, 60, 120]

    response = None
    last_error = None

    for model_name in models_to_try:
        print(f"  ▸ Tentative avec le modèle : {model_name}")
        for attempt in range(len(delays)):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2,
                        max_output_tokens=4096,
                    ),
                )
                print(f"  ✓ Réponse reçue ({model_name}, tentative {attempt+1})")
                break
            except genai_errors.ServerError as e:
                last_error = e
                if attempt < len(delays) - 1:
                    wait = delays[attempt]
                    print(f"    ⚠ Serveur indisponible — retry dans {wait}s (tentative {attempt+2}/{len(delays)})")
                    time.sleep(wait)
                else:
                    print(f"    ❌ Échec après {len(delays)} tentatives sur {model_name}")
            except genai_errors.ClientError as e:
                last_error = e
                code = str(getattr(e, "code", ""))
                if code == "429" and attempt < len(delays) - 1:
                    wait = delays[attempt]
                    print(f"    ⚠ Rate limit — retry dans {wait}s")
                    time.sleep(wait)
                elif code == "404":
                    print(f"    ⚠ Modèle {model_name} introuvable")
                    break
                else:
                    raise
        if response is not None:
            break

    if response is None:
        raise RuntimeError(f"Impossible d'obtenir une réponse Gemini. Dernière erreur : {last_error}")

    raw_text = response.text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
        return json.loads(cleaned)


def _strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()
