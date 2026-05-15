import time

from flox.clipboard import get as get_clipboard_text

class SteamPluginUICommandsMixin:
    OWNED_API_QUERY_ALIASES = {"api", "api key", "apikey",}
    SWITCH_ACCOUNT_QUERY_ALIASES = {"switch", "account", "user", "sw", "acc"}
    STATUS_QUERY_ALIASES = {"status", "statuses", "s"}
    EXIT_QUERY_ALIASES = {"exit", "quit", "kill"}
    RESTART_QUERY_ALIASES = {"restart", "relaunch", "reboot", "r"}
    CLEAR_QUERY_ALIASES = {"clear", "clean", "purge", "cl"}
    SETTINGS_QUERY_ALIASES = {"settings", "setting", "s"}
    SETTINGS_TREE_QUERY_ALIASES = {"tree", "t"}
    SETTINGS_HELP_QUERY_ALIASES = {"?", "help", "h"}
    SETTINGS_FZF_QUERY_ALIASES = frozenset({"fzf", "fuzzy", "find"})
    SETTINGS_FZF_MAX_RESULTS = 40
    WISHLIST_QUERY_ALIASES = {"wishlist", "wish list", "w"}
    HELP_QUERY_ALIASES = {"?", "help", "h"}
    STEAM_STATUS_OPTIONS = (
        ("online", "online"),
        ("away", "away"),
        ("invisible", "invisible"),
        ("offline", "offline"),
    )
    STATUS_CURRENT_RESULT_SCORE = 1_000_000
    STATUS_OPTION_BASE_SCORE = 999_000

    WISHLIST_ERROR_HINTS = {
        "Steam API Not Configured": "no api key",
        "Steam API Bound to Another Account": "key bound to another account",
        "No active Steam account found": "no active account",
    }
    SWITCH_AUTOLOGIN_HINT_SUBTITLE = (
        "settings → interface → 'ask which account to use each time steam starts'"
    )

    def get_status_icon_path(self, status_key):
        return {
            "online": self.ONLINE_ICON,
            "offline": self.OFFLINE_ICON,
            "invisible": self.INVISIBLE_ICON,
        }.get(str(status_key or "").strip().lower(), self.COMMUNITY_ICON)

    def is_owned_api_query(self, search_term):
        return str(search_term or "").strip().lower() in self.OWNED_API_QUERY_ALIASES

    def is_switch_account_query(self, search_term):
        return self._extract_query_suffix(search_term, self.SWITCH_ACCOUNT_QUERY_ALIASES) is not None

    def get_switch_query_text(self, search_term):
        value = self._extract_query_suffix(search_term, self.SWITCH_ACCOUNT_QUERY_ALIASES)
        return value if value is not None else ""

    def is_status_query(self, search_term):
        raw_value = str(search_term or "").strip().lower()
        if raw_value in self.STATUS_QUERY_ALIASES:
            return True
        for alias in self.STATUS_QUERY_ALIASES:
            prefix = f"{alias} "
            if raw_value.startswith(prefix):
                return True
        return False

    def get_status_query_text(self, search_term):
        raw_value = str(search_term or "").strip()
        normalized = raw_value.lower()
        for alias in sorted(self.STATUS_QUERY_ALIASES, key=len, reverse=True):
            if normalized == alias:
                return ""
            prefix = f"{alias} "
            if normalized.startswith(prefix):
                return raw_value[len(prefix) :].strip()
        return ""

    def is_exit_query(self, search_term):
        return str(search_term or "").strip().lower() in self.EXIT_QUERY_ALIASES

    def is_wishlist_query(self, search_term):
        return self.get_wishlist_query_text(search_term) is not None

    def is_help_query(self, search_term):
        return str(search_term or "").strip().lower() in self.HELP_QUERY_ALIASES

    def _extract_query_suffix(self, search_term, aliases):
        raw_value = str(search_term or "").strip()
        normalized = raw_value.lower()
        for alias in sorted(set(aliases), key=len, reverse=True):
            if normalized == alias:
                return ""
            prefix = f"{alias} "
            if normalized.startswith(prefix):
                return raw_value[len(prefix) :].strip()
        return None

    def get_wishlist_query_text(self, search_term):
        raw_value = str(search_term or "").strip()
        normalized = raw_value.lower()
        first_token = normalized.split(" ", 1)[0]
        if first_token.startswith("wishl"):
            return raw_value.split(" ", 1)[1].strip() if " " in raw_value else ""
        for alias in sorted(self.WISHLIST_QUERY_ALIASES, key=len, reverse=True):
            if normalized == alias:
                return ""
            prefix = f"{alias} "
            if normalized.startswith(prefix):
                return raw_value[len(alias):].strip()
        return None

    def is_restart_query(self, search_term):
        return str(search_term or "").strip().lower() in self.RESTART_QUERY_ALIASES

    def get_clear_query_text(self, search_term):
        raw_value = str(search_term or "").strip()
        if not raw_value:
            return None
        normalized = raw_value.lower()
        first_token = normalized.split(None, 1)[0]
        if first_token not in self.CLEAR_QUERY_ALIASES:
            return None
        parts = raw_value.split(None, 1)
        return parts[1].strip() if len(parts) > 1 else ""

    def is_clear_query(self, search_term):
        return self.get_clear_query_text(search_term) is not None

    def is_settings_query(self, search_term):
        return self._extract_query_suffix(search_term, self.SETTINGS_QUERY_ALIASES) is not None

    def get_settings_query_text(self, search_term):
        value = self._extract_query_suffix(search_term, self.SETTINGS_QUERY_ALIASES)
        return value if value is not None else ""

    @staticmethod
    def _settings_subsequence_score(needle, haystack):
        if not needle:
            return 10**9
        n, h = needle.lower(), haystack.lower()
        positions = []
        j = 0
        for ch in n:
            while j < len(h) and h[j] != ch:
                j += 1
            if j >= len(h):
                return None
            positions.append(j)
            j += 1
        first = positions[0]
        gaps = sum(positions[i + 1] - positions[i] - 1 for i in range(len(positions) - 1))
        return len(n) * 1000 - first * 10 - gaps

    def _settings_hub_categories(self):
        return (
            ("general", "general purpose links", self.DEFAULT_ICON),
            ("profile", "profile related", self.COMMUNITY_ICON),
            ("edit", "profile settings, appearance & privacy", self.PROPERTIES_ICON),
            ("account", "account preferences & security", self.BROWSER_ICON),
            ("steam", "client settings sidebar tabs", self.SETTINGS_ICON),
            ("client", "steam:// protocol (friends/, url/, nav/)", self.SETTINGS_ICON),
        )

    def _settings_leaf_rows(self, category):
        """return (title, subtitle, icon_path, action, score) per row"""
        if category == "general":
            return [
                ("library", "steam://nav/games", self.DEFAULT_ICON, self.build_action("open_steam_library_nav"), 21820),
                ("community home", "steam://open/community", self.COMMUNITY_ICON, self.build_action("open_steam_community_home"), 21819),
                ("activity feed", "steam://open/activity", self.COMMUNITY_ICON, self.build_action("open_steam_activity_feed"), 21818),
                ("friends", "steam://friends", self.COMMUNITY_ICON, self.build_action("open_steam_friends"), 21817),
                ("market", "steam://open/market", self.COMMUNITY_ICON, self.build_action("open_steam_market"), 21816),
                ("store", "steam://open/store", self.BROWSER_ICON, self.build_action("open_steam_store_front"), 21815),
                ("notifications", "", self.COMMUNITY_ICON, self.build_action("open_steam_my_path", "/notifications"), 21814),
                ("points shop", "store points", self.BROWSER_ICON, self.build_action("open_steam_points_shop"), 21813),
                ("comment history", "", self.COMMUNITY_ICON, self.build_action("open_steam_my_path", "/commenthistory"), 21812),
            ]
        if category == "profile":
            return [
                ("my profile", "steamcommunity.com/my", self.DEFAULT_ICON, self.build_action("open_steam_my_profile_client"), 21820),
                ("groups", "steam://open/groups", self.COMMUNITY_ICON, self.build_action("open_steam_my_groups"), 21819),
                ("inventory", "", self.COMMUNITY_ICON, self.build_action("open_steam_my_path", "/inventory"), 21818),
                ("games", "", self.COMMUNITY_ICON, self.build_action("open_steam_my_path", "/games"), 21817),
                ("screenshots", "", self.SCREENSHOT_ICON, self.build_action("open_steam_my_path", "/screenshots"), 21816),
                ("videos", "", self.COMMUNITY_ICON, self.build_action("open_steam_my_path", "/videos"), 21815),
                ("workshop items", "", self.COMMUNITY_ICON, self.build_action("open_steam_my_path", "/myworkshopfiles"), 21814),
                ("artwork", "", self.COMMUNITY_ICON, self.build_action("open_steam_my_path", "/images"), 21813),
                ("guides", "", self.GUIDES_ICON, self.build_action("open_steam_my_path", "/myworkshopfiles/?section=guides"), 21812),
            ]
        if category == "edit":
            return [
                ("general", "edit profile info", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/info"), 21810),
                ("avatar", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/avatar"), 21809),
                ("profile background", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/background"), 21808),
                ("miniprofile", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/miniprofile"), 21807),
                ("theme", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/theme"), 21806),
                ("game profile", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/goldenprofile"), 21805),
                ("featured badge", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/favoritebadge"), 21804),
                ("favorite group", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/favoritegroup"), 21803),
                ("showcase manager", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit/showcases"), 21802),
                ("privacy settings", "/edit/", self.SETTINGS_ICON, self.build_action("open_steam_my_path", "/edit"), 21801),
            ]
        if category == "account":
            return [
                ("account details", "preferences", self.BROWSER_ICON, self.build_action("open_steam_url", "https://store.steampowered.com/account/"), 21810),
                ("store preferences", "preferences", self.BROWSER_ICON, self.build_action("open_steam_url", "https://store.steampowered.com/account/preferences"), 21809),
                ("family management", "preferences", self.BROWSER_ICON, self.build_action("open_steam_url", "https://store.steampowered.com/account/familymanagement"), 21808),
                ("security & devices", "preferences", self.BROWSER_ICON, self.build_action("open_steam_url", "https://store.steampowered.com/account/authorizeddevices"), 21807),
                ("language preferences", "preferences", self.BROWSER_ICON, self.build_action("open_steam_url", "https://store.steampowered.com/account/languagepreferences"), 21806),
                ("data & browsing", "preferences", self.BROWSER_ICON, self.build_action("open_steam_url", "https://store.steampowered.com/account/cookiepreferences"), 21805),
                ("notification settings", "preferences", self.BROWSER_ICON, self.build_action("open_steam_url", "https://store.steampowered.com/account/notificationsettings"), 21804),
                ("playtests", "preferences", self.BROWSER_ICON, self.build_action("open_steam_url", "https://store.steampowered.com/account/gatedaccess"), 21803),
            ]
        if category == "steam":
            return [
                ("account", "steam://settings/account", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "account"), 21795),
                ("friends & chat", "steam://settings/friends", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "friends"), 21794),
                ("family", "steam://settings/family", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "family"), 21793),
                ("security", "steam://settings/security", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "security"), 21792),
                ("notifications", "steam://settings/notifications", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "notifications"), 21791),
                ("interface", "steam://settings/interface", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "interface"), 21790),
                ("store", "steam://settings/store", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "store"), 21789),
                ("library", "steam://settings/library", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "library"), 21788),
                ("downloads", "steam://settings/downloads", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "downloads"), 21787),
                ("storage", "steam://settings/storage", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "storage"), 21786),
                ("cloud", "steam://settings/cloud", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "cloud"), 21785),
                ("in game", "steam://settings/ingame", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "ingame"), 21784),
                ("accessibility", "steam://settings/accessibility", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "accessibility"), 21783),
                ("controller", "steam://settings/controller", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "controller"), 21782),
                ("game recording", "steam://settings/gamerecording", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "gamerecording"), 21781),
                ("voice", "steam://settings/voice", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "voice"), 21780),
                ("broadcast", "steam://settings/broadcast", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "broadcast"), 21778),
                ("music", "steam://settings/music", self.SETTINGS_ICON, self.build_action("open_steam_settings_sub_page", "music"), 21777),
            ]
        if category == "client":
            return [
                ("recent players", "steam://friends/players", self.COMMUNITY_ICON, self.build_action("open_steam_friends_recent_players"), 21949),
                ("steam workshop", "steam://url/SteamWorkshop", self.DEFAULT_ICON, self.build_action("open_steam_url_named_page", "SteamWorkshop"), 21941),
                ("community home", "steam://url/CommunityHome/", self.COMMUNITY_ICON, self.build_action("open_steam_url_named_page", "CommunityHome/"), 21940),
                ("comment notifications", "steam://url/CommentNotifications", self.COMMUNITY_ICON, self.build_action("open_steam_url_named_page", "CommentNotifications"), 21937),
                ("family sharing", "steam://url/FamilySharing", self.COMMUNITY_ICON, self.build_action("open_steam_url_named_page", "FamilySharing"), 21936),
                ("my help requests", "steam://url/MyHelpRequests", self.COMMUNITY_ICON, self.build_action("open_steam_url_named_page", "MyHelpRequests"), 21935),
                ("console", "steam://nav/console", self.DEFAULT_ICON, self.build_action("open_steam_nav_component", "console"), 21934),
                ("downloads", "steam://nav/downloads", self.DOWNLOAD_ICON, self.build_action("open_steam_nav_component", "downloads"), 21933),
                ("games", "steam://nav/games", self.DEFAULT_ICON, self.build_action("open_steam_nav_component", "games"), 21932),
                ("hidden collection", "steam://nav/library/collection/hidden", self.DEFAULT_ICON, self.build_action("open_steam_nav_component", "library/collection/hidden"), 21928),
            ]
        return []

    def _settings_row(self, category, title, subtitle, icon_path, action, score):
        ac = self.build_plugin_query("settings", category, title)
        return self.build_result(
            title,
            subtitle,
            icon_path,
            action,
            auto_complete_text=ac,
            Score=score,
        )

    def _filter_settings_category_rows(self, _category, needle, rows):
        if not needle:
            return list(rows)
        needle_l = needle.lower().strip()
        tokens = [t for t in needle_l.split() if t]
        out = []
        for title, subtitle, icon_path, action, score in rows:
            hay = f"{title} {subtitle}".lower()
            if needle_l in hay:
                out.append((title, subtitle, icon_path, action, score))
            elif tokens and all(t in hay for t in tokens):
                out.append((title, subtitle, icon_path, action, score))
        return out

    def _build_settings_category_view(self, category, needle, settings_query):
        rows = self._settings_leaf_rows(category)
        if not rows:
            return [
                self.build_result(
                    title=f"unknown settings category: {category}",
                    subtitle="",
                    icon_path=self.WARNING_ICON,
                    action=self.build_change_query_action(settings_query),
                    auto_complete_text=settings_query,
                    Score=21800,
                ),
            ]
        filtered = self._filter_settings_category_rows(category, needle, rows)
        if needle and not filtered:
            fzf_hint = self.build_plugin_query("settings", "fzf", needle)
            return [
                self.build_result(
                    title="no matches in this category",
                    subtitle="",
                    icon_path=self.WARNING_ICON,
                    action=self.build_change_query_action(fzf_hint),
                    auto_complete_text=fzf_hint,
                    Score=21800,
                ),
            ]
        return [
            self._settings_row(category, title, subtitle, icon_path, action, score)
            for title, subtitle, icon_path, action, score in filtered
        ]

    def _build_settings_fzf_results(self, needle):
        settings_query = self.build_plugin_query("settings")
        settings_fzf_base = self.build_plugin_query("settings", "fzf")
        entries = []
        for cat in ("general", "profile", "edit", "account", "steam", "client"):
            for title, subtitle, icon_path, action, score in self._settings_leaf_rows(cat):
                entries.append(
                    {
                        "category": cat,
                        "title": title,
                        "subtitle": subtitle,
                        "icon_path": icon_path,
                        "action": action,
                        "score": score,
                    }
                )
        if not needle:
            entries.sort(key=lambda e: (-e["score"], e["title"].lower()))
            picked = entries[: self.SETTINGS_FZF_MAX_RESULTS]
        else:
            scored = []
            for e in entries:
                blob = f"{e['category']} {e['title']} {e['subtitle']}"
                fs = self._settings_subsequence_score(needle, blob)
                if fs is not None:
                    scored.append((fs, e))
            scored.sort(key=lambda item: (-item[0], item[1]["title"].lower()))
            picked = [e for _fs, e in scored[: self.SETTINGS_FZF_MAX_RESULTS]]
        if not picked:
            return [
                self.build_result(
                    title="no fuzzy matches",
                    subtitle="",
                    icon_path=self.WARNING_ICON,
                    action=self.build_change_query_action(settings_fzf_base + " "),
                    auto_complete_text=settings_fzf_base,
                    Score=21800,
                ),
            ]
        results = []
        for rank, e in enumerate(picked):
            ac = self.build_plugin_query("settings", e["category"], e["title"])
            results.append(
                self.build_result(
                    e["title"],
                    e["subtitle"],
                    e["icon_path"],
                    e["action"],
                    auto_complete_text=ac,
                    Score=21850 - rank,
                )
            )
        return results

    def build_switch_account_results(self, filter_text=""):
        switch_query = self.build_plugin_query("switch")
        all_accounts = self.get_switchable_steam_accounts()
        if not all_accounts:
            return [
                self.build_result(
                    title="no other accounts",
                    subtitle="",
                    icon_path=self.DEFAULT_ICON,
                    auto_complete_text=switch_query,
                    Score=21000,
                )
            ]

        filter_key = str(filter_text or "").strip().lower()

        def _account_matches(account):
            if not filter_key:
                return True
            label = self.get_steam_account_label(account).lower()
            account_name = str(account.get("account_name", "") or "").strip().lower()
            steamid = str(account.get("steamid64", "") or "")
            return (
                filter_key in label
                or (account_name and filter_key in account_name)
                or (filter_key in steamid)
            )

        switchable_accounts = [a for a in all_accounts if _account_matches(a)]
        if filter_key and not switchable_accounts:
            return [
                self.build_result(
                    title="no matching accounts",
                    subtitle=f"try: {switch_query}",
                    icon_path=self.DEFAULT_ICON,
                    auto_complete_text=switch_query,
                    action=self.build_change_query_action(switch_query),
                    Score=21000,
                )
            ]

        results = []
        if not filter_key:
            results.append(
                self.build_result(
                    title="please disable this!",
                    subtitle=self.SWITCH_AUTOLOGIN_HINT_SUBTITLE,
                    icon_path=self.SETTINGS_ICON,
                    auto_complete_text=switch_query,
                    Score=21100,
                )
            )
        for score_offset, account in enumerate(switchable_accounts, start=1):
            account_label = self.get_steam_account_label(account)
            title = account_label.lower()
            subtitle_parts = [""]
            account_name = str(account.get("account_name", "") or "").strip()
            if account_name and account_name != account_label:
                subtitle_parts.append(f"@{account_name}")
            if not account.get("remember_password", True):
                subtitle_parts.append("password may be required")
            results.append(
                self.build_result(
                    title=title,
                    subtitle="".join(subtitle_parts),
                    icon_path=account.get("icon_path") or self.DEFAULT_ICON,
                    action=self.build_action("switch_steam_account", account.get("steamid64")),
                    auto_complete_text=self.build_plugin_query("switch", title),
                    Score=21001 - score_offset,
                )
            )
        return results

    def build_exit_results(self):
        return [
            self.build_result(
                title="exit",
                subtitle="close client + kill helpers",
                icon_path=self.WARNING_ICON,
                action=self.build_action("exit_steam"),
                Score=21850,
            ),
        ]

    def build_restart_results(self):
        return [
            self.build_result(
                title="restart",
                subtitle="close steam then launch again",
                icon_path=self.WARNING_ICON,
                action=self.build_action("restart_steam"),
                Score=21845,
            ),
        ]

    def build_clear_results(self, _tail=""):
        clear_query = self.build_plugin_query("clear")
        return [
            self.build_result(
                title="clear cache & logs",
                subtitle="delete var/*.log, cache*.json, *.lock — resets caches",
                icon_path=self.TRASH_ICON,
                action=self.build_action("clear_steamflow_runtime_artifacts"),
                auto_complete_text=clear_query,
                Score=21844,
            ),
            self.build_result(
                title="open plugin data folder",
                subtitle="var/ (runtime logs + json caches)",
                icon_path=self.LOCATION_ICON,
                action=self.build_action("open_steamflow_data_folder"),
                auto_complete_text=clear_query,
                Score=21843,
            ),
            self.build_result(
                title="open steam client log folder",
                subtitle="<install>/logs",
                icon_path=self.SETTINGS_ICON,
                action=self.build_action("open_steam_install_logs_folder"),
                auto_complete_text=clear_query,
                Score=21842,
            ),
        ]

    def build_settings_results(self, query_text=""):
        settings_query = self.build_plugin_query("settings")
        settings_tree_query = self.build_plugin_query("settings", "tree")
        settings_fzf_query = self.build_plugin_query("settings", "fzf")
        query_value = str(query_text or "").strip().lower()
        parts = query_value.split()
        head = parts[0] if parts else ""
        tail = " ".join(parts[1:]).strip().lower() if len(parts) > 1 else ""

        categories = self._settings_hub_categories()
        category_names = {name for name, _subtitle, _icon in categories}

        if not head:
            return [
                self.build_result(
                    title=name,
                    subtitle="",
                    icon_path=icon,
                    action=self.build_change_query_action(self.build_plugin_query("settings", name)),
                    auto_complete_text=self.build_plugin_query("settings", name),
                    Score=21820 - idx,
                )
                for idx, (name, subtitle, icon) in enumerate(categories, start=1)
            ] + [
                self.build_result(
                    title="tree",
                    subtitle="",
                    icon_path=self.LOCATION_ICON,
                    action=self.build_action("open_settings_tree"),
                    auto_complete_text=settings_tree_query,
                    Score=21812,
                ),
                self.build_result(
                    title="fzf",
                    subtitle="",
                    icon_path=self.DEFAULT_ICON,
                    action=self.build_change_query_action(settings_fzf_query + " "),
                    auto_complete_text=settings_fzf_query,
                    Score=21811,
                ),
            ]

        if head in self.SETTINGS_FZF_QUERY_ALIASES:
            return self._build_settings_fzf_results(tail)

        if head in self.SETTINGS_TREE_QUERY_ALIASES:
            return [
                self.build_result(
                    title="open tree overview",
                    subtitle="",
                    icon_path=self.LOCATION_ICON,
                    action=self.build_action("open_settings_tree"),
                    auto_complete_text=settings_tree_query,
                    Score=21850,
                ),
            ]

        if head in self.SETTINGS_HELP_QUERY_ALIASES:
            return [
                self.build_result(
                    title="tree",
                    subtitle="",
                    icon_path=self.LOCATION_ICON,
                    action=self.build_action("open_settings_tree"),
                    auto_complete_text=settings_tree_query,
                    Score=21850,
                ),
                self.build_result(
                    title="general/profile/edit/account/steam/client",
                    subtitle="",
                    icon_path=self.DEFAULT_ICON,
                    action=self.build_change_query_action(settings_query),
                    auto_complete_text=settings_query,
                    Score=21849,
                ),
                self.build_result(
                    title="fzf",
                    subtitle="",
                    icon_path=self.DEFAULT_ICON,
                    action=self.build_change_query_action(settings_fzf_query + " "),
                    auto_complete_text=settings_fzf_query,
                    Score=21848,
                ),
            ]

        resolved_category = None
        if head in category_names:
            resolved_category = head
        else:
            category_matches = [
                (name, subtitle, icon)
                for name, subtitle, icon in categories
                if head in name or name.startswith(head)
            ]
            if len(category_matches) == 1:
                resolved_category = category_matches[0][0]
            elif len(category_matches) > 1:
                return [
                    self.build_result(
                        title=name,
                        subtitle="",
                        icon_path=icon,
                        action=self.build_change_query_action(self.build_plugin_query("settings", name)),
                        auto_complete_text=self.build_plugin_query("settings", name),
                        Score=21830 - idx,
                    )
                    for idx, (name, subtitle, icon) in enumerate(category_matches, start=1)
                ]

        if resolved_category:
            return self._build_settings_category_view(resolved_category, tail, settings_query)

        return [
            self.build_result(
                title=f"unknown settings category: {head}",
                subtitle="",
                icon_path=self.WARNING_ICON,
                action=self.build_change_query_action(settings_query),
                auto_complete_text=settings_query,
                Score=21800,
            ),
        ]

    def build_help_results(self):
        keyword = self.get_current_plugin_keyword()
        api_query = self.build_plugin_query("api")
        switch_query = self.build_plugin_query("switch")
        status_query = self.build_plugin_query("status")
        exit_query = self.build_plugin_query("exit")
        restart_query = self.build_plugin_query("restart")
        clear_query = self.build_plugin_query("clear")
        settings_query = self.build_plugin_query("settings")
        wishlist_query = self.build_plugin_query("wishlist")

        _items, wishlist_error = self.get_wishlist_items()
        api_configured = self.has_owned_api_key()

        hint = self.WISHLIST_ERROR_HINTS.get(wishlist_error)
        wishlist_subtitle = f"wishlist | {hint}" if hint else "price, date & reviews"

        results = []

        if not api_configured:
            results.append(
                self.build_result(
                    title="setup: api",
                    subtitle="enable wishlist, owned detection, profile status",
                    icon_path=self.SETTINGS_ICON,
                    action=self.build_change_query_action(api_query),
                    Score=22100,
                )
            )

        results += [
            self.build_result(
                title=f"{keyword} [game]",
                subtitle="search library & store",
                icon_path=self.DEFAULT_ICON,
                action=self.build_change_query_action(keyword + " ", requery=False),
                Score=22050,
            ),
        ]
        if self.should_show_help_api():
            results.append(
            self.build_result(
                title="api",
                subtitle="",
                icon_path=self.OWNED_ICON,
                action=self.build_change_query_action(api_query),
                Score=22000,
                )
            )
        if self.should_show_help_switch():
            results.append(
            self.build_result(
                title="switch",
                subtitle="switch between registered accounts",
                icon_path=self.COMMUNITY_ICON,
                action=self.build_change_query_action(switch_query),
                Score=21999,
                )
            )
        if self.should_show_help_status():
            results.append(
            self.build_result(
                title="status",
                subtitle="set online/away/invisible/offline",
                icon_path=self.ONLINE_ICON,
                action=self.build_change_query_action(status_query),
                Score=21998,
                )
            )
        if self.should_show_help_wishlist():
            results.append(
            self.build_result(
                title="wishlist",
                subtitle=wishlist_subtitle,
                icon_path=self.WISHLIST_ICON,
                action=self.build_change_query_action(wishlist_query),
                Score=21997,
                )
            )
        if self.should_show_help_settings():
            results.append(
                self.build_result(
                    title="settings",
                    subtitle="open grouped links",
                    icon_path=self.SETTINGS_ICON,
                    action=self.build_change_query_action(settings_query),
                    Score=21996,
                )
            )
        if self.should_show_help_restart():
            results.append(
                self.build_result(
                    title="restart",
                    subtitle="",
                    icon_path=self.WARNING_ICON,
                    action=self.build_change_query_action(restart_query),
                    Score=21995,
                )
            )
        if self.should_show_help_exit():
            results.append(
                self.build_result(
                    title="exit",
                    subtitle="",
                    icon_path=self.WARNING_ICON,
                    action=self.build_change_query_action(exit_query),
                    Score=21994,
                )
            )
        if self.should_show_help_clear():
            results.append(
                self.build_result(
                    title="clear",
                    subtitle="logs & cache json in var/",
                    icon_path=self.TRASH_ICON,
                    action=self.build_change_query_action(clear_query),
                    Score=21993,
                )
            )
        return results

    def build_status_results(self, filter_text=None):
        status_query = self.build_plugin_query("status")
        steamid64 = self.get_active_steam_user_steamid64()
        if not steamid64:
            return [
                self.build_result(
                    title="no active account",
                    subtitle="sign into steam first",
                    icon_path=self.COMMUNITY_ICON,
                    action=self.build_change_query_action(status_query),
                    Score=self.STATUS_CURRENT_RESULT_SCORE,
                )
            ]

        filter_lower = str(filter_text or "").strip().lower()
        normalized_filter = filter_lower.replace(" ", "")

        user_details = self.get_steam_user_details(steamid64)
        account_label = (
            str(user_details.get("persona_name", "") or "").strip()
            or str(user_details.get("account_name", "") or "").strip()
            or "steam user"
        ).lower()
        current_state = self.get_active_local_persona_state()
        current_label = self.get_local_persona_state_label(current_state)
        current_protocol = self.get_local_persona_state_protocol(current_state)

        if current_label:
            current_result = self.build_result(
                title=f"current: {current_label}",
                subtitle="",
                icon_path=self.get_status_icon_path(current_protocol),
                action=self.build_change_query_action(status_query),
                Score=self.STATUS_CURRENT_RESULT_SCORE,
            )
        else:
            current_result = self.build_result(
                title="current: unknown",
                subtitle="",
                icon_path=self.WARNING_ICON,
                action=self.build_change_query_action(status_query),
                Score=self.STATUS_CURRENT_RESULT_SCORE,
            )

        results = [] if normalized_filter else [current_result]
        preferred_key = None
        if normalized_filter:
            for status_key, status_label in self.STEAM_STATUS_OPTIONS:
                if normalized_filter in {status_key, status_label, status_label.replace(" ", "")}:
                    preferred_key = status_key
                    break

        for score_offset, (status_key, status_label) in enumerate(self.STEAM_STATUS_OPTIONS, start=1):
            if current_protocol == status_key:
                continue
            if normalized_filter and not (
                normalized_filter in status_key
                or normalized_filter in status_label
                or normalized_filter in status_label.replace(" ", "")
            ):
                continue
            score_bonus = 0
            if preferred_key and status_key == preferred_key:
                score_bonus = 50
            results.append(
                self.build_result(
                    title=status_label,
                    subtitle="",
                    icon_path=self.get_status_icon_path(status_key),
                    action=self.build_action("set_steam_friends_status", status_key),
                    Score=self.STATUS_OPTION_BASE_SCORE + score_bonus - score_offset,
                )
            )
        return results

    def build_owned_api_results(self):
        status_title, status_subtitle = self.get_owned_games_status()
        has_key = self.has_owned_api_key()
        status_result = self.build_result(
            title=status_title.lower(),
            subtitle=status_subtitle.lower(),
            icon_path=self.OWNED_ICON,
            Score=19997 if not has_key else 20000,
        )
        save_key_result = self.build_result(
            title="save key from clipboard",
            subtitle="encrypted via dpapi",
            icon_path=self.CLIPBOARD_ICON,
            action=self.build_action("save_owned_api_key_from_clipboard"),
            Score=19999,
        )
        remove_key_result = self.build_result(
            title="remove stored key",
            subtitle="remove key + cached account data",
            icon_path=self.TRASH_ICON,
            action=self.build_action("remove_owned_api_key_action"),
            Score=19998,
        )
        open_key_page_result = self.build_result(
            title="get api key",
            subtitle="open steamcommunity.com/dev/apikey",
            icon_path=self.BROWSER_ICON,
            action=self.build_action("open_steam_web_api_key_page"),
            Score=20000,
        )

        if has_key:
            return [status_result, remove_key_result]
        return [open_key_page_result, save_key_result, status_result]

    def show_owned_api_message(self, title, subtitle):
        show_msg = getattr(self, "show_msg", None)
        if callable(show_msg):
            try:
                show_msg(title, subtitle, self.OWNED_ICON)
            except Exception:
                pass

    def save_owned_api_key_from_clipboard(self):
        self.ensure_startup_initialized()
        clipboard_text = get_clipboard_text()
        api_key = self.normalize_steam_web_api_key(clipboard_text)
        if not api_key:
            message = "clipboard has no valid api key"
            self.show_owned_api_message("api key not saved", message)
            return message

        steamid64 = self.get_active_steam_user_steamid64()
        if not steamid64:
            message = "no active steam account"
            self.show_owned_api_message("api key not saved", message)
            return message

        try:
            owned_app_ids, owned_game_playtimes = self.fetch_owned_app_ids_from_api(api_key, steamid64, timeout=5)
        except Exception as error:
            self.log("error", f"api key validation failed: {error}")
            err = str(error).strip()
            message = f"api key validation failed: {err}" if err else "api key validation failed"
            self.show_owned_api_message("api key not saved", message)
            return message

        user_details = self.get_steam_user_details(steamid64)
        self.save_owned_api_key(
            api_key,
            steamid64,
            persona_name=user_details.get("persona_name"),
            account_name=user_details.get("account_name"),
        )
        with self.state_lock:
            self.owned_games_last_attempt = time.time()
            self.owned_games_last_sync = time.time()
            self.owned_games_public_profile = True
            self.owned_games_steamid64 = steamid64
            self.owned_app_ids = set(owned_app_ids)
            self.owned_game_playtimes = dict(owned_game_playtimes)
            self.owned_games_cache_loaded = True
        self.save_owned_games_cache()
        message = f"saved, bound to {user_details.get('persona_name') or steamid64}"
        self.show_owned_api_message("api key saved", message)
        return message

    def remove_owned_api_key_action(self):
        self.ensure_startup_initialized()
        self.remove_owned_api_key()
        message = "api key removed"
        self.show_owned_api_message("api key removed", message)
        return message

    def open_steam_web_api_key_page(self):
        return self.open_steam_url("https://steamcommunity.com/dev/apikey")
