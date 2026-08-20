from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config.texts import TEXTS
from src.services.metrics_service import (
    MetricsService,
)


def render_storage_section(
    df: pd.DataFrame,
    quota_gb: float,
) -> float:

    total_size_gb = (
        MetricsService.total_size_gb(df)
    )

    remaining_gb = (
        MetricsService.remaining_storage(
            df,
            quota_gb,
        )
    )

    pct_used = (
        MetricsService.quota_usage_percent(
            df,
            quota_gb,
        )
    )

    pct_remaining = (
        max(
            0,
            100 - pct_used,
        )
    )

    avg_file_mb = (
        df["size_mb"].mean()
        if not df.empty
        else 0
    )

    st.subheader(
        TEXTS["kpis"][
            "section_storage"
        ]
    )

    st.progress(
        pct_used / 100,
        text=(
            f"Utilisation du quota Zoom : "
            f"**{pct_used:.1f}%** "
            f"({total_size_gb:.2f} Go / "
            f"{quota_gb:.1f} Go)"
        ),
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        TEXTS["kpis"]["quota_used"],
        f"{pct_used:.1f}%",
        f"{total_size_gb:.2f} Go utilisés",
    )

    c2.metric(
        TEXTS["kpis"]["quota_remaining"],
        f"{pct_remaining:.1f}%",
        f"{remaining_gb:.2f} Go libres",
    )

    c3.metric(
        TEXTS["kpis"]["avg_file_size"],
        f"{avg_file_mb:.1f} Mo",
        f"{len(df)} vidéos",
    )

    return remaining_gb


def render_projection_section(
    df: pd.DataFrame,
    quota_gb: float,
    remaining_gb: float,
):

    st.subheader(
        TEXTS["kpis"][
            "section_projection"
        ]
    )

    monthly_rate = (
        MetricsService.monthly_storage_rate(
            df
        )
    )

    if (
        monthly_rate > 0
        and remaining_gb > 0
    ):

        months_left = (
            remaining_gb
            / monthly_rate
        )

        estimated_date = (
            datetime.now()
            + pd.Timedelta(
                days=months_left * 30.4
            )
        ).strftime(
            "%B %Y"
        )

        st.info(
            TEXTS["kpis"][
                "projection_info"
            ].format(
                rate=monthly_rate,
                quota=quota_gb,
                date=estimated_date,
                months=months_left,
            )
        )

    elif remaining_gb <= 0:

        st.error(
            "Quota de stockage atteint."
        )

    else:

        st.success(
            TEXTS["kpis"][
                "projection_unlimited"
            ]
        )


def render_activity_section(
    df: pd.DataFrame,
):

    st.subheader(
        TEXTS["kpis"][
            "section_activity"
        ]
    )

    activity = (
        MetricsService.monthly_activity(
            df
        )
    )

    avg_duration = (
        df["duration"].mean()
        if not df.empty
        else 0
    )

    total_hours = (
        df["duration"].sum()
        // 60
        if not df.empty
        else 0
    )

    a1, a2, a3 = st.columns(3)

    a1.metric(
        TEXTS["kpis"]["monthly_count"],
        activity["current_count"],
        f"{activity['count_delta']:+d} "
        "vs mois dernier",
    )

    a2.metric(
        TEXTS["kpis"]["monthly_size"],
        f"{activity['current_size_gb']:.2f} Go",
        f"{activity['size_delta_gb']:+.2f} Go",
    )

    a3.metric(
        TEXTS["kpis"]["avg_duration"],
        f"{int(avg_duration)} min",
        f"Total : {int(total_hours)}h",
    )


def render_quick_wins_section(
    df: pd.DataFrame,
):

    st.subheader(
        TEXTS["kpis"][
            "section_quick_wins"
        ]
    )

    masks = (
        MetricsService.quick_win_masks(
            df
        )
    )

    q1, q2, q3 = st.columns(3)

    quick_wins = [
        (
            q1,
            "short",
            "Vidéo(s) < 5 min",
        ),
        (
            q2,
            "old",
            "Vidéo(s) > 24 mois",
        ),
        (
            q3,
            "small",
            "Vidéo(s) < 10 Mo",
        ),
    ]

    for column, key, label in quick_wins:

        subset = df[masks[key]]

        with column:

            st.warning(
                f"**{len(subset)}** "
                f"{label}\n\n"
                f"Volume : **"
                f"{subset['size_mb'].sum() / 1024:.2f}"
                f" Go**"
            )

            if st.button(
                TEXTS["kpis"][
                    "quick_win_filter_btn"
                ],
                key=f"metric_{key}",
            ):

                st.session_state[
                    "active_quick_win"
                ] = key

                st.toast(
                    "Filtre appliqué !"
                )


def render_cleanup_section(
    df: pd.DataFrame,
    quota_gb: float,
):

    st.subheader(
        "Potentiel de nettoyage"
    )

    reclaimable = (
        MetricsService.reclaimable_dataframe(
            df
        )
    )

    total_gb = (
        MetricsService.total_size_gb(df)
    )

    reclaimable_gb = (
        reclaimable["size_mb"].sum()
        / 1024
    )

    percentage = (
        reclaimable_gb
        / total_gb
        * 100
        if total_gb > 0
        else 0
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Volume récupérable",
        f"{reclaimable_gb:.2f} Go",
        f"{percentage:.1f}% du stock",
    )

    c2.metric(
        "Vidéos concernées",
        len(reclaimable),
        f"{len(reclaimable) / len(df) * 100:.1f}%"
        if len(df)
        else "0%",
    )

    c3.metric(
        "Espace après purge",
        f"{max(0, quota_gb - total_gb + reclaimable_gb):.2f} Go",
    )


def render_top_videos_section(
    df: pd.DataFrame,
):

    st.subheader(
        TEXTS["kpis"][
            "section_top"
        ]
    )

    top = (
        df.sort_values(
            "size_mb",
            ascending=False,
        )
        .head(5)
        [
            [
                "topic",
                "start_time",
                "duration",
                "size_mb",
            ]
        ]
        .copy()
    )

    if top.empty:
        return

    top["start_time"] = (
        top["start_time"]
        .dt.strftime(
            "%d/%m/%Y %H:%M"
        )
    )

    top.columns = [
        "Titre",
        "Date",
        "Durée (min)",
        "Taille (Mo)",
    ]

    st.dataframe(
        top,
        use_container_width=True,
        hide_index=True,
    )


def render_host_section(
    df: pd.DataFrame,
):

    st.subheader(
        "Gouvernance par animateur"
    )

    grouped = (
        MetricsService.host_statistics(
            df
        )
    )

    if grouped.empty:

        st.info(
            "Information animateur "
            "non disponible."
        )

        return

    col1, col2 = st.columns([3, 2])

    with col1:

        display = grouped.rename(
            columns={
                "Animateur": "Animateur",
                "nb_videos": "Vidéos",
                "total_gb": "Volume (Go)",
                "avg_min": "Durée moyenne (min)",
                "mb_per_min": "Mo / Min",
            }
        )

        st.dataframe(
            display[
                [
                    "Animateur",
                    "Vidéos",
                    "Volume (Go)",
                    "Durée moyenne (min)",
                    "Mo / Min",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with col2:

        fig = px.bar(
            grouped.head(10),
            x="mb_per_min",
            y="Animateur",
            orientation="h",
            labels={
                "mb_per_min": "Mo / Min",
                "Animateur": "",
            },
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


def render_temporal_section(
    df: pd.DataFrame,
):

    st.subheader(
        "Temporalité"
    )

    data = df.copy()

    days = [
        "Lundi",
        "Mardi",
        "Mercredi",
        "Jeudi",
        "Vendredi",
        "Samedi",
        "Dimanche",
    ]

    data["Jour"] = (
        data["start_time"]
        .dt.weekday
        .map(dict(enumerate(days)))
    )

    data["size_gb"] = (
        data["size_mb"] / 1024
    )

    stats = (
        data.groupby("Jour")
        .agg(
            volume=("size_gb", "sum"),
            count=("size_gb", "count"),
        )
        .reindex(days)
        .fillna(0)
        .reset_index()
    )

    c1, c2 = st.columns(2)

    with c1:

        fig = px.bar(
            stats,
            x="Jour",
            y="volume",
            title="Volume par jour",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with c2:

        fig = px.bar(
            stats,
            x="Jour",
            y="count",
            title="Nombre d'enregistrements",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


def render_monthly_chart(
    df: pd.DataFrame,
):

    st.subheader(
        TEXTS["kpis"][
            "section_chart"
        ]
    )

    data = df.copy()

    data["size_gb"] = (
        data["size_mb"] / 1024
    )

    data["Année"] = (
        data["start_time"]
        .dt.year
        .astype(str)
    )

    data["Mois_Num"] = (
        data["start_time"]
        .dt.month
    )

    months = {
        1: "Janv",
        2: "Févr",
        3: "Mars",
        4: "Avril",
        5: "Mai",
        6: "Juin",
        7: "Juil",
        8: "Août",
        9: "Sept",
        10: "Oct",
        11: "Nov",
        12: "Déc",
    }

    data["Mois"] = (
        data["Mois_Num"]
        .map(months)
    )

    grouped = (
        data.groupby(
            [
                "Mois_Num",
                "Mois",
                "Année",
            ]
        )["size_gb"]
        .sum()
        .reset_index()
        .sort_values("Mois_Num")
    )

    fig = px.bar(
        grouped,
        x="Mois",
        y="size_gb",
        color="Année",
        barmode="group",
        category_orders={
            "Mois": list(months.values())
        },
        labels={
            "size_gb": "Stockage (Go)",
            "Mois": "",
            "Année": "Année",
        },
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


def render_metrics_view(
    df: pd.DataFrame,
    quota_gb: float,
):

    remaining = render_storage_section(
        df,
        quota_gb,
    )

    render_projection_section(
        df,
        quota_gb,
        remaining,
    )

    render_activity_section(df)

    st.markdown("---")

    render_quick_wins_section(df)

    render_cleanup_section(
        df,
        quota_gb,
    )

    st.markdown("---")

    render_top_videos_section(df)

    render_host_section(df)

    st.markdown("---")

    render_temporal_section(df)

    render_monthly_chart(df)