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
Shared helpers for the Xfce panel applet install logic.

xfce4-panel 4.18 (and older) only loads plugins from the panel's own
compiled-in directories:
  - desktop files: $DATADIR/xfce4/panel/plugins   (usually /usr/share/...)
  - modules:       $LIBDIR/xfce4/panel/plugins    (usually /usr/lib(64)/...
                     or /usr/lib/<multiarch>/... on Debian/Ubuntu)
so the plugin must be installed there (requires root). Newer 4.20+ panels
additionally scan $XDG_DATA_DIRS.
"""

from __future__ import annotations

import glob
import os
import subprocess
from os.path import isdir, join

__all__ = ["get_libdir"]


def get_multiarch() -> str:
	try:
		proc = subprocess.run(
			["dpkg-architecture", "-qDEB_HOST_MULTIARCH"],
			capture_output=True,
			text=True,
			check=False,
		)
	except OSError:
		return ""
	if proc.returncode != 0:
		return ""
	return proc.stdout.strip()


def has_plugin_modules(path: str) -> bool:
	if not isdir(path):
		return False
	try:
		return any(name.endswith(".so") for name in os.listdir(path))
	except OSError:
		return False


def get_libdir(prefix: str) -> str:
	libdir = "lib"
	multiarch = get_multiarch()
	if multiarch:
		libdir = join("lib", multiarch)
	if isdir(join(prefix, libdir, "xfce4", "panel", "plugins")):
		return libdir
	for path in [
		join(prefix, "lib64", "xfce4", "panel", "plugins"),
		join(prefix, "lib", "xfce4", "panel", "plugins"),
		*glob.glob("/usr/lib/*/xfce4/panel/plugins"),
	]:
		if has_plugin_modules(path):
			if path.startswith(prefix + os.sep):
				return path[len(prefix) + 1 :]
			return path
	return libdir
