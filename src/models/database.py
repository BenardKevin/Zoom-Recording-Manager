import json
import aiosqlite
import pandas as pd
from src.config.logger import log_error, log_info, log_warning
from src.config.settings import DB_FILE

async def init_db():
    """Initialise la table SQLite si elle n'existe pas."""
    try:
        async with aiosqlite.connect(DB_FILE) as conn:
            await conn.execute("""
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
            """)
            await conn.commit()
    except aiosqlite.Error as e:
        log_error(f"Erreur d'initialisation BDD : {e}", exc_info=True)

async def get_oldest_recording_date():
    """Récupère la date du plus ancien enregistrement enregistré."""
    try:
        async with aiosqlite.connect(DB_FILE) as conn:
            async with conn.execute("SELECT MIN(start_time) FROM recordings") as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    oldest_date = pd.to_datetime(result[0]).date()
                    log_info(
                        f"Date du plus ancien enregistrement local : {oldest_date}"
                    )
                    return oldest_date
    except Exception as e:
        log_warning(
            f"Erreur lors de la recherche du plus ancien enregistrement : {e}"
        )

    return pd.to_datetime("2024-01-01").date()

async def get_latest_recording_date():
    """Récupère la date de l'enregistrement le plus récent enregistré en BDD."""
    try:
        async with aiosqlite.connect(DB_FILE) as conn:
            async with conn.execute("SELECT MAX(start_time) FROM recordings") as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    latest_date = pd.to_datetime(result[0]).date()
                    log_info(f"Date du plus récent enregistrement local : {latest_date}")
                    return latest_date
    except Exception as e:
        log_warning(f"Erreur lors de la recherche du plus récent enregistrement : {e}")

    return pd.to_datetime("2024-01-01").date()

async def save_recording(conn: aiosqlite.Connection, meeting_data: dict):
    """Insère ou met à jour un enregistrement dans SQLite."""
    await conn.execute(
        """
        INSERT OR REPLACE INTO recordings 
        (uuid, meeting_id, topic, start_time, duration, total_size, file_count, share_url, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            meeting_data["uuid"],
            meeting_data["id"],
            meeting_data["topic"],
            meeting_data["start_time"],
            meeting_data["duration"],
            meeting_data["total_size"],
            meeting_data["recording_count"],
            meeting_data.get("share_url", ""),
            json.dumps(meeting_data),
        ),
    )

async def delete_recording_from_db(meeting_uuid: str) -> bool:
    """Supprime un enregistrement de la BDD localement."""
    try:
        async with aiosqlite.connect(DB_FILE) as conn:
            await conn.execute(
                "DELETE FROM recordings WHERE uuid = ?", (meeting_uuid,)
            )
            await conn.commit()
        return True
    except aiosqlite.Error as e:
        log_error(
            f"Échec de suppression BDD pour UUID={meeting_uuid} : {e}"
        )
        return False

async def load_local_data() -> pd.DataFrame:
    """Charge les données SQLite dans un DataFrame Pandas."""
    try:
        async with aiosqlite.connect(DB_FILE) as conn:
            async with conn.execute("SELECT * FROM recordings") as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]

        df = pd.DataFrame(rows, columns=columns)

        if not df.empty:
            df["start_time"] = pd.to_datetime(df["start_time"])
            df["size_mb"] = (df["total_size"] / (1024 * 1024)).round(2)
        return df
    except Exception as e:
        log_error(f"Erreur lors de la lecture des données locales : {e}")
        return pd.DataFrame()