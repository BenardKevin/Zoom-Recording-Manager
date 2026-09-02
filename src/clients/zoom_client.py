from typing import List

import requests

from src.config.logger import log_error, log_info
from src.config.settings import (
    API_TIMEOUT,
    BASE_ZOOM_URL,
)


class ZoomClient:

    def __init__(
        self,
        base_url: str = BASE_ZOOM_URL,
        timeout: int = API_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ==================================================================
    # HEADERS
    # ==================================================================

    @staticmethod
    def _get_headers(
        access_token: str,
    ) -> dict:

        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    # ==================================================================
    # RECORDINGS
    # ==================================================================

    def get_recordings(
        self,
        access_token: str,
        from_date: str,
        to_date: str,
    ) -> List[dict]:
        """
        Récupère toutes les réunions enregistrées
        sur une période donnée.

        Gère automatiquement la pagination Zoom.
        """

        endpoint = (
            f"{self.base_url}"
            "/accounts/me/recordings"
        )

        headers = self._get_headers(
            access_token
        )

        meetings = []

        next_page_token = None

        while True:

            params = {
                "from": from_date,
                "to": to_date,
                "page_size": 300,
            }

            if next_page_token:
                params["next_page_token"] = (
                    next_page_token
                )

            try:

                response = requests.get(
                    endpoint,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                )

            except requests.RequestException as exc:

                log_error(
                    f"Erreur réseau Zoom : {exc}",
                    exc_info=True,
                )

                raise

            if response.status_code != 200:

                log_error(
                    f"Erreur API Zoom "
                    f"{response.status_code} : "
                    f"{response.text}"
                )

                response.raise_for_status()

            data = response.json()

            page_meetings = data.get(
                "meetings",
                [],
            )

            meetings.extend(
                page_meetings
            )

            next_page_token = data.get(
                "next_page_token"
            )

            if not next_page_token:
                break

        return meetings

    # ==================================================================
    # DELETE
    # ==================================================================

    def delete_recording(
        self,
        access_token: str,
        recording_uuid: str,
        action: str = "trash",
    ) -> bool:

        import urllib.parse

        encoded_uuid = urllib.parse.quote(
            urllib.parse.quote(
                recording_uuid,
                safe="",
            ),
            safe="",
        )

        endpoint = (
            f"{self.base_url}"
            f"/meetings/{encoded_uuid}/recordings"
        )

        params = {
            "action": action
        }

        try:

            response = requests.delete(
                endpoint,
                headers=self._get_headers(
                    access_token
                ),
                params=params,
                timeout=self.timeout,
            )

        except requests.RequestException as exc:

            log_error(
                f"Erreur réseau lors de la "
                f"suppression Zoom : {exc}",
                exc_info=True,
            )

            return False

        if response.status_code in (200, 204):

            log_info(
                f"Enregistrement {recording_uuid} "
                f"supprimé de Zoom."
            )

            return True

        log_error(
            f"Échec suppression Zoom "
            f"{recording_uuid} : "
            f"{response.status_code} "
            f"{response.text}"
        )

        return False