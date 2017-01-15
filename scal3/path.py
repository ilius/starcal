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

import os
from os.path import dirname, join, abspath

from scal3.os_utils import getOsName

APP_NAME = "starcal3"

osName = getOsName()

srcDir = dirname(__file__)
cwd = os.getcwd()
if srcDir in (".", ""):
	srcDir = cwd
elif os.sep == "/":
	if srcDir.startswith("./"):
		srcDir = cwd + srcDir[1:]
	elif srcDir[0] != "/":
		srcDir = join(cwd, srcDir)
elif os.sep == "\\":
	if srcDir.startswith(".\\"):
		srcDir = cwd + srcDir[1:]
#print("srcDir=%r"%srcDir)

rootDir = abspath(dirname(srcDir))
pixDir = join(rootDir, "pixmaps")
plugDir = join(rootDir, "plugins")

if osName in ("linux", "unix"):
	homeDir = os.getenv("HOME")
	confDir = homeDir + "/." + APP_NAME
	sysConfDir = "/etc/" + APP_NAME
	tmpDir = "/tmp"
	#user = os.getenv("USER")
elif osName == "mac":
	homeDir = os.getenv("HOME")
	confDir = homeDir + "/Library/Preferences/" + APP_NAME
	# OR "/Library/" + APP_NAME
	sysConfDir = join(rootDir, "config")  # FIXME
	tmpDir = "/tmp"
	#user = os.getenv("USER")
elif osName == "win":
	#homeDrive = os.environ["HOMEDRIVE"]
	homeDir = os.getenv("HOMEPATH")
	confDir = os.getenv("APPDATA") + "\\" + APP_NAME
	sysConfDir = join(rootDir, "config")
	tmpDir = os.getenv("TEMP")
	#user = os.getenv("USERNAME")
else:
	raise OSError("Unkown operating system!")

deskDir = join(homeDir, "Desktop")  # in all operating systems? FIXME

userPlugConf = join(confDir, "plugin.conf")
modDir = "%s/cal_types" % srcDir
plugDirUser = join(confDir, "plugins")
objectDir = join(confDir, "objects")

purpleDir = join(homeDir, ".purple")  # FIXME
