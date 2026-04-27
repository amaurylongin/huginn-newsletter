"""Analyse des articles via l'API Gemini — retry automatique + fallback modèles."""
import os
import json
import re
import time

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

MODEL_NAME = "gemini-3.1-flash-lite-preview"

SYSTEM_PROMPT = """Tu es HUGINN, agent de veille OSINT pour ARQUUS (constructeur français de véhicules blindés terrestres).

Mission : analyser une liste d'articles RSS de défense et produire une newsletter visuelle ultra-concise.

RÈGLES ABSOLUES :
1. Ne retenir QUE les articles qui ont un champ image_url non null — les articles sans image sont EXCLUS systématiquement, sans exception.
2. Filtrer selon les critères thématiques (inclusion/exclusion fournis).
3. Minimum 2 articles retenus, maximum 10.
4. Générer un titre en français de 6 MOTS MAXIMUM par article — percutant et factuel.
5. Traduire intégralement en français.
6. Ne jamais inventer d'information.
7. Retourner UNIQUEMENT du JSON valide, sans balises markdown.

THÈMES (exactement ces libellés) :
- "Contrats & Industrie"
- "Front ukrainien"
- "Innovation & Technologie"
- "Géopolitique"
- "Conflits & Zones chaudes"

SCHÉMA JSON STRICT (aucun autre champ) :
{
  "articles": [
    {
      "title_fr": "titre 6 mots max",
      "theme": "un des 5 thèmes",
      "source": "nom de la source",
      "date": "date ISO",
      "link": "URL originale",
      "image_url": "URL image — JAMAIS null ici"
    }
  ]
}
"""


def analyze_articles(raw_articles, criteria):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquant.")

    client = genai.Client(api_key=api_key)

    # On n'envoie à Gemini que les articles qui ont déjà une image
    # pour lui simplifier la tâche et économiser des tokens
    articles_with_image = [a for a in raw_articles if a.get("image_url")]
    articles_without   = len(raw_articles) - len(articles_with_image)
    print(f"  → {len(articles_with_image)} articles avec image / {articles_without} sans image (ignorés)")

    if not articles_with_image:
        print("  ⚠ Aucun article avec image cette semaine.")
        return {"articles": []}

    compact = []
    for a in articles_with_image:
        compact.append({
            "title":     a["title"][:200],
            "summary":   _strip_html(a.get("summary", ""))[:300],
            "link":      a["link"],
            "source":    a["source"],
            "date":      a["date"],
            "image_url": a["image_url"],
        })

    user_prompt = (
        f"# CRITÈRES\n\n{criteria}\n\n"
        f"# ARTICLES (tous ont une image)\n\n"
        f"{json.dumps(compact, ensure_ascii=False, indent=2)}\n\n"
        "Produis le JSON final. Rappel : ne garder que les articles pertinents selon les critères."
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
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
        result = json.loads(cleaned)

    # Sécurité : on filtre côté Python aussi au cas où Gemini aurait quand même
    # inclus un article sans image
    result["articles"] = [a for a in result.get("articles", []) if a.get("image_url")]
    return result


def _strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()
