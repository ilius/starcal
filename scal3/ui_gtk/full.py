import signal
import sys

from gi.repository.GLib import timeout_add

from scal3 import event_lib, ui
from scal3.ui_gtk import gtk, pixcache, starcal
from scal3.ui_gtk import hijri as hijri_gtk

ui.init()

ui.winKeepAbove = False

pixcache.cacheSaveStart()
ui.eventUpdateQueue.startLoop()

starcal.listener.dateChange.add(hijri_gtk.HijriMonthsExpirationListener())
hijri_gtk.checkHijriMonthsExpiration()

starcal.checkEventsReadOnly(False)
event_lib.info.updateAndSave()

mainWin = starcal.MainWin(statusIconMode=2)

mainWin.present()


def tick():
	while gtk.events_pending():
		gtk.main_iteration_do(False)


def openAllWindows():
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

	mainWin.yearWheelShow()
	while ui.yearWheelWin.is_visible():
		tick()

	mainWin.onExportClick()
	while mainWin.exportDialog.is_visible():
		tick()

	mainWin.aboutShow()
	while mainWin.aboutDialog.is_visible():
		tick()


signal.signal(signal.SIGINT, sys.exit)

mainWin.dayCalWinShow()

timeout_add(500, openAllWindows)

sys.exit(gtk.main())
