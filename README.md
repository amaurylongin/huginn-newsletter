# 🐦‍⬛ HUGINN — Bot de veille technologique ARQUUS

Bot OSINT automatisé qui collecte chaque semaine les actualités pertinentes de défense terrestre, les filtre via IA, et les diffuse par mail à une liste de destinataires. S'exécute automatiquement — ordi éteint, aucune action requise.

---

# 📖 PARTIE 1 — Comment ça fonctionne

## Vue d'ensemble

```
cron-job.org
    │  (déclenche chaque lundi matin)
    ▼
GitHub Actions
    │
    ├── 1. Collecte les articles depuis les flux RSS définis
    │         ↓ (articles de la semaine uniquement)
    ├── 2. Filtre via Gemini IA selon les critères ARQUUS
    │         ↓ (2 à 10 articles retenus, traduits en français)
    ├── 3. Génère la revue en HTML
    │         ↓
    ├── 4. Archive l'édition sur GitHub Pages
    │         ↓
    └── 5. Envoie par mail à la liste des destinataires
```

---

## Étape par étape

### 1. Collecte des articles (rss.py)

Le bot lit en temps réel les flux RSS des sources définies dans `config/sources.txt`. Il récupère uniquement les articles publiés dans les 7 derniers jours. Si un article n'a pas d'image dans le flux RSS, il tente de la récupérer directement sur la page de l'article (via `og:image`).

### 2. Filtrage par Gemini (llm.py)

Les articles collectés sont envoyés à l'IA Gemini avec les critères définis dans `config/criteria.md`. Gemini :
- Exclut les articles hors-sujet (aviation, marine, RH militaire...)
- Conserve uniquement ceux avec une image (règle stricte)
- Génère un titre en français de 6 mots maximum pour chaque article retenu
- Sélectionne entre 2 et 10 articles selon leur pertinence pour ARQUUS

### 3. Génération de la revue (renderer.py + newsletter.html)

Le résultat est mis en forme en HTML avec le design HUGINN/ARQUUS — grille d'articles en 2 colonnes, photo + titre + lien pour chaque article.

### 4. Archivage (archiver.py)

Chaque édition est sauvegardée en HTML dans `docs/editions/` et référencée sur la page d'archive GitHub Pages. Le numéro d'édition est calculé automatiquement (nombre de fichiers dans `docs/editions/` + 1).

### 5. Envoi (mailer.py)

La revue est envoyée via SMTP Gmail à tous les destinataires listés dans le secret GitHub `RECIPIENTS`. Tous sont dans le champ "To" et reçoivent le mail simultanément.

---

## Structure des fichiers

```
huginn-newsletter/
├── .github/workflows/newsletter.yml    # Workflow GitHub Actions
├── src/
│   ├── main.py                         # Orchestrateur principal
│   ├── rss.py                          # Collecte RSS + extraction og:image
│   ├── llm.py                          # Filtrage et traduction Gemini
│   ├── renderer.py                     # Rendu HTML Jinja2
│   ├── mailer.py                       # Envoi SMTP Gmail
│   └── archiver.py                     # Archives GitHub Pages
├── templates/
│   ├── newsletter.html                 # Template de la revue mail
│   └── archive_index.html              # Template de la page d'archive
├── config/
│   ├── sources.txt                     # Flux RSS suivis
│   ├── recipients.txt                  # (vide — destinataires dans le secret)
│   └── criteria.md                     # Critères de filtrage ARQUUS
├── docs/
│   ├── index.html                      # Page d'archive (auto-générée)
│   ├── editions/                       # Éditions archivées en HTML
│   └── assets/                         # Logos (huginn, arquus dark, arquus white)
├── requirements.txt
└── README.md
```

---

# ⚙️ PARTIE 2 — Configuration

## Gestion courante

### Ajouter ou retirer un destinataire

Les destinataires sont stockés dans le secret GitHub `RECIPIENTS`.

**Settings → Secrets and variables → Actions → `RECIPIENTS` → ✏️ Update**

Format : adresses séparées par des virgules, sans espaces :
```
prenom.nom@entreprise.com,collegue1@entreprise.com,collegue2@entreprise.com
```

### Ajouter ou retirer une source RSS

Éditer `config/sources.txt` dans GitHub (✏️) — une URL par ligne. Les lignes commençant par `#` sont ignorées.

```
# Actif
https://army-technology.com/feed/
https://militaryleak.com/feed/

# Désactivé temporairement
# https://breakingdefense.com/feed/
```

### Ajuster les critères de filtrage

Éditer `config/criteria.md` dans GitHub — ajouter ou retirer des mots-clés, thèmes, exclusions. Plus les critères sont précis, meilleur est le filtrage.

### Modifier le jour ou l'heure d'envoi

Se connecter sur **https://cron-job.org** → job HUGINN → onglet Schedule → modifier.

> Les heures sont en UTC. Paris en été = UTC+2, en hiver = UTC+1.
> Exemple : lundi 8h Paris (été) = lundi 6h UTC.

### Déclencher un envoi manuel

**Actions → Revue Huginn — envoi hebdomadaire → Run workflow → Run workflow**

---

## Secrets et variables GitHub

**Settings → Secrets and variables → Actions**

### Onglet Secrets

| Nom | Description |
|---|---|
| `GEMINI_API_KEY` | Clé API Gemini (https://aistudio.google.com/apikey) |
| `SMTP_USER` | Adresse Gmail d'envoi |
| `SMTP_PASSWORD` | Mot de passe d'application Gmail (16 caractères, sans espaces) |
| `RECIPIENTS` | Destinataires séparés par des virgules |

### Onglet Variables

| Nom | Description |
|---|---|
| `GH_PAGES_URL` | URL GitHub Pages sans slash final (ex: `https://username.github.io/huginn-newsletter`) |
| `GH_MODE` | Mode d'exécution : `rss` (par défaut et recommandé) |

---

## Générer un mot de passe d'application Gmail

Le mot de passe d'application est différent du mot de passe du compte Gmail. Il est généré spécifiquement pour HUGINN.

1. Activer la validation en 2 étapes : https://myaccount.google.com/security
2. Aller sur : https://myaccount.google.com/apppasswords
3. Nommer l'application `HUGINN`
4. Copier les 16 caractères générés **en retirant les espaces**
5. Coller dans le secret `SMTP_PASSWORD`

> Si le mot de passe est refusé (erreur 535), le supprimer et en regénérer un nouveau.

---

## Gérer les éditions archivées

### Supprimer des éditions et réinitialiser le compteur

Le numéro d'édition = nombre de fichiers dans `docs/editions/` + 1.

**Exemple : repartir à N°3 en conservant 2 éditions**

1. Ouvrir `docs/editions/` dans GitHub
2. Supprimer toutes les éditions sauf les 2 à conserver
   - **Méthode rapide** : GitHub Desktop → supprimer en local → push en un seul commit
   - **Méthode GitHub web** : ouvrir chaque fichier → 🗑️ → commit
3. Renommer les 2 fichiers conservés :
   - `YYYY-MM-DD-edition-001.html` (le plus ancien)
   - `YYYY-MM-DD-edition-002.html`
4. Supprimer `docs/index.html` (sera régénéré automatiquement)
5. Lancer un Run workflow → la prochaine édition sera N°003

### Tout réinitialiser (repartir à N°1)

Supprimer tout le contenu de `docs/editions/` et `docs/index.html`, puis relancer.

---

## Installer depuis zéro

### Étape 1 — Cloner le repo

Utiliser **GitHub Desktop** (File → Clone repository) ou :
```bash
git clone https://github.com/votre-username/huginn-newsletter.git
```

### Étape 2 — Configurer les secrets GitHub

Renseigner les 4 secrets et 2 variables décrits dans la section "Secrets et variables GitHub" ci-dessus.

### Étape 3 — Activer GitHub Pages

**Settings → Pages** → Source : `main` / Folder : `/docs` → Save.

### Étape 4 — Déposer les logos

Dans `docs/assets/` :
- `huginn-logo.png`
- `arquus-logo-dark.png`
- `arquus-logo-white.png`

### Étape 5 — Autoriser les écritures du workflow

**Settings → Actions → General** → cocher **"Read and write permissions"** → Save.

### Étape 6 — Configurer l'automatisation via cron-job.org

GitHub Actions est peu fiable pour les crons sur les repos peu actifs. On utilise **cron-job.org** (gratuit).

**6.1 — Personal Access Token GitHub**
1. Avatar → **Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. **Generate new token** → cocher uniquement **`workflow`** → copier le token

**6.2 — Job sur cron-job.org**
1. Créer un compte sur **https://cron-job.org**
2. **Create cronjob** :
   - **URL** : `https://api.github.com/repos/VOTRE-USERNAME/huginn-newsletter/actions/workflows/newsletter.yml/dispatches`
   - **Schedule** : jour et heure souhaités (en UTC)
3. Onglet **Advanced** :
   - **Method** : `POST`
   - **Body** : `{"ref":"main"}`
   - **Headers** :
     - `Authorization` : `Bearer ghp_VOTRE_TOKEN`
     - `Content-Type` : `application/json`
4. Tester avec **Run now**

---

## Dépannage

| Problème | Solution |
|---|---|
| Aucun mail reçu | Vérifier dans Actions que le workflow s'est lancé. Si absent, vérifier cron-job.org. |
| Erreur 535 SMTP | Regénérer le mot de passe d'application Gmail et mettre à jour `SMTP_PASSWORD` |
| "Aucun destinataire" | Vérifier que le secret `RECIPIENTS` est bien renseigné et transmis dans le workflow |
| Quota Gemini épuisé | Attendre la réinitialisation à ~9h Paris (minuit Pacific) |
| Moins de 2 articles retenus | Semaine creuse ou critères trop stricts — assouplir `config/criteria.md` |
| Page d'archive cassée | Supprimer `docs/index.html` et relancer le workflow |
| Couleurs incorrectes dans Outlook | Fichier → Options → Général → cocher "Ne jamais modifier la couleur des messages" |
| Images non affichées | Ajouter l'adresse d'envoi aux contacts du destinataire |

---

*Huginn — La pensée qui survole le monde.*
