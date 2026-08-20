import json
import sqlite3
from datetime import date
from typing import Optional

import pandas as pd

from src.config.logger import log_error, log_info
from src.config.settings import (
    DB_FILE,
    DEFAULT_HISTORY_START_DATE,
)
from src.models.recording import Recording


class RecordingRepository:
    """Accès aux données SQLite des enregistrements."""

    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file

    # =========================================================================
    # DATABASE
    # =========================================================================

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_file,
            timeout=30,
        )

        conn.execute("PRAGMA foreign_keys = ON")

        return conn

    def init_db(self) -> None:

        try:

            with self._connect() as conn:

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS recordings (
                        uuid TEXT PRIMARY KEY,
                        meeting_id INTEGER NOT NULL,
                        topic TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        duration INTEGER DEFAULT 0,
                        total_size INTEGER DEFAULT 0,
                        file_count INTEGER DEFAULT 0,
                        share_url TEXT DEFAULT '',
                        raw_data TEXT
                    )
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_recordings_start_time
                    ON recordings(start_time)
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_recordings_meeting_id
                    ON recordings(meeting_id)
                    """
                )

                conn.commit()

            log_info("Base de données initialisée.")

        except sqlite3.Error as exc:

            log_error(
                f"Erreur initialisation BDD : {exc}",
                exc_info=True,
            )

            raise

    # =========================================================================
    # DATES
    # =========================================================================

    def get_oldest_recording_date(self) -> date:

        try:

            with self._connect() as conn:

                row = conn.execute(
                    """
                    SELECT MIN(start_time)
                    FROM recordings
                    """
                ).fetchone()

            if row and row[0]:

                return pd.to_datetime(
                    row[0]
                ).date()

        except Exception as exc:

            log_error(
                f"Erreur recherche ancienne date : {exc}",
                exc_info=True,
            )

        return pd.to_datetime(
            DEFAULT_HISTORY_START_DATE
        ).date()

    def get_latest_recording_date(self) -> date:

        try:

            with self._connect() as conn:

                row = conn.execute(
                    """
                    SELECT MAX(start_time)
                    FROM recordings
                    """
                ).fetchone()

            if row and row[0]:

                return pd.to_datetime(
                    row[0]
                ).date()

        except Exception as exc:

            log_error(
                f"Erreur recherche date récente : {exc}",
                exc_info=True,
            )

        return pd.to_datetime(
            DEFAULT_HISTORY_START_DATE
        ).date()

    # =========================================================================
    # WRITE
    # =========================================================================

    def save_recording(
        self,
        recording: Recording,
    ) -> None:

        query = """
            INSERT INTO recordings (
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

            ON CONFLICT(uuid) DO UPDATE SET
                meeting_id = excluded.meeting_id,
                topic = excluded.topic,
                start_time = excluded.start_time,
                duration = excluded.duration,
                total_size = excluded.total_size,
                file_count = excluded.file_count,
                share_url = excluded.share_url,
                raw_data = excluded.raw_data
        """

        with self._connect() as conn:

            conn.execute(
                query,
                recording.to_db_tuple(),
            )

            conn.commit()

    def save_recordings(
        self,
        recordings: list[Recording],
    ) -> int:

        if not recordings:
            return 0

        query = """
            INSERT INTO recordings (
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

            ON CONFLICT(uuid) DO UPDATE SET
                meeting_id = excluded.meeting_id,
                topic = excluded.topic,
                start_time = excluded.start_time,
                duration = excluded.duration,
                total_size = excluded.total_size,
                file_count = excluded.file_count,
                share_url = excluded.share_url,
                raw_data = excluded.raw_data
        """

        rows = [
            recording.to_db_tuple()
            for recording in recordings
        ]

        with self._connect() as conn:

            conn.executemany(
                query,
                rows,
            )

            conn.commit()

        log_info(
            f"{len(rows)} enregistrement(s) sauvegardé(s) en BDD."
        )

        return len(rows)

    # =========================================================================
    # DELETE
    # =========================================================================

    def delete_recording(
        self,
        recording_uuid: str,
    ) -> bool:

        try:

            with self._connect() as conn:

                cursor = conn.execute(
                    """
                    DELETE FROM recordings
                    WHERE uuid = ?
                    """,
                    (recording_uuid,),
                )

                conn.commit()

                return cursor.rowcount > 0

        except sqlite3.Error as exc:

            log_error(
                f"Erreur suppression BDD "
                f"{recording_uuid}: {exc}",
                exc_info=True,
            )

            return False

    # =========================================================================
    # READ
    # =========================================================================

    def load_dataframe(self) -> pd.DataFrame:

        try:

            with self._connect() as conn:

                df = pd.read_sql_query(
                    """
                    SELECT *
                    FROM recordings
                    ORDER BY start_time DESC
                    """,
                    conn,
                )

            if df.empty:
                return df

            df["start_time"] = pd.to_datetime(
                df["start_time"],
                errors="coerce",
            )

            df["size_mb"] = (
                df["total_size"] /
                (1024 * 1024)
            ).round(2)

            df["size_gb"] = (
                df["total_size"] /
                (1024 * 1024 * 1024)
            ).round(4)

            return df

        except Exception as exc:

            log_error(
                f"Erreur lecture BDD : {exc}",
                exc_info=True,
            )

            return pd.DataFrame()