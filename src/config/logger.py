import logging
from pathlib import Path

from src.config.settings import LOG_DIR


LOG_DIR.mkdir(parents=True, exist_ok=True)


LOG_FILE = LOG_DIR / "application.log"


# =============================================================================
# LOGGER
# =============================================================================

logger = logging.getLogger("zoom_storage_manager")

logger.setLevel(logging.INFO)

if not logger.handlers:

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Fichier
    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


# =============================================================================
# HELPERS
# =============================================================================

def log_info(message: str) -> None:
    logger.info(message)


def log_warning(message: str) -> None:
    logger.warning(message)


def log_error(
    message: str,
    exc_info: bool = False,
) -> None:
    logger.error(
        message,
        exc_info=exc_info,
    )