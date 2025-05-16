from __future__ import annotations

from scal3 import logger

log = logger.get()

import sys
from typing import TYPE_CHECKING

from scal3.locale_man import popenDefaultLang

if TYPE_CHECKING:
	import subprocess

__all__ = ["popenFile"]


def getDefaultAppCommand(fpath: str) -> str | None:
	from gi.repository import Gio as gio

	mime_type = gio.content_type_guess(fpath)[0]
	try:
		app = gio.app_info_get_all_for_type(mime_type)[0]
	except IndexError:
		return
	return app.get_executable()


def popenFile(fpath: str) -> subprocess.Popen | None:
	command = getDefaultAppCommand(fpath)
	if not command:
		return
	return popenDefaultLang(
		[
			command,
			fpath,
		],
	)


if __name__ == "__main__":
	log.info(getDefaultAppCommand(sys.argv[1]))
