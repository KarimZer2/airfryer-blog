# Croustille & Cie — blog airfryer automatisé

Un blog statique qui publie automatiquement un article SEO de ~2500 mots par jour
sur la thématique des airfryers, avec insertion automatique de liens d'affiliation Amazon.

## Ce que fait le système

Chaque jour, à 8h (heure de Paris), GitHub Actions :
1. Prend le prochain sujet dans `config/topics.json` (comparatif, guide d'achat, recette, avis produit...)
2. Demande à Claude de rédiger un article complet de 2500 mots optimisé SEO (`generate_article.py`)
3. Insère automatiquement les bons liens Amazon avec ton tag d'affiliation (`build.py`)
4. Publie le site mis à jour sur GitHub Pages

Aucune intervention de ta part n'est nécessaire une fois que c'est branché.

## Mise en route (15-20 minutes, une seule fois)

### 1. Créer le dépôt GitHub
- Va sur github.com, crée un nouveau dépôt **public** nommé par exemple `airfryer-blog`
- Depuis ton terminal, dans ce dossier :
```bash
git init
git add .
git commit -m "Premier commit"
git branch -M main
git remote add origin https://github.com/TON-PSEUDO/airfryer-blog.git
git push -u origin main
```

### 2. Ajouter ta clé API Anthropic
- Crée une clé sur [console.anthropic.com](https://console.anthropic.com) (section API Keys)
- Dans ton dépôt GitHub : **Settings → Secrets and variables → Actions → New repository secret**
- Nom : `ANTHROPIC_API_KEY`, valeur : ta clé
- ⚠️ Ce n'est PAS le même compte que ton abonnement Claude.ai — il faut créer un compte API séparé et y ajouter du crédit (quelques euros suffisent pour des mois d'articles).

### 3. Activer GitHub Pages
- **Settings → Pages → Source → GitHub Actions**

### 4. Renseigner ton URL et ton tag Amazon
- Dans `build.py`, remplace `SITE_URL = "https://REMPLACE-MOI.github.io/airfryer-blog"` par ta vraie URL (`https://TON-PSEUDO.github.io/airfryer-blog`)
- Dans `config/products.json`, remplace `"amazon_tag": "REMPLACE-MOI-21"` par ton vrai tag Amazon Associates (tu l'auras une fois ton compte validé)
- Commit et push ces deux changements

### 5. Lancer le premier article manuellement
- Onglet **Actions** de ton dépôt → sélectionne "Publication quotidienne d'un article" → **Run workflow**
- Après 1-2 minutes, ton site est en ligne à `https://TON-PSEUDO.github.io/airfryer-blog`

C'est cette URL que tu donnes à Amazon Associates pour ta candidature (site web + éventuellement rien pour "applis mobiles").

## Pour aller plus loin

- **Ajouter des produits** : édite `config/products.json` (id, nom, ASIN Amazon, prix, points forts)
- **Ajouter des sujets d'articles** : ajoute des entrées dans `config/topics.json` avec `"statut": "en_attente"`
- **Changer l'heure de publication** : modifie la ligne `cron` dans `.github/workflows/daily-article.yml` (l'heure est en UTC)
- **Nom de domaine perso** : une fois que tu en as un, ajoute un fichier `static/CNAME` avec ton domaine dedans, et configure le DNS chez ton registrar

## Tester en local avant de pousser

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="ta-cle"
python generate_article.py   # génère un article
python build.py              # construit le site dans dist/
```

Ouvre ensuite `dist/index.html` dans ton navigateur pour prévisualiser.

## Important — mentions légales

Le footer inclut déjà la mention obligatoire Amazon Associates ("En tant que Partenaire Amazon...").
Pense aussi, une fois le trafic réel, à ajouter une page Mentions légales / Politique de confidentialité
(obligatoire en France pour tout site avec cookies/affiliation).
