import os
from os.path import join
from scal3.core import APP_NAME

winStartupRelPath = r'\Microsoft\Windows\Start Menu\Programs\Startup'
winStartupDir = os.getenv('APPDATA') + winStartupRelPath
#winStartupDirSys = os.getenv('ALLUSERSPROFILE') + winStartupRelPath
winStartupFile = join(winStartupDir, APP_NAME + '.lnk')


def winMakeShortcut(srcPath, dstPath, iconPath=None):
	from win32com.client import Dispatch
	shell = Dispatch('WScript.Shell')
	shortcut = shell.CreateShortCut(dstPath)
	shortcut.Targetpath = srcPath
	#shortcut.WorkingDirectory = ...
	shortcut.save()
