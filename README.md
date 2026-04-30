# 🐦‍⬛ HUGINN — Bot de veille technologique ARQUUS

Bot OSINT automatisé qui collecte chaque semaine les actualités pertinentes de défense terrestre depuis des flux RSS, les filtre via IA, et les diffuse par mail à une liste de destinataires sous forme de revue visuelle. S'exécute automatiquement — ordi éteint, aucune action requise.

---

# 📖 PARTIE 1 — Utilisation au quotidien

Cette partie regroupe toutes les actions courantes qu'on peut faire sur le bot une fois qu'il est en place.

## 👥 Gérer les destinataires

Les destinataires sont stockés dans un secret GitHub pour ne pas exposer les adresses publiquement.

**Pour ajouter ou retirer un destinataire :**
1. Aller dans le repo GitHub → **Settings → Secrets and variables → Actions**
2. Onglet **"Secrets"** → trouver `RECIPIENTS` → cliquer ✏️ **Update**
3. Coller la nouvelle liste, **séparée par des virgules sans espaces** :
   ```
   prenom.nom@entreprise.com,collegue1@entreprise.com,collegue2@entreprise.com
   ```
4. **Update secret**

> Le changement est pris en compte au prochain envoi. Pas besoin de toucher au code.

---

## 📰 Modifier les sources RSS suivies

**Pour ajouter ou retirer une source :**
1. Aller dans `config/sources.txt` sur GitHub
2. Cliquer ✏️ pour éditer
3. **Une URL par ligne**. Les lignes commençant par `#` sont des commentaires (ignorées).
4. Commit

**Exemple de fichier :**
```
# Sources principales
https://breakingdefense.com/feed/
https://militaryleak.com/feed/
https://army-technology.com/feed/

# Sources Ukraine
https://kyivindependent.com/tag/war/feed/

# Source désactivée temporairement
# https://defensenews.com/arc/outboundfeeds/rss/
```

> Pour vérifier qu'un flux RSS fonctionne, copier l'URL dans un navigateur — si du XML s'affiche, c'est bon.

---

## 🎯 Ajuster les critères de filtrage (thèmes, mots-clés)

C'est ce qui définit quels articles sont retenus par l'IA. Le fichier `config/criteria.md` contient :
- Les **domaines à inclure** (mots-clés positifs)
- Les **domaines à exclure** absolument
- Le **contexte ARQUUS** que l'IA utilise pour juger la pertinence

**Pour modifier :**
1. Aller dans `config/criteria.md` sur GitHub
2. Cliquer ✏️ pour éditer
3. Ajouter ou retirer des mots-clés dans les sections existantes (ou créer de nouvelles sections)
4. Commit

**Exemples concrets :**

*Ajouter un nouveau thème* :
```markdown
### Robotique militaire avancée
Robot terrestre, robot tactique, robot de combat, swarm robotics, 
intelligence artificielle militaire, autonomie de niveau 4.
```

*Exclure un sujet* :
```markdown
- **Drones de surveillance civile** : drones agricoles, drones de loisirs
```

> Plus les mots-clés sont précis et nombreux, meilleur sera le filtrage.

---

## ⏰ Modifier le jour ou l'heure d'envoi

Le bot est déclenché par un service externe **cron-job.org** (compte gratuit).

1. Aller sur **https://cron-job.org** et se connecter
2. Trouver le job `HUGINN` → cliquer dessus
3. Onglet **"Schedule"** → modifier le jour et l'heure
4. **Save**

> ⚠️ Les heures sur cron-job.org sont en **UTC**.
> - Paris en été = UTC+2 → soustraire 2h. Exemple : lundi 8h Paris → lundi 6h UTC
> - Paris en hiver = UTC+1 → soustraire 1h. Exemple : lundi 8h Paris → lundi 7h UTC

---

## ▶️ Déclencher un envoi manuel

Pour envoyer la revue immédiatement (test, vérification, rattrapage) :

1. Aller dans **Actions → Revue Huginn — envoi hebdomadaire**
2. Bouton **Run workflow** (à droite) → confirmer **Run workflow**
3. Patienter 2-3 min, le mail arrive après

---

## 🗑️ Gérer les éditions archivées

Le numéro d'édition est calculé automatiquement à partir du nombre de fichiers présents dans `docs/editions/`.

### Réinitialiser le compteur (exemple : repartir à N°3)

1. Aller dans `docs/editions/` sur GitHub
2. Identifier les **deux éditions à conserver** (futures N°1 et N°2)
3. Supprimer toutes les autres :
   - Le plus rapide : utiliser **GitHub Desktop** pour tout supprimer en local et pousser en un seul commit
   - Sinon : ouvrir chaque fichier sur GitHub → 🗑️ → commit
4. Renommer les deux éditions conservées :
   - La plus ancienne → `YYYY-MM-DD-edition-001.html`
   - La seconde → `YYYY-MM-DD-edition-002.html`
5. Supprimer `docs/index.html` (sera régénéré)
6. **Actions → Run workflow** → la prochaine édition sera **N°003**

### Tout réinitialiser

1. Supprimer tout le contenu de `docs/editions/`
2. Supprimer `docs/index.html`
3. La prochaine édition sera **N°001**

---

## 📧 Changer l'adresse mail d'envoi

1. **Settings → Secrets and variables → Actions → Secrets**
2. Modifier les secrets concernés :
   - `SMTP_USER` : nouvelle adresse mail
   - `SMTP_PASSWORD` : mot de passe d'application correspondant
   - `SMTP_HOST` : `smtp.gmail.com` (Gmail) ou `smtp.office365.com` (Outlook entreprise)

> Pour Outlook entreprise, demander à l'IT le serveur SMTP autorisé et générer un mot de passe d'application via le portail Microsoft 365.

---

## 🛟 Dépannage rapide

| Problème | Solution |
|---|---|
| Aucun mail reçu cette semaine | Vérifier dans **Actions** que le workflow s'est bien lancé. Si pas de run, vérifier cron-job.org. |
| Couleurs cassées dans Outlook | Outlook en mode sombre. Fichier → Options → Général → cocher "Ne jamais modifier la couleur des messages" |
| Images non affichées dans le mail | Ajouter l'expéditeur aux contacts du destinataire (Outlook le fait automatiquement après le 1er mail) |
| Tous les articles d'une seule source | Les autres flux RSS sont peut-être cassés. Vérifier les logs du dernier run dans Actions. |
| "Quota exceeded" Gemini | Trop de tests manuels dans la journée. Attendre la réinitialisation à minuit Pacific (~9h Paris). |
| Page d'archive cassée | Supprimer `docs/index.html` et relancer le workflow |
| Mode sombre Outlook modifie les couleurs | Fichier → Options → Général → cocher "Ne jamais modifier la couleur des messages" |

---

# 🛠️ PARTIE 2 — Installation & déploiement

Cette partie est à suivre **une seule fois**, lors du premier déploiement du bot.

## 🗂 Structure du projet

```
huginn-newsletter/
├── .github/workflows/newsletter.yml    # Workflow GitHub Actions
├── src/
│   ├── main.py                         # Orchestrateur
│   ├── rss.py                          # Collecte RSS + extraction og:image
│   ├── llm.py                          # Filtrage Gemini
│   ├── renderer.py                     # Rendu HTML Jinja2
│   ├── mailer.py                       # Envoi SMTP (To groupé)
│   └── archiver.py                     # Archives GitHub Pages
├── templates/
│   ├── newsletter.html                 # Template du mail
│   └── archive_index.html              # Page d'archive web
├── config/
│   ├── sources.txt                     # Flux RSS suivis
│   ├── recipients.txt                  # (vide — destinataires dans le secret)
│   └── criteria.md                     # Critères de filtrage ARQUUS
├── docs/
│   ├── index.html                      # Page d'archive (auto-générée)
│   ├── editions/                       # Éditions archivées
│   └── assets/                         # Logos
├── requirements.txt
└── README.md
```

## ⚙️ Architecture

```
cron-job.org ──► GitHub Actions ──► RSS sources
                      │                    │
                      │              Gemini IA (filtrage + traduction FR)
                      │                    │
                      └──► SMTP ──► Destinataires
                      └──► GitHub Pages ──► Archives web
```

**Coût total : 0 €** — tout repose sur des tiers gratuits (cron-job.org, GitHub Actions, Gemini tier gratuit, SMTP).

---

## 🚀 Installation pas-à-pas

### Étape 1 — Cloner le repo

Utiliser **GitHub Desktop** (File → Clone repository) ou en ligne de commande :

```bash
git clone https://github.com/votre-username/huginn-newsletter.git
```

### Étape 2 — Obtenir une clé API Gemini (gratuite)

1. Aller sur **https://aistudio.google.com/apikey**
2. Se connecter avec un compte Google
3. **Create API Key** → **Create API key in new project**
4. Copier la clé (commence par `AIza...`)

### Étape 3 — Générer un mot de passe d'application mail

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
| `SMTP_HOST` | `smtp.gmail.com` ou `smtp.office365.com` |
| `RECIPIENTS` | Destinataires séparés par des virgules |

**Onglet "Variables"** :

| Nom | Valeur |
|---|---|
| `GH_PAGES_URL` | URL GitHub Pages sans slash final |

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

GitHub Actions est peu fiable pour les crons sur les repos peu actifs. On utilise **cron-job.org** (gratuit) pour déclencher le bot à heure fixe.

**8.1 — Personal Access Token GitHub**
1. Avatar → **Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. **Generate new token** → Cocher uniquement **`workflow`**
3. Copier le token (commence par `ghp_...`)

**8.2 — Job sur cron-job.org**
1. Créer un compte sur **https://cron-job.org**
2. **Create cronjob** :
   - **Title** : `HUGINN`
   - **URL** : `https://api.github.com/repos/VOTRE-USERNAME/huginn-newsletter/actions/workflows/newsletter.yml/dispatches`
   - **Schedule** : jour et heure souhaités
3. Onglet **Advanced** :
   - **Method** : `POST`
   - **Body** : `{"ref":"main"}`
   - **Headers** :
     - `Authorization` : `Bearer ghp_VOTRE_TOKEN`
     - `Content-Type` : `application/json`
4. Tester avec **Run now**

---

## 📜 Notes techniques

- Le filtrage est réalisé par IA Gemini (modèle `gemini-3.1-flash-lite-preview` en principal)
- L'API Gemini est utilisée sur le tier gratuit (1 requête par run = largement suffisant)
- GitHub Actions offre 2 000 minutes/mois gratuites — largement suffisant
- Toutes les archives sont disponibles indéfiniment via GitHub Pages
- Les boutons 👍 / ✉ Contactez-nous dans le mail permettent de remonter du feedback

---

*Huginn — La pensée qui survole le monde.*
