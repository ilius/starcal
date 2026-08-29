# StarCal Xfce panel applet

An Xfce4-panel plugin that replaces the StarCal tray/status icon: it shows
the current date icon in the panel and forwards clicks to the running StarCal
process.

- Left-click: toggle the StarCal main window
- Middle-click: copy the current date
- Right-click: StarCal's status-icon menu

## Requirements

- xfce4-panel and `libxfce4panel` (development files)
- meson, ninja, and a C compiler
- StarCal (GTK3)

## Build and install

Requires root: xfce4-panel 4.18 (and older) only loads plugins from its own
installed directories, so the plugin must be installed into `/usr/share` and
the panel's library directory (it is **not** enough to install under
`/usr/local`). The default prefix is `/usr` and the script detects the
multiarch library directory on Debian/Ubuntu.

```
sudo ./install.py            # installs to /usr (+ multiarch libdir)
# or:
sudo ./install.py /usr
```

Then restart the panel and add the plugin:

```
xfce4-panel -r
```

Right-click the panel → *Panel* → *Add New Items* → *StarCalendar*.

On xfce4-panel 4.20+ (which scans `$XDG_DATA_DIRS`), a per-user install is
also possible instead of the system one:

```
./install.py ~/.local
```

(adjust `STARCAL_XFCE_APPLET_DIR` if your XDG data dirs differ).

## How it works

StarCal serves the applet from `~/.starcal3/xfce-applet/` whenever a status
icon is active:

- `starcal3-indicator-*.png` — the rendered status icon, saved to a
  hash-named file just like the AppIndicator backend does (a new file when the
  icon changes; the plugin picks the newest)
- `tooltip.txt` — the tooltip text (watched by the plugin)
- `applet.sock` — a Unix socket for click events

Just run StarCal normally (the tray icon is left untouched):

```
starcal
```

The applet in the panel mirrors the tray icon and forwards clicks.

Optionally, run StarCal in applet mode instead — this **replaces** the tray
icon (no tray icon is created):

```
starcal --xfce-applet --hide
```

or with the main window visible at startup:

```
starcal --xfce-applet
```

If StarCal is not running, clicking the applet (left, middle or right) launches
it again: StarCal records its own launch command in the applet dir
(`launch-command`), which the plugin uses first. `install.py` also writes this
file (as a bootstrap, using the `starcal3` command or the launcher in this
source tree). As a fallback the plugin looks up `starcal3` in `PATH`,
`~/.local/bin`, `/usr/bin` and `/usr/local/bin`, or the `STARCAL_APP`
environment variable. Repeated clicks are rate-limited to avoid launching
several instances. The applet dir can be overridden with the
`STARCAL_XFCE_APPLET_DIR` environment variable on both sides.

## Troubleshooting

- Panel plugin messages (`Launching starcal`, `starcal command not found`,
  `Failed to launch starcal`, ...) are logged by xfce4-panel; see
  `journalctl --since "1 hour ago" | grep -i starcal` (or run
  `xfce4-panel --debug` in a terminal to watch them live).
- StarCal's own errors go to `~/.starcal3/log/error` and
  `~/.starcal3/log/debug`.

To remove the plugin, use *Panel* → *Panel Preferences*, or hover the panel
with *Lock panel* turned off and remove it via its handle. Since the applet
replaces the status icon, right-clicking it shows StarCal's menu instead of
the panel's item menu.