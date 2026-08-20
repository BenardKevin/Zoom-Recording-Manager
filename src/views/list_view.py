from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import streamlit as st

from src.config.texts import TEXTS
from src.repositories.recording_repository import (
    RecordingRepository,
)
from src.services.zoom_service import ZoomService


def _render_quick_win_banner() -> Optional[str]:

    active_qw = st.session_state.get(
        "active_quick_win"
    )

    if active_qw:

        labels = {
            "short": "Vidéos < 5 minutes",
            "old": "Vidéos > 24 mois",
            "small": "Vidéos < 10 Mo",
        }

        st.info(
            TEXTS["filters"][
                "quick_win_active"
            ].format(
                name=labels.get(
                    active_qw,
                    active_qw,
                )
            )
        )

        if st.button(
            TEXTS["filters"][
                "btn_clear_filter"
            ]
        ):

            st.session_state[
                "active_quick_win"
            ] = None

            st.rerun()

    return active_qw


def _render_filter_controls():

    st.subheader(
        TEXTS["filters"]["subheader"]
    )

    f1, f2, f3, f4 = st.columns(4)

    with f1:

        search_query = st.text_input(
            TEXTS["filters"]["search_label"],
            "",
        )

    with f2:

        sort_by = st.selectbox(
            TEXTS["filters"]["sort_by_label"],
            TEXTS["filters"]["sort_options"],
            index=2,
        )

    with f3:

        sort_order = st.radio(
            TEXTS["filters"]["order_label"],
            TEXTS["filters"]["order_options"],
            index=1,
        )

    with f4:

        min_size = st.number_input(
            TEXTS["filters"]["min_size_label"],
            min_value=0,
            value=0,
            step=50,
        )

    return (
        search_query,
        sort_by,
        sort_order,
        min_size,
    )


def _filter_and_sort_recordings(
    df: pd.DataFrame,
    active_qw: Optional[str],
    search_query: str,
    sort_by: str,
    sort_order: str,
    min_size: int,
) -> pd.DataFrame:

    result = df.copy()

    now = datetime.now()

    # Quick wins
    if active_qw == "short":
        result = result[
            result["duration"] < 5
        ]

    elif active_qw == "old":

        result = result[
            result["start_time"]
            < now - timedelta(days=365 * 2)
        ]

    elif active_qw == "small":

        result = result[
            result["size_mb"] < 10
        ]

    # Recherche
    if search_query:

        result = result[
            result["topic"]
            .astype(str)
            .str.contains(
                search_query,
                case=False,
                na=False,
                regex=False,
            )
        ]

    # Taille
    if min_size > 0:

        result = result[
            result["size_mb"]
            >= min_size
        ]

    # Tri
    sort_map = {
        TEXTS["filters"]["sort_options"][0]:
            "start_time",

        TEXTS["filters"]["sort_options"][1]:
            "size_mb",

        TEXTS["filters"]["sort_options"][2]:
            "duration",
    }

    ascending = (
        sort_order
        == TEXTS["filters"][
            "order_options"
        ][0]
    )

    column = sort_map.get(sort_by)

    if column:

        result = result.sort_values(
            column,
            ascending=ascending,
        )

    return result


def _render_export_bar(
    df: pd.DataFrame,
):

    col_count, col_export = st.columns(
        [3, 1]
    )

    with col_count:

        st.caption(
            TEXTS["filters"][
                "count_caption"
            ].format(
                count=len(df)
            )
        )

    with col_export:

        csv_data = (
            df.to_csv(
                index=False
            )
            .encode("utf-8")
        )

        st.download_button(
            label=TEXTS["filters"][
                "btn_export_csv"
            ],
            data=csv_data,
            file_name=(
                "zoom_recordings_"
                f"{datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
        )


def _render_recording_card(
    row: pd.Series,
    zoom_service: ZoomService,
):

    uuid = row["uuid"]

    with st.container():

        col_title, col_info, col_size, col_btn = (
            st.columns([3, 2, 2, 1])
        )

        with col_title:

            st.subheader(
                row["topic"]
            )

            st.caption(
                f"ID: `{row['meeting_id']}`"
            )

        with col_info:

            st.write(
                TEXTS["card"][
                    "date_format"
                ].format(
                    date_str=row[
                        "start_time"
                    ].strftime(
                        "%d/%m/%Y"
                    ),
                    time_str=row[
                        "start_time"
                    ].strftime(
                        "%H:%M"
                    ),
                )
            )

            st.write(
                TEXTS["card"][
                    "duration_format"
                ].format(
                    duration=row[
                        "duration"
                    ]
                )
            )

        with col_size:

            st.write(
                TEXTS["card"][
                    "size_format"
                ].format(
                    size=row["size_mb"]
                )
            )

            if row["share_url"]:

                st.markdown(
                    TEXTS["card"][
                        "link_label"
                    ].format(
                        url=row[
                            "share_url"
                        ]
                    )
                )

        with col_btn:

            if st.button(
                TEXTS["card"]["btn_delete"],
                key=f"delete_{uuid}",
            ):

                with st.spinner(
                    TEXTS["card"][
                        "deleting_spinner"
                    ]
                ):

                    success = (
                        zoom_service.delete_recording(
                            uuid
                        )
                    )

                    if success:

                        st.toast(
                            TEXTS["card"][
                                "toast_deleted"
                            ]
                        )

                        st.rerun()

        st.divider()


def render_list_view(
    df: pd.DataFrame,
    zoom_service: ZoomService,
):

    active_qw = (
        _render_quick_win_banner()
    )

    (
        search_query,
        sort_by,
        sort_order,
        min_size,
    ) = _render_filter_controls()

    filtered_df = (
        _filter_and_sort_recordings(
            df,
            active_qw,
            search_query,
            sort_by,
            sort_order,
            min_size,
        )
    )

    _render_export_bar(
        filtered_df
    )

    st.markdown("---")

    for _, row in filtered_df.iterrows():

        _render_recording_card(
            row,
            zoom_service,
        )