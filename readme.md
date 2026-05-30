# steamflow

flow launcher plugin to control your entire steam profile from the keyboard

## usage

- `steam` -> browse your library
- `steam ?` -> help
- `steam [name]` -> search library + store
- `steam api` -> access more features (enables owned sync, wishlist, profile status)
- `steam switch` -> switch between signed-in accounts
- `steam status` -> online / away / dnd / invisible / offline
- `steam wishlist [name]` -> browse + search wishlist
- `steam settings` -> collection of frequently accessed URIs, with [fuzzy search](https://www.meilisearch.com/blog/fuzzy-search)
right click/right arrow any result for per game actions (store, steamdb, guides, refund, install/uninstall, open folder, etc)

## install

unzip [latest release](https://github.com/vahrina/steamflow/releases/latest) into your plugin folder, e.g. `%appdata%/FlowLauncher/Plugins`

feel free to make your own changes, the ui will automatically change upon saving the file

## ui explanation

as per `steamflow/ui.py`, l:107 - if the markers are confusing, swap them for whatever you prefer

```py
UPDATE_STATUS_MARKERS = {
    "Updating": " ~~",
    "Update Paused": " ||",
    "Update Queued": " ..",
    "Update Required": " !!",
}
```

additional (not- &) installed games can be found in `store_metrics.py` l:484

```py
title_marker = " >>" if not self.get_install_path(
    app_id) else " --"
```

### ideas for markers if you're unsatisfied with the defaults

**symbolic/arrow**

```py
"Updating": " =>",
"Update Paused": " -|",
"Update Queued": " ->",
"Update Required": " !>",
# installed: " **" or " ::"
# not installed: " ++" or " >>"
```

**unicode**

```py
"Updating": " ↻ ",
"Update Paused": " ⏸ ",
"Update Queued": " ⏳ ",
"Update Required": " ↑ ",
# installed: " ✔ "
# not installed: " ○ " or " ◌ "
```

## shortcuts

always get where you want immediately, you may change the shortcuts to your liking in `steamflow/ui-commands.py`, l:7-19

```py
class SteamPluginUICommandsMixin:
    OWNED_API_QUERY_ALIASES = {"api", "api key", "apikey", }
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
```

## steam web api

> the api key is encrypted with windows DPAPI & bound to your steam account

- detects owned games
- enables wishlist browsing
- change your active profile status

## settings

`settings -> plugins -> steamflow` - tune display options, result limits, context menu entries, etc
