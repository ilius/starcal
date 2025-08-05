#!/usr/bin/env python3
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

import os
import signal
import sys
from os.path import dirname
from typing import TYPE_CHECKING

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3 import logger

log = logger.get()


import scal3.account.starcal  # noqa: F401

try:
	import scal3.account.google  # noqa: F401
except Exception as e:
	log.error(f"error loading google account module: {e}")

from scal3 import core, ui
from scal3.cell import init as initCell
from scal3.event_lib import ev
from scal3.ui import conf
from scal3.ui_gtk import (
	gtk,
	listener,
	pixcache,
)
from scal3.ui_gtk import hijri as hijri_gtk
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.starcal_import_all import doFullImport
from scal3.ui_gtk.starcal_mainwin import MainWin

if TYPE_CHECKING:
	from scal3.ui_gtk.pytypes import CalObjType

__all__ = ["MainWin", "checkEventsReadOnly", "listener", "main"]


# _ = locale_man.loadTranslator()  # FIXME

ui.uiName = "gtk"


# -------------------------------------------------------------------------3


# app_info.COMMAND = sys.argv[0] # OR __file__ # ????????


gtk.init_check(sys.argv)  # type: ignore[call-arg]

# from scal3.os_utils import openUrl
# clickWebsite = lambda widget, url: openUrl(url)
# gtk.link_button_set_uri_hook(clickWebsite)
# gtk.about_dialog_set_url_hook(clickWebsite)

# gtk_link_button_set_uri_hook has been deprecated since version 2.24
# and should not be used in newly-written code.
# Use the “clicked” signal instead
# FIXME

# gtk_about_dialog_set_url_hook has been deprecated since version 2.24
# and should not be used in newly-written code.
# Use the “activate-link” signal
# FIXME


for plug in core.allPlugList.v:
	if plug is None:
		continue
	if hasattr(plug, "onCurrentDateChange"):
		listener.dateChange.add(plug)


def main() -> None:
	statusIconMode = 2
	action = ""
	if conf.showMain.v:
		action = "show"
	if len(sys.argv) > 1:
		if sys.argv[1] in {"--no-tray-icon", "--no-status-icon"}:
			statusIconMode = 0
			action = "show"
		elif sys.argv[1] == "--hide":
			action = ""
		elif sys.argv[1] == "--show":
			action = "show"
		# elif sys.argv[1] == "--html":#????????????
		# 	action = "html"
		# elif sys.argv[1] == "--svg":#????????????
		# 	action = "svg"
	# -------------------------------
	ui.init()
	initCell()
	# -------------------------------
	pixcache.cacheSaveStart()
	ui.eventUpdateQueue.startLoop()
	# -------------------------------
	listener.dateChange.add(hijri_gtk.HijriMonthsExpirationListener())
	hijri_gtk.checkHijriMonthsExpiration()
	# -------------------------------
	checkEventsReadOnly(False)
	# FIXME: right place?
	ev.info.updateAndSave()
	# -------------------------------
	mainWin = MainWin(statusIconMode=statusIconMode)
	mainWin.broadcastConfigChange()
	if TYPE_CHECKING:
		_mainWin: CalObjType = mainWin
	if os.getenv("STARCAL_FULL_IMPORT"):
		doFullImport(mainWin)
	# -------------------------------
	# if action == "html":
	# 	mainWin.exportHtml("calendar.html") # exportHtml(path, months, title)
	# 	sys.exit(0)
	# elif action == "svg":
	# 	mainWin.export.exportSvg(f"{core.deskDir}/2010-01.svg", [(2010, 1)])
	# 	sys.exit(0)
	if action == "show" or not mainWin.sicon:
		mainWin.win.present()
	if conf.showDesktopWidget.v:
		mainWin.dayCalWinShow()
	# ud.rootWindow.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
	# FIXME: ^
	# mainWin.app.run(None)
	signal.signal(signal.SIGINT, mainWin.quitOnSignal)
	gtk.main()


if __name__ == "__main__":
	main()
