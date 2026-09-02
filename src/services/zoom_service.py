from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List

from src.clients.zoom_client import ZoomClient
from src.config.logger import log_error, log_info
from src.config.settings import SYNC_INTERVAL_DAYS
from src.repositories.recording_repository import RecordingRepository
from src.services.auth_service import AuthService


class ZoomService:
    """
    Service métier responsable de la gestion des enregistrements Zoom.

    Architecture :

        View
          ↓
        ZoomService
        ↙        ↘
    AuthService  ZoomClient
                    ↓
                  Zoom API

        ZoomService
              ↓
        RecordingRepository
              ↓
            SQLite
    """

    def __init__(
        self,
        auth_service: AuthService,
        zoom_client: ZoomClient,
        repository: RecordingRepository,
    ):
        self.auth_service = auth_service
        self.zoom_client = zoom_client
        self.repository = repository

    # ==================================================================
    # AUTHENTIFICATION
    # ==================================================================

    def set_credentials(
        self,
        client_id: str,
        client_secret: str,
    ) -> None:
        """
        Met à jour les credentials Zoom utilisés pour la session.
        """

        self.auth_service.set_credentials(
            client_id=client_id,
            client_secret=client_secret,
        )

    def _get_access_token(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> str:

        if client_id and client_secret:
            self.auth_service.set_credentials(
                client_id,
                client_secret,
            )

        access_token = self.auth_service.get_access_token()

        if not access_token:
            raise RuntimeError(
                "Impossible d'obtenir un token Zoom."
            )

        return access_token

    # ==================================================================
    # SYNCHRONISATION
    # ==================================================================

    def sync_recordings(
        self,
        from_date: str,
        client_id: str | None = None,
        client_secret: str | None = None,
        max_workers: int = 5,
    ) -> str:
        """
        Synchronise les enregistrements Zoom avec la BDD locale.

        Args:
            from_date:
                Date de début au format YYYY-MM-DD.

            max_workers:
                Nombre maximum de requêtes parallèles.

        Returns:
            Nombre d'enregistrements sauvegardés.
        """

        log_info(
            f"Synchronisation Zoom demandée depuis le {from_date}."
        )

        # --------------------------------------------------------------
        # 1. Validation de la date
        # --------------------------------------------------------------

        try:
            start_dt = datetime.strptime(
                from_date,
                "%Y-%m-%d",
            )

        except ValueError as exc:
            raise ValueError(
                "Format de date invalide. "
                "Le format attendu est YYYY-MM-DD."
            ) from exc

        # --------------------------------------------------------------
        # 2. Authentification
        # --------------------------------------------------------------

        access_token = self._get_access_token()

        # --------------------------------------------------------------
        # 3. Construction des périodes
        # --------------------------------------------------------------

        end_dt = datetime.now()

        date_ranges = []

        current_start = start_dt

        while current_start < end_dt:

            current_end = min(
                current_start
                + timedelta(days=SYNC_INTERVAL_DAYS),
                end_dt,
            )

            date_ranges.append(
                (
                    current_start.strftime("%Y-%m-%d"),
                    current_end.strftime("%Y-%m-%d"),
                )
            )

            current_start = (
                current_end + timedelta(days=1)
            )

        log_info(
            f"{len(date_ranges)} période(s) "
            "à synchroniser."
        )

        # --------------------------------------------------------------
        # 4. Récupération parallèle
        # --------------------------------------------------------------

        all_meetings: List[dict] = []

        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:

            futures = {
                executor.submit(
                    self.zoom_client.get_recordings,
                    access_token,
                    from_str,
                    to_str,
                ): (
                    from_str,
                    to_str,
                )
                for from_str, to_str in date_ranges
            }

            for future in as_completed(futures):

                from_str, to_str = futures[future]

                try:

                    meetings = future.result()

                    all_meetings.extend(
                        meetings
                    )

                    log_info(
                        f"Période {from_str} → {to_str} : "
                        f"{len(meetings)} enregistrement(s)."
                    )

                except Exception as exc:

                    log_error(
                        f"Erreur période "
                        f"{from_str} → {to_str} : {exc}",
                        exc_info=True,
                    )

        # --------------------------------------------------------------
        # 5. Aucun résultat
        # --------------------------------------------------------------

        if not all_meetings:

            log_info(
                "Aucun enregistrement Zoom trouvé."
            )

            return 0

        # --------------------------------------------------------------
        # 6. Sauvegarde en une transaction
        # --------------------------------------------------------------

        try:

            saved_count = (
                self.repository.save_recordings(
                    all_meetings
                )
            )

        except Exception as exc:

            log_error(
                "Échec de la sauvegarde des "
                f"enregistrements : {exc}",
                exc_info=True,
            )

            raise

        log_info(
            "Synchronisation terminée : "
            f"{saved_count} enregistrement(s) sauvegardé(s)."
        )

        return saved_count

    # ==================================================================
    # SUPPRESSION
    # ==================================================================

    def delete_recording(
        self,
        recording_uuid: str,
    ) -> bool:
        """
        Supprime un enregistrement de Zoom puis de SQLite.
        """

        try:

            access_token = self._get_access_token()

        except Exception as exc:

            log_error(
                f"Impossible de supprimer "
                f"{recording_uuid} : {exc}",
                exc_info=True,
            )

            return False

        # --------------------------------------------------------------
        # 1. Suppression côté Zoom
        # --------------------------------------------------------------

        try:

            success = (
                self.zoom_client.delete_recording(
                    access_token=access_token,
                    recording_uuid=recording_uuid,
                )
            )

        except Exception as exc:

            log_error(
                f"Erreur suppression Zoom "
                f"{recording_uuid} : {exc}",
                exc_info=True,
            )

            return False

        if not success:
            return False

        # --------------------------------------------------------------
        # 2. Suppression côté SQLite
        # --------------------------------------------------------------

        deleted = (
            self.repository.delete_recording(
                recording_uuid
            )
        )

        if not deleted:

            log_error(
                f"Enregistrement {recording_uuid} "
                "supprimé de Zoom mais absent "
                "de la BDD locale."
            )

            return False

        log_info(
            f"Enregistrement {recording_uuid} "
            "supprimé de Zoom et de la BDD."
        )

        return True