import os
from pathlib import Path

from dotenv import load_dotenv


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

ENV_FILE = BASE_DIR / ".env"
DB_FILE = BASE_DIR / "zoom_recordings.db"
LOG_DIR = BASE_DIR / "logs"


# =============================================================================
# ENVIRONMENT
# =============================================================================

load_dotenv(ENV_FILE)


# =============================================================================
# ZOOM API
# =============================================================================

BASE_ZOOM_URL = "https://api.zoom.us/v2"
ZOOM_OAUTH_URL = "https://zoom.us/oauth/token"


# =============================================================================
# API CONFIGURATION
# =============================================================================

API_TIMEOUT = 15

# Nombre maximum de tentatives après une erreur temporaire
API_MAX_RETRIES = 3

# Délai initial entre les retries
API_RETRY_DELAY = 1.0

# Nombre de résultats Zoom par page
API_PAGE_SIZE = 300

# Nombre de requêtes parallèles maximum
MAX_WORKERS = 5


# =============================================================================
# TOKEN
# =============================================================================

# Zoom fournit généralement un access token valable environ 1 heure.
# On garde une marge de sécurité.
TOKEN_CACHE_TTL_SECONDS = 3300


# =============================================================================
# SYNCHRONISATION
# =============================================================================

SYNC_INTERVAL_DAYS = 30


# =============================================================================
# APPLICATION
# =============================================================================

DEFAULT_QUOTA_GB = 532.5

DEFAULT_HISTORY_START_DATE = "2024-01-01"


# =============================================================================
# ENV CREDENTIALS
# =============================================================================

def get_env_credentials() -> tuple[str, str, str]:
    """Récupère les credentials Zoom depuis les variables d'environnement."""

    client_id = os.getenv("ZOOM_CLIENT_ID", "").strip()
    client_secret = os.getenv("ZOOM_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("ZOOM_REFRESH_TOKEN", "").strip()

    return client_id, client_secret, refresh_token