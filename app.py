import pandas as pd
import streamlit as st

from src.config.settings import (
    get_env_credentials,
)
from src.config.texts import TEXTS
from src.repositories.recording_repository import (
    RecordingRepository,
)
from src.services.auth_service import AuthService
from src.services.zoom_service import ZoomService
from src.views.list_view import render_list_view
from src.views.metrics_view import render_metrics_view
from src.views.sidebar import render_sidebar


# =============================================================================
# CONFIG
# =============================================================================

st.set_page_config(
    page_title=TEXTS["page_title"],
    page_icon=TEXTS["page_icon"],
    layout="wide",
)


# =============================================================================
# DEPENDENCIES
# =============================================================================

env_client_id, env_client_secret, env_refresh_token = (
    get_env_credentials()
)


repository = RecordingRepository()

repository.init_db()


auth_service = AuthService(
    client_id=env_client_id,
    client_secret=env_client_secret,
    refresh_token=env_refresh_token,
)


zoom_service = ZoomService(
    auth_service=auth_service,
    repository=repository,
)


# =============================================================================
# UI
# =============================================================================

st.title(
    TEXTS["app_header"]
)


client_id, client_secret, quota_gb = (
    render_sidebar(
        env_client_id,
        env_client_secret,
        zoom_service,
        repository,
    )
)


# Important :
# Les credentials peuvent avoir été modifiés dans la sidebar.
auth_service.client_id = client_id
auth_service.client_secret = client_secret


# =============================================================================
# DATA
# =============================================================================

df = repository.load_dataframe()


if df.empty:

    st.info(
        TEXTS["empty_db_info"]
    )

else:

    # Normalisation timezone
    if (
        pd.api.types.is_datetime64_any_dtype(
            df["start_time"]
        )
        and getattr(
            df["start_time"].dt,
            "tz",
            None,
        ) is not None
    ):

        df["start_time"] = (
            df["start_time"]
            .dt.tz_localize(None)
        )

    # ========================================================================
    # TABS
    # ========================================================================

    tab_metrics, tab_list = st.tabs(
        [
            TEXTS["tabs"]["metrics"],
            TEXTS["tabs"]["list"],
        ]
    )

    with tab_metrics:

        render_metrics_view(
            df,
            quota_gb,
        )

    with tab_list:

        render_list_view(
            df,
            zoom_service,
        )