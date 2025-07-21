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

# no logging in this file

import os
from os.path import abspath, dirname, join

from scal3.os_utils import getOsName

APP_NAME = "starcal3"

__all__ = [
	"APP_NAME",
	"cacheDir",
	"confDir",
	"deskDir",
	"homeDir",
	"modDir",
	"pixDir",
	"plugDir",
	"plugDirUser",
	"sourceDir",
	"svgDir",
	"sysConfDir",
	"tmpDir",
]

osName = getOsName()

scalDir = dirname(__file__)
cwd = os.getcwd()
if scalDir in {".", ""}:
	scalDir = cwd
elif os.sep == "/":
	if scalDir.startswith("./"):
		scalDir = cwd + scalDir[1:]
	elif scalDir[0] != "/":
		scalDir = join(cwd, scalDir)
elif os.sep == "\\":  # noqa: SIM102
	if scalDir.startswith(".\\"):
		scalDir = cwd + scalDir[1:]

plugDirName = "plugins"

sourceDir = abspath(dirname(scalDir))
pixDir = join(sourceDir, "pixmaps")
svgDir = join(sourceDir, "svg")
plugDir = join(sourceDir, plugDirName)


def mustEnv(name: str) -> str:
	value = os.getenv(name)
	assert value, f"missing env {name}"
	return value


if osName in {"linux", "unix"}:
	homeDir = mustEnv("HOME")
	confDir = homeDir + "/." + APP_NAME
	sysConfDir = "/etc/" + APP_NAME
	tmpDir = "/tmp"
	cacheDir = join(homeDir, ".cache", APP_NAME)
	# user = mustEnv("USER")
elif osName == "mac":
	homeDir = mustEnv("HOME")
	_libDir = join(homeDir, "Library")
	confDir = join(_libDir, "Preferences", APP_NAME)
	# OR "/Library/" + APP_NAME
	sysConfDir = join(sourceDir, "config")  # FIXME
	tmpDir = "/tmp"
	cacheDir = join(_libDir, "Caches", APP_NAME)
	# user = mustEnv("USER")
elif osName == "win":
	# homeDrive = os.environ["HOMEDRIVE"]
	homeDir = mustEnv("HOMEPATH")
	_appData = mustEnv("APPDATA")
	confDir = _appData + "\\" + APP_NAME
	sysConfDir = join(sourceDir, "config")
	tmpDir = mustEnv("TEMP")
	cacheDir = join(confDir, "Cache")  # FIXME: right directory?
	# user = mustEnv("USERNAME")
else:
	raise OSError("Unkown operating system!")

deskDir = join(homeDir, "Desktop")  # in all operating systems? FIXME

userPlugConf = join(confDir, "plugin.conf")
modDir = f"{scalDir}/cal_types"
plugDirUser = join(confDir, plugDirName)

purpleDir = join(homeDir, ".purple")  # FIXME
