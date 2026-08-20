from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Recording:
    """Représente un enregistrement Zoom."""

    uuid: str
    meeting_id: int
    topic: str
    start_time: str
    duration: int
    total_size: int
    file_count: int
    share_url: str = ""
    raw_data: Optional[dict[str, Any]] = None

    @property
    def size_mb(self) -> float:
        """Retourne la taille en Mo."""

        return self.total_size / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Retourne la taille en Go."""

        return self.total_size / (1024 * 1024 * 1024)

    @classmethod
    def from_zoom_data(cls, data: dict[str, Any]) -> "Recording":
        """Construit un Recording depuis une réponse Zoom."""

        return cls(
            uuid=str(data.get("uuid", "")),
            meeting_id=int(data.get("id", 0)),
            topic=str(data.get("topic", "Sans titre")),
            start_time=str(data.get("start_time", "")),
            duration=int(data.get("duration", 0)),
            total_size=int(data.get("total_size", 0)),
            file_count=int(
                data.get(
                    "recording_count",
                    len(data.get("recording_files", [])),
                )
            ),
            share_url=str(data.get("share_url", "")),
            raw_data=data,
        )

    def to_db_tuple(self) -> tuple:
        """Convertit le modèle en tuple compatible SQLite."""

        import json

        return (
            self.uuid,
            self.meeting_id,
            self.topic,
            self.start_time,
            self.duration,
            self.total_size,
            self.file_count,
            self.share_url,
            json.dumps(
                self.raw_data or {},
                ensure_ascii=False,
            ),
        )