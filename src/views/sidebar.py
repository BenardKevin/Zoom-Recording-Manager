import streamlit as st

from src.config.logger import (
    log_error,
    log_info,
    log_warning,
)
from src.config.settings import DEFAULT_QUOTA_GB
from src.config.texts import TEXTS
from src.repositories.recording_repository import RecordingRepository
from src.services.zoom_service import ZoomService


def render_sidebar(
    env_client_id: str,
    env_client_secret: str,
    zoom_service: ZoomService,
    repository: RecordingRepository,
):

    with st.sidebar:

        # ==================================================================
        # CREDENTIALS
        # ==================================================================

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

        # ==================================================================
        # QUOTA
        # ==================================================================

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

        # ==================================================================
        # SYNCHRONISATION
        # ==================================================================

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

        # ------------------------------------------------------------------
        # Synchronisation depuis le dernier enregistrement
        # ------------------------------------------------------------------

        if (
            sync_mode
            == TEXTS["sidebar"]["sync_modes"][0]
        ):

            from_date = latest_date

            st.info(
                f"{TEXTS['sidebar']['sync_info_prefix']} "
                f"**{from_date.strftime('%d/%m/%Y')}**"
            )

        # ------------------------------------------------------------------
        # Synchronisation depuis une date
        # ------------------------------------------------------------------

        else:

            from_date = st.date_input(
                TEXTS["sidebar"]["date_input_label"],
                value=oldest_date,
            )

        # ==================================================================
        # BOUTON SYNCHRONISATION
        # ==================================================================

        if st.button(
            TEXTS["sidebar"]["btn_sync"]
        ):

            # --------------------------------------------------------------
            # Validation credentials
            # --------------------------------------------------------------

            if not client_id or not client_secret:

                log_warning(
                    "Tentative de synchronisation "
                    "sans credentials Zoom."
                )

                st.warning(
                    TEXTS["sidebar"][
                        "warning_missing_creds"
                    ]
                )

            else:

                log_info(
                    "Bouton de synchronisation cliqué."
                )

                try:

                    # ------------------------------------------------------
                    # Transmission des credentials à AuthService
                    # ------------------------------------------------------

                    zoom_service.set_credentials(
                        client_id=client_id,
                        client_secret=client_secret,
                    )

                    # ------------------------------------------------------
                    # Synchronisation
                    # ------------------------------------------------------

                    count = (
                        zoom_service.sync_recordings(
                            from_date=from_date.isoformat()
                        )
                    )

                    log_info(
                        "Synchronisation Zoom terminée : "
                        f"{count} enregistrement(s)."
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

                    log_error(
                        "Échec de la synchronisation Zoom : "
                        f"{exc}",
                        exc_info=True,
                    )

                    st.error(
                        "Erreur lors de la synchronisation : "
                        f"{exc}"
                    )

    return (
        client_id,
        client_secret,
        quota_gb,
    )