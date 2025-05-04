import signal
import sys

import gi

from scal3.ui import conf

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk as gtk
from gi.repository.GLib import idle_add

from scal3 import ui
from scal3.cell import init as initCell
from scal3.event_lib import state as event_state
from scal3.ui_gtk import hijri as hijri_gtk
from scal3.ui_gtk import pixcache, starcal
from scal3.ui_gtk.event.export import MultiGroupExportDialog
from scal3.ui_gtk.starcal_import_all import doFullImport

ui.init()
initCell()

conf.winKeepAbove.v = False

pixcache.cacheSaveStart()
ui.eventUpdateQueue.startLoop()

starcal.listener.dateChange.add(hijri_gtk.HijriMonthsExpirationListener())
hijri_gtk.checkHijriMonthsExpiration()

starcal.checkEventsReadOnly(False)
event_state.info.updateAndSave()

mainWin = starcal.MainWin(statusIconMode=2)

doFullImport(mainWin)

mainWin.present()


def tick() -> None:
	while gtk.events_pending():
		gtk.main_iteration_do(False)


def openAllWindows() -> None:
	mainWin.dayInfoShow()
	while mainWin.dayInfoDialog.is_visible():
		tick()

	mainWin.goToday()

	mainWin.selectDateShow()
	while mainWin.selectDateDialog.is_visible():
		tick()

	mainWin.timeLineShowSelectedDay()
	while ui.timeLineWin.is_visible():
		tick()

	mainWin.customizeShow()
	while mainWin.customizeWindow.is_visible():
		tick()

	mainWin.prefShow()
	while ui.prefWindow.is_visible():
		tick()

	mainWin.eventManShow()
	while ui.eventManDialog.is_visible():
		tick()

	mainWin.eventSearchShow()
	while ui.eventSearchWin.is_visible():
		tick()

	dialog = MultiGroupExportDialog()
	dialog.run()

	mainWin.yearWheelShow()
	while ui.yearWheelWin.is_visible():
		tick()

	mainWin.onExportClick()
	while mainWin.exportDialog.is_visible():
		tick()

	mainWin.aboutShow()
	while mainWin.aboutDialog.is_visible():
		tick()


def onSigInt(*args) -> None:
	# args: (status: int, frame)
	print(f"SIGINT recieved: {args}")
	sys.exit(1)


signal.signal(signal.SIGINT, onSigInt)

mainWin.dayCalWinShow()

idle_add(openAllWindows)

sys.exit(gtk.main())
