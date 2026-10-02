// Traductions de l'interface — même esprit que l'application de bureau :
// le français est la langue de référence, les données (catégories,
// difficultés...) restent toujours stockées en français en interne, seul
// l'affichage change selon la langue choisie.

const TRANSLATIONS = {
  fr: {
    common_back: "Retour",
    common_minus: "Diminuer",
    common_delete: "Supprimer",
    common_undo: "Annuler",
    common_plus: "Augmenter",
    startup_error_title: "Le démarrage a échoué",
    startup_error_message: "L'application n'a pas pu accéder à ses données locales. Vos recettes ne sont pas perdues — ceci arrive parfois en navigation privée, quand l'espace de stockage est plein, ou juste après une mise à jour du navigateur. Réessayez, ou redémarrez votre navigateur si le problème persiste.",
    startup_error_reload: "Réessayer",
    startup_error_details: "Détails techniques",
    storage_write_error: "Impossible d'enregistrer cette modification (problème de stockage local). Rien n'a été perdu de votre côté, mais réessayez avant de continuer.",
    app_name: "Mes Recettes",
    skip_to_content: "Aller au contenu principal",
    nav_home: "Accueil",
    nav_recipes: "Recettes",
    nav_shopping: "Courses",
    nav_pantry: "Garde-manger",
    home_title: "👋 Bonjour !",
    home_add_recipe: "➕ Nouvelle recette",
    home_view_recipes: "📖 Voir mes recettes",
    home_manage_ingredients: "🥕 Gérer les ingrédients",
    home_import_url: "🌐 Importer depuis un lien",
    nav_import_url: "Importer depuis un lien",
    import_url_label: "Lien de la recette",
    import_url_placeholder: "https://exemple.com/ma-recette",
    import_url_clear_button: "Effacer",
    import_url_paste_button: "📋 Coller le lien copié",
    import_url_paste_empty: "Aucune adresse trouvée dans le presse-papiers.",
    import_url_paste_error: "Impossible de lire le presse-papiers (autorisation refusée par le navigateur). Collez le lien manuellement dans le champ ci-dessus.",
    import_url_button: "🌐 Récupérer la recette",
    import_url_fetching: "Récupération en cours…",
    import_url_error: "Impossible de récupérer cette recette. Le site n'est peut-être pas compatible, ou le lien est incorrect.",
    import_url_error_offline: "Impossible de récupérer cette recette : internet semble indisponible. Vérifiez votre connexion et réessayez.",
    import_url_intro_title: "Ajoutez une recette trouvée sur internet en quelques secondes.",
    import_url_step1: "Sur le site de la recette, copiez l'adresse de la page (ou, si l'application est installée, touchez « Partager » dans votre navigateur et choisissez Mes Recettes).",
    import_url_step2: "Collez-la ci-dessous, puis touchez « Récupérer la recette ».",
    import_url_step3: "Relisez le résultat avant d'enregistrer : les quantités et unités ne sont pas toujours parfaitement reconnues.",
    import_url_compat: "Fonctionne avec la plupart des grands sites de recettes. Les pages réservées aux abonnés ou demandant une connexion ne peuvent pas être lues.",
    import_url_privacy: "🔒 Pour lire la page, l'adresse que vous collez passe par un service intermédiaire (un navigateur ne peut pas lire directement une page d'un autre site ; plusieurs services sont essayés si besoin). Seule cette adresse est transmise, jamais vos recettes ni vos données.",
    import_url_duplicate_warning: "💡 Si un ingrédient de la recette existe déjà dans votre liste sous un nom un peu différent (« oignon jaune » / « oignon »), il peut être ajouté en double. Vous pourrez le corriger dans le formulaire avant d'enregistrer.",
    import_url_failure_warning: "Le site n'a peut-être pas répondu à temps. Réessayez dans quelques secondes ; si cela échoue encore, faites une capture d'écran de la recette et utilisez « Importer depuis une photo ».",
    import_url_no_url: "Collez d'abord une adresse internet.",
    ingredient_duplicates_button: "🔍 Vérifier les doublons",
    ingredient_duplicates_title: "Doublons possibles",
    ingredient_duplicates_none_found: "Aucun doublon détecté.",
    ingredient_duplicates_show_more: "Afficher plus ({count} restantes)",
    ingredient_duplicates_loading: "Recherche de doublons en cours…",
    ingredient_duplicates_hint: "Ces paires d'ingrédients se ressemblent fortement. Fusionnez-les si c'est bien le même ingrédient, ou indiquez que ce n'en est pas un pour ne plus le voir apparaître.",
    ingredient_duplicates_merge_button: "Fusionner",
    ingredient_duplicates_dismiss_button: "Pas un doublon",
    ingredient_duplicates_merge_title: "Lequel garder ?",
    ingredient_duplicates_merge_hint: "L'autre nom sera remplacé par celui-ci dans toutes vos recettes.",
    shopping_save_list_button: "💾 Enregistrer cette liste pour plus tard",
    shopping_save_list_prompt: "Nom de la liste :",
    shopping_saved_lists_button: "📋 Listes enregistrées",
    shopping_saved_lists_title: "Listes de courses enregistrées",
    shopping_saved_lists_empty: "Aucune liste enregistrée.",
    shopping_load_list_button: "Recharger",
    shopping_load_list_confirm: "Remplacer la liste de courses actuelle par celle-ci ?",
    shopping_qr_share_button: "📱 Partager via QR code",
    shopping_qr_scan_button: "📷 Scanner un QR code",
    qrcode_shopping_title: "QR code de la liste de courses",
    qrcode_shopping_hint: "À scanner depuis un autre appareil utilisant l'application, pour y ajouter directement ces articles.",
    qrscan_title: "Scanner un QR code",
    qrscan_hint: "Visez le QR code d'une liste de courses ou d'une recette partagée depuis un autre appareil (mobile ou bureau).",
    qrscan_camera_denied: "Accès à la caméra refusé ou indisponible. Vérifiez les autorisations de l'application dans les réglages du téléphone.",
    qrscan_camera_denied_permission: "L'autorisation d'utiliser l'appareil photo est désactivée pour cette application. Pour l'activer : Réglages du téléphone → Applications → (nom de l'application) → Autorisations → Appareil photo → Autoriser. En attendant, vous pouvez importer une photo déjà prise.",
    qrscan_camera_denied_notfound: "Aucune caméra détectée sur cet appareil.",
    qrscan_camera_denied_busy: "La caméra est utilisée par une autre application. Fermez-la, puis réessayez.",
    qrscan_camera_https_hint: "L'accès à la caméra nécessite une connexion sécurisée (HTTPS) — indisponible tant que l'application n'est pas mise en ligne.",
    qrscan_no_code_found: "Aucun QR code détecté dans l'image. Rapprochez ou éloignez le téléphone, ou vérifiez l'éclairage.",
    qrscan_image_load_error: "Impossible de lire ce fichier comme une image — vérifiez qu'il s'agit bien d'une photo ou d'une capture d'écran valide.",
    qrscan_using_native: "Détection native du système activée — visez le QR code.",
    qrscan_using_jsqr: "Détection standard activée — visez le QR code.",
    qrscan_native_fallback: "Le lecteur natif du système n'est pas disponible sur cet appareil — bascule vers le lecteur de secours.",
    shopping_qr_paste_button_short: "📋 Coller texte",
    home_group_import: "Importer une recette",
    home_group_organize: "Organiser",
    home_group_tools: "Outils",
    home_timer: "⏱️ Minuteur",
    standalone_timers_title: "Minuteurs",
    standalone_timers_intro: "Un ou plusieurs minuteurs indépendants, sans avoir besoin d'ouvrir une recette. Fermer cette fenêtre ne les arrête pas — vous pouvez naviguer ailleurs dans l'app, la notification préviendra le moment venu.",
    home_group_other: "Autre",
    qrpaste_title: "Coller le texte d'un QR code",
    qrpaste_hint: "Scannez le QR code avec une autre application (l'appareil photo, une app de scan...), copiez le texte obtenu, puis collez-le ici.",
    qrpaste_label: "Texte du QR code",
    qrpaste_submit_button: "Importer",
    qrpaste_empty: "Collez d'abord le texte du QR code.",
    qrscan_manual_button: "📷 Scanner maintenant",
    qrscan_choose_image_button: "🖼️ Choisir une image du QR code",
    qrscan_paste_fallback_link: "Le scan ne fonctionne pas ? Coller le contenu du QR code",
    qrscan_not_recognized: "Ce QR code n'est ni une liste de courses ni une recette reconnue par l'application.",
    qrscan_recipe_import_confirm: "Importer « {name} » comme nouvelle recette ?",
    qrscan_import_confirm: "Ajouter ces {count} article(s) à la liste de courses actuelle ?",
    qrscan_import_success: "Liste importée avec succès.",
    qrscan_lib_load_error: "Impossible de charger le lecteur de QR code. Vérifiez votre connexion et réessayez.",
    shopping_delete_list_confirm: "Supprimer cette liste enregistrée ?",
    shopping_list_item_count: "{count} article(s)",
    home_import_photo: "📷 Importer depuis une photo",
    import_photo_title: "Importer depuis une photo",
    import_photo_disclaimer_main: "Prenez ou choisissez une photo d'une recette (livre, magazine, note manuscrite lisible). Le texte est reconnu directement sur votre téléphone — rien n'est envoyé à un service extérieur, mais la reconnaissance télécharge un fichier de quelques Mo la première fois,",
    import_photo_disclaimer_warning: " et n'est jamais parfaite : vérifiez toujours le résultat avant d'enregistrer.",
    import_photo_savedata_warning: "📶 Économie de données activée sur ce téléphone : la reconnaissance de texte va télécharger un modèle de langue (quelques Mo) s'il n'est pas déjà en cache. Vous pouvez continuer, ou attendre d'être en Wi-Fi.",
    import_photo_choose_button: "📷 Choisir une photo",
    import_photo_add_camera: "📷 Prendre une photo",
    import_photo_add_gallery: "🖼️ Choisir depuis la galerie",
    import_photo_add_more: "+ Ajouter une autre photo",
    import_photo_max_reached: "Nombre maximal de photos atteint pour cette recette.",
    import_photo_section_label: "Cette photo contient :",
    import_photo_section_ingredients: "Ingrédients",
    import_photo_section_preparation: "Préparation",
    import_photo_section_general: "Infos générales",
    import_photo_section_mixed: "Recette complète",
    import_photo_section_other: "Autre",
    import_photo_auto_detected: "détecté automatiquement",
    import_photo_manual_needed: "Non déterminé — choisissez la section ci-dessous",
    import_photo_processing_short: "Analyse en cours…",
    import_photo_remove: "Retirer cette photo",
    import_photo_thumbnail_alt: "Photo de recette importée",
    import_photo_crop_button: "✂️ Recadrer",
    import_photo_crop_hint: "Faites glisser les coins pour ne garder que la zone utile, puis validez.",
    import_photo_crop_confirm: "✅ Valider le recadrage",
    import_photo_crop_cancel: "Annuler",
    import_photo_crop_reset: "↺ Réinitialiser",
    import_photo_crop_handle_tl: "Coin haut-gauche du cadre de recadrage",
    import_photo_crop_handle_tr: "Coin haut-droit du cadre de recadrage",
    import_photo_crop_handle_bl: "Coin bas-gauche du cadre de recadrage",
    import_photo_crop_handle_br: "Coin bas-droit du cadre de recadrage",
    import_photo_crop_failed_reverted: "L'analyse du recadrage a échoué : le précédent résultat a été conservé.",
    import_photo_merge_button: "✅ Fusionner et continuer",
    import_photo_merge_hint: "Combine le texte de toutes les photos analysées en une seule recette, à vérifier ensuite dans le formulaire.",
    import_photo_persons_label: "Nombre de personnes pour cette recette :",
    import_photo_persons_detected: "détecté sur une photo",
    import_photo_persons_assumed: "non détecté — valeur supposée, à vérifier",
    import_photo_processing: "Analyse du texte en cours… (peut prendre une minute la première fois)",
    import_photo_error: "Impossible d'analyser cette photo. Réessayez avec une photo plus nette, bien cadrée et bien éclairée.",
    import_photo_no_text: "Aucun texte reconnu sur cette photo.",
    home_statistics: "📊 Statistiques",
    stats_title: "Statistiques",
    stats_total_recipes: "{count} recette(s) au total",
    stats_by_category: "Par catégorie",
    stats_by_difficulty: "Par difficulté",
    stats_favorites_count: "{count} favori(s)",
    stats_most_cooked_heading: "Les plus cuisinées",
    stats_none_cooked_yet: "Aucune recette cuisinée pour l'instant.",
    stats_cooked_line: "{name} — {count} fois",
    stats_never_cooked_heading: "Jamais cuisinées ({count})",
    stats_all_cooked: "Toutes vos recettes ont déjà été cuisinées !",
    stats_and_others: "… et {count} autre(s)",
    stats_stale_heading: "Pas cuisinées depuis {days}+ jours",
    stats_stale_line: "{name} — il y a {days} jours",
    stats_no_stale_recipe: "Aucune recette dans ce cas.",
    stats_avg_cost_heading: "Coût moyen par personne",
    stats_avg_cost_line: "{avg} € (sur {count} recette(s) avec prix connu)",
    stats_no_priced_recipe: "Aucun prix d'ingrédient renseigné pour l'instant.",
    stats_avg_kcal_heading: "Calories moyennes par personne",
    stats_avg_kcal_line: "{avg} kcal (sur {count} recette(s))",
    stats_no_recognized_recipe: "Aucune valeur nutritionnelle disponible pour l'instant.",
    stats_monthly_chart_title: "Recettes cuisinées par mois",
    stats_empty: "Ajoutez des recettes pour voir apparaître des statistiques.",
    home_manage_substitutions: "🔄 Gérer les substituts",
    manage_substitutions_title: "Gérer les substituts",
    manage_substitutions_hint: "Ingrédients ayant au moins un substitut connu. Recherchez n'importe quel ingrédient pour lui en ajouter un.",
    manage_substitutions_search_placeholder: "Rechercher un ingrédient…",
    manage_substitutions_none: "Aucun ingrédient n'a de substitut enregistré pour l'instant.",
    manage_substitutions_count: "{count} substitut(s)",
    home_cookbook_export: "📖 Exporter un livre de cuisine",
    cookbook_title: "Mon Livre de Recettes",
    cookbook_export_hint: "Choisissez les recettes à inclure, dans l'ordre où elles apparaîtront.",
    cookbook_select_all: "Tout sélectionner",
    cookbook_deselect_all: "Tout désélectionner",
    cookbook_export_button: "📖 Générer le PDF",
    cookbook_no_selection: "Sélectionnez au moins une recette.",
    cookbook_recipe_count: "{count} recette(s)",
    cookbook_toc_title: "Sommaire",
    home_what_can_i_cook: "🍳 Que puis-je cuisiner ?",
    whatcancook_title: "Que puis-je cuisiner ?",
    whatcancook_hint: "Repris de votre garde-manger — ajoutez ou retirez des ingrédients pour cette vérification, sans changer le garde-manger lui-même.",
    whatcancook_add_ingredient: "Ajouter un ingrédient",
    whatcancook_no_ingredients: "Ajoutez au moins un ingrédient pour voir les recettes réalisables.",
    whatcancook_no_matches: "Aucune recette ne correspond, même partiellement.",
    whatcancook_feasible: "✅ Réalisable",
    whatcancook_almost: "🟡 Presque ({have}/{total})",
    whatcancook_missing: "Manque : {list}",
    recipe_qrcode_button: "📱 QR code de la recette",
    qrcode_title: "QR code de la recette",
    qrcode_hint: "À scanner avec un autre téléphone pour recevoir le nom et les ingrédients, sans lien ni fichier.",
    qrcode_multi_hint: "Cette recette est trop longue pour un seul QR code : elle a été répartie en {total} QR à scanner l'un après l'autre, dans n'importe quel ordre.",
    qrcode_part_indicator: "QR {current} sur {total}",
    qrcode_part_prev: "◀ Précédent",
    qrcode_part_next: "Suivant ▶",
    qrscan_multi_progress: "✅ Partie {current} sur {total} scannée. Scannez maintenant le prochain QR de cette recette.",
    qrscan_multi_already_have: "Cette partie a déjà été scannée.",
    qrscan_multi_new_batch: "⚠️ Ce QR fait partie d'une autre recette — reprise à zéro pour ce nouveau lot.",
    qrscan_multi_inconsistent: "⚠️ Ce fragment ne correspond pas au lot en cours (nombre de parties incohérent) — ignoré.",
    qrscan_multi_checksum_failed: "❌ Le contenu reconstitué ne correspond pas à la somme de contrôle attendue — une partie est peut-être endommagée. Veuillez recommencer le scan.",
    qrcode_save_button: "💾 Enregistrer en image",
    qrcode_loading: "Génération en cours…",
    qrcode_load_error: "Impossible de générer le QR code (bibliothèque indisponible). Vérifiez votre connexion et réessayez.",
    quick_search_label: "Recherche rapide",
    home_trash: "🗑️ Corbeille",
    trash_title: "Corbeille",
    trash_empty: "La corbeille est vide.",
    trash_restore_button: "Restaurer",
    trash_delete_forever_button: "Supprimer définitivement",
    trash_delete_forever_confirm: "Supprimer définitivement cette recette ? Impossible à annuler.",
    trash_empty_all_button: "🗑 Vider la corbeille",
    trash_empty_all_confirm: "Supprimer définitivement toutes les recettes de la corbeille ?",
    trash_deleted_on: "Supprimée le {date}",
    home_unit_converter: "📐 Convertisseur d'unités",
    unitconv_title: "Convertisseur d'unités",
    unitconv_intro: "Petit outil indépendant de toute recette, pratique pour une recette trouvée ailleurs (ex. en tasses/onces).",
    unitconv_quantity_label: "Quantité",
    unitconv_from_label: "De",
    unitconv_to_label: "Vers",
    unitconv_convert_button: "Convertir",
    unitconv_error_invalid_quantity: "Quantité invalide.",
    unitconv_result: "{quantity} {from_unit} ≈ {result} {to_unit}",
    unitconv_density_warning: "⚠️ Cette conversion suppose une densité proche de celle de l'eau : 1 mL ≈ 1 g. Le résultat peut être inexact pour d'autres ingrédients, notamment la farine, l'huile ou le miel.",
    unitconv_gram: "Gramme (g)",
    unitconv_kilogram: "Kilogramme (kg)",
    unitconv_ounce: "Once (oz)",
    unitconv_pound: "Livre (lb)",
    unitconv_milliliter: "Millilitre (ml)",
    unitconv_centiliter: "Centilitre (cl)",
    unitconv_liter: "Litre (L)",
    unitconv_teaspoon: "Cuillère à café",
    unitconv_tablespoon: "Cuillère à soupe",
    unitconv_cup: "Tasse",
    home_backup: "💾 Sauvegarde / restauration",
    home_compare_recipes: "⚖️ Comparer deux recettes",
    nav_backup: "Sauvegarde",
    nav_diagnostic: "Diagnostic",
    privacy_policy_link: "Confidentialité",
    diagnostic_title: "Diagnostic technique",
    diagnostic_intro: "Informations techniques utiles en cas de problème à signaler — ne contient aucune recette, aucun contenu personnel ni aucune adresse importée.",
    diagnostic_app_version: "Version de l'application",
    diagnostic_cache_version: "Version du cache",
    diagnostic_browser: "Navigateur",
    diagnostic_os: "Système",
    diagnostic_install_mode: "Mode d'utilisation",
    diagnostic_install_standalone: "Application installée",
    diagnostic_install_browser: "Onglet de navigateur",
    diagnostic_storage_persistent: "Stockage persistant",
    diagnostic_storage_granted: "Accordé",
    diagnostic_storage_not_granted: "Non accordé",
    diagnostic_storage_unsupported: "Non pris en charge par ce navigateur",
    diagnostic_storage_used: "Espace local utilisé (approximatif)",
    diagnostic_storage_used_value: "{size} Mo",
    diagnostic_last_backup: "Dernière sauvegarde réussie",
    diagnostic_never: "Jamais",
    diagnostic_last_import_service: "Dernier service d'import utilisé",
    diagnostic_last_import_error: "Dernière erreur d'import",
    diagnostic_last_share_error: "Dernière erreur de partage",
    diagnostic_last_worker_error: "Dernière erreur du Worker",
    diagnostic_none: "Aucune",
    diagnostic_connection: "État de la connexion",
    diagnostic_online: "En ligne",
    diagnostic_offline: "Hors connexion",
    diagnostic_qr_native: "Détecteur QR natif",
    diagnostic_available: "Disponible",
    diagnostic_unavailable: "Indisponible",
    diagnostic_copy_button: "📋 Copier le diagnostic",
    diagnostic_copied: "Copié !",
    diagnostic_report_title: "Signaler un problème",
    diagnostic_report_hint: "Décrivez ce qui s'est passé — les informations techniques ci-dessus seront jointes automatiquement.",
    diagnostic_report_placeholder: "Décrivez ici le problème rencontré…",
    diagnostic_report_empty: "Décrivez d'abord le problème rencontré avant de le signaler.",
    diagnostic_report_button: "📨 Signaler ce problème",
    diagnostic_report_share_title: "Signalement — Mes Recettes, Mes Courses",
    diagnostic_report_fallback: "Le texte du signalement a été copié — envoyez-le par exemple par e-mail à majogari81@gmail.com, ou collez-le où vous le souhaitez.",
    backup_export_title: "Exporter mes données",
    backup_export_text: "Enregistre toutes vos recettes, courses, garde-manger et ingrédients personnalisés dans un seul fichier, pour les garder en sécurité ou les transférer sur un autre appareil.",
    backup_export_button: "📤 Exporter (.json)",
    backup_import_title: "Importer des données",
    backup_shared_title: "Sauvegarde partagée avec l'app Windows",
    backup_shared_text: "Format compatible avec l'application de bureau — recettes (avec leurs photos), ingrédients connus, garde-manger et personnalisations. Le planning, les menus et les listes de courses enregistrées ne sont pas encore inclus dans ce format.",
    backup_shared_export_button: "Exporter (.zip)",
    backup_shared_import_button: "Importer depuis l'app Windows (.zip)",
    backup_shared_import_success: "Importé : {imported} nouvelle(s) recette(s), {updated} mise(s) à jour.",
    backup_import_text: "Charge un fichier exporté précédemment. Choisissez ce que vous voulez en faire ci-dessous.",
    backup_import_button: "📥 Choisir un fichier à importer",
    backup_no_file_chosen: "Aucun fichier choisi",
    backup_import_mode_title: "Comment importer ?",
    backup_import_mode_replace: "Remplacer tout",
    backup_import_mode_merge: "Fusionner (sans effacer)",
    backup_import_confirm_replace: "Ceci va effacer toutes vos données actuelles et les remplacer par celles du fichier. Continuer ?",
    backup_import_success: "Import réussi !",
    backup_import_success_with_safety: "Import réussi ! Vos anciennes données ont aussi été téléchargées par précaution avant le remplacement.",
    backup_import_error: "Ce fichier n'est pas un fichier de sauvegarde valide.",
    backup_import_large_file_warning: "Ce fichier est volumineux ({size} Mo). L'analyser peut prendre un moment. Continuer ?",
    backup_import_too_large: "Ce fichier dépasse la limite de {size} Mo et ne peut pas être importé.",
    backup_preview_text: "{date}{recipes} recette(s), {ingredients} ingrédient(s), {menus} menu(s), {shopping} article(s) dans la liste de courses.\n\nContinuer avec cette sauvegarde ?",
    backup_ignored_items: "\n\n⚠️ {count} élément(s) ignoré(s) car invalide(s).",
    backup_photos_removed: "\n📷 {count} photo(s) invalide(s) retirée(s).",
    backup_numbers_fixed: "\n🔢 {count} valeur(s) numérique(s) incorrecte(s) corrigée(s).",
    backup_structural_fixes: "\n🛠️ {count} élément(s) mal formé(s) corrigé(s) ou retiré(s) (nom, note, catégorie, unité...).",
    backup_export_success: "Sauvegarde téléchargée avec succès.",
    backup_share_button: "📤 Partager la sauvegarde (Drive, Dropbox...)",
    backup_share_preparing: "⏳ Préparation...",
    backup_share_hint: "Ouvre le menu de partage de votre téléphone : choisissez votre application cloud pour y envoyer la sauvegarde, en dehors du navigateur.",
    backup_share_fallback_notice: "Le partage direct n'est pas disponible sur cet appareil — la sauvegarde a été enregistrée dans le dossier Téléchargements à la place.",
    backup_android_tip_title: "💡 Conserver une copie dans le cloud",
    backup_android_tip_text: "Le bouton \"Exporter\" enregistre la sauvegarde uniquement sur cet appareil (dossier Téléchargements) — elle n'apparaît pas automatiquement sur vos autres appareils. Pour l'envoyer vers Google Drive, OneDrive ou un autre service et la retrouver ailleurs, utilisez plutôt \"Partager la sauvegarde\" ci-dessous.",
    backup_android_tip_text_no_share: "Le bouton \"Exporter\" enregistre la sauvegarde uniquement sur cet appareil (dossier Téléchargements) — elle n'apparaît pas automatiquement sur vos autres appareils. Votre navigateur ne propose pas ici de partage direct : pour l'envoyer vers Google Drive, OneDrive ou un autre service, ouvrez ce dossier Téléchargements et envoyez le fichier vous-même vers l'application de votre choix.",
    home_empty_restore_hint: "Vous avez déjà une sauvegarde ? Vous pouvez la restaurer.",
    home_empty_restore_button: "Restaurer une sauvegarde",
    backup_share_title: "Sauvegarde Mes Recettes",
    home_backup_reminder: "💾 Ça fait un moment que vous n'avez pas sauvegardé vos données. Touchez ici pour le faire en un instant.",
    home_backup_reminder_urgent: "⚠️ Cela fait plus d'un mois que vous n'avez pas sauvegardé vos données. Touchez ici pour le faire maintenant.",
    home_backup_reminder_critical: "🔴 Cela fait plus de deux mois sans sauvegarde — vos données ne sont protégées que sur cet appareil. Touchez ici pour les mettre en sécurité.",
    pantry_reduction_summary_title: "D'après votre garde-manger",
    pantry_reduction_fully_covered: "{name} : déjà assez au garde-manger, non ajouté",
    pantry_reduction_reduced: "{name} : quantité réduite grâce à ce que vous avez déjà ({qty} {unit} suffisent)",
    pantry_reduction_confirm_continue: "Continuer avec ces ajustements ?",
    update_available_banner: "🔄 Une nouvelle version est disponible.",
    update_available_button: "Mettre à jour maintenant",
    substitutes_title: "Substituts possibles",
    substitutes_none: "Aucun substitut connu pour les ingrédients de cette recette.",
    substitutes_disclaimer: "Suggestions culinaires, pas des équivalences garanties.",
    compare_title: "Comparer deux recettes",
    compare_recipe_a: "Recette A",
    compare_recipe_b: "Recette B",
    compare_select_both: "Choisissez deux recettes pour les comparer.",
    compare_category: "Catégorie",
    compare_difficulty: "Difficulté",
    compare_prep: "Préparation",
    compare_cook: "Cuisson",
    compare_persons: "Personnes",
    compare_common_ingredients: "Ingrédients communs",
    compare_only_in: "Seulement dans",
    compare_none: "Aucun",
    compare_view_recipe: "Voir cette recette",
    home_menus: "📋 Mes menus",
    nav_menus: "Mes menus",
    menu_new_title: "Nouveau menu",
    menu_edit_title: "Modifier le menu",
    menu_name_label: "Nom du menu",
    menu_name_placeholder: "ex. Repas de fête",
    menu_add_recipe: "Ajouter une recette au menu",
    menu_recipes_label: "Recettes du menu",
    menu_no_recipes: "Aucune recette dans ce menu pour l'instant.",
    menu_no_menus: "Vous n'avez pas encore de menu.",
    menu_delete_confirm: "Supprimer ce menu ?",
    menu_generate_shopping: "🛒 Ajouter tout aux courses",
    menu_error_name: "Donnez un nom au menu.",
    home_planning: "📅 Planning de la semaine",
    nav_planning: "Planning",
    planning_empty_slot: "+ Ajouter",
    planning_generate_shopping: "🛒 Générer la liste de courses",
    planning_clear: "🗑 Tout effacer",
    planning_clear_confirm: "Effacer tout le planning de la semaine ?",
    planning_save_template: "💾 Enregistrer comme modèle",
    planning_save_template_prompt: "Nom du modèle :",
    planning_templates_title: "Modèles de planning",
    planning_apply_template: "Appliquer",
    planning_apply_template_confirm: "Remplacer le planning actuel par ce modèle ?",
    planning_delete_template_confirm: "Supprimer ce modèle ?",
    planning_no_templates: "Aucun modèle enregistré.",
    planning_history_title: "Historique du planning",
    planning_view_history: "🕘 Historique des semaines passées",
    planning_history_empty: "Aucune semaine archivée pour l'instant.",
    planning_history_week_of: "Semaine du {date}",
    planning_history_reapply: "Recharger",
    planning_history_reapply_confirm: "Recharger cette semaine dans le planning actuel ? Le planning actuellement affiché sera remplacé.",
    planning_history_delete_confirm: "Supprimer cette semaine de l'historique ?",
    planning_pick_recipe_title: "Choisir une recette",
    slot_breakfast: "Petit-déjeuner",
    slot_lunch: "Déjeuner",
    slot_dinner: "Dîner",
    weekday_monday: "Lundi",
    weekday_tuesday: "Mardi",
    weekday_wednesday: "Mercredi",
    weekday_thursday: "Jeudi",
    weekday_friday: "Vendredi",
    weekday_saturday: "Samedi",
    weekday_sunday: "Dimanche",
    home_donate_button: "☕ Faire un don",
    nav_manage_ingredients: "Gérer les ingrédients",
    ingredient_search_placeholder: "Rechercher un ingrédient…",
    ingredient_no_results: "Aucun ingrédient trouvé.",
    ingredient_list_truncated_hint: "{shown} ingrédients affichés sur {total} — tapez ci-dessus pour rechercher parmi tous les autres.",
    ingredient_name_label: "Nom de l'ingrédient",
    ingredient_edit_title: "Modifier l'ingrédient",
    ingredient_new_title: "Nouvel ingrédient",
    ingredient_delete_confirm: "Supprimer « {name} » de la liste des ingrédients ?",
    ingredient_already_exists: "Cet ingrédient existe déjà.",
    ingredient_did_you_mean: "💡 Vouliez-vous dire « {name} » ?",
    ingredient_nutrition_hint: "Valeurs pour 100 g ou 100 ml. Laissez vide si vous ne les connaissez pas.",
    home_shopping_list: "🛒 Liste de courses",
    search_placeholder: "Rechercher une recette…",
    filter_favorites: "⭐ Favoris",
    filter_quick: "⏱️ Rapide",
    filter_vegetarian: "🥗 Végé",
    filter_wishlist: "💭 Envies",
    category_filter_label: "Catégorie",
    category_filter_all: "Toutes",
    sort_label: "Trier",
    sort_name: "Alphabétique",
    sort_expiration: "Date de péremption",
    sort_rayon: "Rayon",
    sort_manual: "Manuel (glisser-déposer)",
    drag_handle_label: "Glisser pour réordonner, ou flèches haut/bas",
    sort_recent: "Plus récentes",
    sort_prep_time: "Temps de préparation",
    sort_favorite_first: "Favoris d'abord",
    no_recipes_found: "Aucune recette trouvée.",
    no_recipes_yet: "Vous n'avez pas encore de recette.\nCommencez par en ajouter une !",
    recipe_persons: "personnes",
    recipe_prep: "Préparation",
    recipe_cook: "Cuisson",
    recipe_difficulty: "Difficulté",
    recipe_ingredients: "Ingrédients",
    recipe_description: "Description",
    recipe_notes: "Notes personnelles",
    recipe_allergens: "Allergènes",
    recipe_add_to_shopping: "🛒 Ajouter aux courses",
    recipe_cooking_mode: "🖥️ Mode cuisine",
    pdf_include_photo_confirm: "Inclure la photo de cette recette dans le PDF ?",
    cookbook_include_photos: "Inclure les photos des recettes",
    recipe_export_pdf: "📄 Exporter en PDF",
    pdf_prep_label: "Préparation",
    pdf_cook_label: "Cuisson",
    pdf_difficulty_label: "Difficulté",
    pdf_ingredients_label: "Ingrédients",
    pdf_description_label: "Description",
    pdf_notes_label: "Notes personnelles",
    pdf_shopping_filename: "liste-de-courses",
    pdf_recipes_filename: "mon-livre-de-recettes",
    pdf_generated_by: "Généré par Mes Recettes",
    recipe_edit: "✏️ Modifier",
    recipe_duplicate: "📄 Dupliquer",
    recipe_duplicate_suffix: " (copie)",
    recipe_duplicate_success: "Recette dupliquée.",
    recipe_delete: "🗑️ Supprimer",
    recipe_delete_confirm: "Supprimer cette recette ?",
    recipe_min: "min",
    diff_facile: "Facile",
    diff_moyen: "Moyen",
    diff_difficile: "Difficile",
    cat_petit_dejeuner: "Petit-déjeuner",
    cat_entree: "Entrée",
    cat_plat: "Plat",
    cat_dessert: "Dessert",
    cat_apero: "Apéro",
    cat_boisson: "Boisson",
    cat_sauce: "Sauce",
    cat_autre: "Autre",
    form_title_new: "Nouvelle recette",
    form_title_edit: "Modifier la recette",
    form_name: "Nom de la recette",
    form_name_placeholder: "ex. Gratin dauphinois",
    form_category: "Catégorie",
    form_difficulty: "Difficulté",
    form_persons: "Personnes",
    form_prep_time: "Préparation (min)",
    form_cook_time: "Cuisson (min)",
    form_favorite: "⭐ Favori",
    form_vegetarian: "🥗 Végétarien",
    form_allergens: "Allergènes présents",
    form_detect_allergens: "🔍 Détecter automatiquement",
    form_allergens_hint: "Basé sur les ingrédients saisis ci-dessus. À vérifier vous-même sur les emballages : ceci reste indicatif.",
    recipe_nutrition: "Valeurs nutritionnelles par personne (estimation)",
    recipe_nutrition_base: "Valeurs nutritionnelles par personne",
    recipe_nutrition_partial: "estimation partielle",
    ingredient_price_label: "Prix",
    ingredient_price_hint: "Facultatif. Laissez vide si vous ne le connaissez pas.",
    ingredient_substitutes_label: "Substituts possibles",
    ingredient_substitutes_hint: "Vos propres suggestions, en plus de celles déjà connues pour cet ingrédient (le cas échéant).",
    ingredient_substitute_name_placeholder: "Nom du substitut",
    ingredient_substitute_note_placeholder: "Note (facultatif)",
    ingredient_add_substitute: "+ Ajouter un substitut",
    ingredient_price_for: "pour",
    shopping_total_label: "Total estimé",
    shopping_unknown_price: "{count} sans prix connu",
    nutrition_kcal: "kcal",
    nutrition_protein: "Protéines",
    nutrition_carbs: "Glucides",
    nutrition_fat: "Lipides",
    form_wishlist: "💭 À essayer",
    form_ingredients: "Ingrédients",
    form_ingredients_hint: "Indiquez les quantités pour 1 personne : l'application les recalcule automatiquement selon le nombre de convives.",
    form_import_quantity_reminder: "💡 Les quantités ci-dessous ont été recalculées pour 1 personne à partir de la recette importée (prévue à l'origine pour {persons} personne(s)) — c'est normal, elles seront remultipliées automatiquement à l'affichage.",
    form_ingredient_name: "Ingrédient",
    form_ingredient_qty: "Qté",
    ingredient_uncertain_tooltip: "Reconnaissance incertaine (import photo) — vérifiez cette ligne.",
    form_ingredient_unit: "Unité",
    pantry_threshold_label: "Seuil d'alerte (optionnel)",
    pantry_threshold_hint: "Un rappel apparaîtra sur l'accueil dès que la quantité passera en dessous (laissez vide pour ne jamais être alerté).",
    pantry_add_quantity_hint: "Stock actuel : {quantity} {unit} — indiquez ici combien vous venez d'en ajouter (ce nombre sera ajouté au stock existant).",
    pantry_threshold_suffix: " (seuil : {threshold})",
    pantry_expiration_label: "Date de péremption (optionnel)",
    pantry_expiration_hint: "Un rappel apparaîtra sur l'accueil si la date approche ou est dépassée (laissez vide pour ne jamais être alerté).",
    pantry_expiration_placeholder: "JJ/MM/AA",
    pantry_expiration_photo_camera: "📷 Prendre en photo",
    pantry_expiration_photo_gallery: "🖼️ Importer une photo",
    pantry_expiration_photo_analyzing: "Analyse de la photo en cours…",
    pantry_expiration_photo_found: "Date détectée : {date} — à vérifier avant d'enregistrer.",
    pantry_expiration_photo_not_found: "Aucune date reconnue sur cette photo. Réessayez avec un cadrage plus net, ou saisissez-la manuellement.",
    pantry_item_deleted_snack: "{name} supprimé du garde-manger.",
    pantry_expiration_incomplete: "Date incomplète — 6 chiffres attendus (JJ/MM/AA).",
    pantry_expiration_invalid: "Cette date n'existe pas (jour ou mois invalide).",
    pantry_expiration_expired_suffix: " (expiré le {date})",
    pantry_expiration_soon_suffix: " (expire le {date})",
    pantry_expiration_future_suffix: " (à consommer avant le {date})",
    home_low_stock_reminder: "📦 {count} ingrédient(s) presque épuisé(s) dans votre garde-manger : {names} — touchez pour les ajouter à la liste de courses",
    home_expiring_reminder: "⏰ {count} article(s) du garde-manger arrivent à expiration ou sont expirés : {names} — touchez pour les voir",
    barcode_scan_button: "📷 Scanner un code-barres",
    barcode_scan_title: "Scanner un code-barres",
    barcode_scan_hint: "Visez le code-barres du produit. Le nom trouvé sera à confirmer — jamais appliqué automatiquement.",
    barcode_manual_fallback_link: "Saisir le code-barres manuellement",
    barcode_native_unavailable: "La lecture de code-barres par caméra n'est pas prise en charge par ce navigateur. Utilisez la saisie manuelle ci-dessous.",
    barcode_manual_title: "Saisir un code-barres",
    barcode_manual_hint: "Tapez les chiffres du code-barres, visibles sous les traits noirs.",
    barcode_manual_label: "Code-barres",
    barcode_manual_invalid: "Ce code-barres semble incomplet (au moins 8 chiffres attendus).",
    barcode_manual_checksum_invalid: "Ce code-barres ne semble pas valide (vérifiez qu'il n'y a pas d'erreur de saisie).",
    barcode_manual_submit_button: "Valider",
    barcode_net_quantity_hint: "Poids/volume net indiqué sur la fiche produit (à titre indicatif) : {quantity}",
    barcode_product_not_found: "Produit non trouvé automatiquement — vérifiez/complétez le nom vous-même.",
    barcode_lookup_network_error: "Impossible de vérifier ce produit en ligne (pas de connexion ou serveur inaccessible) — complétez le nom vous-même.",
    barcode_import_photo_button: "🖼️ Importer depuis une photo",
    barcode_photo_not_found: "Aucun code-barres reconnu sur cette photo. Réessayez avec une image plus nette, ou saisissez le code-barres manuellement.",
    form_edit_ingredient: "Modifier l'ingrédient",
    form_add_ingredient: "+ Ajouter un ingrédient",
    form_draft_found_confirm: "Une recette non terminée a été retrouvée : « {name} ». La reprendre là où vous l'aviez laissée ?",
    form_draft_untitled: "sans nom",
    form_remove: "🗑",
    form_description: "Description / étapes",
    form_notes: "Notes personnelles",
    form_my_rating_label: "Ma note",
    form_family_opinion_label: "Avis de la famille",
    form_family_opinion_placeholder: "Ex. : Les enfants ont adoré",
    form_improvement_notes_label: "À améliorer la prochaine fois",
    form_improvement_notes_placeholder: "Ex. : Mettre moins de sel",
    form_actual_difficulty_label: "Difficulté réellement constatée",
    form_actual_difficulty_placeholder: "— Comme indiqué —",
    recipe_my_rating: "Ma note",
    recipe_family_opinion: "Avis de la famille",
    recipe_improvement_notes: "À améliorer la prochaine fois",
    recipe_actual_difficulty: "Difficulté réellement constatée",
    form_photo: "📷 Ajouter une photo",
    form_import_source_photos_label: "Photo(s) importée(s) — touchez pour comparer",
    form_import_source_photo_alt: "Photo source de l'import",
    form_save: "💾 Enregistrer",
    common_ok: "OK",
    form_cancel: "Annuler",
    form_error_name: "Donnez un nom à la recette.",
    form_error_ingredient: "Ajoutez au moins un ingrédient.",
    recipeform_duplicate_ingredient_message: "« {list} » apparaît plusieurs fois dans cette recette.\n\nGarder tel quel ou fusionner (quantités additionnées) ?",
    recipeform_keep_duplicates_button: "Garder tel quel",
    recipeform_merge_duplicates_button: "Fusionner",
    shopping_title: "Liste de courses",
    shopping_empty: "Votre liste de courses est vide.\nAjoutez des recettes depuis leur fiche.",
    shopping_clear: "🗑 Vider la liste",
    shopping_clear_confirm: "Vider toute la liste de courses ?",
    shopping_item_delete_confirm: "Supprimer \"{name}\" de la liste ?",
    shopping_quantity_partial_suffix: " + quantité non précisée",
    shopping_checked_of: "cochés",
    unit_piece: "pièce",
    unit_g: "g",
    unit_kg: "kg",
    unit_cl: "cl",
    unit_l: "L",
    unit_tbsp: "c. à soupe",
    unit_tsp: "c. à café",
    unit_can: "boîte/pot/sachet",
    unit_tray: "barquette",
    unit_drizzle: "filet",
    unit_slice: "tranche",
    unit_clove: "gousse",
    unit_other: "autre",
    pantry_empty: "Votre garde-manger est vide.",
    pantry_reservations_title: "Réservations en cours",
    pantry_reservations_hint: "Sert à ne pas vous faire racheter ce que vous avez déjà : quand une recette est ajoutée à la liste de courses, la quantité déjà présente ici est mise de côté plutôt que redemandée.",
    pantry_reservation_from_recipe: "depuis une recette",
    pantry_reservation_legacy: "ancienne réservation (origine non conservée)",
    pantry_reservation_from_shopping: "pour l'article \"{name}\"",
    pantry_reservation_from_shopping_deleted: "pour un article de courses déjà supprimé",
    pantry_reservation_cancel: "Annuler cette réservation",
    pantry_reservations_reset_all: "Réinitialiser toutes les réservations",
    pantry_reservations_reset_confirm: "Réinitialiser toutes les réservations du garde-manger ? Les prochains ajouts à la liste de courses considéreront à nouveau tout le stock comme disponible.",
    pantry_reservations_none: "Aucune réservation en cours.",
    pantry_add: "➕ Ajouter un article",
    cooking_close: "✕ Fermer",
    cooking_timer: "⏲️ Minuteur",
    cooking_timer_start: "▶️ Démarrer",
    cooking_timer_reset: "🔄 Réinitialiser",
    cooking_timer_pause: "⏸ Pause",
    cooking_add_timer: "➕ Ajouter un minuteur",
    cooking_wake_lock_active: "🔆 Écran maintenu allumé pendant la cuisine",
    cooking_wake_lock_unavailable: "L'écran peut s'éteindre automatiquement (fonction indisponible sur cet appareil ou refusée par l'économie d'énergie).",
    cooking_remove_timer: "Supprimer ce minuteur",
    cooking_min_label: "Min.",
    cooking_sec_label: "Sec.",
    cooking_timer_done: "Terminé !",
    cooking_notification_title: "⏰ Minuteur terminé",
    cooking_notification_body: "Votre minuteur de cuisine est arrivé à zéro.",
    cooking_notification_permission_denied: "Les notifications sont bloquées dans les réglages de votre navigateur — le minuteur continuera de sonner et vibrer normalement dans l'application.",
    cooking_read_aloud: "🔊 Lire à voix haute",
    cooking_stop_reading: "⏹ Arrêter la lecture",
    recipe_cooked_button: "🍳 J'ai cuisiné ça !",
    cooklog_title: "Journal de cuisine",
    cooklog_add_note_label: "Une note sur cette fois-ci (facultatif)",
    cooklog_add_photo_label: "Une photo (facultatif)",
    cooklog_save_button: "Enregistrer",
    cooklog_skip_button: "Passer",
    cooklog_no_entries: "Aucune note pour l'instant.",
    cooklog_view_button: "📔 Journal de cuisine",
    cooklog_remove_photo_button: "🗑 Retirer la photo",
    cooklog_delete_confirm: "Supprimer cette entrée du journal ?",
    cooking_stop_alarm: "Arrêter la sonnerie",
    theme_toggle: "🌙 Thème",
    lang_label: "Langue",
    lang_picker_title: "Choisir la langue",
    install_prompt_title: "Installer l'application",
    install_prompt_text: "Ajoutez cette application à votre écran d'accueil pour l'ouvrir comme une vraie app.",
    install_prompt_button: "Installer",
    install_prompt_dismiss: "Plus tard",
    home_install_button: "📲 Installer l'application",
    install_ios_title: "Installer l'application",
    install_ios_instructions: "Sur iPhone/iPad, l'installation se fait via le navigateur : appuyez sur l'icône Partager 􀈂 en bas de l'écran (Safari), puis sur « Sur l'écran d'accueil ».",
    install_ios_close: "Compris",
    install_already_installed: "L'application est déjà installée sur cet appareil.",
  },
};

const ALLERGEN_OPTIONS = ["Gluten", "Lactose", "Œufs", "Arachides", "Fruits à coque",
  "Soja", "Poisson", "Crustacés", "Sésame", "Céleri", "Moutarde",
  "Sulfites", "Lupin", "Mollusques"];

const ALLERGEN_TRANSLATIONS = {
  en: {
    gluten: "Gluten", lactose: "Lactose", "œufs": "Eggs", arachides: "Peanuts",
    "fruits à coque": "Tree nuts", soja: "Soy", poisson: "Fish", "crustacés": "Shellfish",
    "sésame": "Sesame", "céleri": "Celery", moutarde: "Mustard", sulfites: "Sulphites",
    lupin: "Lupin", mollusques: "Molluscs",
  },
  es: {
    gluten: "Gluten", lactose: "Lactosa", "œufs": "Huevos", arachides: "Cacahuetes",
    "fruits à coque": "Frutos de cáscara", soja: "Soja", poisson: "Pescado", "crustacés": "Crustáceos",
    "sésame": "Sésamo", "céleri": "Apio", moutarde: "Mostaza", sulfites: "Sulfitos",
    lupin: "Altramuces", mollusques: "Moluscos",
  },
  de: {
    gluten: "Gluten", lactose: "Laktose", "œufs": "Eier", arachides: "Erdnüsse",
    "fruits à coque": "Schalenfrüchte", soja: "Soja", poisson: "Fisch", "crustacés": "Krebstiere",
    "sésame": "Sesam", "céleri": "Sellerie", moutarde: "Senf", sulfites: "Sulfite",
    lupin: "Lupinen", mollusques: "Weichtiere",
  },
  id: {
    gluten: "Gluten", lactose: "Laktosa", "œufs": "Telur", arachides: "Kacang tanah",
    "fruits à coque": "Kacang pohon", soja: "Kedelai", poisson: "Ikan", "crustacés": "Krustasea",
    "sésame": "Wijen", "céleri": "Seledri", moutarde: "Mustar", sulfites: "Sulfit",
    lupin: "Lupin", mollusques: "Moluska",
  },
  pt: {
    gluten: "Glúten", lactose: "Lactose", "œufs": "Ovos", arachides: "Amendoim",
    "fruits à coque": "Frutos de casca rija", soja: "Soja", poisson: "Peixe", "crustacés": "Crustáceos",
    "sésame": "Sésamo", "céleri": "Aipo", moutarde: "Mostarda", sulfites: "Sulfitos",
    lupin: "Tremoço", mollusques: "Moluscos",
  },
  it: {
    gluten: "Glutine", lactose: "Lattosio", "œufs": "Uova", arachides: "Arachidi",
    "fruits à coque": "Frutta a guscio", soja: "Soia", poisson: "Pesce", "crustacés": "Crostacei",
    "sésame": "Sesamo", "céleri": "Sedano", moutarde: "Senape", sulfites: "Solfiti",
    lupin: "Lupini", mollusques: "Molluschi",
  },
  sv: {
    gluten: "Gluten", lactose: "Laktos", "œufs": "Ägg", arachides: "Jordnötter",
    "fruits à coque": "Nötter", soja: "Soja", poisson: "Fisk", "crustacés": "Kräftdjur",
    "sésame": "Sesam", "céleri": "Selleri", moutarde: "Senap", sulfites: "Sulfiter",
    lupin: "Lupin", mollusques: "Blötdjur",
  },
  no: {
    gluten: "Gluten", lactose: "Laktose", "œufs": "Egg", arachides: "Peanøtter",
    "fruits à coque": "Nøtter", soja: "Soya", poisson: "Fisk", "crustacés": "Krepsdyr",
    "sésame": "Sesam", "céleri": "Selleri", moutarde: "Sennep", sulfites: "Sulfitter",
    lupin: "Lupin", mollusques: "Bløtdyr",
  },
};
const RAYON_KEYWORDS = [
  ["Fruits & Légumes", [
    "ail", "oignon", "echalote", "poireau", "carotte", "celeri", "panais",
    "navet", "betterave", "radis", "pomme de terre", "patate", "topinambour",
    "tomate", "concombre", "courgette", "aubergine", "poivron", "piment",
    "chou", "brocoli", "epinard", "blette", "oseille", "roquette", "mache",
    "laitue", "batavia", "endive", "chicoree", "cresson", "pissenlit",
    "fenouil", "artichaut", "asperge", "petit pois", "haricot vert",
    "haricot beurre", "feve", "mais", "courge", "potiron", "citrouille",
    "champignon", "girolle", "cepe", "truffe", "igname", "manioc", "gombo",
    "salsifis", "cardon", "crosne", "chayotte", "cornichon", "avocat",
    "pomme", "poire", "banane", "orange", "clementine", "mandarine",
    "pamplemousse", "pomelo", "citron", "kiwi", "fraise", "framboise",
    "myrtille", "mure", "groseille", "cassis", "cerise", "griotte",
    "abricot", "peche", "nectarine", "prune", "mirabelle", "reine-claude",
    "raisin", "melon", "pasteque", "ananas", "mangue", "papaye",
    "fruit de la passion", "litchi", "grenade", "figue", "datte", "coing",
    "kaki", "rhubarbe", "noix de coco", "kumquat", "goyave", "carambole",
    "persil", "basilic", "thym", "romarin", "origan",
    "marjolaine", "sauge", "laurier", "menthe", "ciboulette", "cerfeuil",
    "estragon", "aneth", "gingembre frais", "curcuma frais", "citronnelle",
    "germe de soja", "pousse", "algue",
  ]],
  ["Viandes & Poissons", [
    "boeuf", "veau", "porc", "lard", "bacon", "jambon", "saucisse",
    "chorizo", "andouille", "boudin", "saucisson", "pancetta", "agneau",
    "mouton", "poulet", "coq", "dinde", "canard", "magret", "confit de",
    "foie gras", "oie", "pintade", "caille", "pigeon", "lapin", "gibier",
    "chevreuil", "sanglier", "cheval", "steak", "viande", "kefta",
    "saumon", "truite", "cabillaud", "morue", "merlu", "colin", "lieu",
    "bar", "loup de mer", "dorade", "daurade", "thon", "espadon",
    "maquereau", "sardine", "anchois", "hareng", "sole", "turbot",
    "flétan", "raie", "rouget", "saint-pierre", "lotte", "baudroie",
    "congre", "anguille", "carpe", "brochet", "perche", "sandre",
    "tilapia", "panga", "poisson", "surimi", "caviar", "tarama",
    "crevette", "gambas", "langoustine", "homard", "langouste", "crabe",
    "tourteau", "etrille", "moule", "huitre", "palourde",
    "coque", "praire", "bulot", "bigorneau", "couteau", "petoncle",
    "coquille saint-jacques", "calamar", "encornet", "seiche", "poulpe",
    "oursin", "ormeau", "escargot", "grenouille",
  ]],
  // "Boulangerie & Pâtisserie" est volontairement testée avant
  // "Crèmerie" : getIngredientRayon() retourne le PREMIER rayon dont un
  // mot-clé apparaît en sous-chaîne du nom normalisé, et "lait"
  // (Crèmerie) est lui-même une sous-chaîne de "chocolat au lait" —
  // sans cet ordre, ce type de nom composé était classé en Crèmerie
  // plutôt qu'en Boulangerie/Épicerie à cause de "chocolat".
  ["Boulangerie & Pâtisserie", [
    "farine", "levure", "bicarbonate", "chocolat", "cacao", "praline",
    "praline", "nougat", "caramel", "gelatine", "agar-agar", "pectine",
    "pate feuilletee", "pate brisee", "pate sablee", "pate a choux",
    "pate a pizza", "pate filo", "pate a crepes", "pate a gaufres",
    "genoise", "biscuit", "boudoir", "speculoos", "meringue",
    "poudre d'amande", "poudre de noisette", "amande effilee",
    "fruits confits", "nappage", "glacage", "fondant", "marron glace",
    "chataigne", "pain", "baguette", "chapelure", "croutons",
    "biscotte", "cracker", "sucre", "cassonade", "vergeoise", "miel",
    "sirop", "melasse", "vanille",
  ]],
  ["Crèmerie", [
    "lait", "creme", "beurre", "margarine", "yaourt",
    "fromage", "faisselle", "petit-suisse", "mascarpone", "ricotta",
    "cottage", "emmental", "gruyere", "comte", "beaufort", "cantal",
    "reblochon", "morbier", "tomme", "camembert", "brie", "coulommiers",
    "munster", "epoisses", "maroilles", "livarot", "pont-l'eveque",
    "roquefort", "bleu", "fourme", "gorgonzola", "chevre",
    "crottin", "feta", "halloumi", "mozzarella", "burrata", "parmesan",
    "pecorino", "grana padano", "provolone", "gouda", "edam", "cheddar",
    "raclette", "fondue", "babeurre", "kefir", "skyr", "oeuf",
  ]],
  ["Épicerie", [
    "riz", "semoule", "couscous", "boulgour", "quinoa", "epeautre",
    "orge", "sarrasin", "avoine", "ble", "fecule", "maizena",
    "tapioca", "pate", "spaghetti", "penne", "fusilli", "tagliatelle",
    "macaroni", "lasagne", "nouille", "vermicelle", "lentille",
    "pois chiche", "soja", "haricot rouge", "haricot blanc",
    "haricot noir", "huile", "graisse", "saindoux", "ghee",
    "moutarde", "ketchup", "mayonnaise", "vinaigre", "sauce",
    "concentre de tomate", "coulis", "pesto", "tapenade", "houmous",
    "tahini", "confiture", "marmelade", "gelee", "chutney", "pickles",
    "cornichons au vinaigre", "capres", "olive", "raifort",
    "wasabi", "bouillon", "fond de veau", "fumet", "tofu", "seitan",
    "tempeh", "conserve", "boite", "chips", "nachos",
    "pop-corn", "biscuit apero", "cacahuete grillee",
  ]],
  ["Herbes & Épices", [
    "poivre", "sel", "paprika", "cumin", "coriandre en", "cannelle",
    "muscade", "girofle", "cardamome", "anis", "curry", "garam masala",
    "ras el hanout", "za'atar", "sumac", "safran", "vanille en poudre",
    "reglisse", "genievre", "moutarde en poudre", "herbes de provence",
    "bouquet garni", "quatre epices", "piment de cayenne",
    "piment d'espelette", "chili en poudre", "epices",
    "curcuma en poudre", "gingembre en poudre", "sesame",
    "graines de", "colorant",
  ]],
  ["Boissons", [
    "vin", "champagne", "porto", "madere", "marsala", "vermouth",
    "cognac", "armagnac", "calvados", "rhum", "whisky", "bourbon", "gin",
    "vodka", "grand marnier", "cointreau", "amaretto", "kirsch",
    "eau de vie", "biere", "cidre", "cafe", "the",
    "eau gazeuse", "jus de", "sirop de grenadine", "sirop de menthe",
  ]],
];

// Ingrédients presque toujours présents dans une cuisine, utilisés pour
// pré-remplir "Que puis-je cuisiner ?" — même liste que la version
// bureau (PANTRY_STAPLES).
const PANTRY_STAPLES = [
  "Sel", "Poivre", "Huile de tournesol", "Huile d'olive", "Beurre",
  "Farine", "Sucre", "Vinaigre", "Moutarde", "Riz", "Pâtes", "Lait",
];

const RAYON_ORDER = [
  "Fruits & Légumes", "Viandes & Poissons", "Crèmerie",
  "Boulangerie & Pâtisserie", "Épicerie", "Herbes & Épices", "Boissons", "Autre",
];

const RAYON_TRANSLATIONS = {
  en: {
    "fruits & légumes": "Fruits & Vegetables", "viandes & poissons": "Meat & Fish",
    "crèmerie": "Dairy", "boulangerie & pâtisserie": "Bakery & Pastry",
    "épicerie": "Grocery", "herbes & épices": "Herbs & Spices",
    "boissons": "Beverages", "autre": "Other",
  },
  es: {
    "fruits & légumes": "Frutas y verduras", "viandes & poissons": "Carnes y pescados",
    "crèmerie": "Lácteos", "boulangerie & pâtisserie": "Panadería y repostería",
    "épicerie": "Almacén", "herbes & épices": "Hierbas y especias",
    "boissons": "Bebidas", "autre": "Otro",
  },
  de: {
    "fruits & légumes": "Obst & Gemüse", "viandes & poissons": "Fleisch & Fisch",
    "crèmerie": "Milchprodukte", "boulangerie & pâtisserie": "Bäckerei & Konditorei",
    "épicerie": "Lebensmittel", "herbes & épices": "Kräuter & Gewürze",
    "boissons": "Getränke", "autre": "Sonstiges",
  },
  id: {
    "fruits & légumes": "Buah & Sayur", "viandes & poissons": "Daging & Ikan",
    "crèmerie": "Produk Susu", "boulangerie & pâtisserie": "Roti & Kue",
    "épicerie": "Sembako", "herbes & épices": "Bumbu & Rempah",
    "boissons": "Minuman", "autre": "Lainnya",
  },
  pt: {
    "fruits & légumes": "Frutas e Legumes", "viandes & poissons": "Carnes e Peixes",
    "crèmerie": "Lacticínios", "boulangerie & pâtisserie": "Padaria e Pastelaria",
    "épicerie": "Mercearia", "herbes & épices": "Ervas e Especiarias",
    "boissons": "Bebidas", "autre": "Outro",
  },
  it: {
    "fruits & légumes": "Frutta e Verdura", "viandes & poissons": "Carne e Pesce",
    "crèmerie": "Latticini", "boulangerie & pâtisserie": "Panetteria e Pasticceria",
    "épicerie": "Drogheria", "herbes & épices": "Erbe e Spezie",
    "boissons": "Bevande", "autre": "Altro",
  },
  sv: {
    "fruits & légumes": "Frukt & Grönt", "viandes & poissons": "Kött & Fisk",
    "crèmerie": "Mejeri", "boulangerie & pâtisserie": "Bageri & Konditori",
    "épicerie": "Skafferi", "herbes & épices": "Örter & Kryddor",
    "boissons": "Drycker", "autre": "Övrigt",
  },
  no: {
    "fruits & légumes": "Frukt & Grønt", "viandes & poissons": "Kjøtt & Fisk",
    "crèmerie": "Meieriprodukter", "boulangerie & pâtisserie": "Bakervarer & Konditori",
    "épicerie": "Tørrvarer", "herbes & épices": "Urter & Krydder",
    "boissons": "Drikke", "autre": "Annet",
  },
};

function getIngredientRayon(name) {
  const key = normalize(name || "");
  for (const [rayon, keywords] of RAYON_KEYWORDS) {
    for (const kw of keywords) {
      if (key.includes(normalize(kw))) return rayon;
    }
  }
  return "Autre";
}
function translateRayonName(rayon) {
  if (!rayon || CURRENT_LANG === "fr") return rayon;
  const key = rayon.toLowerCase();
  return (RAYON_TRANSLATIONS[CURRENT_LANG] && RAYON_TRANSLATIONS[CURRENT_LANG][key]) || rayon;
}

function translateAllergen(name) {
  if (!name || CURRENT_LANG === "fr") return name;
  const key = name.toLowerCase();
  return (ALLERGEN_TRANSLATIONS[CURRENT_LANG] && ALLERGEN_TRANSLATIONS[CURRENT_LANG][key]) || name;
}

const WEEKDAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
const MEAL_SLOTS = ["Petit-déjeuner", "Déjeuner", "Dîner"];
const WEEKDAY_KEYS = {
  "Lundi": "weekday_monday", "Mardi": "weekday_tuesday", "Mercredi": "weekday_wednesday",
  "Jeudi": "weekday_thursday", "Vendredi": "weekday_friday", "Samedi": "weekday_saturday", "Dimanche": "weekday_sunday",
};
const SLOT_KEYS = {
  "Petit-déjeuner": "slot_breakfast", "Déjeuner": "slot_lunch", "Dîner": "slot_dinner",
};
function translateWeekday(day) {
  return t(WEEKDAY_KEYS[day] || "") || day;
}
function translateSlot(slot) {
  return t(SLOT_KEYS[slot] || "") || slot;
}

const CATEGORY_KEYS = {
  "Petit-déjeuner": "cat_petit_dejeuner",
  "Entrée": "cat_entree",
  "Plat": "cat_plat",
  "Dessert": "cat_dessert",
  "Apéro": "cat_apero",
  "Boisson": "cat_boisson",
  "Sauce": "cat_sauce",
  "Autre": "cat_autre",
};
const DIFFICULTY_KEYS = {
  "Facile": "diff_facile",
  "Moyen": "diff_moyen",
  "Difficile": "diff_difficile",
};
const UNIT_KEYS = {
  "pièce": "unit_piece",
  "g": "unit_g",
  "kg": "unit_kg",
  "cl": "unit_cl",
  "L": "unit_l",
  "c. à soupe": "unit_tbsp",
  "c. à café": "unit_tsp",
  "boîte": "unit_can",
  "barquette": "unit_tray",
  "tranche": "unit_slice",
  "gousse": "unit_clove",
  "filet": "unit_drizzle",
  "autre": "unit_other",
};

// Liste de référence des langues proposées dans le sélecteur (menu
// déroulant, voir renderTopbar) — un seul endroit à modifier pour en
// ajouter une nouvelle plus tard, plutôt qu'un ordre codé en dur répété
// à plusieurs endroits comme avant (ancien bouton qui les faisait
// défiler une à une, devenu impraticable au-delà de 3-4 langues).
const SUPPORTED_LANGUAGES = [
  { code: "fr", flag: "🇫🇷", nativeName: "Français" },
  { code: "en", flag: "🇬🇧", nativeName: "English" },
  { code: "es", flag: "🇪🇸", nativeName: "Español" },
  { code: "de", flag: "🇩🇪", nativeName: "Deutsch" },
  { code: "id", flag: "🇮🇩", nativeName: "Bahasa Indonesia" },
  { code: "pt", flag: "🇵🇹", nativeName: "Português" },
  { code: "it", flag: "🇮🇹", nativeName: "Italiano" },
  { code: "sv", flag: "🇸🇪", nativeName: "Svenska" },
  { code: "no", flag: "🇳🇴", nativeName: "Norsk" },
];

// Textes de l'interface des langues autres que le français : chargés à
// la demande depuis i18n/<code>.json (voir ensureUiTranslationsLoaded
// ci-dessous), pas embarqués ici comme avant — seul le français (langue
// de référence, utilisée en repli partout, voir t()) reste toujours
// disponible immédiatement, sans réseau. Avec 617 clés par langue
// (~40-45 Ko), ce fichier pesait ~176 Ko pour 4 langues alors que la
// quasi-totalité des personnes n'en utilisent qu'une seule à la fois —
// visant une dizaine de langues à terme (voir conversation), ce coût
// aurait continué de grossir pour rien à chaque premier lancement.
const _uiTranslationLoadPromises = {};
async function ensureUiTranslationsLoaded(lang) {
  if (lang === "fr" || TRANSLATIONS[lang]) return;
  if (_uiTranslationLoadPromises[lang]) return _uiTranslationLoadPromises[lang];
  _uiTranslationLoadPromises[lang] = (async () => {
    try {
      const res = await fetch(`./i18n/${lang}.json`);
      TRANSLATIONS[lang] = res.ok ? await res.json() : {};
    } catch (e) {
      // Hors connexion : cette langue reste simplement sans traduction
      // (repli sur le français, déjà géré par t() ci-dessous) plutôt que
      // de faire échouer tout le chargement.
      TRANSLATIONS[lang] = TRANSLATIONS[lang] || {};
    } finally {
      delete _uiTranslationLoadPromises[lang];
    }
  })();
  return _uiTranslationLoadPromises[lang];
}
// Resynchronise le titre de la page et le lien d'évitement (voir
// index.html — hors de #app, jamais retouché par render()) avec
// TRANSLATIONS[CURRENT_LANG] tel qu'il est CE moment : appelée une
// première fois de façon synchrone au chargement (avec ce qui est déjà
// disponible — le français, ou une langue déjà chargée une session
// précédente et reconstituée... non, jamais persistée : donc toujours
// le français à ce stade pour une langue non-fr), puis une seconde fois
// une fois le fichier de langue téléchargé (voir plus bas et setLang).
function applyDocumentChrome() {
  if (typeof document === "undefined") return;
  document.title = t("app_name");
  const skipLinkEl = document.getElementById("skip-link");
  if (skipLinkEl) skipLinkEl.textContent = t("skip_to_content");
}

let CURRENT_LANG = localStorage.getItem("lang") || (navigator.language || "en").slice(0, 2);
// Repli sur l'anglais (pas le français) : la langue du navigateur/
// téléphone n'est pas forcément liée à la nationalité de la personne
// qui l'utilise, et l'anglais reste la langue la plus généralement
// comprise parmi celles non couvertes par les traductions disponibles.
// Vérifié contre SUPPORTED_LANGUAGES (pas contre TRANSLATIONS comme
// avant) : une langue prise en charge mais pas encore chargée (voir
// ci-dessus) doit rester acceptée, pas retomber sur l'anglais.
if (!SUPPORTED_LANGUAGES.some((l) => l.code === CURRENT_LANG)) CURRENT_LANG = "en";
// Synchronise dès le chargement initial (pas seulement lors d'un
// changement manuel via setLang) — sans ça, un appareil détecté en
// anglais/espagnol/allemand dès la première visite gardait quand même
// l'attribut "fr" figé dans index.html, faisant prononcer le contenu
// dans la mauvaise langue par un lecteur d'écran.
if (typeof document !== "undefined") {
  document.documentElement.lang = CURRENT_LANG;
  // Utilise ce qui est déjà disponible tout de suite (le français, voir
  // le repli dans t()) ; si CURRENT_LANG n'est pas "fr", ces deux
  // éléments restent temporairement en français le temps du
  // téléchargement ci-dessous, puis se corrigent tout seuls.
  applyDocumentChrome();
  if (CURRENT_LANG !== "fr") {
    ensureUiTranslationsLoaded(CURRENT_LANG).then(applyDocumentChrome);
  }
}

function t(key, params) {
  let str = (TRANSLATIONS[CURRENT_LANG] && TRANSLATIONS[CURRENT_LANG][key]) || TRANSLATIONS.fr[key] || key;
  if (params) {
    Object.keys(params).forEach((p) => {
      str = str.replace(new RegExp("\\{" + p + "\\}", "g"), params[p]);
    });
  }
  return str;
}
function setLang(lang) {
  if (!SUPPORTED_LANGUAGES.some((l) => l.code === lang)) return;
  CURRENT_LANG = lang;
  localStorage.setItem("lang", lang);
  document.documentElement.lang = lang;
  applyDocumentChrome();
  // Retrie immédiatement selon la traduction de la nouvelle langue —
  // sans ça, la liste restait triée selon l'ordre de la langue
  // précédente jusqu'au prochain redémarrage de l'application.
  if (typeof state !== "undefined" && state.ingredientNames && typeof sortIngredientNamesForDisplay === "function") {
    sortIngredientNamesForDisplay(state.ingredientNames);
  }
  // Textes d'interface ET traductions d'ingrédients/substitutions (voir
  // ensureIngredientTranslationsLoaded dans app.js, chargé après ce
  // fichier — d'où cette vérification défensive, comme les autres
  // ci-dessus) de CETTE langue : chargés à la demande plutôt que tout
  // d'un coup au démarrage. Mis au bon endroit — DANS setLang() plutôt
  // qu'à chaque site d'appel — pour que tout appel à setLang(), y
  // compris depuis les tests ou un futur appelant qui l'ignore,
  // déclenche bien ces deux chargements sans avoir à y penser à chaque
  // fois. Si cette langue est nouvelle pour la session, l'interface et
  // les noms d'ingrédients restent temporairement affichés en français
  // le temps du téléchargement, puis se corrigent tout seuls via un
  // nouveau render() une fois prêts.
  ensureUiTranslationsLoaded(lang).then(() => {
    applyDocumentChrome();
    if (typeof render === "function") render();
  });
  if (typeof ensureIngredientTranslationsLoaded === "function" && typeof render === "function") {
    ensureIngredientTranslationsLoaded(lang).then(() => render());
  }
}
function translateCategory(cat) {
  return t(CATEGORY_KEYS[cat] || "cat_autre");
}
function translateDifficulty(diff) {
  return diff ? t(DIFFICULTY_KEYS[diff] || "") || diff : "";
}
function translateUnit(unit) {
  return unit ? (t(UNIT_KEYS[unit] || "") || unit) : "";
}
