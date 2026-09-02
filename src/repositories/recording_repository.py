import json
from datetime import date
from typing import Optional

import pandas as pd

from src.config.logger import log_error, log_info
from src.config.settings import DB_FILE


class RecordingRepository:
    """
    Repository responsable de l'accès aux données locales SQLite.

    Le repository ne contient aucune logique Zoom/API.
    Il est uniquement responsable de la persistance des recordings.
    """

    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file

    # ==================================================================
    # INITIALISATION
    # ==================================================================

    def init_db(self) -> None:
        """Crée la table recordings si elle n'existe pas."""

        import sqlite3

        try:
            with sqlite3.connect(self.db_file) as conn:

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS recordings (
                        uuid TEXT PRIMARY KEY,
                        meeting_id INTEGER,
                        topic TEXT,
                        start_time TEXT,
                        duration INTEGER,
                        total_size INTEGER,
                        file_count INTEGER,
                        share_url TEXT,
                        raw_data TEXT
                    )
                    """
                )

                conn.commit()

        except sqlite3.Error as exc:

            log_error(
                f"Erreur d'initialisation BDD : {exc}",
                exc_info=True,
            )

            raise

    # ==================================================================
    # SAVE
    # ==================================================================

    def save_recording(
        self,
        meeting_data: dict,
    ) -> None:
        """Insère ou met à jour un enregistrement."""

        import sqlite3

        try:

            with sqlite3.connect(self.db_file) as conn:

                conn.execute(
                    """
                    INSERT OR REPLACE INTO recordings
                    (
                        uuid,
                        meeting_id,
                        topic,
                        start_time,
                        duration,
                        total_size,
                        file_count,
                        share_url,
                        raw_data
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        meeting_data["uuid"],
                        meeting_data["id"],
                        meeting_data.get("topic", ""),
                        meeting_data["start_time"],
                        meeting_data.get("duration", 0),
                        meeting_data.get("total_size", 0),
                        meeting_data.get("recording_count", 0),
                        meeting_data.get("share_url", ""),
                        json.dumps(
                            meeting_data,
                            ensure_ascii=False,
                        ),
                    ),
                )

                conn.commit()

        except sqlite3.Error as exc:

            log_error(
                f"Erreur de sauvegarde recording : {exc}",
                exc_info=True,
            )

            raise

    # ==================================================================
    # SAVE MANY
    # ==================================================================

    def save_recordings(
        self,
        meetings: list[dict],
    ) -> int:
        """
        Sauvegarde plusieurs enregistrements dans une transaction.

        Returns:
            Nombre d'enregistrements sauvegardés.
        """

        import sqlite3

        if not meetings:
            return 0

        try:

            records = [
                (
                    meeting["uuid"],
                    meeting["id"],
                    meeting.get("topic", ""),
                    meeting["start_time"],
                    meeting.get("duration", 0),
                    meeting.get("total_size", 0),
                    meeting.get("recording_count", 0),
                    meeting.get("share_url", ""),
                    json.dumps(
                        meeting,
                        ensure_ascii=False,
                    ),
                )
                for meeting in meetings
            ]

            with sqlite3.connect(self.db_file) as conn:

                conn.executemany(
                    """
                    INSERT OR REPLACE INTO recordings
                    (
                        uuid,
                        meeting_id,
                        topic,
                        start_time,
                        duration,
                        total_size,
                        file_count,
                        share_url,
                        raw_data
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    records,
                )

                conn.commit()

            log_info(
                f"{len(records)} enregistrement(s) sauvegardé(s)."
            )

            return len(records)

        except sqlite3.Error as exc:

            log_error(
                f"Erreur de sauvegarde multiple : {exc}",
                exc_info=True,
            )

            raise

    # ==================================================================
    # LOAD
    # ==================================================================

    def load_recordings(self) -> pd.DataFrame:
        """
        Charge tous les enregistrements locaux.

        Returns:
            DataFrame contenant les recordings.
        """

        import sqlite3

        try:

            with sqlite3.connect(self.db_file) as conn:

                df = pd.read_sql_query(
                    """
                    SELECT *
                    FROM recordings
                    """,
                    conn,
                )

            if df.empty:
                return df

            # ----------------------------------------------------------
            # Conversion date
            # ----------------------------------------------------------

            df["start_time"] = pd.to_datetime(
                df["start_time"],
                errors="coerce",
            )

            # ----------------------------------------------------------
            # Taille MB
            # ----------------------------------------------------------

            df["size_mb"] = (
                df["total_size"]
                / (1024 * 1024)
            ).round(2)

            return df

        except Exception as exc:

            log_error(
                f"Erreur lors du chargement des recordings : {exc}",
                exc_info=True,
            )

            return pd.DataFrame()

    # ==================================================================
    # LATEST DATE
    # ==================================================================

    def get_latest_recording_date(self) -> date:
        """Retourne la date du dernier enregistrement local."""

        import sqlite3

        try:

            with sqlite3.connect(self.db_file) as conn:

                cursor = conn.execute(
                    """
                    SELECT MAX(start_time)
                    FROM recordings
                    """
                )

                result = cursor.fetchone()

            if result and result[0]:

                latest_date = (
                    pd.to_datetime(
                        result[0]
                    ).date()
                )

                return latest_date

        except Exception as exc:

            log_error(
                f"Erreur récupération dernière date : {exc}",
                exc_info=True,
            )

        # Valeur par défaut
        return pd.to_datetime(
            "2024-01-01"
        ).date()

    # ==================================================================
    # OLDEST DATE
    # ==================================================================

    def get_oldest_recording_date(self) -> date:
        """Retourne la date du plus ancien enregistrement local."""

        import sqlite3

        try:

            with sqlite3.connect(self.db_file) as conn:

                cursor = conn.execute(
                    """
                    SELECT MIN(start_time)
                    FROM recordings
                    """
                )

                result = cursor.fetchone()

            if result and result[0]:

                oldest_date = (
                    pd.to_datetime(
                        result[0]
                    ).date()
                )

                return oldest_date

        except Exception as exc:

            log_error(
                f"Erreur récupération première date : {exc}",
                exc_info=True,
            )

        return pd.to_datetime(
            "2024-01-01"
        ).date()

    # ==================================================================
    # DELETE
    # ==================================================================

    def delete_recording(
        self,
        recording_uuid: str,
    ) -> bool:
        """Supprime un enregistrement de la BDD locale."""

        import sqlite3

        try:

            with sqlite3.connect(self.db_file) as conn:

                cursor = conn.execute(
                    """
                    DELETE FROM recordings
                    WHERE uuid = ?
                    """,
                    (recording_uuid,),
                )

                conn.commit()

                deleted = cursor.rowcount > 0

            if deleted:

                log_info(
                    f"Recording {recording_uuid} "
                    "supprimé de la BDD locale."
                )

            return deleted

        except sqlite3.Error as exc:

            log_error(
                f"Erreur suppression {recording_uuid} : {exc}",
                exc_info=True,
            )

            return False

    # ==================================================================
    # COUNT
    # ==================================================================

    def count_recordings(self) -> int:
        """Retourne le nombre total d'enregistrements."""

        import sqlite3

        try:

            with sqlite3.connect(self.db_file) as conn:

                cursor = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM recordings
                    """
                )

                result = cursor.fetchone()

            return int(result[0]) if result else 0

        except sqlite3.Error as exc:

            log_error(
                f"Erreur comptage recordings : {exc}",
                exc_info=True,
            )

            return 0