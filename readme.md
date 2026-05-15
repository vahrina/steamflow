# steamflow (fork)

fork of the original [SteamFlow](https://github.com/keekyslusus/SteamFlow) - qol stuff + toggles

## usage

- `steam` -> browse installed library
- `steam ?` -> help
- `steam [name]` -> search library + store
- `steam api` -> set up web api key (enables owned sync, wishlist, profile status)
- `steam switch` -> switch between signed-in accounts
- `steam status` -> online / away / dnd / invisible / offline
- `steam wishlist [name]` -> browse + search wishlist

right-click any result for per-game actions (store, steamdb, guides, refund, install/uninstall, open folder, etc.)

## install

unzip [latest release](https://github.com/vahrina/steamflow/releases/latest) into `%appdata%/FlowLauncher/Plugins`

## settings

`settings -> plugins -> steamflow` - tune display options, result limits, context menu entries, etc

## steam web api

> api key is encrypted with windows DPAPI & bound to your steam account

- detects owned games
- enables wishlist browsing
- change your active profile status
