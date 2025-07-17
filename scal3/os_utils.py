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

from __future__ import annotations

import logging
import os
import shutil
import sys
from os.path import isdir, isfile

__all__ = [
	"fixStrForFileName",
	"getOsName",
	"getUserDisplayName",
	"goodkill",
	"makeDir",
	"openUrl",
	"osName",
]


log = logging.getLogger("starcal3")


def getOsName() -> str:
	"""returns: "linux", "win", "mac", "unix"."""
	# psys = platform.system().lower()-- "linux", "windows", "darwin", ...
	plat = sys.platform  # "linux2", "win32", "darwin"
	if plat.startswith("linux"):
		return "linux"
	if plat.startswith("win"):
		return "win"
	if plat == "darwin":
		# os.environ["OSTYPE"] == "darwin10.0"
		# os.environ["MACHTYPE"] == "x86_64-apple-darwin10.0"
		# platform.dist() == ("", "", "")
		# platform.release() == "10.3.0"
		return "mac"
	if os.sep == "\\":
		return "win"
	if os.sep == "/":
		return "unix"
	raise OSError("Unkown operating system!")


osName = getOsName()


def makeDir(direc: str) -> None:
	if not isdir(direc):
		os.makedirs(direc)


def getUsersData() -> list[dict[str, str]]:
	data = []
	with open("/etc/passwd", encoding="utf-8") as fp:
		for line in fp:
			parts = line.strip().split(":")
			if len(parts) < 7:
				continue
			data.append(
				{
					"login": parts[0],
					"uid": parts[2],
					"gid": parts[3],
					"real_name": parts[4],
					"home_dir": parts[5],
					"shell": parts[6],
				},
			)
	return data


def getUserDisplayName() -> str | None:
	if os.sep == "/":
		username = os.getenv("USER")
		if isfile("/etc/passwd"):
			for user in getUsersData():
				if user["login"] == username:
					if user["real_name"]:
						return user["real_name"]
					return username
		return username
	# FIXME
	return os.getenv("USERNAME")


def kill(pid: int, signal: int = 0) -> bool:
	"""
	Sends a signal to a process
	returns True if the pid is dead
	with no signal argument, sends no signal.
	"""
	# if "ps --no-headers" returns no lines, the pid is dead
	try:
		os.kill(pid, signal)
	except OSError as e:
		if e.errno == 3:  # process is dead
			return True
		if e.errno == 1:  # no permissions
			return False
		raise
	return True


def dead(pid: int) -> bool:
	if kill(pid):
		return True

	# maybe the pid is a zombie that needs us to wait for it
	from os import WNOHANG, waitpid

	try:
		dead = waitpid(pid, WNOHANG)[0]
	except OSError as e:
		# pid is not a child
		if e.errno == 10:
			return False
		raise
	return dead > 0


# def kill(pid, sig=0): pass #DEBUG: test hang condition


def goodkill(pid: int, interval: float = 1, hung: int = 20) -> None:
	"""Let process die gracefully, gradually send harsher signals if necessary."""
	from signal import SIGHUP, SIGINT, SIGKILL, SIGTERM
	from time import sleep

	for signal in (SIGTERM, SIGINT, SIGHUP):
		if kill(pid, signal):
			return
		if dead(pid):
			return
		sleep(interval)

	for _i in range(hung):
		if kill(pid, SIGKILL):
			return
		if dead(pid):
			return
		sleep(interval)

	raise OSError(f"Process {pid} is hung. Giving up kill.")


def fixStrForFileNameForWindows(fname: str) -> str:
	import re

	fname = re.sub(r'[\x00-\x1f\\/:"*?<>|]+', "_", fname)
	fname = re.sub(r"[ _]+", "_", fname)
	if fname.upper() in {
		"COM1",
		"COM2",
		"COM3",
		"COM4",
		"COM5",
		"COM6",
		"COM7",
		"COM8",
		"COM9",
		"LPT1",
		"LPT2",
		"LPT3",
		"LPT4",
		"LPT5",
		"LPT6",
		"LPT7",
		"LPT8",
		"LPT9",
		"CON",
		"PRN",
		"AUX",
		"NUL",
	}:
		fname += "-1"
	return fname


def fixStrForFileName(fname: str) -> str:
	if osName == "win":
		return fixStrForFileNameForWindows(fname)
	return fname.replace("/", "_").replace("\\", "_")


# returns False if could not find any browser or command to open the URL
def openUrl(url: str) -> bool:
	from subprocess import Popen

	if osName == "win":
		Popen([url])  # noqa: S603
		return True
	if osName == "mac":
		Popen(["open", url])  # noqa: S603, S607
		return True
	try:
		Popen(["xdg-open", url])  # noqa: S603, S607
	except Exception:
		log.exception("")
	else:
		return True
	# if not url.startswith("http"):  # FIXME
	# 	return
	try:
		import webbrowser
	except ImportError:
		pass
	else:
		webbrowser.open(url)
		return True
	try:
		import gnomevfs
	except ImportError:
		pass
	else:
		gnomevfs.url_show(url)
		return True
	for commandName in ("gnome-www-browser", "firefox", "iceweasel", "konqueror"):
		command = shutil.which(commandName)
		if not command:
			continue
		try:
			Popen([command, url])  # noqa: S603
		except Exception as e:
			log.error(f"{e}")
		else:
			return True
	return False
