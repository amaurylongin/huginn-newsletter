# 🐦‍⬛ HUGINN — Revue de veille ARQUUS

Agent de veille OSINT automatisé qui collecte chaque semaine les articles pertinents de défense terrestre, les filtre via IA, et envoie une newsletter en grille visuelle à une liste de destinataires. S'exécute automatiquement via cron-job.org + GitHub Actions — ordi éteint, aucune action requise.

---

## 🗂 Structure du projet

```
huginn-newsletter/
├── .github/workflows/newsletter.yml    # Workflow GitHub Actions
├── src/
│   ├── main.py                         # Orchestrateur (mode RSS ou Search)
│   ├── rss.py                          # Collecte RSS + extraction og:image
│   ├── searcher.py                     # Recherche autonome multilingue (mode Search)
│   ├── llm.py                          # Filtrage Gemini (mode RSS)
│   ├── renderer.py                     # Rendu HTML Jinja2
│   ├── mailer.py                       # Envoi SMTP (To groupé)
│   └── archiver.py                     # Archives GitHub Pages
├── templates/
│   ├── newsletter.html                 # Template du mail
│   └── archive_index.html              # Page d'archive web
├── config/
│   ├── sources.txt                     # 👉 Flux RSS (mode RSS uniquement)
│   ├── recipients.txt                  # (vide — voir secret RECIPIENTS)
│   └── criteria.md                     # 👉 Critères de filtrage ARQUUS
├── docs/
│   ├── index.html                      # Page d'archive (auto-générée)
│   ├── editions/                       # Éditions archivées
│   └── assets/                         # Logos
├── requirements.txt
└── README.md
```

---

## ⚙️ Architecture

```
cron-job.org ──► GitHub Actions
                      │
       ┌──────────────┴──────────────┐
       │                             │
   Mode RSS                      Mode Search
   (par défaut)                  (test, gourmand en tokens)
       │                             │
   RSS sources                   Gemini + Google Search
   + Gemini filtrage             multilingue + scoring fiabilité
       │                             │
       └─────────────┬───────────────┘
                     │
              Gmail/Outlook SMTP ──► Destinataires
              GitHub Pages       ──► Archives web
```

**Coût total : 0 €** — tout repose sur des tiers gratuits.

---

## 🚀 Installation pas-à-pas

### Étape 1 — Cloner le repo

Utiliser GitHub Desktop (File → Clone repository) ou en ligne de commande :

```bash
git clone https://github.com/votre-username/huginn-newsletter.git
```

### Étape 2 — Obtenir une clé API Gemini (gratuite)

1. Aller sur **https://aistudio.google.com/apikey**
2. Se connecter avec un compte Google
3. **Create API Key** → **Create API key in new project**
4. Copier la clé (commence par `AIza...`)

### Étape 3 — Générer un mot de passe d'application

**Pour Gmail :**
1. Activer la validation en 2 étapes : https://myaccount.google.com/security
2. Créer un mot de passe d'application : https://myaccount.google.com/apppasswords
3. Nommer `HUGINN` et copier les 16 caractères

**Pour Outlook entreprise (Microsoft 365) :**
- Demander à l'IT le serveur SMTP autorisé (généralement `smtp.office365.com`)
- Créer un mot de passe d'application via le portail Microsoft 365

### Étape 4 — Configurer les secrets GitHub

**Settings → Secrets and variables → Actions → Secrets**

| Nom | Valeur |
|---|---|
| `GEMINI_API_KEY` | Clé Gemini (`AIza...`) |
| `SMTP_USER` | Adresse mail d'envoi |
| `SMTP_PASSWORD` | Mot de passe d'application |
| `SMTP_HOST` | `smtp.gmail.com` ou `smtp.office365.com` (selon fournisseur) |
| `RECIPIENTS` | Destinataires séparés par des virgules |

**Onglet "Variables"** :

| Nom | Valeur |
|---|---|
| `GH_PAGES_URL` | URL GitHub Pages sans slash final |
| `GH_MODE` | `rss` (recommandé) ou `search` (gourmand en tokens) |

### Étape 5 — Activer GitHub Pages

**Settings → Pages**
- Source : `Deploy from a branch`
- Branch : `main` / Folder : `/docs`

### Étape 6 — Déposer les logos

Dans `docs/assets/` :
- `huginn-logo.png`
- `arquus-logo-dark.png`
- `arquus-logo-white.png`

### Étape 7 — Permissions du workflow

**Settings → Actions → General** → tout en bas → cocher **"Read and write permissions"** → Save.

### Étape 8 — Automatisation via cron-job.org

GitHub Actions est peu fiable pour les crons sur les repos peu actifs. On utilise **cron-job.org** (gratuit).

**8.1 — Personal Access Token GitHub**
1. Avatar → **Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. **Generate new token** → Cocher uniquement **`workflow`**
3. Copier le token

**8.2 — Job sur cron-job.org**
1. Créer un compte sur **https://cron-job.org**
2. **Create cronjob** :
   - **URL** : `https://api.github.com/repos/VOTRE-USERNAME/huginn-newsletter/actions/workflows/newsletter.yml/dispatches`
   - **Schedule** : jour et heure souhaités
3. Onglet **Advanced** :
   - **Method** : `POST`
   - **Body** : `{"ref":"main"}`
   - **Headers** :
     - `Authorization` : `Bearer ghp_VOTRE_TOKEN`
     - `Content-Type` : `application/json`

---

## ⚙️ Personnalisation courante

### Ajouter / retirer une source RSS

Éditer `config/sources.txt` (une URL par ligne, `#` pour commenter).

### Ajouter / retirer un destinataire

Mettre à jour le secret `RECIPIENTS` dans GitHub.
Format : `prenom.nom@exemple.fr,contact@exemple.fr,autre@exemple.fr`

### Modifier le jour / l'heure d'envoi

Modifier le planning sur **cron-job.org** (heures en UTC).

### Ajuster les critères de filtrage

Éditer `config/criteria.md`.

### Changer le mode (RSS ↔ Search)

Modifier la variable `GH_MODE` dans GitHub Settings → Variables.

### Relancer manuellement

**Actions → Revue Huginn → Run workflow**.

---

## 🗑️ Gérer les éditions archivées

### Supprimer d'anciennes éditions et réinitialiser le compteur

Le numéro d'édition est calculé automatiquement par `archiver.py` : il compte les fichiers présents dans `docs/editions/` et ajoute 1. Donc pour repartir à un numéro précis, il suffit de garder le bon nombre de fichiers.

**Exemple — repartir à l'édition N°3** :

1. Aller dans `docs/editions/` sur GitHub
2. Identifier les **deux éditions à conserver** (ce seront les futures N°1 et N°2)
3. Supprimer toutes les autres éditions, **une par une** :
   - Ouvrir chaque fichier indésirable
   - Cliquer sur l'icône 🗑️ en haut à droite
   - Commit
4. **Renommer les deux éditions conservées** :
   - Ouvrir le fichier le plus ancien → ✏️ → renommer en `YYYY-MM-DD-edition-001.html`
   - Faire pareil pour le second en `YYYY-MM-DD-edition-002.html`
   - Le `YYYY-MM-DD` doit être conservé (ne change pas la date)
5. Supprimer `docs/index.html` (sera régénéré au prochain run)
6. **Actions → Run workflow** → la prochaine édition sera bien N°003

> ⚠️ Astuce alternative plus rapide : **GitHub Desktop** permet de supprimer plusieurs fichiers d'un coup en local puis de pousser le tout en un seul commit.

### Tout réinitialiser (repartir de zéro)

1. Supprimer **tout le contenu** du dossier `docs/editions/`
2. Supprimer `docs/index.html`
3. La prochaine édition sera N°001

---

## 🧪 Modes de fonctionnement

### Mode RSS (par défaut, recommandé)

- Le code lit les flux RSS définis dans `config/sources.txt`
- Gemini filtre uniquement (1 requête, ~5 000 tokens)
- Très peu coûteux, stable

### Mode Search (gourmand)

- Gemini cherche lui-même sur Google dans 7 langues
- Évalue la fiabilité des sources (score 1-5)
- ~50 000 à 100 000 tokens par exécution
- ⚠️ Peut épuiser le quota gratuit Gemini en quelques tests par jour

Pour basculer : modifier la variable `GH_MODE` (`rss` ou `search`).

---

## 🛟 Dépannage

| Problème | Cause probable | Solution |
|---|---|---|
| Workflow ne se déclenche pas | GitHub Actions peu fiable sur crons | Utiliser cron-job.org (étape 8) |
| "SMTP authentication failed" | Mot de passe d'application invalide | Regénérer un mot de passe |
| "GEMINI_API_KEY not set" | Secret absent ou mal nommé | Vérifier l'étape 4 |
| "Quota exceeded" | Trop de requêtes en mode Search | Repasser en mode RSS, attendre la réinitialisation à minuit Pacific |
| Moins de 2 articles retenus | Semaine creuse ou critères trop stricts | Assouplir `config/criteria.md` |
| Mode Search ne se lance pas | Variable `GH_MODE` non transmise | Vérifier que le workflow `.yml` contient bien `GH_MODE: ${{ vars.GH_MODE }}` dans les `env:` |
| Logos absents | Fichiers manquants dans `docs/assets/` | Vérifier l'étape 6 |
| GitHub Pages 404 | Pages non activé | Vérifier l'étape 5 |
| Page d'archive cassée (HTML dupliqué) | Mauvais collage dans le template | Supprimer `docs/index.html`, vérifier que `templates/archive_index.html` ne contient qu'une seule fois `<!DOCTYPE html>` |
| Couleurs incorrectes dans Outlook | Mode sombre Outlook actif | Fichier → Options → Général → cocher "Ne jamais modifier la couleur des messages" |
| Images non affichées | Sécurité du client mail | Ajouter l'expéditeur aux contacts pour téléchargement automatique |

---

## 📜 Notes

- Le filtrage est réalisé par IA — des faux positifs/négatifs sont possibles.
- Les boutons 👍 / ✉ Contactez-nous permettent de remonter du feedback.
- L'API Gemini est utilisée sur le tier gratuit (suffisant en mode RSS).
- GitHub Actions offre 2 000 minutes/mois gratuites — largement suffisant.
- Toutes les archives sont disponibles indéfiniment via GitHub Pages.

---

*Huginn — La pensée qui survole le monde.*
