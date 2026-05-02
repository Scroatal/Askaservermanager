# ASKA Server Manager

Version: `0.2.1`

Local Windows desktop manager for ASKA and Windrose dedicated servers. It is built with Python 3 and Tkinter, using only the Python standard library.

The UI uses colors inspired by the public ASKA site at <https://playaska.com/> and an original generated app emblem.

## Download And Install

1. Download the latest release zip from:

   <https://github.com/Scroatal/Askaservermanager/releases>

2. Extract the zip to a folder, for example:

   ```text
   C:\Tools\ASKA Server Manager
   ```

3. Run:

   ```text
   ASKA Server Manager.exe
   ```

Windows may show a SmartScreen warning because the app is not code-signed. Choose `More info` and `Run anyway` if you trust the download source.

The app creates local files beside the executable:

```text
settings.json
mods.json
```

Do not share those files if they contain private paths or a Nexus API key.

## First Run Setup

Open the Settings tab and confirm these paths match your machine:

```text
Server install folder
Launcher batch file
Server properties file
SteamCMD executable
BepInEx plugins folder
BepInEx config folder
Save folder
Backup folder
```

Click `Auto-detect Paths` to let the app find paths from the running `AskaServer.exe`, Steam library manifests, and common SteamCMD locations. Review the detected values, then click `Save Settings`, close and reopen the app once to confirm settings persist.

Recommended first test:

1. Stop the ASKA server.
2. Click `Backup Now`.
3. Confirm a backup appears in the Backups tab.
4. Start the server from the app.
5. Confirm Dashboard shows `Running`.

## Safety Rules

The app refuses to restore, wipe, edit server config, edit mod config, install mod ZIPs, or update the server while `AskaServer.exe` is running.

Before restore, wipe, server update, and mod ZIP install, the app creates backups. If the required pre-wipe backup fails, the wipe is aborted.

Windrose actions use the same cautious rule: stop `WindroseServer.exe` before editing config or updating with SteamCMD.

## Windows Startup And Auto-Restart

The Settings tab has three startup/watchdog options:

```text
Launch ASKA Server Manager when Windows starts
Start ASKA server when the manager opens
Auto-restart ASKA server if it stops unexpectedly
```

When Windows startup is enabled, the app creates a startup batch file in the current user's Windows Startup folder. Disabling the option removes that file.

Auto-restart only acts when the manager believes the server should be running. Clicking `Start Server` or enabling `Start ASKA server when the manager opens` sets that expectation. Clicking `Stop Server` clears it so the app does not restart a server you intentionally stopped.

## Run

For normal users, use the release `.exe`.

For development, run from source:

```bat
python aska_server_manager.py
```

The app creates `settings.json` beside the script on first run.

## Paths

Default server install:

```text
E:\steam\steamapps\common\ASKA Dedicated Server
```

Default launcher:

```text
E:\steam\steamapps\common\ASKA Dedicated Server\AskaServer.bat
```

Default save folder:

```text
%USERPROFILE%\AppData\LocalLow\Sand Sailor Studio\Aska\data\server
```

Default backup folder:

```text
E:\aska_backups
```

Use the Settings tab to change any of these paths.

## Backups

Manual backups are created with the `Backup Now` button. Automatic backups can be enabled from the Dashboard. By default, automatic backups run every 60 minutes while the app is open and old backups are deleted after 24 hours.

Backup names use:

```text
backup_YYYY-MM-DD_HH-mm
```

Logs are written to:

```text
E:\aska_backups\aska_manager.log
```

or to the backup folder configured in Settings.

## Restore

Open the Backups tab, select a backup, and click `Restore Selected Backup`.

Important: stop the ASKA server before restoring or wiping. The app refuses restore and wipe actions while `AskaServer.exe` is running. Before restore or wipe, it creates an emergency backup in the backup folder.

Wiping the current save requires two confirmations. The first asks whether you are sure, and the second asks whether you are really sure and requires typing `DELETE`. By default, the app creates a clearly named secure before-wipe backup:

```text
secure_before_wipe_YYYY-MM-DD_HH-mm
```

If the before-wipe backup fails, the wipe is aborted.

## Config

The Config tab edits recognised keys in `server properties.txt` and preserves comments plus unknown settings. Before saving, it creates a timestamped backup next to the config file.

The bundled config fields follow the original app prompt plus Wimtzw's ASKA dedicated server guide 1.1. The guide notes that `steam game port`, `steam query port`, and `authentication token` must be set for a working public server. Steam game server tokens are created at:

```text
https://steamcommunity.com/dev/managegameservers
```

Use ASKA app ID:

```text
1898300
```

Keep the authentication token private.

The guide also recommends moving `AskaServer.bat` and `server properties.txt` outside the Steam install folder to avoid losing local edits during server updates. If you do that, update `Server launcher batch file` and `Server properties file` in the Settings tab.

## BepInEx Mods

The Mods tab manages the BepInEx folders:

```text
E:\steam\steamapps\common\ASKA Dedicated Server\BepInEx\plugins
E:\steam\steamapps\common\ASKA Dedicated Server\BepInEx\config
```

It lists installed `.dll` plugins and `.cfg` config files. Select a config file to edit it in the built-in text editor. Saving a mod config creates a timestamped backup beside the original config first.

The app refuses to save BepInEx config files while `AskaServer.exe` is running. Stop the server first so the server and app do not write the same config at the same time.

Use `Backup BepInEx Mods` to copy both `plugins` and `config` into:

```text
E:\aska_backups\bepinex_backup_YYYY-MM-DD_HH-mm
```

Use `Install Mod ZIP` after manually downloading a mod from Nexus Mods. The app stops if the server is running, backs up BepInEx first, then copies `.dll` files into `plugins` and `.cfg` files into `config`.

For Nexus tracking, select a plugin DLL and click `Set Nexus URL`. The app stores the source in `mods.json` beside the executable. `Open Nexus Page` opens the tracked page in your browser. `Check Nexus Updates` can query Nexus metadata if you add your own Nexus API key in Settings.

Nexus SSO is not built into this app because Nexus requires an approved application slug for SSO clients. Manual API key entry is simpler and works without registering this app with Nexus.

## Windrose

The Windrose tab manages the Windrose Dedicated Server tool separately from ASKA.

It can:

```text
Start, stop, and restart WindroseServer.exe
Install or repair the Windrose Dedicated Server with SteamCMD
Back up the configured Windrose save folder and ServerDescription.json
Edit ServerDescription.json with JSON validation
Check the local Steam build against Steam
Update the server with SteamCMD
Auto-detect the install path from Steam manifests or a running WindroseServer.exe process
```

Default Windrose paths:

```text
E:\steam\steamapps\common\Windrose Dedicated Server
E:\steam\steamapps\common\Windrose Dedicated Server\StartServerForeground.bat
E:\steam\steamapps\common\Windrose Dedicated Server\R5\ServerDescription.json
E:\steam\steamapps\common\Windrose Dedicated Server\R5\Saved\SaveProfiles\Default\RocksDB
E:\windrose_backups
```

Windrose uses Steam dedicated server app ID:

```text
4129620
```

The first Windrose release deliberately does not include restore or wipe buttons. Confirm the generated save folder on the host first, then backups can be restored manually from the backup folder if needed.

If Windrose Dedicated Server is not installed yet, set `SteamCMD executable`, confirm the Windrose install folder, then click `Install Windrose Server`. The app runs the equivalent of:

```bat
steamcmd.exe +login anonymous +force_install_dir "E:\steam\steamapps\common\Windrose Dedicated Server" +app_update 4129620 validate +quit
```

## Server Updates

The Dashboard includes `Update Server`, which runs SteamCMD for the ASKA Dedicated Server Steam app ID:

```text
3246670
```

The Dashboard also shows `Server update`. The app reads the local Steam build ID from:

```text
appmanifest_3246670.acf
```

Then it checks Steam's public `ISteamApps/UpToDateCheck` endpoint. The status will show `Latest`, `Update available`, `Checking`, or `Check failed`.

Configure `SteamCMD executable` in Settings. Default:

```text
C:\steamcmd\steamcmd.exe
```

The update command is equivalent to:

```bat
steamcmd.exe +login anonymous +force_install_dir "E:\steam\steamapps\common\ASKA Dedicated Server" +app_update 3246670 validate +quit
```

The app refuses to update while `AskaServer.exe` is running. Before updating, it creates:

```text
before_server_update_YYYY-MM-DD_HH-mm
server_update_preflight_YYYY-MM-DD_HH-mm
```

The preflight backup includes `server properties.txt`, `AskaServer.bat`, and BepInEx plugin/config folders where found.

## Package To EXE

Install PyInstaller if needed:

```bat
python -m pip install pyinstaller
```

Then run:

```bat
build_exe.bat
```

The build output will be:

```text
dist\ASKA Server Manager.exe
```

When running the packaged `.exe`, `settings.json` is created beside the executable so the app can be shared as a folder containing the `.exe` and its local settings.
