# JobScrapper

**Agrégateur d'offres d'emploi — application desktop multi-sources**

[![Release](https://img.shields.io/github/v/release/Bono2007/JobScrapper?style=flat-square)](https://github.com/Bono2007/JobScrapper/releases)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey?style=flat-square)](#téléchargement)
[![Electron](https://img.shields.io/badge/Electron-28-47848F?style=flat-square&logo=electron)](https://www.electronjs.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

JobScrapper centralise toutes vos recherches d'emploi en un seul endroit. Il scrape simultanément **14 plateformes** françaises, déduplique les résultats et vous permet de gérer votre pipeline de candidatures directement depuis l'interface.

---

## Fonctionnalités

- **Multi-sources** — scrape 14 job boards en parallèle depuis une seule recherche
- **Résultats en temps réel** — progression par site affichée via Server-Sent Events
- **Gestion des candidatures** — statuts Nouveau / Vu / Intéressé / Rejeté
- **Corbeille** — archivez les offres non pertinentes, restaurez-les si besoin
- **Filtres dynamiques** — par site, par statut, recherche textuelle instantanée
- **Export CSV** — exportez vos offres filtrées (compatible Excel UTF-8)
- **Déduplication intelligente** — hash + matching flou (85% seuil) pour éviter les doublons
- **Mode sombre / clair** — thème persistant entre les sessions
- **100% local** — aucune donnée envoyée vers un serveur tiers, base SQLite locale
- **Anti-détection** — curl-cffi TLS fingerprinting + Playwright Stealth pour les sites protégés

---

## Captures d'écran

### Recherche
![Recherche](docs/screenshots/search.png)

Saisissez vos mots-clés, localisation, rayon et sélectionnez les sites à scraper.

### Résultats en direct
![Progression](docs/screenshots/progress.png)

La progression s'affiche en direct pendant le scraping, site par site.

### Gestion des offres
![Résultats](docs/screenshots/results.png)

Cards expansibles avec description, actions directes et sidebar de navigation par source.

### Mode clair
![Thème clair](docs/screenshots/light-theme.png)

---

## Sites supportés

| Site | Méthode | Notes |
|------|---------|-------|
| [APEC](https://www.apec.fr) | HTTP | Résolution géographique via autocomplete |
| [LinkedIn](https://www.linkedin.com/jobs) | Playwright | Scraping headless |
| [Indeed](https://fr.indeed.com) | curl-cffi | TLS fingerprinting |
| [Glassdoor](https://www.glassdoor.fr) | Playwright | Interception payload RSC |
| [Welcome to the Jungle](https://www.welcometothejungle.com) | Playwright | Interception Algolia |
| [France Travail](https://www.francetravail.fr) | HTTP | API officielle |
| [Cadremploi](https://www.cadremploi.fr) | HTTP | — |
| [Cadres Online](https://www.cadresonline.com) | HTTP | — |
| [HelloWork](https://www.hellowork.com) | HTTP | — |
| [Malt](https://www.malt.fr) | HTTP | Freelance / missions |
| [Monster](https://www.monster.fr) | HTTP | — |
| [Adzuna](https://www.adzuna.fr) | HTTP | — |
| [Jobijoba](https://www.jobijoba.com) | HTTP | — |
| [Wizbii](https://www.wizbii.com) | HTTP | — |

---

## Téléchargement

Rendez-vous sur la page [**Releases**](https://github.com/Bono2007/JobScrapper/releases) pour télécharger la dernière version.

| Plateforme | Fichier |
|------------|---------|
| macOS (Apple Silicon / Intel) | `JobScrapper-x.x.x-arm64.dmg` |
| Windows 11 | `JobScrapper Setup x.x.x.exe` |

### macOS — première ouverture

macOS peut afficher « l'application est endommagée » car elle n'est pas signée avec un certificat Apple. Pour l'ouvrir :

```bash
xattr -cr /Applications/JobScrapper.app
```

Puis double-cliquez normalement.

---

## Développement

### Prérequis

- [Node.js](https://nodejs.org/) ≥ 20
- [Python](https://www.python.org/) ≥ 3.12
- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets Python)
- [Playwright](https://playwright.dev/) navigateurs installés

### Installation

```bash
git clone https://github.com/Bono2007/JobScrapper.git
cd JobScrapper

# Dépendances Node
npm install

# Dépendances Python
cd python
uv sync
uv run playwright install chromium
cd ..
```

### Lancer en mode dev

```bash
npm run dev
```

Cela lance esbuild en mode watch et Electron simultanément.

### Lancer le backend seul (pour tester les scrapers)

```bash
cd python
uv run uvicorn src.api:app --reload --port 8000
```

Puis ouvrez `http://localhost:8000/docs` pour l'interface Swagger.

---

## Architecture

```
JobScrapper/
├── src/
│   ├── main/           # Electron main process
│   │   ├── index.js    # BrowserWindow, cycle de vie app
│   │   └── python.js   # Spawn du backend Python
│   ├── renderer/       # Interface utilisateur
│   │   ├── index.html
│   │   ├── style.css   # Thèmes dark/light (CSS variables)
│   │   └── tabs/       # search.js, results.js
│   └── preload.js      # Bridge IPC sécurisé
├── python/
│   └── src/
│       ├── api.py           # FastAPI endpoints
│       ├── scrapers/        # 14 scrapers
│       ├── models/          # JobOffer, SearchQuery, JobStatus
│       └── db/              # Repository SQLite
├── dist/                    # Bundle JS généré (gitignore)
├── resources/
│   └── python-dist/         # Binaires PyInstaller (gitignore)
└── .github/workflows/
    └── release.yml          # CI/CD Mac + Windows
```

**Flux de données :**

```
UI (Electron Renderer)
    ↕ HTTP (localhost)
FastAPI Backend (Python subprocess)
    ↕ Playwright / curl-cffi / httpx
14 Job Boards
    ↕
SQLite (~/Library/Application Support/JobScrapper)
```

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Desktop | Electron 28 |
| Bundler JS | esbuild |
| Packaging | electron-builder |
| Backend API | FastAPI + Uvicorn |
| HTTP scraping | curl-cffi, httpx |
| Browser scraping | Playwright + Stealth |
| HTML parsing | BeautifulSoup4, selectolax |
| Base de données | SQLite (stdlib) |
| Déduplication | thefuzz |
| Binaire Python | PyInstaller |
| CI/CD | GitHub Actions |

---

## Licence

MIT — voir [LICENSE](LICENSE)
