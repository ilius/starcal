#!/usr/bin/env python3
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

"""
Build and install the StarCal Xfce panel applet plugin.

xfce4-panel 4.18 (and older) only loads plugins from the panel's own
compiled-in directories:
  - desktop files: $DATADIR/xfce4/panel/plugins   (usually /usr/share/...)
  - modules:       $LIBDIR/xfce4/panel/plugins    (usually /usr/lib(64)/...
                     or /usr/lib/<multiarch>/... on Debian/Ubuntu)
so the plugin must be installed there (requires root). Newer 4.20+ panels
additionally scan $XDG_DATA_DIRS.

Usage: ./install.py [prefix]   (default prefix: /usr)
"""

from __future__ import annotations

import os
import pwd
import shutil
import subprocess
import sys
from os.path import abspath, dirname, join

SCRIPT_DIR = dirname(abspath(__file__))
REPO_DIR = dirname(SCRIPT_DIR)

sys.path.insert(0, join(REPO_DIR, "distro", "base"))
from xfce_panel import get_libdir  # noqa: E402


def run(cmd: list[str]) -> None:
	print(f"+ {' '.join(cmd)}")
	subprocess.run(cmd, check=True)


def get_applet_dir() -> str:
	applet_dir = os.environ.get("STARCAL_XFCE_APPLET_DIR")
	if applet_dir:
		return applet_dir
	home = os.environ.get("HOME")
	sudo_user = os.environ.get("SUDO_USER")
	if sudo_user and sudo_user != "root":
		try:
			home = pwd.getpwnam(sudo_user).pw_dir
		except KeyError:
			pass
	if not home:
		return join(".starcal3", "xfce-applet")
	return join(home, ".starcal3", "xfce-applet")


def write_launch_command() -> None:
	"""
	Record how to launch starcal so the applet can start it on click, even
	when starcal is not installed in PATH (e.g. run from the source tree).
	The plugin reads this file; starcal overwrites it with its exact command
	whenever it starts.
	"""
	applet_dir = get_applet_dir()
	os.makedirs(applet_dir, exist_ok=True)
	launch_cmd_path = join(applet_dir, "launch-command")
	if os.path.isfile(launch_cmd_path) and os.path.getsize(launch_cmd_path) > 0:
		return
	cmd = os.environ.get("STARCAL_APP")
	if not cmd:
		cmd = shutil.which("starcal3")
	if not cmd:
		repo_launcher = join(REPO_DIR, "starcal")
		if os.access(repo_launcher, os.X_OK):
			cmd = repo_launcher
	if cmd:
		with open(launch_cmd_path, "w", encoding="utf-8") as fp:
			fp.write(cmd + "\n")


def main() -> None:
	prefix = sys.argv[1] if len(sys.argv) > 1 else "/usr"
	libdir = get_libdir(prefix)
	build_dir = join(SCRIPT_DIR, "build")
	shutil.rmtree(build_dir, ignore_errors=True)
	run(
		[
			"meson",
			"setup",
			build_dir,
			f"-Dprefix={prefix}",
			f"-Dlibdir={libdir}",
		],
	)
	run(["meson", "compile", "-C", build_dir])
	run(["meson", "install", "-C", build_dir])
	print(
		f"Installed to {prefix}/{libdir}/xfce4/panel/plugins "
		f"and {prefix}/share/xfce4/panel/plugins.",
	)
	write_launch_command()
	print("Restart the panel (xfce4-panel -r), then add 'StarCalendar' to the panel.")


if __name__ == "__main__":
	main()
