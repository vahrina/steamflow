import os
import re
import subprocess
import time
from pathlib import Path

_STEAM_SETTINGS_PAGE_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


class SteamPluginActionsMixin:
    STEAM_GAMES_URI = "steam://nav/games"
    STEAM_FRIENDS_STATUS_URIS = {
        "online": "steam://friends/status/online",
        "away": "steam://friends/status/away",
        "invisible": "steam://friends/status/invisible",
        "offline": "steam://friends/status/offline",
    }
    _STATUS_KEY_TO_PERSONA_STATE = {
        "online": 1,
        "away": 3,
        "invisible": 7,
        "offline": 0,
    }

    def _log_action_error(self, message):
        log_method = getattr(self, "log", None)
        if callable(log_method):
            log_method("error", message)

    def _log_action_exception(self, message):
        log_exception = getattr(self, "log_exception", None)
        if callable(log_exception):
            log_exception(message)

    def _open_https_in_steam_client(self, url):
        target = str(url or "").strip()
        if not target:
            return "missing url"
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"
        steam_uri = f"steam://openurl/{target}"
        try:
            os.startfile(steam_uri)
            return f"opened in steam: {target}"
        except Exception as error:
            self._log_action_error(f"failed to open in steam: {steam_uri}: {error}")
            return f"failed to open in steam: {str(error)}"

    def _start_steam_protocol(self, uri):
        target = str(uri or "").strip()
        if not target:
            return "missing steam uri"
        try:
            os.startfile(target)
            return f"opened {target}"
        except Exception as error:
            self._log_action_error(f"failed to open steam uri {target}: {error}")
            return f"failed to open steam uri: {str(error)}"

    def open_steam_community_home(self):
        return self._start_steam_protocol("steam://open/communityHome/")

    def open_steam_activity_feed(self):
        return self._start_steam_protocol("steam://open/activity")

    def open_steam_library_nav(self):
        return self._start_steam_protocol(self.STEAM_GAMES_URI)

    def open_steam_market(self):
        return self._start_steam_protocol("steam://openurl/https://steamcommunity.com/market/")

    def open_steam_my_groups(self):
        return self._start_steam_protocol("steam://openurl/https://steamcommunity.com/my/groups/")

    def open_steam_my_profile_client(self):
        steamid64 = str(self.get_active_steam_user_steamid64() or "").strip()
        if steamid64.isdigit():
            return self._start_steam_protocol(f"steam://open/profiles/{steamid64}")
        return self.open_steam_url("https://steamcommunity.com/my")

    def open_steam_store_front(self):
        return self._start_steam_protocol("steam://openurl/https://store.steampowered.com/")

    def open_steam_points_shop(self):
        return self._open_https_in_steam_client("https://store.steampowered.com/points/shop")

    def open_steam_url(self, url):
        target = str(url or "").strip()
        if not target:
            return "missing url"
        return self._open_https_in_steam_client(target)

    def open_steam_friends_recent_players(self):
        return self._start_steam_protocol("steam://friends/players")

    def open_steam_settings_sub_page(self, page):
        raw = str(page or "").strip().lower()
        if not raw or _STEAM_SETTINGS_PAGE_RE.match(raw) is None:
            return f"invalid settings page: {page}"
        return self._start_steam_protocol(f"steam://settings/{raw}")

    def open_steam_url_named_page(self, path_segment):
        seg = str(path_segment or "").strip()
        if not seg:
            return "missing url page name"
        return self._start_steam_protocol(f"steam://url/{seg}")

    _STEAM_NAV_COMPONENT_EXACT = frozenset(
        {
            "console",
            "downloads",
            "games",
            "games/grid",
            "games/list",
            "library/collection/hidden",
        }
    )

    def open_steam_nav_component(self, component_path):
        raw = str(component_path or "").strip().strip("/")
        if not raw or ".." in raw or "\\" in raw:
            return "invalid steam://nav component"
        if raw in self._STEAM_NAV_COMPONENT_EXACT:
            return self._start_steam_protocol(f"steam://nav/{raw}")
        prefix = "games/details/"
        if raw.startswith(prefix):
            tail = raw[len(prefix) :]
            if tail.isdigit():
                return self._start_steam_protocol(f"steam://nav/{raw}")
        return f"invalid steam://nav component: {component_path}"

    _STEAM_NATIVE_MY_PATH_SUFFIXES = {
        "/friends": "steam://friends",
        "/home": "steam://open/activity",
    }

    def open_steam_my_path(self, suffix):
        normalized_suffix = str(suffix or "").strip()
        if not normalized_suffix:
            normalized_suffix = "/"
        if not normalized_suffix.startswith("/"):
            normalized_suffix = f"/{normalized_suffix}"
        steam_uri = self._STEAM_NATIVE_MY_PATH_SUFFIXES.get(normalized_suffix)
        if steam_uri:
            return self._start_steam_protocol(steam_uri)
        return self.open_steam_url(f"https://steamcommunity.com/my{normalized_suffix}")

    def open_settings_tree(self):
        ensure_startup_initialized = getattr(self, "ensure_startup_initialized", None)
        startup_initialized = getattr(self, "startup_initialized", False)
        if callable(ensure_startup_initialized) and not startup_initialized:
            ensure_startup_initialized()

        get_tree_path = getattr(self, "get_settings_tree_file_path", None)
        get_opener = getattr(self, "get_settings_tree_opener_exe", None)
        if not callable(get_tree_path):
            return "settings tree not configured"

        tree_path = get_tree_path()
        if not tree_path.exists():
            return f"tree file not found: {tree_path}"

        opener_raw = get_opener() if callable(get_opener) else ""
        opener = str(opener_raw or "").strip().strip('"').strip("'")

        if opener:
            exe_path = Path(opener)
            if not exe_path.is_file():
                return f"opener exe not found: {exe_path}"
            try:
                subprocess.Popen(
                    [str(exe_path), str(tree_path)],
                    close_fds=True,
                )
                return f"opened tree with {exe_path.name}"
            except Exception as error:
                self._log_action_error(f"failed to launch tree opener: {error}")
                return f"failed to launch opener: {str(error)}"

        try:
            os.startfile(str(tree_path))
            return f"opened {tree_path.name}"
        except Exception as error:
            self._log_action_error(f"failed to open tree file: {error}")
            return f"failed to open tree: {str(error)}"

    def open_steam_store_page(self, app_id):
        uri = f"steam://store/{app_id}"
        try:
            os.startfile(uri)
            return f"store page opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to open store page for appid {app_id}: {error}")
            return f"failed to open store page: {str(error)}"

    def open_steam_guides_page(self, app_id):
        uri = f"steam://openurl/https://steamcommunity.com/app/{app_id}/guides/"
        try:
            os.startfile(uri)
            return f"guides opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to open guides for app {app_id}: {error}")
            return f"failed to open guides: {str(error)}"

    def open_steam_discussions_page(self, app_id):
        uri = f"steam://openurl/https://steamcommunity.com/app/{app_id}/discussions/"
        try:
            os.startfile(uri)
            return f"discussions opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to open discussions for app {app_id}: {error}")
            return f"failed to open discussions: {str(error)}"

    def open_steam_game_properties_page(self, app_id):
        uri = f"steam://gameproperties/{app_id}"
        try:
            os.startfile(uri)
            return f"game properties opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to open game properties for app {app_id}: {error}")
            return f"failed to open game properties: {str(error)}"

    def open_steam_screenshots_page(self, app_id):
        uri = f"steam://open/screenshots/{app_id}"
        try:
            os.startfile(uri)
            return f"recordings & screenshots opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to open recordings & screenshots for appid {app_id}: {error}")
            return f"failed to open recordings & screenshots: {str(error)}"

    def open_steam_refund_page(self, app_id):
        uri = f"steam://openurl/https://help.steampowered.com/en/wizard/HelpWithGameIssue/?appid={app_id}&issueid=108"
        try:
            os.startfile(uri)
            return f"refund page opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to open refund page for appid {app_id}: {error}")
            return f"failed to open refund page: {str(error)}"

    def open_steam(self):
        try:
            os.startfile(self.STEAM_GAMES_URI)
            return "steam opened"
        except Exception:
            ensure_startup_initialized = getattr(self, "ensure_startup_initialized", None)
            startup_initialized = getattr(self, "startup_initialized", False)
            if callable(ensure_startup_initialized) and not startup_initialized:
                ensure_startup_initialized()

            steam_path = getattr(self, "steam_path", None)
            if steam_path:
                steam_exe = Path(steam_path) / "steam.exe"
                if steam_exe.exists():
                    try:
                        subprocess.run([str(steam_exe)])
                        return "steam opened"
                    except Exception:
                        self._log_action_exception("failed to launch steam.exe directly")
            return "failed to open steam"

    def exit_steam(self):
        ensure_startup_initialized = getattr(self, "ensure_startup_initialized", None)
        startup_initialized = getattr(self, "startup_initialized", False)
        if callable(ensure_startup_initialized) and not startup_initialized:
            ensure_startup_initialized()

        terminator = getattr(self, "terminate_steam_processes", None)
        if not callable(terminator):
            return "exit not supported"
        try:
            terminator()
            change_query = getattr(self, "change_query", None)
            if callable(change_query):
                try:
                    build_plugin_query = getattr(self, "build_plugin_query", None)
                    plugin_home_query = build_plugin_query() if callable(build_plugin_query) else ""
                    change_query(plugin_home_query, True)
                except Exception:
                    self._log_action_exception("failed to reset launcher query after exit")
            return "steam closed"
        except Exception as error:
            self._log_action_error(f"failed to close steam: {error}")
            return f"failed to close steam: {str(error)}"

    def restart_steam(self):
        close_result = self.exit_steam()
        if str(close_result).lower().startswith("failed"):
            return close_result
        open_result = self.open_steam()
        if str(open_result).lower().startswith("failed"):
            return f"steam closed, but relaunch failed: {open_result}"
        return "steam restarted"

    def open_steam_settings(self):
        try:
            os.startfile("steam://settings/")
            return "settings opened"
        except Exception as error:
            self._log_action_error(f"failed to open settings: {error}")
            return f"failed to open settings: {str(error)}"

    def open_steam_friends(self):
        try:
            os.startfile("steam://friends")
            return "friends opened"
        except Exception as error:
            self._log_action_error(f"failed to open friends: {error}")
            return f"failed to open friends: {str(error)}"

    def set_steam_friends_status(self, status):
        normalized_status = str(status or "").strip().lower()
        uri = self.STEAM_FRIENDS_STATUS_URIS.get(normalized_status)
        if not uri:
            return f"invalid status: {status}"

        try:
            os.startfile(uri)
            pending_state = self._STATUS_KEY_TO_PERSONA_STATE.get(normalized_status)
            if pending_state is not None:
                with self.state_lock:
                    self._pending_persona_state = pending_state
                    self._pending_persona_state_expiry = time.time() + 15.0
            change_query = getattr(self, "change_query", None)
            if callable(change_query):
                try:
                    build_plugin_query = getattr(self, "build_plugin_query", None)
                    plugin_home_query = build_plugin_query() if callable(build_plugin_query) else ""
                    change_query(plugin_home_query, True)
                except Exception:
                    self._log_action_exception("failed to reset launcher query after changing status")
            return f"status set to {normalized_status.title()}"
        except Exception as error:
            self._log_action_error(f"failed to set friends status to {normalized_status}: {error}")
            return f"failed to set status: {str(error)}"

    def open_steam_library_game_details(self, app_id):
        uri = f"steam://nav/games/details/{app_id}"
        try:
            os.startfile(uri)
            return f"library details opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to open library details for app {app_id}: {error}")
            return f"failed to open library details: {str(error)}"

    def open_my_steam_wishlist(self):
        return self._open_https_in_steam_client("https://steamcommunity.com/my/wishlist/")

    def install_steam_game(self, app_id):
        try:
            os.startfile(f"steam://install/{app_id}")
            schedule_refresh = getattr(self, "schedule_installed_games_refresh", None)
            if callable(schedule_refresh):
                schedule_refresh(delay_seconds=2)
            return f"install opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to install game {app_id}: {error}")
            return f"failed to install game: {str(error)}"

    def uninstall_steam_game(self, app_id):
        try:
            os.startfile(f"steam://uninstall/{app_id}")
            schedule_refresh = getattr(self, "schedule_installed_games_refresh", None)
            if callable(schedule_refresh):
                schedule_refresh(delay_seconds=2)
            return f"uninstall opened for appid: {app_id}"
        except Exception as error:
            self._log_action_error(f"failed to uninstall game {app_id}: {error}")
            return f"failed to uninstall game: {str(error)}"

    def open_local_files(self, install_path):
        try:
            if install_path and Path(install_path).exists():
                os.startfile(install_path)
                return "local files opened"
            return "local files folder not found"
        except Exception as error:
            self._log_action_error(f"failed to open local files '{install_path}': {error}")
            return f"failed to open local files: {str(error)}"

    def open_steamdb_page(self, app_id):
        return self._open_https_in_steam_client(f"https://steamdb.info/app/{app_id}/")

    def get_steamflow_runtime_dir(self):
        rd = getattr(self, "runtime_dir", None)
        if rd is not None:
            return Path(rd)
        return (Path(getattr(self, "plugin_dir", Path(__file__).resolve().parent.parent)) / "var").resolve()

    def open_steamflow_data_folder(self):
        rd = self.get_steamflow_runtime_dir()
        rd.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(rd))
            return f"opened {rd}"
        except Exception as error:
            self._log_action_error(f"failed to open plugin data folder: {error}")
            return f"failed to open folder: {str(error)}"

    def open_steam_install_logs_folder(self):
        steam_path = getattr(self, "steam_path", None)
        if not steam_path:
            return "steam installation path unknown"
        logs_dir = Path(steam_path) / "logs"
        if not logs_dir.is_dir():
            return "steam logs folder not found"
        try:
            os.startfile(str(logs_dir))
            return f"opened {logs_dir}"
        except Exception as error:
            self._log_action_error(f"failed to open steam logs folder: {error}")
            return f"failed to open folder: {str(error)}"

    def clear_steamflow_runtime_artifacts(self):
        ensure_startup_initialized = getattr(self, "ensure_startup_initialized", None)
        if callable(ensure_startup_initialized):
            ensure_startup_initialized()
        rd = self.get_steamflow_runtime_dir()
        rd.mkdir(parents=True, exist_ok=True)
        removed = []
        errors = []
        for path in rd.iterdir():
            if not path.is_file():
                continue
            nl = path.name.lower()
            if not (
                nl.endswith(".log")
                or nl.endswith(".lock")
                or (nl.startswith("cache") and nl.endswith(".json"))
            ):
                continue
            try:
                path.unlink()
                removed.append(path.name)
            except OSError as error:
                errors.append(f"{path.name}: {error}")
        reset = getattr(self, "reset_steamflow_runtime_caches_in_memory", None)
        if callable(reset):
            reset()
        update_installed_games = getattr(self, "update_installed_games", None)
        if callable(update_installed_games):
            try:
                update_installed_games(force=True, allow_background=True)
            except Exception:
                self._log_action_exception("refresh installed games after clear failed")
        summary = f"removed {len(removed)} file(s) under var/"
        if errors:
            summary += "; " + "; ".join(errors)
        return summary
