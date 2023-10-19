from scal3 import logger

log = logger.get()

import os
from os.path import isdir, isfile, join

from scal3 import core
from scal3.core import APP_NAME
from scal3.os_utils import makeDir, osName
from scal3.path import homeDir, sourceDir

comDeskDir = f"{homeDir}/.config/autostart"
comDesk = f"{comDeskDir}/{APP_NAME}.desktop"
# kdeDesk = f"{homeDir}/.kde/Autostart/{APP_NAME}.desktop"


def addStartup():
	if osName == "win":
		from scal3.windows import winMakeShortcut, winStartupDir, winStartupFile

		makeDir(winStartupDir)
		# fname = APP_NAME + ("-qt" if uiName=="qt" else "") + ".pyw"
		fname = core.COMMAND + ".pyw"
		fpath = join(sourceDir, fname)
		try:
			winMakeShortcut(fpath, winStartupFile)
		except Exception:
			return False
		else:
			return True
	elif isdir(f"{homeDir}/.config"):
		# osName in ("linux", "mac")
		# maybe Gnome/KDE on Solaris, *BSD, ...
		text = f"""[Desktop Entry]
Type=Application
Name={core.APP_DESC} {core.VERSION}
Icon=starcal32
Exec={core.COMMAND}"""
		# FIXME: double quotes needed when the exec path has space
		# f"{core.COMMAND!r}" or repr(core.COMMAND) adds single quotes
		# does it work with single quotes too??
		makeDir(comDeskDir)
		try:
			fp = open(comDesk, "w")
		except Exception:
			log.exception("")
			return False
		else:
			fp.write(text)
			return True
	elif osName == "mac":  # FIXME
		pass
	return False


def removeStartup():
	if osName == "win":  # FIXME
		from scal3.windows import winStartupFile

		if isfile(winStartupFile):
			os.remove(winStartupFile)
	elif isfile(comDesk):
		os.remove(comDesk)


def checkStartup():
	if osName == "win":
		from scal3.windows import winStartupFile

		return isfile(winStartupFile)
	if isfile(comDesk):
		return True
	return False
