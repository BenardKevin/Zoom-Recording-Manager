import time
from typing import Optional

import requests
import streamlit as st
from dotenv import set_key

from src.config.logger import (
    log_error,
    log_info,
    log_warning,
)
from src.config.settings import (
    API_TIMEOUT,
    ENV_FILE,
    TOKEN_CACHE_TTL_SECONDS,
    ZOOM_OAUTH_URL,
)


class AuthService:
    """
    Gère l'authentification OAuth2 auprès de Zoom.

    Responsabilités :
    - gérer les credentials OAuth ;
    - récupérer un access token ;
    - mettre en cache l'access token ;
    - gérer le renouvellement du refresh token ;
    - persister le nouveau refresh token dans le .env.
    """

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        refresh_token: str = "",
    ):
        self.client_id = client_id
        self.client_secret = client_secret

        # Le refresh token courant est conservé dans la session
        # car Zoom peut en fournir un nouveau lors du refresh.
        if "current_refresh_token" not in st.session_state:
            st.session_state.current_refresh_token = refresh_token

    # ==========================================================================
    # CREDENTIALS
    # ==========================================================================

    def set_credentials(
        self,
        client_id: str,
        client_secret: str,
    ) -> None:
        """
        Met à jour les credentials OAuth utilisés pendant la session.
        """

        self.client_id = client_id
        self.client_secret = client_secret

        log_info(
            "Credentials Zoom mis à jour pour la session."
        )

        # Les credentials pouvant changer depuis la sidebar,
        # on invalide le token courant afin d'éviter d'utiliser
        # un token obtenu avec d'autres credentials.
        self.invalidate_token()

    # ==========================================================================
    # ACCESS TOKEN
    # ==========================================================================

    def get_access_token(self) -> Optional[str]:
        """
        Retourne un access token Zoom valide.

        Utilise le token en cache lorsqu'il est encore valide.
        Sinon, effectue automatiquement un refresh OAuth.
        """

        # ----------------------------------------------------------------------
        # 1. Validation des credentials
        # ----------------------------------------------------------------------

        if not self.client_id or not self.client_secret:

            log_error(
                "Impossible d'obtenir un token Zoom : "
                "credentials manquants."
            )

            return None

        now = time.time()

        # ----------------------------------------------------------------------
        # 2. Vérification du token en cache
        # ----------------------------------------------------------------------

        cached_token = st.session_state.get(
            "access_token"
        )

        token_expires_at = st.session_state.get(
            "token_expires_at"
        )

        if (
            cached_token
            and token_expires_at
            and now < token_expires_at
        ):
            return cached_token

        # ----------------------------------------------------------------------
        # 3. Récupération du refresh token
        # ----------------------------------------------------------------------

        refresh_token = st.session_state.get(
            "current_refresh_token",
            "",
        )

        if not refresh_token:

            log_error(
                "Aucun Refresh Token Zoom disponible."
            )

            return None

        # ----------------------------------------------------------------------
        # 4. Appel OAuth Zoom
        # ----------------------------------------------------------------------

        log_info(
            "Demande d'un nouveau token d'accès Zoom..."
        )

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        try:

            response = requests.post(
                ZOOM_OAUTH_URL,
                auth=(
                    self.client_id,
                    self.client_secret,
                ),
                data=payload,
                timeout=API_TIMEOUT,
            )

        except requests.exceptions.RequestException as exc:

            log_error(
                "Erreur réseau lors de "
                f"l'authentification Zoom : {exc}",
                exc_info=True,
            )

            return None

        # ----------------------------------------------------------------------
        # 5. Vérification HTTP
        # ----------------------------------------------------------------------

        if response.status_code != 200:

            log_error(
                "Erreur d'authentification Zoom "
                f"({response.status_code}) : "
                f"{response.text}"
            )

            return None

        # ----------------------------------------------------------------------
        # 6. Parsing JSON
        # ----------------------------------------------------------------------

        try:

            data = response.json()

        except ValueError as exc:

            log_error(
                f"Réponse OAuth Zoom invalide : {exc}",
                exc_info=True,
            )

            return None

        # ----------------------------------------------------------------------
        # 7. Extraction des tokens
        # ----------------------------------------------------------------------

        access_token = data.get(
            "access_token"
        )

        new_refresh_token = data.get(
            "refresh_token"
        )

        expires_in = data.get(
            "expires_in"
        )

        if not access_token:

            log_error(
                "Zoom n'a pas retourné d'access token."
            )

            return None

        # ----------------------------------------------------------------------
        # 8. Calcul du TTL
        # ----------------------------------------------------------------------

        if expires_in:

            ttl = max(
                60,
                int(expires_in) - 60,
            )

        else:

            ttl = TOKEN_CACHE_TTL_SECONDS

        # ----------------------------------------------------------------------
        # 9. Mise en cache
        # ----------------------------------------------------------------------

        st.session_state.access_token = (
            access_token
        )

        st.session_state.token_expires_at = (
            now + ttl
        )

        # ----------------------------------------------------------------------
        # 10. Rotation du Refresh Token
        # ----------------------------------------------------------------------

        if new_refresh_token:

            st.session_state.current_refresh_token = (
                new_refresh_token
            )

            try:

                set_key(
                    ENV_FILE,
                    "ZOOM_REFRESH_TOKEN",
                    new_refresh_token,
                )

                log_info(
                    "Nouveau Refresh Token Zoom sauvegardé."
                )

            except Exception as exc:

                log_warning(
                    "Impossible de sauvegarder le nouveau "
                    f"Refresh Token : {exc}"
                )

        log_info(
            "Token d'accès Zoom obtenu avec succès."
        )

        return access_token

    # ==========================================================================
    # INVALIDATION
    # ==========================================================================

    def invalidate_token(self) -> None:
        """
        Invalide le token actuellement présent en session.
        """

        st.session_state.pop(
            "access_token",
            None,
        )

        st.session_state.pop(
            "token_expires_at",
            None,
        )

        log_info(
            "Token d'accès Zoom invalidé."
        )