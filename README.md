# 🐦‍⬛ HUGINN — Bot de veille technologique ARQUUS

Bot OSINT automatisé qui collecte chaque semaine les actualités de défense terrestre depuis des flux RSS, les filtre via IA, et les diffuse par mail. S'exécute automatiquement chaque lundi matin — aucune action requise.

---

# PARTIE 1 — Comment ça fonctionne

## Vue d'ensemble

```
GitHub Actions (cron automatique)
    │
    ├── 1. Collecte les articles depuis les flux RSS
    │         ↓ articles de la semaine uniquement
    ├── 2. Filtre via Gemini IA selon les critères ARQUUS
    │         ↓ 2 à 10 articles retenus, traduits en français
    ├── 3. Génère la revue en HTML
    │         ↓
    ├── 4. Archive l'édition sur GitHub Pages
    │         ↓
    └── 5. Envoie par mail à tous les destinataires
```

## Détail de chaque étape

**1. Collecte RSS (`rss.py`)**
Le bot lit en temps réel les flux RSS définis dans `config/sources.txt`. Il ne garde que les articles des 7 derniers jours. Si un article n'a pas d'image dans le flux, il tente de la récupérer sur la page de l'article via `og:image`.

**2. Filtrage Gemini (`llm.py`)**
Les articles sont envoyés à l'IA Gemini avec les critères de `config/criteria.md`. Gemini exclut les articles hors-sujet, ne retient que ceux avec image, génère un titre en français (6 mots max) et sélectionne entre 2 et 10 articles selon leur pertinence pour ARQUUS.

**3. Génération (`renderer.py` + `templates/newsletter.html`)**
Mise en forme HTML avec le design HUGINN/ARQUUS — grille 2 colonnes, photo + titre + lien pour chaque article.

**4. Archivage (`archiver.py`)**
Chaque édition est sauvegardée dans `docs/editions/`. Le numéro d'édition = nombre de fichiers dans `docs/editions/` + 1. La page d'archive est régénérée automatiquement.

**5. Envoi (`mailer.py`)**
Envoi via SMTP Gmail à tous les destinataires listés dans le secret `RECIPIENTS`. Tous reçoivent le mail simultanément.

## Structure des fichiers

```
huginn-newsletter/
├── .github/workflows/newsletter.yml    # Workflow et cron GitHub Actions
├── src/
│   ├── main.py                         # Orchestrateur principal
│   ├── rss.py                          # Collecte RSS + extraction og:image
│   ├── llm.py                          # Filtrage Gemini
│   ├── renderer.py                     # Rendu HTML
│   ├── mailer.py                       # Envoi SMTP Gmail
│   └── archiver.py                     # Archivage GitHub Pages
├── templates/
│   ├── newsletter.html                 # Template de la revue
│   └── archive_index.html              # Template page d'archive
├── config/
│   ├── sources.txt                     # Flux RSS suivis
│   ├── recipients.txt                  # (vide — destinataires dans le secret)
│   └── criteria.md                     # Critères de filtrage ARQUUS
├── docs/
│   ├── index.html                      # Page d'archive (auto-générée)
│   ├── editions/                       # Éditions archivées
│   └── assets/                         # Logos
└── requirements.txt
```

---

# PARTIE 2 — Configuration et gestion

## Secrets et variables GitHub

**Settings → Secrets and variables → Actions**

### Secrets

| Nom | Description |
|---|---|
| `GEMINI_API_KEY` | Clé API Gemini — https://aistudio.google.com/apikey |
| `SMTP_USER` | Adresse Gmail d'envoi |
| `SMTP_PASSWORD` | Mot de passe d'application Gmail (16 caractères, sans espaces) |
| `RECIPIENTS` | Destinataires séparés par des virgules |

### Variables

| Nom | Description |
|---|---|
| `GH_PAGES_URL` | URL GitHub Pages sans slash final |
| `GH_MODE` | `rss` (valeur par défaut et recommandée) |

---

## Modifier les destinataires

**Settings → Secrets and variables → Actions → `RECIPIENTS` → ✏️ Update**

```
prenom.nom@entreprise.com,collegue1@entreprise.com,collegue2@entreprise.com
```

---

## Modifier les sources RSS

Ouvrir `config/sources.txt` → ✏️

Une URL par ligne. Les lignes commençant par `#` sont ignorées (pratique pour désactiver temporairement une source).

```
https://army-technology.com/feed/
https://militaryleak.com/feed/

# Désactivé temporairement
# https://breakingdefense.com/feed/
```

---

## Modifier les critères de filtrage

Ouvrir `config/criteria.md` → ✏️

Ce fichier définit ce que Gemini doit retenir ou exclure. Il contient :
- Le contexte ARQUUS (qui on est, ce qui nous intéresse)
- Les domaines à inclure avec les mots-clés associés
- Les domaines à exclure absolument

Plus les critères sont précis, meilleur est le filtrage.

---

## Modifier le jour et l'heure d'envoi

Ouvrir `.github/workflows/newsletter.yml` → ✏️

Chercher la ligne :
```yaml
- cron: "0 6 * * 1"
```

Format : `"minute heure jour-du-mois mois jour-de-semaine"`

| Souhait | Valeur |
|---|---|
| Lundi 8h Paris (été) | `"0 6 * * 1"` |
| Lundi 8h Paris (hiver) | `"0 7 * * 1"` |
| Vendredi 17h Paris (été) | `"0 15 * * 5"` |
| Jeudi 10h Paris (été) | `"0 8 * * 4"` |

> ⚠️ Les heures sont en **UTC**. Paris = UTC+2 en été, UTC+1 en hiver.
> Convertisseur : https://crontab.guru

---

## Déclencher un envoi manuel

**Actions → Revue Huginn — envoi hebdomadaire → Run workflow → Run workflow**

---

## Gérer les éditions archivées

Le numéro d'édition est calculé automatiquement : nombre de fichiers dans `docs/editions/` + 1.

### Supprimer des éditions et réinitialiser le compteur

**Méthode rapide (GitHub Desktop) :**
1. Ouvrir le dossier local du repo
2. Aller dans `docs/editions/`
3. Supprimer les fichiers à retirer
4. Renommer les fichiers conservés : `YYYY-MM-DD-edition-001.html`, `YYYY-MM-DD-edition-002.html`...
5. Supprimer `docs/index.html`
6. Commit → Push
7. La prochaine exécution régénère `index.html` avec le bon compteur

**Méthode GitHub web :**
Ouvrir chaque fichier à supprimer → icône 🗑️ → commit (une opération par fichier)

---

## Générer un mot de passe d'application Gmail

Nécessaire si l'envoi échoue avec une erreur `535`.

1. Aller sur https://myaccount.google.com/apppasswords
2. Supprimer l'ancien mot de passe HUGINN si présent
3. Créer un nouveau → nommer `HUGINN`
4. Copier les 16 caractères **sans espaces**
5. Mettre à jour le secret `SMTP_PASSWORD` dans GitHub

---

## Dépannage

| Problème | Solution |
|---|---|
| Aucun mail reçu | Vérifier dans **Actions** que le workflow s'est lancé. Si non, faire un commit sur le repo pour réactiver le cron (GitHub désactive les crons sur les repos inactifs). |
| Erreur 535 SMTP | Regénérer le mot de passe d'application Gmail |
| "Aucun destinataire" | Vérifier que `RECIPIENTS` est renseigné et présent dans le bloc `env:` du workflow |
| Quota Gemini épuisé | Attendre la réinitialisation (~9h Paris). En mode RSS, 1 seule requête par semaine — ne pas lancer plusieurs tests dans la journée. |
| Moins de 2 articles | Semaine creuse ou critères trop stricts — assouplir `config/criteria.md` |
| Page d'archive cassée | Supprimer `docs/index.html` et relancer le workflow |
| Couleurs incorrectes dans Outlook | Fichier → Options → Général → cocher "Ne jamais modifier la couleur des messages" |
| Images non affichées | Ajouter l'adresse d'envoi aux contacts du destinataire |

---

*Huginn — La pensée qui survole le monde.*
