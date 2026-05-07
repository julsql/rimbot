# Rimbot — Monorepo

Générateur de poèmes français aléatoires. Projet sous forme de monorepo : **API Flask** + **base PostgreSQL** seedée + **front React (Vite)**, le tout dockerisé et testé en CI (tests unitaires, intégration et e2e).

> [rimbot.julsql.fr](http://rimbot.julsql.fr)

## Sommaire

- [Architecture](#architecture)
- [Démarrage rapide (Docker)](#démarrage-rapide-docker)
- [Développement local](#développement-local)
- [Tests](#tests)
- [CI / CD](#ci--cd)
- [API](#api)
- [Régénérer le seed depuis le SQLite original](#régénérer-le-seed-depuis-le-sqlite-original)
- [Recalculer les syllabes des phrases](#recalculer-les-syllabes-des-phrases)

## Architecture

```
.
├── backend/              # API Flask (Python 3.12) + générateur
│   ├── app/
│   │   ├── routes/       # Blueprints HTTP (poem, help, health)
│   │   ├── services/     # Algorithme de génération
│   │   ├── db.py         # Pool psycopg
│   │   └── config.py
│   ├── tests/            # pytest
│   └── Dockerfile
├── frontend/             # SPA React (Vite) + nginx en prod
│   ├── src/
│   │   ├── pages/        # HomePage, HelpPage
│   │   ├── components/   # PoemForm, PoemDisplay
│   │   ├── api/          # client axios
│   │   └── __tests__/    # vitest + Testing Library
│   ├── cypress/e2e/      # tests e2e Cypress
│   └── Dockerfile
├── db/                   # Image Postgres avec seed automatique
│   ├── init/             # 01_schema.sql + 02_seed.sql + CSV
│   ├── scripts/          # export_from_sqlite.py, compute_syllabes.py
│   └── Dockerfile
├── docker-compose.yml
└── .github/workflows/    # CI/CD
```

## Démarrage rapide (Docker)

Pré-requis : Docker + Docker Compose v2.

```bash
cp .env.example .env       # facultatif (valeurs par défaut OK)
docker compose up --build
```

- Front : http://localhost:8080
- API   : http://localhost:5000/api/health
- DB    : `localhost:5432` (user/pwd/db = `rimbot`)

Le premier démarrage est plus long : Postgres exécute les scripts d'init et
charge ~143 000 lignes via `\copy`.

## Développement local

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL="postgresql://rimbot:rimbot@localhost:5432/rimbot"
python wsgi.py    # lance Flask en mode dev
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173 (proxy vers :5000 pour /api)
```

## Tests

### Backend (pytest)

Tests unitaires (sans base, faux pool de connexions) :

```bash
cd backend
pip install -r requirements-dev.txt
pytest -m "not integration"
```

Tests d'intégration (vraie Postgres seedée — par ex. celle du compose) :

```bash
DATABASE_URL=postgresql://rimbot:rimbot@localhost:5432/rimbot \
  pytest -m integration
```

### Frontend (vitest)

```bash
cd frontend
npm install
npm test
```

Tests basés sur Testing Library + jsdom. Les appels API sont mockés.

### Frontend (e2e Cypress)

Nécessite la stack lancée (`docker compose up`) :

```bash
cd frontend
npm install
CYPRESS_BASE_URL=http://localhost:8080 npm run test:e2e
```

## CI / CD

Cinq workflows GitHub Actions :

- **`backend.yml`** — pytest unitaires + intégration (avec service Postgres
  seedé) + build Docker.
- **`frontend.yml`** — vitest + `npm run build` + build Docker.
- **`e2e.yml`** — démarre la stack via docker-compose, exécute Cypress contre
  le front réel.
- **`release.yml`** — sur tag `v*.*.*`, build & push des trois images
  (`backend`, `frontend`, `db`) vers GHCR (`ghcr.io/<owner>/rimbot-*`).
- **`deploy.yml`** — sur push `main`, SSH vers le serveur, `git pull` puis
  rebuild **incrémental** + redémarrage de la stack docker-compose.
  Secrets requis : `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `DEPLOY_PATH`.

## API

Toutes les routes sont préfixées par `/api`.

| Méthode | Route                  | Description                                    |
|---------|------------------------|------------------------------------------------|
| GET     | `/api/health`          | Vérifie le pool DB.                            |
| GET     | `/api/help/syllables`  | Liste des syllabes utilisables comme rime.     |
| POST    | `/api/poem/preview`    | Aperçu de la forme et des contraintes saisies. |
| POST    | `/api/poem/generate`   | Génère le poème complet.                       |

Body JSON pour `preview` / `generate` :

```json
{
  "forme": "ABBA CDDC EEF GGF",
  "sylla": "1=12",
  "phone": "A=t@t,B=se"
}
```

Réponse `generate` :

```json
{ "poem": ["Vers 1.", "Vers 2.", "..."], "err1": "", "err2": "" }
```

## Régénérer le seed depuis le SQLite original

Le seed est versionné dans `db/init/seed/*.csv`. Pour le régénérer à partir
de `PoemeDB.sqlite3` :

```bash
python3 db/scripts/export_from_sqlite.py path/to/PoemeDB.sqlite3 db/init/seed
```

## Recalculer les syllabes des phrases

Lorsqu'on ajoute ou modifie des entrées dans `db/init/seed/phrases.csv`, le
champ `nbsyllabe` peut être laissé à `0` : le script
`db/scripts/compute_syllabes.py` le recalcule à partir de `mots.csv` en
sommant le `nbsyll` de chaque mot composant la phrase.

```bash
# Aperçu : affiche les écarts entre la valeur stockée et la valeur calculée,
# sans modifier le fichier.
python3 db/scripts/compute_syllabes.py --check

# Réécrit phrases.csv en place avec les valeurs calculées.
python3 db/scripts/compute_syllabes.py
```

Règles appliquées :

- Tokenisation par espaces ; les composés à tirets (`là-bas`, `peut-être`,
  `vois-tu`) sont d'abord cherchés tels quels dans `mots.csv`, puis
  décomposés en fallback si l'entrée composée est absente.
- Les apostrophes utiles dans un mot sont conservées (`Aujourd'hui`).
- Les particules d'élision écrites isolément selon la convention du seed
  (`L hiver`, `j aime`, `qu il`…) — soit `l`, `d`, `n`, `s`, `j`, `t`, `c`,
  `m`, `qu`, `jusqu`, `lorsqu`, `puisqu`, `presqu`, `quoiqu` — comptent **0
  syllabe**, car phonétiquement elles s'agglutinent au mot suivant.
- Les mots inconnus du dictionnaire sont signalés sur stderr (avec l'id et
  la phrase pour repérage manuel) et comptés 0 syllabe ; il faut alors
  corriger l'orthographe dans la phrase, ajouter le mot à `mots.csv`, ou
  l'inscrire dans le dictionnaire d'appoint `EXTRA_DICT` en tête du script
  (utile pour les noms propres : poètes, chanteurs, lieux).

> Note : le compte produit suit la prononciation standard (le `e` muet ne
> compte pas), pas la métrique poétique classique où le `e` muet devant
> consonne intérieure compte une syllabe. Les vers de Verlaine en
> 9 syllabes apparaissent donc en 8 dans `phrases.csv` — c'est le comportement
> attendu : le moteur de génération raisonne sur ce même dictionnaire.

## Auteurs

- Jul SQL
