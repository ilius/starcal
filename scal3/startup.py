#!/usr/bin/env python3
from scal3 import logger
log = logger.get()

from os.path import isfile, isdir

from scal3.path import *
from scal3.os_utils import makeDir

from scal3 import core
from scal3.core import osName

comDeskDir = f"{homeDir}/.config/autostart"
comDesk = f"{comDeskDir}/{APP_NAME}.desktop"
#kdeDesk = f"{homeDir}/.kde/Autostart/{APP_NAME}.desktop"


def addStartup():
	if osName == "win":
		from scal3.windows import winMakeShortcut, winStartupFile
		makeDir(winStartupDir)
		#fname = APP_NAME + ("-qt" if uiName=="qt" else "") + ".pyw"
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
Icon={APP_NAME}
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
	if osName == "win":## FIXME
		from scal3.windows import winStartupFile
		if isfile(winStartupFile):
			os.remove(winStartupFile)
	elif isfile(comDesk):
		os.remove(comDesk)


def checkStartup():
	if osName == "win":
		from scal3.windows import winStartupFile
		return isfile(winStartupFile)
	elif isfile(comDesk):
		return True
	return False
