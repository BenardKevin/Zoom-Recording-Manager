from datetime import datetime, timedelta

import pandas as pd


class MetricsService:

    # =========================================================================
    # STORAGE
    # =========================================================================

    @staticmethod
    def total_size_gb(df: pd.DataFrame) -> float:

        return df["size_mb"].sum() / 1024

    @staticmethod
    def remaining_storage(
        df: pd.DataFrame,
        quota_gb: float,
    ) -> float:

        return max(
            0.0,
            quota_gb
            - MetricsService.total_size_gb(df),
        )

    @staticmethod
    def quota_usage_percent(
        df: pd.DataFrame,
        quota_gb: float,
    ) -> float:

        if quota_gb <= 0:
            return 0.0

        total = MetricsService.total_size_gb(df)

        return min(
            100.0,
            total / quota_gb * 100,
        )

    # =========================================================================
    # PROJECTION
    # =========================================================================

    @staticmethod
    def monthly_storage_rate(
        df: pd.DataFrame,
    ) -> float:

        if df.empty:
            return 0.0

        now = datetime.now()

        three_months_ago = (
            now - timedelta(days=90)
        )

        recent = df[
            df["start_time"]
            >= three_months_ago
        ]

        return (
            recent["size_mb"].sum()
            / 1024
            / 3
        )

    # =========================================================================
    # QUICK WINS
    # =========================================================================

    @staticmethod
    def quick_win_masks(
        df: pd.DataFrame,
    ) -> dict[str, pd.Series]:

        now = datetime.now()

        return {
            "short": df["duration"] < 5,

            "old": (
                df["start_time"]
                < now - timedelta(days=365 * 2)
            ),

            "small": df["size_mb"] < 10,
        }

    @staticmethod
    def reclaimable_dataframe(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        masks = MetricsService.quick_win_masks(df)

        mask = (
            masks["short"]
            | masks["old"]
            | masks["small"]
        )

        return df[mask]

    # =========================================================================
    # ACTIVITY
    # =========================================================================

    @staticmethod
    def monthly_activity(
        df: pd.DataFrame,
    ) -> dict:

        now = datetime.now()

        first_current = datetime(
            now.year,
            now.month,
            1,
        )

        first_previous = (
            first_current
            - timedelta(days=1)
        ).replace(day=1)

        current = df[
            df["start_time"]
            >= first_current
        ]

        previous = df[
            (df["start_time"] >= first_previous)
            & (df["start_time"] < first_current)
        ]

        current_size = (
            current["size_mb"].sum() / 1024
        )

        previous_size = (
            previous["size_mb"].sum() / 1024
        )

        return {
            "current_count": len(current),
            "previous_count": len(previous),
            "count_delta": (
                len(current)
                - len(previous)
            ),

            "current_size_gb": current_size,
            "size_delta_gb": (
                current_size
                - previous_size
            ),
        }

    # =========================================================================
    # HOST
    # =========================================================================

    @staticmethod
    def extract_host_email(
        raw_data: str,
    ) -> str:

        import json

        if not isinstance(
            raw_data,
            str,
        ):
            return ""

        try:

            data = json.loads(raw_data)

            return data.get(
                "host_email",
                "",
            )

        except (ValueError, TypeError):

            return ""

    @staticmethod
    def format_host_name(
        email_or_name: str,
    ) -> str:

        if (
            not email_or_name
            or not isinstance(
                email_or_name,
                str,
            )
        ):
            return "Inconnu"

        prefix = (
            email_or_name.split("@")[0]
            if "@"
            in email_or_name
            else email_or_name
        )

        if "+" in prefix:

            return (
                prefix
                .split("+")[-1]
                .upper()
            )

        if "." in prefix:

            return " ".join(
                part.capitalize()
                for part in prefix.split(".")
            )

        return prefix.replace(
            "-",
            " ",
        ).title()

    @classmethod
    def prepare_hosts(
        cls,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        result = df.copy()

        if (
            "host_email"
            not in result.columns
            and "raw_data"
            in result.columns
        ):

            result["host_email"] = (
                result["raw_data"]
                .apply(cls.extract_host_email)
            )

        if "host_email" not in result.columns:
            return result

        result["Animateur"] = (
            result["host_email"]
            .apply(cls.format_host_name)
        )

        result["size_gb"] = (
            result["size_mb"] / 1024
        )

        return result

    @classmethod
    def host_statistics(
        cls,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df_hosts = cls.prepare_hosts(df)

        if (
            "Animateur"
            not in df_hosts.columns
        ):
            return pd.DataFrame()

        grouped = (
            df_hosts
            .groupby("Animateur")
            .agg(
                nb_videos=(
                    "size_mb",
                    "count",
                ),
                total_gb=(
                    "size_gb",
                    "sum",
                ),
                total_min=(
                    "duration",
                    "sum",
                ),
                avg_min=(
                    "duration",
                    "mean",
                ),
            )
            .reset_index()
        )

        grouped["mb_per_min"] = (
            grouped["total_gb"] * 1024
            /
            grouped["total_min"].replace(
                0,
                1,
            )
        )

        return grouped.sort_values(
            "total_gb",
            ascending=False,
        )