from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from datetime import datetime, timedelta

import streamlit as st

from src.clients.zoom_client import (
    ZoomAPIError,
    ZoomAuthenticationError,
    ZoomClient,
)
from src.config.logger import log_error, log_info
from src.config.settings import (
    MAX_WORKERS,
    SYNC_INTERVAL_DAYS,
)
from src.models.recording import Recording
from src.repositories.recording_repository import (
    RecordingRepository,
)
from src.services.auth_service import AuthService


class ZoomService:
    """Logique métier liée aux enregistrements Zoom."""

    def __init__(
        self,
        auth_service: AuthService,
        repository: RecordingRepository,
    ):

        self.auth_service = auth_service
        self.repository = repository

    # =========================================================================
    # CLIENT
    # =========================================================================

    def _get_client(self) -> ZoomClient | None:

        token = self.auth_service.get_access_token()

        if not token:
            return None

        return ZoomClient(token)

    # =========================================================================
    # DATE RANGES
    # =========================================================================

    @staticmethod
    def _build_date_ranges(
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[str, str]]:

        ranges = []

        current_start = start_date

        while current_start < end_date:

            current_end = min(
                current_start
                + timedelta(days=SYNC_INTERVAL_DAYS - 1),
                end_date,
            )

            ranges.append(
                (
                    current_start.strftime(
                        "%Y-%m-%d"
                    ),
                    current_end.strftime(
                        "%Y-%m-%d"
                    ),
                )
            )

            current_start = (
                current_end
                + timedelta(days=1)
            )

        return ranges

    # =========================================================================
    # SINGLE RANGE
    # =========================================================================

    def _fetch_range(
        self,
        client: ZoomClient,
        date_range: tuple[str, str],
    ) -> list[Recording]:

        from_date, to_date = date_range

        raw_recordings = client.get_recordings(
            from_date,
            to_date,
        )

        recordings = []

        for raw in raw_recordings:

            try:

                recording = Recording.from_zoom_data(
                    raw
                )

                if recording.uuid:
                    recordings.append(
                        recording
                    )

            except (ValueError, TypeError, KeyError) as exc:

                log_error(
                    f"Enregistrement Zoom invalide : "
                    f"{exc}"
                )

        return recordings

    # =========================================================================
    # SYNC
    # =========================================================================

    def sync_recordings(
        self,
        from_date: str,
        max_workers: int = MAX_WORKERS,
    ) -> int:

        try:

            start_dt = datetime.strptime(
                from_date,
                "%Y-%m-%d",
            )

        except ValueError:

            raise ValueError(
                "La date doit être au format YYYY-MM-DD."
            )

        end_dt = datetime.now()

        if start_dt > end_dt:
            raise ValueError(
                "La date de début ne peut pas être "
                "dans le futur."
            )

        client = self._get_client()

        if not client:
            return 0

        date_ranges = self._build_date_ranges(
            start_dt,
            end_dt,
        )

        if not date_ranges:
            return 0

        all_recordings: list[Recording] = []

        log_info(
            f"Synchronisation Zoom : "
            f"{from_date} → "
            f"{end_dt.strftime('%Y-%m-%d')}"
        )

        # =====================================================================
        # PARALLEL REQUESTS
        # =====================================================================

        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:

            future_map = {
                executor.submit(
                    self._fetch_range,
                    client,
                    date_range,
                ): date_range
                for date_range in date_ranges
            }

            for future in as_completed(
                future_map
            ):

                date_range = future_map[future]

                try:

                    recordings = future.result()

                    all_recordings.extend(
                        recordings
                    )

                except ZoomAuthenticationError as exc:

                    log_error(
                        f"Authentification Zoom échouée "
                        f"pour {date_range}: {exc}"
                    )

                except ZoomAPIError as exc:

                    log_error(
                        f"Erreur API Zoom "
                        f"pour {date_range}: {exc}"
                    )

                except Exception as exc:

                    log_error(
                        f"Erreur inattendue "
                        f"pour {date_range}: {exc}",
                        exc_info=True,
                    )

        # =====================================================================
        # DEDUPLICATION
        # =====================================================================

        unique_recordings = {
            recording.uuid: recording
            for recording in all_recordings
        }

        recordings = list(
            unique_recordings.values()
        )

        if not recordings:

            log_info(
                "Aucun nouvel enregistrement trouvé."
            )

            return 0

        # =====================================================================
        # DATABASE
        # =====================================================================

        saved_count = (
            self.repository.save_recordings(
                recordings
            )
        )

        log_info(
            f"Synchronisation terminée : "
            f"{saved_count} enregistrement(s)."
        )

        return saved_count

    # =========================================================================
    # DELETE
    # =========================================================================

    def delete_recording(
        self,
        recording_uuid: str,
        action: str = "trash",
    ) -> bool:

        client = self._get_client()

        if not client:
            return False

        try:

            success = client.delete_recording(
                recording_uuid,
                action,
            )

            if not success:
                return False

            # On supprime seulement après succès Zoom
            self.repository.delete_recording(
                recording_uuid
            )

            return True

        except ZoomAPIError as exc:

            log_error(
                f"Erreur suppression Zoom : {exc}"
            )

            return False