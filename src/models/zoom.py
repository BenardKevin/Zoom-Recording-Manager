import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ==============================================================================
# CONFIGURATION
# ==============================================================================

LOG_DIR = Path(
    os.getenv("ZOOM_LOG_DIR", "logs")
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

LOG_LEVEL = os.getenv(
    "ZOOM_LOG_LEVEL",
    "INFO",
).upper()

LOG_FILE = LOG_DIR / "zoom_app.log"

LOGGER_NAME = "zoom_app"


# ==============================================================================
# LOGGER
# ==============================================================================

logger = logging.getLogger(LOGGER_NAME)


def _configure_logger() -> None:
    """Configure le logger principal de l'application."""

    if logger.handlers:
        return

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --------------------------------------------------------------------------
    # Console
    # --------------------------------------------------------------------------

    console_handler = logging.StreamHandler()

    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # --------------------------------------------------------------------------
    # Fichier
    # --------------------------------------------------------------------------

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.propagate = False


_configure_logger()


# ==============================================================================
# PUBLIC FUNCTIONS
# ==============================================================================

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


def log_debug(message: str) -> None:
    logger.debug(message)