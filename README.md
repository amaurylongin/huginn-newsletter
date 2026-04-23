# 🐦‍⬛ HUGINN — Revue de veille ARQUUS

Agent de veille OSINT automatisé qui collecte chaque semaine les articles pertinents de défense terrestre, les filtre et traduit via IA, puis envoie une newsletter par mail à une liste de destinataires. S'exécute automatiquement via cron-job.org + GitHub Actions — ordi éteint, aucune action requise.

---

## 🗂 Structure du projet

```
huginn-newsletter/
├── .github/workflows/newsletter.yml    # Workflow GitHub Actions
├── src/
│   ├── main.py                         # Orchestrateur principal
│   ├── rss.py                          # Collecte des flux RSS
│   ├── llm.py                          # Filtrage et traduction via Gemini
│   ├── renderer.py                     # Rendu HTML Jinja2
│   ├── mailer.py                       # Envoi SMTP Gmail
│   └── archiver.py                     # Archives GitHub Pages
├── templates/
│   ├── newsletter.html                 # Template du mail
│   └── archive_index.html             # Template de la page d'archive
├── config/
│   ├── sources.txt                     # 👉 Flux RSS (ligne = une URL)
│   ├── recipients.txt                  # (vide — destinataires dans le secret RECIPIENTS)
│   └── criteria.md                     # 👉 Critères de filtrage thématique
├── docs/
│   ├── index.html                      # Page d'archive (GitHub Pages)
│   ├── editions/                       # Éditions archivées
│   └── assets/                         # Logos
├── requirements.txt
└── README.md
```

---

## ⚙️ Architecture

```
cron-job.org ──► GitHub Actions ──► RSS (12 sources)
                      │                    │
                      │              Gemini IA (filtrage + traduction FR)
                      │                    │
                      └──► Gmail SMTP ──► Destinataires
                      └──► GitHub Pages ──► Archive web
```

**Coût total : 0 €** — tout repose sur des tiers gratuits.

---

## 🚀 Installation pas-à-pas

### Étape 1 — Cloner le repo

Utiliser GitHub Desktop : File → Clone repository, ou en ligne de commande :

```bash
git clone https://github.com/votre-username/huginn-newsletter.git
```

### Étape 2 — Obtenir une clé API Gemini (gratuite)

1. Aller sur **https://aistudio.google.com/apikey**
2. Se connecter avec un compte Google
3. Cliquer **"Create API Key"** → **"Create API key in new project"**
4. Copier la clé (commence par `AIza...`)

### Étape 3 — Générer un mot de passe d'application Gmail

1. Se connecter au compte Gmail d'envoi
2. Activer la **validation en 2 étapes** : https://myaccount.google.com/security
3. Créer un mot de passe d'application : https://myaccount.google.com/apppasswords
4. Nommer l'application `HUGINN` et copier les 16 caractères générés (sans les espaces)

### Étape 4 — Configurer les secrets GitHub

Dans le repo : **Settings → Secrets and variables → Actions → Secrets**

| Nom | Valeur |
|---|---|
| `GEMINI_API_KEY` | La clé Gemini (`AIza...`) |
| `SMTP_USER` | Adresse Gmail d'envoi (ex: `votre.adresse@gmail.com`) |
| `SMTP_PASSWORD` | Le mot de passe d'application de 16 caractères |
| `RECIPIENTS` | Destinataires séparés par des virgules (ex: `prenom.nom@exemple.fr,contact@exemple.fr`) |

Dans l'onglet **"Variables"** :

| Nom | Valeur |
|---|---|
| `GH_PAGES_URL` | URL GitHub Pages sans slash final (ex: `https://votre-username.github.io/huginn-newsletter`) |

### Étape 5 — Activer GitHub Pages

Dans le repo : **Settings → Pages**
- Source : `Deploy from a branch`
- Branch : `main` / Folder : `/docs`
- Cliquer **Save**

### Étape 6 — Déposer les logos

Placer les 3 fichiers dans `docs/assets/` du repo :
- `huginn-logo.png`
- `arquus-logo-dark.png`
- `arquus-logo-white.png`

### Étape 7 — Autoriser les écritures du workflow

**Settings → Actions → General** → section "Workflow permissions" → cocher **"Read and write permissions"** → Save.

### Étape 8 — Configurer l'automatisation via cron-job.org

GitHub Actions n'est pas fiable pour les crons sur les repos peu actifs. On utilise **cron-job.org** (gratuit) pour déclencher le workflow à heure fixe.

#### 8.1 — Créer un Personal Access Token GitHub

1. GitHub → avatar → **Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. **Generate new token (classic)**
3. Nom : `HUGINN cron trigger` / Expiration : `No expiration`
4. Cocher uniquement : **`workflow`**
5. Copier le token (commence par `ghp_...`)

#### 8.2 — Créer le job sur cron-job.org

1. Créer un compte sur **https://cron-job.org**
2. Cliquer **"Create cronjob"** et remplir :
   - **Title** : `HUGINN Newsletter`
   - **URL** : `https://api.github.com/repos/VOTRE-USERNAME/huginn-newsletter/actions/workflows/newsletter.yml/dispatches`
   - **Schedule** : choisir le jour et l'heure souhaités
3. Onglet **"Advanced"** :
   - **Request method** : `POST`
   - **Request body** : `{"ref":"main"}`
   - **Headers** → ajouter deux headers :

| Name | Value |
|---|---|
| `Authorization` | `Bearer ghp_VOTRE_TOKEN` |
| `Content-Type` | `application/json` |

4. Cliquer **"Create"** puis tester avec **"Run now"**

---

## ⚙️ Personnalisation courante

### Ajouter / retirer une source RSS

Éditer `config/sources.txt` (une URL par ligne, `#` pour commenter), commiter.

### Ajouter / retirer un destinataire

Mettre à jour le secret `RECIPIENTS` dans **Settings → Secrets and variables → Actions**.

Format : `prenom.nom@exemple.fr,contact@exemple.fr,autre@exemple.fr`

### Modifier le jour / l'heure d'envoi

Modifier le planning directement sur **cron-job.org** dans les paramètres du job HUGINN.

> ⚠️ Les heures sur cron-job.org sont en UTC.
> Paris = UTC+2 en été (mars→octobre), UTC+1 en hiver (octobre→mars).
> Exemple : lundi 08h00 Paris en été = lundi **06h00 UTC**.

### Ajuster les critères de filtrage

Éditer `config/criteria.md` — ajouter des mots-clés, affiner les exclusions, modifier les thèmes.

### Relancer manuellement

Dans GitHub : **Actions → Revue Huginn → Run workflow → Run workflow**.

---

## 🧪 Tester en local (facultatif)

```bash
pip install -r requirements.txt

export GEMINI_API_KEY="AIza..."
export SMTP_USER="votre.adresse@gmail.com"
export SMTP_PASSWORD="xxxxxxxxxxxxxxxx"
export RECIPIENTS="prenom.nom@exemple.fr,contact@exemple.fr"
export GH_PAGES_URL="https://votre-username.github.io/huginn-newsletter"

python src/main.py
```

---

## 🛟 Dépannage

| Problème | Cause probable | Solution |
|---|---|---|
| Workflow ne se déclenche pas automatiquement | GitHub Actions peu fiable sur crons | Utiliser cron-job.org (étape 8) |
| "SMTP authentication failed" | Mot de passe d'application invalide | Regénérer un mot de passe sur myaccount.google.com/apppasswords |
| "GEMINI_API_KEY not set" | Secret absent ou mal nommé | Vérifier l'étape 4 |
| Moins de 2 articles retenus | Semaine creuse ou critères trop stricts | Assouplir `config/criteria.md` |
| Tous les articles viennent d'une seule source | Autres sources bloquent les requêtes | Mettre à jour `config/sources.txt` |
| Logos absents dans le mail | Fichiers manquants dans `docs/assets/` | Vérifier l'étape 6 |
| GitHub Pages 404 | Pages non activé ou URL incorrecte | Vérifier étape 5 et la variable `GH_PAGES_URL` |
| Workflow ne peut pas commiter l'archive | Permissions insuffisantes | Settings → Actions → General → "Read and write permissions" |
| Couleurs incorrectes dans Outlook | Mode sombre Outlook actif | Fichier → Options → Général → cocher "Ne jamais modifier la couleur des messages" |

---

## 📜 Notes

- Le filtrage est réalisé par IA — des faux positifs/négatifs sont possibles. Les boutons 👍 / 👎 en bas de chaque newsletter permettent de signaler les problèmes.
- L'API Gemini est utilisée sur le tier gratuit (suffisant pour 1 newsletter/semaine).
- GitHub Actions offre 2 000 minutes/mois gratuites — largement suffisant.
- Toutes les archives sont disponibles indéfiniment via GitHub Pages.

---

*Huginn — La pensée qui survole le monde.*
