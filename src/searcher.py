"""Recherche autonome via Gemini + Google Search — multilingue + scoring fiabilité."""
import os
import json
import re
import time
from datetime import datetime

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

MODEL_NAME = "gemini-2.0-flash"

# Sources reconnues comme fiables en défense terrestre (score de référence)
TRUSTED_SOURCES = """
SOURCES DE HAUTE FIABILITÉ (score 5/5) :
Jane's Defence Weekly, Defense News, Breaking Defense, Army Recognition,
Army Technology, The War Zone, RUSI, IISS, Congressional Research Service,
Ministère des Armées (France), Bundeswehr, US Army, NATO official,
Shephard Media, Armée de Terre officielle, DGA officielle,
Oryx (analyses pertes vérifiées par images), ISW (Institute for the Study of War)

SOURCES FIABLES (score 4/5) :
Military Leak, Quwa Defense News, Defense Post, Bulgarian Military,
The Defense Post, Militarnyi, Kyiv Independent (rubrique guerre),
Euromaidan Press, MWI West Point, Defense Industry Daily,
Forces Opérations Blog, Air & Cosmos Défense, Le Fauteuil de Colbert

SOURCES MOYENNEMENT FIABLES (score 3/5) :
Blogs militaires établis avec auteurs identifiés, médias généralistes
avec desk défense reconnu (Le Monde, Guardian, Reuters, AFP, dpa, EFE),
Think tanks régionaux, médias officiels étrangers neutres

SOURCES À TRAITER AVEC PRÉCAUTION (score 2/5) :
Médias d'État (RT, TASS, Xinhua, PressTV, Al-Mayadeen) — peuvent
contenir de la désinformation, à inclure seulement si l'info est
corroborée ailleurs. Telegram channels militaires non vérifiés.

SOURCES À EXCLURE (score 1/5) :
Sites sans auteur identifié, sites créés récemment sans historique,
sites connus pour la désinformation, forums anonymes, réseaux sociaux
sans source primaire identifiable.
"""

SEARCH_PROMPT = f"""Tu es HUGINN, agent de veille OSINT pour ARQUUS (constructeur français de véhicules militaires terrestres).

Ta mission : rechercher et sélectionner les actualités défense les plus importantes de la semaine, dans TOUTES LES LANGUES disponibles.

LANGUES À COUVRIR OBLIGATOIREMENT :
- Anglais (US, UK, australien) — médias anglophones dominants en défense
- Français — presse défense française et francophone
- Allemand — industrie blindée européenne (Rheinmetall, KNDS...)
- Polonais — pays en forte réarmement, proche Ukraine
- Ukrainien et/ou russe — informations de terrain sur le conflit
- Hébreu — conflit israélien, industrie défense (Elbit, Rafael...)
- Coréen — industrie blindée (Hanwha, K2, K21...)
- Espagnol/portugais — marchés export Amérique latine
- Toute autre langue pertinente selon l'actualité

ÉVALUATION DE LA FIABILITÉ DES SOURCES :
{TRUSTED_SOURCES}

Pour chaque article trouvé, tu DOIS :
1. Évaluer la fiabilité de la source (score 1 à 5)
2. N'inclure QUE les articles avec score >= 3
3. Si une info vient d'une source score 2 (média d'État, Telegram), ne l'inclure
   que si elle est corroborée par une autre source score >= 3

SÉLECTION DES ARTICLES :
- Uniquement des articles liés au métier d'ARQUUS (voir critères fournis)
- Entre 6 et 10 articles au total
- Priorité aux articles avec image disponible
- Titre en français, 6 mots maximum, percutant et factuel

SCHÉMA JSON STRICT (aucun autre champ, sans balises markdown) :
{{
  "articles": [
    {{
      "title_fr": "titre 6 mots max en français",
      "source": "nom exact du média",
      "source_score": 4,
      "date": "YYYY-MM-DD",
      "link": "URL complète de l'article",
      "image_url": "URL image ou null"
    }}
  ]
}}
"""


def search_articles(criteria, start_date, end_date):
    """Recherche multilingue avec scoring de fiabilité des sources."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY manquant.")

    client = genai.Client(api_key=api_key)

    period = f"du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"

    user_prompt = (
        f"Recherche les actualités défense terrestre pour ARQUUS parues {period}.\n\n"
        f"Effectue des recherches dans TOUTES CES LANGUES :\n"
        f"- Anglais : armored vehicle news, military vehicle contract, UGV combat, IFV news\n"
        f"- Français : véhicule blindé actualité, contrat défense terrestre, char combat\n"
        f"- Allemand : Schützenpanzer aktuell, Rüstungsvertrag Panzer, Kampfpanzer\n"
        f"- Polonais : czołg aktualności, pojazd opancerzony kontrakt\n"
        f"- Ukrainien : бронетехніка новини, танк, БПЛА проти танків\n"
        f"- Hébreu : טנק חדשות, רכב קרבי, עסקת נשק\n"
        f"- Coréen : 전차 뉴스, 장갑차 계약, K2 전차\n\n"
        f"Critères ARQUUS pour évaluer la pertinence :\n{criteria}\n\n"
        f"Évalue la fiabilité de chaque source et n'inclus que les articles "
        f"de sources avec score >= 3. Produis le JSON final."
    )

    delays = [20, 45, 90]
    response = None
    last_error = None

    for attempt in range(len(delays)):
        try:
            print(f"  ▸ Recherche multilingue (tentative {attempt+1}/{len(delays)})...")
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
        raise RuntimeError(f"Impossible d'obtenir une réponse. Erreur : {last_error}")

    raw_text = response.text.strip() if response.text else ""

    # Extraire le JSON de la réponse
    json_match = re.search(r'\{[\s\S]*?"articles"[\s\S]*?\}(?=\s*$|\s*```)', raw_text)
    if not json_match:
        json_match = re.search(r'\{[\s\S]*?"articles"[\s\S]*\}', raw_text)

    raw_json = json_match.group(0) if json_match else raw_text
    raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_json, flags=re.MULTILINE).strip()

    try:
        result = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON invalide : {e}")
        print(f"  Raw (300 chars) : {raw_text[:300]}")
        return []

    articles = result.get("articles", [])

    # Double vérification Python : exclure les sources score < 3
    filtered = [a for a in articles if int(a.get("source_score", 3)) >= 3]
    excluded = len(articles) - len(filtered)

    if excluded > 0:
        print(f"  → {excluded} article(s) exclu(s) pour fiabilité insuffisante (score < 3)")

    # Normaliser le format
    normalized = []
    for a in filtered:
        normalized.append({
            "title_fr":    (a.get("title_fr") or a.get("title") or "").strip(),
            "source":      a.get("source", ""),
            "source_score": int(a.get("source_score", 3)),
            "date":        _normalize_date(a.get("date", ""), end_date),
            "link":        a.get("link", ""),
            "image_url":   a.get("image_url") or None,
        })

    with_img    = sum(1 for a in normalized if a["image_url"])
    without_img = len(normalized) - with_img

    print(f"  → {len(normalized)} article(s) retenus")
    print(f"  → {with_img} avec image / {without_img} sans image")

    if normalized:
        score_labels = {5: "★★★★★ Référence", 4: "★★★★☆ Fiable   ",
                        3: "★★★☆☆ Acceptable", 2: "★★☆☆☆ Prudence ",
                        1: "★☆☆☆☆ Exclu    "}
        print("")
        print("  ┌─────────────────────────────────────────────────┐")
        print("  │         FIABILITÉ DES SOURCES RETENUES          │")
        print("  ├───────────────────────────────┬─────────────────┤")
        print("  │ Source                        │ Score           │")
        print("  ├───────────────────────────────┼─────────────────┤")
        for a in normalized:
            score = a.get("source_score", 3)
            label = score_labels.get(score, "—")
            source = a["source"][:29].ljust(29)
            print(f"  │ {source} │ {score}/5 {label} │")
        print("  └───────────────────────────────┴─────────────────┘")

    return normalized


def _normalize_date(date_str, fallback):
    if not date_str:
        return fallback.isoformat()
    try:
        if len(date_str) == 10:
            return date_str + "T00:00:00+00:00"
        return date_str
    except Exception:
        return fallback.isoformat()
