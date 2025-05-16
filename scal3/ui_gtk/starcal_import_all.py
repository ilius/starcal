from gi.repository import Gtk as gtk

__all__ = ["doFullImport"]
# to help with testing phase and also tell code analyzers these are imported


def doFullImport(win: gtk.Window) -> None:
	import scal3.cal_types.import_all
	import scal3.event_lib_import_all
	import scal3.ui_gtk.event.import_all
	from scal3.ui_gtk.event.occurrence_view import LimitedHeightDayOccurrenceView

	LimitedHeightDayOccurrenceView().getOptionsWidget()

	from scal3.ui_gtk.mainwin_items.dayCal import CalObj

	CalObj(win).getOptionsWidget()

	from scal3.ui_gtk.mainwin_items.labelBox import CalObj

	CalObj(win).getOptionsWidget()

	from scal3.ui_gtk.mainwin_items.monthCal import CalObj

	CalObj(win).getOptionsWidget()

	from scal3.ui_gtk.mainwin_items.monthPBar import CalObj

	CalObj(win).getOptionsWidget()

	from scal3.ui_gtk.mainwin_items.seasonPBar import CalObj

	CalObj(win).getOptionsWidget()

	from scal3.ui_gtk.mainwin_items.toolbar import CalObj

	CalObj(win).getOptionsWidget()

	from scal3.ui_gtk.mainwin_items.weekCal import CalObj

	CalObj(win).getOptionsWidget()

	from scal3.ui_gtk.mainwin_items.yearPBar import CalObj

	CalObj(win).getOptionsWidget()

	from scal3.ui_gtk.pluginsText import PluginsTextBox

	CalObj(win).getOptionsWidget()
