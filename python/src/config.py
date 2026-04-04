import sys
from pathlib import Path

# En mode PyInstaller (frozen), le binaire extrait dans un dossier temp.
# On place jobs.db à côté du binaire lancé, pas dans le dossier temp.
if getattr(sys, "frozen", False):
    _ROOT = Path(sys.executable).parent
else:
    _ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = _ROOT / "data"
DB_PATH = DATA_DIR / "jobs.db"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 2.0
MAX_RETRIES = 3
FUZZY_DEDUP_THRESHOLD = 85
