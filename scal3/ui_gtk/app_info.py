from __future__ import annotations

import os

from scal3 import locale_man, logger

log = logger.get()

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import subprocess

__all__ = ["popenFile"]


def getDefaultAppCommand(fpath: str) -> str | None:
	from gi.repository import Gio as gio

	mime_type = gio.content_type_guess(fpath)[0]
	try:
		app = gio.app_info_get_all_for_type(mime_type)[0]
	except IndexError:
		return None
	return app.get_executable()


def popenFile(fpath: str) -> subprocess.Popen[bytes] | None:
	from subprocess import Popen

	command = getDefaultAppCommand(fpath)
	if not command:
		return None
	os.environ["LANG"] = locale_man.sysLangDefault
	p = Popen([command, fpath])
	os.environ["LANG"] = locale_man.lang.v
	return p


if __name__ == "__main__":
	log.info(repr(getDefaultAppCommand(sys.argv[1])))
