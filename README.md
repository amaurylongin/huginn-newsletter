# 🐦‍⬛ HUGINN — Revue de veille ARQUUS

Agent de veille OSINT automatisé qui collecte chaque semaine les articles pertinents de défense terrestre, les filtre et traduit via IA, puis envoie une newsletter par mail à une liste de destinataires. S'exécute sur GitHub Actions (100 % gratuit, ordi éteint OK).

---

## 🗂 Structure du projet

```
huginn-newsletter/
├── .github/workflows/newsletter.yml    # Cron hebdomadaire (jour/heure à ajuster)
├── src/
│   ├── main.py                         # Orchestrateur
│   ├── rss.py                          # Collecte des flux RSS
│   ├── llm.py                          # Appels Gemini (filtrage + traduction)
│   ├── renderer.py                     # Rendu HTML Jinja2
│   ├── mailer.py                       # Envoi SMTP Gmail
│   └── archiver.py                     # Archives GitHub Pages
├── templates/
│   ├── newsletter.html                 # Template du mail (éditable)
│   └── archive_index.html              # Template de la page d'archive
├── config/
│   ├── sources.txt                     # 👉 Flux RSS (ligne = une URL)
│   ├── recipients.txt                  # 👉 Destinataires (ligne = un mail)
│   └── criteria.md                     # 👉 Critères de filtrage thématique
├── assets/                             # 👉 Vos logos ici
│   ├── huginn-logo.png                 #    (à déposer par vous)
│   └── arquus-logo.png                 #    (à déposer par vous)
├── docs/                               # Généré auto — GitHub Pages
│   ├── index.html                      # Page d'archive
│   ├── editions/                       # Archive des éditions
│   └── assets/                         # Copie des logos pour GitHub Pages
├── requirements.txt
└── README.md
```

---

## 🚀 Installation pas-à-pas

### Étape 1 — Créer le repo GitHub

1. Créez un nouveau repo **privé** sur GitHub (p. ex. `huginn-newsletter`).
2. Clonez-le localement et copiez-y l'intégralité de ce projet.
3. Committez et poussez :
   ```bash
   git add .
   git commit -m "🎬 Initialisation HUGINN"
   git push origin main
   ```

### Étape 2 — Obtenir une clé API Gemini (gratuite)

1. Allez sur https://aistudio.google.com/apikey
2. Connectez-vous avec un compte Google (peut être `arquus.osint@gmail.com`).
3. Cliquez sur **"Create API Key"** → **"Create API key in new project"**.
4. **Copiez la clé** (elle commence par `AIza...`). Gardez-la pour l'étape 4.

> **Limites du tier gratuit Gemini 2.5 Flash** : largement suffisantes pour 1 newsletter/semaine (plusieurs centaines de requêtes/jour autorisées).

### Étape 3 — Générer un mot de passe d'application Gmail

1. Connectez-vous à `arquus.osint@gmail.com`.
2. Activez la **validation en 2 étapes** (obligatoire) : https://myaccount.google.com/security → "Validation en 2 étapes".
3. Une fois activée, allez sur https://myaccount.google.com/apppasswords.
4. Créez un mot de passe d'application (sélectionnez "Autre" et nommez-le "HUGINN").
5. **Copiez les 16 caractères** générés. Gardez-les pour l'étape 4.

### Étape 4 — Configurer les secrets GitHub

Dans votre repo GitHub : **Settings → Secrets and variables → Actions**.

**Onglet "Secrets"** — cliquez "New repository secret" et créez les trois suivants :

| Nom | Valeur |
|---|---|
| `GEMINI_API_KEY` | La clé récupérée à l'étape 2 |
| `SMTP_USER` | `arquus.osint@gmail.com` |
| `SMTP_PASSWORD` | Le mot de passe d'application à 16 caractères de l'étape 3 |

**Onglet "Variables"** — cliquez "New repository variable" :

| Nom | Valeur |
|---|---|
| `GH_PAGES_URL` | `https://VOTRE-USERNAME.github.io/huginn-newsletter` (remplacer par votre URL réelle après l'étape 6) |

### Étape 5 — Configurer les destinataires

Éditez `config/recipients.txt` (dans votre repo, via l'interface web GitHub ou localement), ajoutez une adresse par ligne, puis committez.

```
# exemple
arquus.osint@gmail.com
jean.dupont@arquus.fr
marie.martin@arquus.fr
```

### Étape 6 — Activer GitHub Pages (pour les archives web)

Dans votre repo : **Settings → Pages** :
- **Source** : "Deploy from a branch"
- **Branch** : `main`
- **Folder** : `/docs`
- Cliquez **Save**.

GitHub Pages sera accessible à l'adresse `https://VOTRE-USERNAME.github.io/huginn-newsletter/`. Mettez cette URL dans la variable `GH_PAGES_URL` de l'étape 4.

### Étape 7 — Déposer les logos

Mettez vos deux logos dans le dossier `assets/` du repo :
- `assets/huginn-logo.png` (idéalement 280px de large, fond transparent)
- `assets/arquus-logo.png` (idéalement 200px de large, fond transparent)

**Copiez-les aussi dans `docs/assets/`** (pour qu'ils soient servis par GitHub Pages) :
```bash
cp assets/*.png docs/assets/
git add assets/ docs/assets/
git commit -m "🎨 Ajout des logos"
git push
```

Ensuite, éditez `templates/newsletter.html` : deux emplacements sont commentés `<!-- Logo HUGINN : remplacez... -->`. Remplacez chaque balise `<span>` par la balise `<img>` indiquée juste à côté dans le commentaire.

### Étape 8 — Tester un premier envoi

Dans votre repo : **Actions → Revue Huginn → Run workflow → Run workflow**.

Le job va :
1. Récupérer les articles des 7 derniers jours depuis les 12 flux RSS
2. Les envoyer à Gemini pour filtrage + traduction en français
3. Générer la newsletter HTML
4. L'envoyer à tous les destinataires
5. Archiver l'édition sur GitHub Pages et committer la mise à jour

Surveillez les logs du workflow en direct. Si tout va bien, le mail arrive dans les boîtes et une nouvelle édition apparaît dans `docs/editions/`.

---

## ⚙️ Personnalisation courante

### Modifier le jour / l'heure d'envoi

Éditez `.github/workflows/newsletter.yml`, ligne `cron: "0 6 * * 1"` :

| Souhait | Valeur cron (UTC) |
|---|---|
| Lundi 08h00 Paris (hiver) | `"0 7 * * 1"` |
| Lundi 09h00 Paris | `"0 7 * * 1"` (hiver) / `"0 8 * * 1"` (été) |
| Vendredi 18h00 Paris | `"0 16 * * 5"` (été) / `"0 17 * * 5"` (hiver) |

Convertisseur : https://crontab.guru. ⚠ GitHub Actions utilise l'UTC, pas l'heure de Paris.

### Ajouter / retirer une source RSS

Éditez `config/sources.txt`, ajoutez/supprimez des lignes, committez. Les lignes commençant par `#` sont ignorées.

### Ajouter / retirer un destinataire

Éditez `config/recipients.txt`, une adresse par ligne, committez.

### Ajuster les critères de filtrage

Éditez `config/criteria.md`. Vous pouvez ajouter de nouveaux mots-clés, affiner les exclusions, ajouter ou retirer des thèmes (si vous retirez un thème, pensez aussi à l'enlever de la liste `THEMES_ORDER` dans `src/renderer.py` et de la liste autorisée dans `src/llm.py`).

### Relancer manuellement un envoi

**Actions → Revue Huginn → Run workflow**.

---

## 🧪 Tester en local (facultatif, pour debug)

```bash
pip install -r requirements.txt

export GEMINI_API_KEY="AIza..."
export SMTP_USER="arquus.osint@gmail.com"
export SMTP_PASSWORD="xxxx xxxx xxxx xxxx"
export GH_PAGES_URL="https://votre-username.github.io/huginn-newsletter"

python src/main.py
```

---

## 🛟 Dépannage

| Problème | Cause probable | Solution |
|---|---|---|
| "SMTP authentication failed" | Mot de passe d'application invalide ou double authentification non activée | Vérifier l'étape 3 |
| "GEMINI_API_KEY not set" | Secret absent ou mal nommé | Vérifier l'étape 4 |
| "Moins de 2 articles retenus" | Semaine creuse ou critères trop stricts | Normal si la semaine est calme ; sinon assouplir `config/criteria.md` |
| Mail reçu sans les logos | Fichiers non copiés dans `docs/assets/` | Voir étape 7 |
| GitHub Pages 404 | Pages non activé ou URL non à jour | Vérifier étape 6 et la variable `GH_PAGES_URL` |
| Workflow se déclenche mais ne pousse pas l'archive | Permissions insuffisantes | Settings → Actions → General → Workflow permissions = "Read and write permissions" |

---

## 📜 À savoir

- Le filtrage est fait par IA — des faux positifs/négatifs sont possibles. Utilisez les boutons 👍 / 👎 en bas de la newsletter pour ajuster progressivement les critères.
- L'API Gemini est gratuite dans les limites du tier gratuit (très généreux pour ce cas d'usage).
- GitHub Actions offre 2 000 minutes/mois gratuites sur repo privé — largement plus qu'il n'en faut.
- Toutes les archives restent disponibles indéfiniment via GitHub Pages.

---

*Huginn — La pensée qui survole le monde.*
