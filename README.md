======================================================================
                  ZOOM STORAGE & RECORDING MANAGER
======================================================================

Tableau de bord Streamlit pour l'analyse, le suivi et la gestion du stockage des enregistrements Zoom Cloud (EDHEC Online).

----------------------------------------------------------------------
1. FONCTIONNALITES
----------------------------------------------------------------------
- Authentification Zoom OAuth
- Rafraîchissement automatique du Access Token
- Synchronisation des enregistrements Zoom
- Pagination API
- Requêtes parallèles
- Gestion des erreurs réseau
- Gestion des rate limits
- Retry automatique
- Stockage local SQLite
- Recherche et filtrage
- Export CSV
- Suppression des enregistrements Zoom
- Tableau de bord de stockage
- Projection de saturation du quota
- Analyse des Quick Wins
- Analyse par animateur
- Analyse temporelle
- Comparaison mensuelle

----------------------------------------------------------------------
2. INSTALLATION & PREREQUIS
----------------------------------------------------------------------
1. Cloner ou télécharger le projet :
   cd zoom-recording-manager

2. Installer les dépendances Python depuis le fichier requirements.txt

----------------------------------------------------------------------
3. CONFIGURATION DE L'AUTHENTIFICATION ZOOM (OAUTH 2.0)
----------------------------------------------------------------------
Lien de l'application Marketplace Zoom : https://marketplace.zoom.us/develop/applications/O_DAMeNlS4SxqMp4y5AqpQ/information
Connecter vous sur Zoom via le sign in en haut à droite. Une fois connecté, sur la page du marketplace en bas à gauche, cliquer sur Developer.

ETAPE 1 : Obtenir le code d'autorisation (Authorization Code)
Dans l'application, sous l'onglet Basic information

Après validation, vous serez redirigé vers une URL du type :
https://zoom.us/?code=VOTRE_CODE_TEMPORAIRE
Copiez la valeur du paramètre "code".

ETAPE 2 : Échanger le Code contre un Refresh Token
Exécutez la commande curl suivante dans votre terminal :

curl -X POST "https://zoom.us/oauth/token?grant_type=authorization_code&code=VOTRE_CODE_TEMPORAIRE&redirect_uri=https://zoom.us" -u "VOTRE_CLIENT_ID:VOTRE_CLIENT_SECRET"

Exemple de réponse JSON reçue :
{
  "access_token": "eyJzdiI6...",
  "token_type": "bearer",
  "refresh_token": "eyJzdiI6...",
  "expires_in": 3599,
  "scope": "cloud_recording:read:list_account_recordings:admin cloud_recording:delete:recording_file:admin cloud_recording:delete:meeting_recording:admin cloud_recording:read:recording:admin",
  "api_url": "https://edhec-online.zoom.us"
}

ETAPE 3 : Configurer le fichier .env
Créez un fichier .env à la racine du projet avec le contenu suivant :

ZOOM_CLIENT_ID=VOTRE_CLIENT_ID
ZOOM_CLIENT_SECRET=VOTRE_CLIENT_SECRET
ZOOM_REFRESH_TOKEN=VOTRE_REFRESH_TOKEN_GENERE

----------------------------------------------------------------------
4. DEMARRAGE DE L'APPLICATION
----------------------------------------------------------------------
Lancez l'application avec Streamlit :

python -m streamlit run app.py

L'interface sera accessible sur votre navigateur à l'adresse : http://localhost:8501

----------------------------------------------------------------------
5. STRUCTURE DU PROJET
----------------------------------------------------------------------
support_it-storage-manager/
│
├── src/
│   │
│   ├── clients/
│   │   └── zoom_client.py
│   │
│   ├── config/
│   │   ├── logger.py
│   │   ├── settings.py
│   │   └── texts.py
│   │
│   ├── models/
│   │   └── recording.py
│   │
│   ├── repositories/
│   │   └── recording_repository.py
│   │
│   ├── services/
│   │   ├── zoom_service.py
│   │   ├── auth_service.py
│   │   └── metrics_service.py
│   │
│   └── views/
│       ├── sidebar.py
│       ├── list_view.py
│       └── metrics_view.py
│
├── app.py
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── zoom_recordings.db
======================================================================
