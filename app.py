import streamlit as st
import pandas as pd

from src.config.settings import get_env_credentials
from src.config.texts import TEXTS

from src.clients.zoom_client import ZoomClient

from src.repositories.recording_repository import (
    RecordingRepository,
)

from src.services.auth_service import (
    AuthService,
)

from src.services.zoom_service import (
    ZoomService,
)

from src.views.sidebar import (
    render_sidebar,
)

from src.views.list_view import (
    render_list_view,
)

from src.views.metrics_view import (
    render_metrics_view,
)


# ==========================================================================
# CONFIGURATION STREAMLIT
# ==========================================================================

st.set_page_config(
    page_title=TEXTS["page_title"],
    page_icon=TEXTS["page_icon"],
    layout="wide",
)


# ==========================================================================
# CONFIGURATION
# ==========================================================================

env_client_id, env_client_secret, env_refresh_token = (
    get_env_credentials()
)


# ==========================================================================
# SESSION STATE
# ==========================================================================

if "current_refresh_token" not in st.session_state:

    st.session_state.current_refresh_token = (
        env_refresh_token
    )


# ==========================================================================
# DEPENDENCIES
# ==========================================================================

repository = RecordingRepository()
repository.init_db()

auth_service = AuthService(
    client_id=env_client_id,
    client_secret=env_client_secret,
)

zoom_client = ZoomClient()

zoom_service = ZoomService(
    auth_service=auth_service,
    zoom_client=zoom_client,
    repository=repository,
)


# ==========================================================================
# HEADER
# ==========================================================================

st.title(
    TEXTS["app_header"]
)


# ==========================================================================
# SIDEBAR
# ==========================================================================

client_id, client_secret, quota_gb = render_sidebar(
    env_client_id=env_client_id,
    env_client_secret=env_client_secret,
    zoom_service=zoom_service,
    repository=repository,
)


# ==========================================================================
# LOAD DATABASE
# ==========================================================================

df = repository.load_recordings()


# ==========================================================================
# EMPTY DATABASE
# ==========================================================================

if df.empty:

    st.info(
        TEXTS["empty_db_info"]
    )

else:

    # ----------------------------------------------------------------------
    # Normalisation datetime
    # ----------------------------------------------------------------------

    if (
        "start_time" in df.columns
        and pd.api.types.is_datetime64_any_dtype(
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
            .dt
            .tz_localize(None)
        )

    # ----------------------------------------------------------------------
    # Tabs
    # ----------------------------------------------------------------------

    tab_metrics, tab_list = st.tabs(
        [
            TEXTS["tabs"]["metrics"],
            TEXTS["tabs"]["list"],
        ]
    )

    # ----------------------------------------------------------------------
    # METRICS
    # ----------------------------------------------------------------------

    with tab_metrics:

        render_metrics_view(
            df,
            quota_gb,
        )

    # ----------------------------------------------------------------------
    # LIST
    # ----------------------------------------------------------------------

    with tab_list:

        render_list_view(
            df,
            zoom_service=zoom_service,
        )