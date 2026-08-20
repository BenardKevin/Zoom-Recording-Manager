import streamlit as st

from src.config.logger import (
    log_info,
    log_warning,
)
from src.config.settings import (
    DEFAULT_QUOTA_GB,
)
from src.config.texts import TEXTS
from src.repositories.recording_repository import (
    RecordingRepository,
)
from src.services.zoom_service import ZoomService


def render_sidebar(
    env_client_id: str,
    env_client_secret: str,
    zoom_service: ZoomService,
    repository: RecordingRepository,
):

    with st.sidebar:

        # =====================================================================
        # CREDENTIALS
        # =====================================================================

        st.header(
            TEXTS["sidebar"]["creds_header"]
        )

        client_id = st.text_input(
            TEXTS["sidebar"]["client_id_label"],
            value=env_client_id,
            type="password",
        )

        client_secret = st.text_input(
            TEXTS["sidebar"]["client_secret_label"],
            value=env_client_secret,
            type="password",
        )

        if client_id and client_secret:
            st.caption(
                TEXTS["sidebar"]["status_ok"]
            )
        else:
            st.caption(
                TEXTS["sidebar"]["status_missing"]
            )

        # =====================================================================
        # QUOTA
        # =====================================================================

        st.markdown("---")

        st.header(
            TEXTS["sidebar"]["quota_header"]
        )

        quota_gb = st.number_input(
            TEXTS["sidebar"]["quota_label"],
            min_value=1.0,
            value=float(DEFAULT_QUOTA_GB),
            step=10.0,
            format="%.1f",
        )

        # =====================================================================
        # SYNC
        # =====================================================================

        st.markdown("---")

        st.header(
            TEXTS["sidebar"]["sync_header"]
        )

        latest_date = (
            repository.get_latest_recording_date()
        )

        oldest_date = (
            repository.get_oldest_recording_date()
        )

        sync_mode = st.radio(
            TEXTS["sidebar"]["sync_mode_label"],
            options=TEXTS["sidebar"]["sync_modes"],
            index=0,
            help=TEXTS["sidebar"]["sync_mode_help"],
        )

        if (
            sync_mode
            == TEXTS["sidebar"]["sync_modes"][0]
        ):

            from_date = latest_date

            st.info(
                f"{TEXTS['sidebar']['sync_info_prefix']} "
                f"**{from_date.strftime('%d/%m/%Y')}**"
            )

        else:

            from_date = st.date_input(
                TEXTS["sidebar"]["date_input_label"],
                oldest_date,
            )

        # =====================================================================
        # BUTTON
        # =====================================================================

        if st.button(
            TEXTS["sidebar"]["btn_sync"]
        ):

            if not client_id or not client_secret:

                log_warning(
                    "Synchronisation sans credentials."
                )

                st.warning(
                    TEXTS["sidebar"][
                        "warning_missing_creds"
                    ]
                )

            else:

                log_info(
                    "Synchronisation demandée "
                    "depuis la sidebar."
                )

                # Le ZoomService utilise les credentials
                # actuellement saisis.
                zoom_service.auth_service.client_id = (
                    client_id
                )

                zoom_service.auth_service.client_secret = (
                    client_secret
                )

                try:

                    count = (
                        zoom_service.sync_recordings(
                            str(from_date)
                        )
                    )

                    st.success(
                        TEXTS["sidebar"][
                            "sync_success"
                        ].format(
                            count=count
                        )
                    )

                    st.rerun()

                except Exception as exc:

                    log_warning(
                        f"Synchronisation échouée : {exc}"
                    )

                    st.error(
                        f"Erreur lors de la synchronisation : "
                        f"{exc}"
                    )

    return (
        client_id,
        client_secret,
        quota_gb,
    )