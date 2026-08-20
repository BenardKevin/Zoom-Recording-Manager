TEXTS = {
    "page_title": "Zoom Storage Manager",
    "page_icon": "🎥",
    "app_header": "Zoom Storage Manager",

    "empty_db_info": (
        "Aucun enregistrement disponible dans la base locale. "
        "Lancez une synchronisation depuis la barre latérale."
    ),

    "tabs": {
        "metrics": "📊 Métriques",
        "list": "🎥 Enregistrements",
    },

    "sidebar": {
        "creds_header": "🔐 Identifiants Zoom",

        "client_id_label": "Zoom Client ID",
        "client_secret_label": "Zoom Client Secret",

        "status_ok": "✅ Identifiants renseignés",
        "status_missing": "⚠️ Identifiants manquants",

        "quota_header": "💾 Quota de stockage",
        "quota_label": "Quota Zoom (Go)",

        "sync_header": "🔄 Synchronisation",
        "sync_mode_label": "Mode de synchronisation",

        "sync_modes": [
            "Synchronisation depuis le dernier enregistrement",
            "Synchronisation depuis une date",
        ],

        "sync_mode_help": (
            "La première option récupère les enregistrements récents. "
            "La seconde permet de reconstruire l'historique."
        ),

        "sync_info_prefix": "Synchronisation depuis le",

        "date_input_label": "Date de début",

        "btn_sync": "🔄 Synchroniser Zoom",

        "sync_success": (
            "Synchronisation terminée : {count} enregistrement(s) traité(s)."
        ),

        "warning_missing_creds": (
            "Veuillez renseigner le Client ID et le Client Secret."
        ),
    },

    "filters": {
        "subheader": "🔎 Filtrer les enregistrements",

        "search_label": "Rechercher",
        "sort_by_label": "Trier par",
        "order_label": "Ordre",
        "min_size_label": "Taille minimale (Mo)",

        "sort_options": [
            "Date",
            "Taille",
            "Durée",
        ],

        "order_options": [
            "Croissant",
            "Décroissant",
        ],

        "quick_win_active": (
            "Filtre Quick Win actif : **{name}**"
        ),

        "btn_clear_filter": "❌ Supprimer le filtre",

        "count_caption": "{count} enregistrement(s)",

        "btn_export_csv": "📥 Export CSV",
    },

    "card": {
        "date_format": "{date_str} à {time_str}",
        "duration_format": "⏱️ {duration} min",
        "size_format": "💾 {size:.2f} Mo",

        "link_label": "[🔗 Voir l'enregistrement]({url})",

        "btn_delete": "🗑️",

        "deleting_spinner": "Suppression de l'enregistrement...",

        "toast_deleted": "Enregistrement supprimé.",
    },

    "kpis": {
        "section_storage": "💾 Stockage",
        "section_projection": "📈 Projection",
        "section_activity": "📅 Activité",
        "section_quick_wins": "⚡ Quick Wins",
        "section_top": "🏆 Enregistrements les plus volumineux",
        "section_chart": "📊 Évolution mensuelle",
        "section_hosts": "👤 Répartition par animateur",

        "quota_used": "Quota utilisé",
        "quota_remaining": "Quota restant",
        "avg_file_size": "Taille moyenne",

        "projection_info": (
            "À raison de **{rate:.2f} Go/mois**, le quota de "
            "**{quota:.1f} Go** devrait être atteint vers **{date}** "
            "(environ {months:.1f} mois)."
        ),

        "projection_unlimited": (
            "Pas suffisamment de données récentes pour calculer "
            "une projection fiable."
        ),

        "monthly_count": "Enregistrements ce mois",
        "monthly_size": "Stockage ce mois",
        "avg_duration": "Durée moyenne",

        "quick_win_filter_btn": "Afficher",

        "volume_by_host": "Volume de stockage par animateur",
        "count_by_host": "Nombre d'enregistrements par animateur",

        "no_host_data": (
            "Aucune donnée d'animateur disponible."
        ),
    },
}