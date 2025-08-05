# mypy: ignore-errors

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from scal3.ui_gtk.starcal_types import MainWinType

__all__ = ["doFullImport"]
# to help with testing phase and also tell code analyzers these are imported


def doFullImport(win: MainWinType) -> None:
	import scal3.cal_types.import_all  # noqa: F401
	import scal3.event_lib_import_all  # noqa: F401
	import scal3.ui_gtk.event.import_all  # noqa: F401
	from scal3.ui_gtk.event.occurrence_view import LimitedHeightDayOccurrenceView

	LimitedHeightDayOccurrenceView(win).getOptionsWidget()

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

	PluginsTextBox(win).getOptionsWidget()
