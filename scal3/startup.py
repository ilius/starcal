from scal3 import logger
from scal3.app_info import APP_DESC, COMMAND

log = logger.get()

import os
from os.path import isdir, isfile, join

from scal3 import core
from scal3.core import APP_NAME
from scal3.os_utils import makeDir, osName
from scal3.path import homeDir, sourceDir

__all__ = ["addStartup", "checkStartup", "removeStartup"]


comDeskDir = f"{homeDir}/.config/autostart"
comDesk = f"{comDeskDir}/{APP_NAME}.desktop"
# kdeDesk = f"{homeDir}/.kde/Autostart/{APP_NAME}.desktop"


def addStartup() -> bool:
	if osName == "win":
		from scal3.windows import winMakeShortcut, winStartupDir, winStartupFile

		makeDir(winStartupDir)
		# fname = APP_NAME + ("-qt" if uiName=="qt" else "") + ".pyw"
		fname = COMMAND + ".pyw"
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
Name={APP_DESC} {core.VERSION}
Icon=starcal32
Exec={COMMAND}"""
		# FIXME: double quotes needed when the exec path has space
		# f"{COMMAND!r}" or repr(COMMAND) adds single quotes
		# does it work with single quotes too??
		makeDir(comDeskDir)
		try:
			with open(comDesk, "w", encoding="utf-8") as _file:
				_file.write(text)
		except Exception:
			log.exception("")
			return False
		else:
			return True
	elif osName == "mac":  # FIXME
		pass
	return False


def removeStartup() -> None:
	if osName == "win":  # FIXME
		from scal3.windows import winStartupFile

		if isfile(winStartupFile):
			os.remove(winStartupFile)
	elif isfile(comDesk):
		os.remove(comDesk)


def checkStartup() -> bool:
	if osName == "win":
		from scal3.windows import winStartupFile

		return isfile(winStartupFile)
	return isfile(comDesk)
