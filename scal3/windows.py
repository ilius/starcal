from __future__ import annotations

import os
from os.path import join

from scal3.core import APP_NAME

__all__ = ["winMakeShortcut", "winStartupDir", "winStartupFile"]
winStartupRelPath = r"\Microsoft\Windows\Start Menu\Programs\Startup"
appData = os.getenv("APPDATA")
assert appData
winStartupDir = appData + winStartupRelPath
# winStartupDirSys = os.getenv("ALLUSERSPROFILE") + winStartupRelPath
winStartupFile = join(winStartupDir, APP_NAME + ".lnk")


def winMakeShortcut(srcPath: str, dstPath: str) -> None:
	from win32com.client import Dispatch

	shell = Dispatch("WScript.Shell")
	shortcut = shell.CreateShortCut(dstPath)
	shortcut.Targetpath = srcPath
	# shortcut.WorkingDirectory = ...
	shortcut.save()
