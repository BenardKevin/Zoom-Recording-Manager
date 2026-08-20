import time
from typing import Optional

import streamlit as st
from dotenv import set_key

from src.clients.zoom_client import (
    ZoomAuthenticationError,
    request_access_token,
)
from src.config.logger import log_error, log_info, log_warning
from src.config.settings import (
    ENV_FILE,
    TOKEN_CACHE_TTL_SECONDS,
)


class AuthService:
    """Gère l'authentification OAuth Zoom."""

    SESSION_ACCESS_TOKEN = "zoom_access_token"
    SESSION_TOKEN_EXPIRY = "zoom_token_expires_at"
    SESSION_REFRESH_TOKEN = "zoom_refresh_token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ):

        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

    def _get_cached_token(self) -> Optional[str]:

        token = st.session_state.get(
            self.SESSION_ACCESS_TOKEN
        )

        expires_at = st.session_state.get(
            self.SESSION_TOKEN_EXPIRY,
            0,
        )

        if (
            token
            and time.time() < expires_at
        ):
            return token

        return None

    def get_access_token(self) -> Optional[str]:

        # ---------------------------------------------------------------------
        # Cache
        # ---------------------------------------------------------------------

        cached_token = self._get_cached_token()

        if cached_token:
            return cached_token

        # ---------------------------------------------------------------------
        # Validation
        # ---------------------------------------------------------------------

        if not self.client_id:
            log_error("Zoom Client ID absent.")
            return None

        if not self.client_secret:
            log_error("Zoom Client Secret absent.")
            return None

        current_refresh_token = (
            st.session_state.get(
                self.SESSION_REFRESH_TOKEN
            )
            or self.refresh_token
        )

        if not current_refresh_token:

            log_error(
                "Zoom Refresh Token absent."
            )

            return None

        # ---------------------------------------------------------------------
        # Refresh
        # ---------------------------------------------------------------------

        try:

            log_info(
                "Renouvellement du token Zoom..."
            )

            data = request_access_token(
                self.client_id,
                self.client_secret,
                current_refresh_token,
            )

        except ZoomAuthenticationError as exc:

            log_error(
                f"Erreur OAuth Zoom : {exc}",
                exc_info=True,
            )

            return None

        access_token = data.get(
            "access_token"
        )

        new_refresh_token = data.get(
            "refresh_token"
        )

        expires_in = data.get(
            "expires_in",
            TOKEN_CACHE_TTL_SECONDS,
        )

        if not access_token:

            log_error(
                "Zoom n'a pas fourni d'access token."
            )

            return None

        # ---------------------------------------------------------------------
        # Cache
        # ---------------------------------------------------------------------

        st.session_state[
            self.SESSION_ACCESS_TOKEN
        ] = access_token

        # Marge de sécurité de 5 minutes
        ttl = min(
            int(expires_in),
            TOKEN_CACHE_TTL_SECONDS,
        )

        st.session_state[
            self.SESSION_TOKEN_EXPIRY
        ] = time.time() + ttl

        # ---------------------------------------------------------------------
        # Refresh token rotation
        # ---------------------------------------------------------------------

        if new_refresh_token:

            st.session_state[
                self.SESSION_REFRESH_TOKEN
            ] = new_refresh_token

            try:

                set_key(
                    str(ENV_FILE),
                    "ZOOM_REFRESH_TOKEN",
                    new_refresh_token,
                )

                log_info(
                    "Nouveau Refresh Token sauvegardé."
                )

            except Exception as exc:

                log_warning(
                    "Impossible de sauvegarder "
                    f"le Refresh Token : {exc}"
                )

        return access_token