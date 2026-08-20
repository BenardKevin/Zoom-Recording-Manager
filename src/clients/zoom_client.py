import time
from typing import Any, Optional
from urllib.parse import quote

import requests

from src.config.logger import log_error, log_info, log_warning
from src.config.settings import (
    API_MAX_RETRIES,
    API_PAGE_SIZE,
    API_RETRY_DELAY,
    API_TIMEOUT,
    BASE_ZOOM_URL,
    ZOOM_OAUTH_URL,
)


class ZoomAPIError(Exception):
    """Erreur générique de l'API Zoom."""


class ZoomAuthenticationError(ZoomAPIError):
    """Erreur d'authentification Zoom."""


class ZoomRateLimitError(ZoomAPIError):
    """Limite API Zoom atteinte."""


class ZoomClient:
    """Client HTTP dédié à l'API Zoom."""

    def __init__(
        self,
        access_token: str,
        timeout: int = API_TIMEOUT,
    ):
        self.access_token = access_token
        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    # =========================================================================
    # HTTP
    # =========================================================================

    def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:

        for attempt in range(1, API_MAX_RETRIES + 1):

            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs,
                )

            except requests.exceptions.Timeout as exc:

                log_warning(
                    f"Timeout API Zoom "
                    f"(tentative {attempt}/{API_MAX_RETRIES})"
                )

                if attempt == API_MAX_RETRIES:
                    raise ZoomAPIError(
                        "Timeout lors de la communication avec Zoom."
                    ) from exc

                time.sleep(API_RETRY_DELAY * attempt)
                continue

            except requests.exceptions.ConnectionError as exc:

                log_warning(
                    f"Erreur de connexion Zoom "
                    f"(tentative {attempt}/{API_MAX_RETRIES})"
                )

                if attempt == API_MAX_RETRIES:
                    raise ZoomAPIError(
                        "Impossible de contacter l'API Zoom."
                    ) from exc

                time.sleep(API_RETRY_DELAY * attempt)
                continue

            except requests.exceptions.RequestException as exc:

                raise ZoomAPIError(
                    f"Erreur HTTP Zoom : {exc}"
                ) from exc

            # =================================================================
            # RATE LIMIT
            # =================================================================

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After",
                    API_RETRY_DELAY * attempt,
                )

                try:
                    retry_after = float(retry_after)
                except ValueError:
                    retry_after = API_RETRY_DELAY * attempt

                log_warning(
                    f"Rate limit Zoom atteint. "
                    f"Nouvelle tentative dans {retry_after}s."
                )

                if attempt == API_MAX_RETRIES:
                    raise ZoomRateLimitError(
                        "Limite de requêtes Zoom atteinte."
                    )

                time.sleep(retry_after)
                continue

            # =================================================================
            # AUTHENTICATION
            # =================================================================

            if response.status_code in (401, 403):

                raise ZoomAuthenticationError(
                    f"Authentification Zoom refusée "
                    f"({response.status_code})."
                )

            # =================================================================
            # SERVER ERRORS
            # =================================================================

            if response.status_code >= 500:

                log_warning(
                    f"Erreur serveur Zoom {response.status_code} "
                    f"(tentative {attempt}/{API_MAX_RETRIES})"
                )

                if attempt == API_MAX_RETRIES:
                    raise ZoomAPIError(
                        f"Erreur serveur Zoom : {response.status_code}"
                    )

                time.sleep(API_RETRY_DELAY * attempt)
                continue

            return response

        raise ZoomAPIError("Nombre maximum de tentatives atteint.")

    # =========================================================================
    # RECORDINGS
    # =========================================================================

    def get_recordings(
        self,
        from_date: str,
        to_date: str,
    ) -> list[dict]:

        endpoint = f"{BASE_ZOOM_URL}/accounts/me/recordings"

        recordings: list[dict] = []
        next_page_token: Optional[str] = None

        while True:

            params = {
                "from": from_date,
                "to": to_date,
                "page_size": API_PAGE_SIZE,
            }

            if next_page_token:
                params["next_page_token"] = next_page_token

            response = self._request(
                "GET",
                endpoint,
                params=params,
            )

            if response.status_code != 200:

                raise ZoomAPIError(
                    f"Erreur récupération recordings "
                    f"({response.status_code}) : {response.text}"
                )

            try:
                data = response.json()
            except ValueError as exc:
                raise ZoomAPIError(
                    "Réponse JSON invalide reçue de Zoom."
                ) from exc

            page_recordings = data.get("meetings", [])

            recordings.extend(page_recordings)

            log_info(
                f"Zoom : {len(page_recordings)} enregistrement(s) "
                f"récupéré(s) pour {from_date} → {to_date}."
            )

            next_page_token = data.get("next_page_token")

            if not next_page_token:
                break

        return recordings

    # =========================================================================
    # DELETE
    # =========================================================================

    def delete_recording(
        self,
        recording_uuid: str,
        action: str = "trash",
    ) -> bool:

        if action not in {"trash", "delete"}:
            raise ValueError(
                "action doit être 'trash' ou 'delete'."
            )

        # Zoom utilise un UUID pouvant contenir des /
        encoded_uuid = quote(
            quote(recording_uuid, safe=""),
            safe="",
        )

        endpoint = (
            f"{BASE_ZOOM_URL}/meetings/"
            f"{encoded_uuid}/recordings"
        )

        response = self._request(
            "DELETE",
            endpoint,
            params={"action": action},
        )

        if response.status_code in (200, 204):

            log_info(
                f"Recording Zoom supprimé : {recording_uuid}"
            )

            return True

        log_warning(
            f"Suppression Zoom échouée : "
            f"{recording_uuid} "
            f"({response.status_code}) - "
            f"{response.text}"
        )

        return False


# =============================================================================
# OAuth helper
# =============================================================================

def request_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> dict:

    response = requests.post(
        ZOOM_OAUTH_URL,
        auth=(client_id, client_secret),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=API_TIMEOUT,
    )

    if response.status_code != 200:

        raise ZoomAuthenticationError(
            f"Impossible de renouveler le token Zoom "
            f"({response.status_code})."
        )

    try:
        return response.json()

    except ValueError as exc:

        raise ZoomAuthenticationError(
            "Zoom a renvoyé une réponse OAuth invalide."
        ) from exc