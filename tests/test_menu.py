import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIB_PATH = PROJECT_ROOT / "lib"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(LIB_PATH) not in sys.path:
    sys.path.insert(0, str(LIB_PATH))

from steamflow.menu import (
    get_game_context_menu_entries,
    get_refund_menu_copy,
    get_steam_user_context_menu_entries,
)


ICON = "icon"


class MenuTests(unittest.TestCase):
    def test_refund_menu_copy_uses_likely_wording(self):
        title, subtitle = get_refund_menu_copy("likely", "NEEDY GIRL OVERDOSE")

        self.assertEqual(title, "refund page")
        self.assertIn("eligible if", subtitle)

    def test_refund_menu_copy_uses_unclear_wording(self):
        title, subtitle = get_refund_menu_copy("unclear", "NEEDY GIRL OVERDOSE")

        self.assertEqual(title, "check refund options")
        self.assertIn("eligibility unclear", subtitle.lower())

    def test_game_context_menu_includes_refund_only_for_local_games_with_refund_state(self):
        entries = get_game_context_menu_entries(
            app_id="1451940",
            name="NEEDY GIRL OVERDOSE",
            install_path="C:/Games/Needy",
            is_owned=False,
            refund_state="likely",
            default_icon=ICON,
            steamdb_icon=ICON,
            guides_icon=ICON,
            discussions_icon=ICON,
            screenshot_icon=ICON,
            refund_icon=ICON,
            properties_icon=ICON,
            location_icon=ICON,
            download_icon=ICON,
            trash_icon=ICON,
        )

        titles = [entry["title"] for entry in entries]
        self.assertIn("refund page", titles)
        self.assertIn("uninstall game", titles)

    def test_game_context_menu_hides_refund_for_store_results(self):
        entries = get_game_context_menu_entries(
            app_id="1451940",
            name="NEEDY GIRL OVERDOSE",
            install_path=None,
            is_owned=False,
            refund_state="likely",
            default_icon=ICON,
            steamdb_icon=ICON,
            guides_icon=ICON,
            discussions_icon=ICON,
            screenshot_icon=ICON,
            refund_icon=ICON,
            properties_icon=ICON,
            location_icon=ICON,
            download_icon=ICON,
            trash_icon=ICON,
        )

        titles = [entry["title"] for entry in entries]
        self.assertNotIn("refund page", titles)
        self.assertNotIn("uninstall game", titles)

    def test_game_context_menu_includes_installed_actions_only_with_install_path(self):
        entries = get_game_context_menu_entries(
            app_id="1962700",
            name="Subnautica 2",
            install_path="C:/Games/Subnautica2",
            is_owned=True,
            refund_state="",
            default_icon=ICON,
            steamdb_icon=ICON,
            guides_icon=ICON,
            discussions_icon=ICON,
            screenshot_icon=ICON,
            refund_icon=ICON,
            properties_icon=ICON,
            location_icon=ICON,
            download_icon=ICON,
            trash_icon=ICON,
        )

        titles = [entry["title"] for entry in entries]
        self.assertIn("launch settings", titles)
        self.assertIn("browse local files", titles)
        self.assertNotIn("install game", titles)

    def test_steam_user_context_menu_includes_profile_and_library(self):
        entries = get_steam_user_context_menu_entries(
            steamid64="76561198000000001",
            name="Kaya",
            is_self=False,
            default_icon=ICON,
            settings_icon=ICON,
            community_icon=ICON,
            browser_icon=ICON,
        )
        titles = [entry["title"] for entry in entries]
        self.assertIn("profile", titles)
        self.assertIn("library", titles)
        self.assertNotIn("settings", titles)

    def test_steam_user_context_menu_includes_settings_only_for_self(self):
        entries = get_steam_user_context_menu_entries(
            steamid64="76561198000000001",
            name="Kaya",
            is_self=True,
            default_icon=ICON,
            settings_icon=ICON,
            community_icon=ICON,
            browser_icon=ICON,
        )
        titles = [entry["title"] for entry in entries]
        self.assertIn("profile", titles)
        self.assertIn("settings", titles)

    def test_game_context_menu_hides_installed_actions_without_install_path(self):
        entries = get_game_context_menu_entries(
            app_id="1962700",
            name="Subnautica 2",
            install_path=None,
            is_owned=True,
            refund_state="",
            default_icon=ICON,
            steamdb_icon=ICON,
            guides_icon=ICON,
            discussions_icon=ICON,
            screenshot_icon=ICON,
            refund_icon=ICON,
            properties_icon=ICON,
            location_icon=ICON,
            download_icon=ICON,
            trash_icon=ICON,
        )

        titles = [entry["title"] for entry in entries]
        self.assertNotIn("open", titles)
        self.assertNotIn("launch settings", titles)
        self.assertNotIn("browse local files", titles)
        self.assertIn("install game", titles)

    def test_game_context_menu_includes_install_for_owned_store_results(self):
        entries = get_game_context_menu_entries(
            app_id="570",
            name="Dota 2",
            install_path=None,
            is_owned=True,
            refund_state="",
            default_icon=ICON,
            steamdb_icon=ICON,
            guides_icon=ICON,
            discussions_icon=ICON,
            screenshot_icon=ICON,
            refund_icon=ICON,
            properties_icon=ICON,
            location_icon=ICON,
            download_icon=ICON,
            trash_icon=ICON,
        )

        titles = [entry["title"] for entry in entries]
        self.assertIn("install game", titles)
        self.assertNotIn("uninstall game", titles)


if __name__ == "__main__":
    unittest.main()
