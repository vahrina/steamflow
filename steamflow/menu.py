def get_refund_menu_copy(refund_state, name):
    if refund_state == "likely":
        return (
            "refund",
            "eligible if: > 2h played within 14d of purchase",
        )
    if refund_state == "unclear":
        return (
            "check refund options",
            "eligibility unclear ",
        )
    return "", ""


def get_steam_user_context_menu_entries(
    steamid64,
    name,
    is_self,
    default_icon,
    settings_icon,
    community_icon,
    browser_icon,
):
    entries = []
    steamid64 = str(steamid64 or "").strip()
    if steamid64.isdigit():
        entries.extend(
            [
                {
                    "title": "profile",
                    "subtitle": "",
                    "icon": default_icon,
                    "method": "open_steam_user_profile",
                    "parameters": [steamid64]
                },
                {
                    "title": "library",
                    "subtitle": "",
                    "icon": browser_icon,
                    "method": "open_steam_user_library",
                    "parameters": [steamid64]
                },
                {
                    "title": "inventory",
                    "subtitle": "",
                    "icon": community_icon,
                    "method": "open_steam_user_inventory",
                    "parameters": [steamid64]
                },
                {
                    "title": "groups",
                    "subtitle": "",
                    "icon": default_icon,
                    "method": "open_steam_my_groups",
                },
            ]
        )
    if is_self:
        entries.extend(
            [
                {
                    "title": "settings",
                    "subtitle": "",
                    "icon": settings_icon,
                    "method": "open_steam_settings"
                }
            ]
        )
    return entries


def get_game_context_menu_entries(
    app_id,
    name,
    install_path,
    is_owned,
    refund_state,
    default_icon,
    steamdb_icon,
    guides_icon,
    discussions_icon,
    screenshot_icon,
    refund_icon,
    properties_icon,
    location_icon,
    download_icon,
    trash_icon,
    is_unreleased=False,
):
    entries = []
    if app_id:
        entries.append(
            {
                "title": f"store page",
                "subtitle": "",
                "icon": default_icon,
                "method": "open_steam_store_page",
                "parameters": [app_id],
            }
        )
        entries.append(
            {
                "title": f"steamdb",
                "subtitle": "",
                "icon": steamdb_icon,
                "method": "open_steamdb_page",
                "parameters": [app_id],
            }
        )
    if app_id and install_path:
        entries.extend(
            [
                {
                    "title": "launch options",
                    "subtitle": "",
                    "icon": properties_icon,
                    "method": "open_steam_game_properties_page",
                    "parameters": [app_id],
                },
                {
                    "title": "local files",
                    "subtitle": "",
                    "icon": location_icon,
                    "method": "open_local_files",
                    "parameters": [install_path],
                },
                {
                    "title": "uninstall",
                    "subtitle": "",
                    "icon": trash_icon,
                    "method": "uninstall_steam_game",
                    "parameters": [app_id]
                }
            ]
        )
        if not is_unreleased:
            entries.append(
                {
                    "title": "guides",
                    "subtitle": "",
                    "icon": guides_icon,
                    "method": "open_steam_guides_page",
                    "parameters": [app_id],
                }
            )
        entries.append(
            {
                "title": "discussions",
                "subtitle": "",
                "icon": discussions_icon,
                "method": "open_steam_discussions_page",
                "parameters": [app_id],
            }
        )
    if app_id and (install_path or is_owned):
        entries.append(
            {
                "title": "recordings & screenshots",
                "subtitle": "",
                "icon": screenshot_icon,
                "method": "open_steam_screenshots_page",
                "parameters": [app_id],
            }
        )
    if app_id and is_owned and not install_path:
        entries.append(
            {
                "title": "install game",
                "subtitle": "",
                "icon": download_icon,
                "method": "install_steam_game",
                "parameters": [app_id],
            }
        )

    refund_title, refund_subtitle = get_refund_menu_copy(refund_state, name)
    if app_id and install_path and refund_title:
        entries.append(
            {
                "title": refund_title,
                "subtitle": refund_subtitle,
                "icon": refund_icon,
                "method": "open_steam_refund_page",
                "parameters": [app_id],
            }
        )

    return entries
