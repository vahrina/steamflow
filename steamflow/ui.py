import os
import subprocess

from . import util_steam_date
from .menu import get_game_context_menu_entries, get_steam_client_context_menu_entries


class SteamPluginUIMixin:
    def get_launch_steam_subtitle(self):
        steamid64 = self.get_active_steam_user_steamid64()
        if not steamid64:
            return "not signed in"
        user_details = self.get_steam_user_details(steamid64)
        account_label = (
            user_details.get("persona_name")
            or user_details.get("account_name")
            or "steam"
        )
        subtitle = str(account_label).lower()
        profile_status = self.get_active_profile_status()
        if profile_status:
            subtitle += f" {str(profile_status).lower()}"
        return subtitle

    def get_launch_steam_result_subtitle(self):
        if self.get_active_steam_user_steamid64():
            return ""
        return "open client or sign in · type ? for commands"

    def format_playtime(self, playtime_minutes):
        if playtime_minutes is None:
            return ""
        if playtime_minutes < 60:
            return f" {playtime_minutes}m"
        hours = playtime_minutes / 60
        return f" {hours:.1f}h"

    def format_last_played(self, last_played_timestamp):
        if not last_played_timestamp:
            return ""
        played_on = util_steam_date.format_steam_last_played(
            last_played_timestamp)
        if not played_on:
            return ""
        return f" {played_on}"

    def format_achievement_progress(self, app_id):
        if not self.should_show_achievements():
            return ""
        achievement_progress = self.get_local_achievement_progress(app_id)
        if not achievement_progress:
            return ""
        unlocked_count, total_count = achievement_progress
        if total_count <= 0:
            return ""
        if unlocked_count <= 0 and not self.has_current_account_local_data(app_id):
            return ""
        return f" {unlocked_count}/{total_count}"

    def get_platform_suffix(self, platforms):
        if not self.should_show_platforms():
            return ""
        labels = [label for key, label in self.PLATFORM_LABELS.items()
                  if platforms.get(key)]
        if not labels:
            return ""
        return f" ({'/'.join(labels)})"

    def build_empty_state_result(self, search_term=None):
        if search_term:
            return self.build_result(
                title=f"no match for '{search_term}'",
                subtitle="try different search",
            )
        return self.build_result(
            title="steamflow",
            subtitle="no installed games",
        )

    def build_api_setup_hint_result(self):
        api_query = self.build_plugin_query("api")
        return self.build_result(
            title="set up api",
            subtitle=f"'{api_query}' -> wishlist, owned detection, profile status",
            icon_path=self.SETTINGS_ICON,
            action=self.build_change_query_action(api_query),
            Score=1,
        )

    def build_search_error_result(self, search_term, error_message):
        return self.build_result(
            title=f"search failed: '{search_term}'",
            subtitle=str(error_message).lower(),
        )

    def build_launch_steam_result(self):
        extra = self.get_launch_steam_result_subtitle()
        return self.build_result(
            title=self.get_launch_steam_subtitle() or "steam",
            subtitle=extra,
            icon_path=self.get_active_steam_avatar_icon(),
            context_data={"menu": "steam_client", "name": "Steam"},
            action=self.build_action("open_steam"),
            Score=10000,
        )

    UPDATE_STATUS_MARKERS = {
        "Updating": " vv",
        "Update Paused": " ||",
        "Update Queued": " ??",
        "Update Required": " !!",
    }

    def should_prefetch_refund_state(self, app_id):
        playtime_minutes = self.get_playtime_minutes(app_id)
        return playtime_minutes is None or playtime_minutes < 120

    def build_local_result(
        self,
        app_id,
        name,
        include_player_count=False,
        player_count=None,
        player_count_loaded=False,
        refund_state=None,
    ):
        status_label = self.get_installed_game_status(app_id)
        title_marker = self.UPDATE_STATUS_MARKERS.get(status_label, "")

        # subtitle: metrics only, no "installed" prefix
        subtitle_parts = []
        if self.should_show_playtime():
            pt = self.format_playtime(self.get_playtime_minutes(app_id))
            if pt:
                subtitle_parts.append(pt.lstrip(" |"))
        ach = self.format_achievement_progress(app_id)
        if ach:
            subtitle_parts.append(ach.lstrip(" |"))
        if self.should_show_last_played():
            lp = self.format_last_played(
                self.get_last_played_timestamp(app_id))
            if lp:
                subtitle_parts.append(lp.lstrip(" |"))
        notice = self.get_local_game_account_notice(app_id)
        if notice:
            subtitle_parts.append(notice.lstrip(" |"))
        if include_player_count and self.should_show_player_count():
            pc = (
                self.format_player_count(player_count)
                if player_count_loaded
                else self.format_player_count(self.get_current_players(app_id))
            )
            if pc:
                subtitle_parts.append(pc.lstrip(" |"))

        subtitle = " · ".join(subtitle_parts)

        if self.should_prefetch_refund_state(app_id):
            self.get_app_details_metadata(app_id, allow_network_on_miss=False)
        if refund_state is None:
            refund_state = self.get_refund_state_for_local_game(
                app_id, allow_network_on_miss=False)
        playtime_minutes = self.get_playtime_minutes(app_id)
        has_current_account_local_data = self.has_current_account_local_data(
            app_id)

        return self.build_result(
            # leading controller emoji: \U0001F3AE
            title=f"{name}{title_marker}",
            subtitle=subtitle,
            icon_path=self.get_local_game_icon(app_id),
            context_data=self.build_context_data(
                app_id=app_id,
                name=name,
                install_path=self.get_install_path(app_id),
                refund_state=refund_state,
                playtime_minutes=playtime_minutes,
                has_current_account_local_data=has_current_account_local_data,
            ),
            action=self.build_action("launch_game", app_id),
        )

    def build_context_menu_item(self, title, subtitle, method, *parameters, icon_path=None):
        return self.build_result(
            title=title,
            subtitle=subtitle,
            icon_path=icon_path or self.DEFAULT_ICON,
            action=self.build_action(method, *parameters),
        )

    def get_steam_client_context_menu_items(self):
        return [
            self.build_context_menu_item(
                entry["title"],
                entry["subtitle"],
                entry["method"],
                icon_path=entry["icon"],
            )
            for entry in get_steam_client_context_menu_entries(
                self.DEFAULT_ICON,
                self.SETTINGS_ICON,
                self.COMMUNITY_ICON,
            )
        ]

    def get_context_menu_items(self, app_id, name, install_path, is_owned=False, refund_state=""):
        cache_key = (str(app_id or ""), name, install_path or "",
                     bool(is_owned), str(refund_state or ""))
        with self.state_lock:
            cached_items = self.context_menu_cache.get(cache_key)
        if cached_items is not None:
            return cached_items

        items = [
            self.build_context_menu_item(
                entry["title"],
                entry["subtitle"],
                entry["method"],
                *entry.get("parameters", []),
                icon_path=entry["icon"],
            )
            for entry in get_game_context_menu_entries(
                app_id,
                name,
                install_path,
                is_owned,
                refund_state,
                self.DEFAULT_ICON,
                self.STEAMDB_ICON,
                self.GUIDES_ICON,
                self.DISCUSSIONS_ICON,
                self.SCREENSHOT_ICON,
                self.REFUND_ICON,
                self.PROPERTIES_ICON,
                self.LOCATION_ICON,
                self.DOWNLOAD_ICON,
                self.TRASH_ICON,
            )
        ]

        with self.state_lock:
            self.context_menu_cache[cache_key] = items
        return items

    def context_menu(self, data):
        if not isinstance(data, dict):
            return

        if data.get("menu") == "steam_client":
            items = self.get_steam_client_context_menu_items()
            for item in items:
                self.add_result(item)
            return

        app_id = str(data.get("app_id", ""))
        name = data.get("name", "Game")
        install_path = data.get(
            "install_path") or self.get_install_path(app_id)
        is_owned = bool(data.get("is_owned"))
        refund_state = str(data.get("refund_state", "") or "")

        for item in self.get_context_menu_items(app_id, name, install_path, is_owned=is_owned, refund_state=refund_state):
            self.add_result(item)

    def launch_game(self, app_id):
        uri = f"steam://rungameid/{app_id}"
        try:
            os.startfile(uri)
            return "Game launched"
        except Exception as original_error:
            try:
                subprocess.run(["start", uri], shell=True)
                return "Game launched"
            except Exception:
                self.log(
                    "error", f"Failed to launch game {app_id}: {original_error}")
                return f"Failed to launch game: {str(original_error)}"
