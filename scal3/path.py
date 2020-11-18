#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

# no logging in this file

import os
from os.path import dirname, join, abspath

from scal3.os_utils import getOsName

APP_NAME = "starcal3"

osName = getOsName()

scalDir = dirname(__file__)
cwd = os.getcwd()
if scalDir in (".", ""):
	scalDir = cwd
elif os.sep == "/":
	if scalDir.startswith("./"):
		scalDir = cwd + scalDir[1:]
	elif scalDir[0] != "/":
		scalDir = join(cwd, scalDir)
elif os.sep == "\\":
	if scalDir.startswith(".\\"):
		scalDir = cwd + scalDir[1:]

sourceDir = abspath(dirname(scalDir))
pixDir = join(sourceDir, "pixmaps")
svgDir = join(sourceDir, "svg")
plugDir = join(sourceDir, "plugins")

if osName in ("linux", "unix"):
	homeDir = os.getenv("HOME")
	confDir = homeDir + "/." + APP_NAME
	sysConfDir = "/etc/" + APP_NAME
	tmpDir = "/tmp"
	# user = os.getenv("USER")
elif osName == "mac":
	homeDir = os.getenv("HOME")
	confDir = homeDir + "/Library/Preferences/" + APP_NAME
	# OR "/Library/" + APP_NAME
	sysConfDir = join(sourceDir, "config")  # FIXME
	tmpDir = "/tmp"
	# user = os.getenv("USER")
elif osName == "win":
	# homeDrive = os.environ["HOMEDRIVE"]
	homeDir = os.getenv("HOMEPATH")
	confDir = os.getenv("APPDATA") + "\\" + APP_NAME
	sysConfDir = join(sourceDir, "config")
	tmpDir = os.getenv("TEMP")
	# user = os.getenv("USERNAME")
else:
	raise OSError("Unkown operating system!")

deskDir = join(homeDir, "Desktop")  # in all operating systems? FIXME

userPlugConf = join(confDir, "plugin.conf")
modDir = f"{scalDir}/cal_types"
plugDirUser = join(confDir, "plugins")
objectDir = join(confDir, "objects")
cacheDir = join(confDir, "cache")

purpleDir = join(homeDir, ".purple")  # FIXME
