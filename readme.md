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

as per `ui.py`, l:107 - if the markers are confusing, swap them for whatever you prefer, e.g. `↓` for updating

```py
UPDATE_STATUS_MARKERS = {
    "Updating": " vv",
    "Update Paused": " ||",
    "Update Queued": " ??",
    "Update Required": " !!",
}
```

## steam web api

> the api key is encrypted with windows DPAPI & bound to your steam account

- detects owned games
- enables wishlist browsing
- change your active profile status

## settings

`settings -> plugins -> steamflow` - tune display options, result limits, context menu entries, etc
