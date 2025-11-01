from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.ui_gtk.pytypes import CustomizableCalObjType

__all__ = ["mainWinItemLoaderByName", "mainWinItemsDesc"]

mainWinItemsDesc = {
	"dayCal": _("Day Calendar"),
	"labelBox": _("Year & Month Bar"),
	"monthCal": _("Month Calendar"),
	"monthPBar": _("Month Progress Bar"),
	"seasonPBar": _("Season Progress Bar"),
	"yearPBar": _("Year Progress Bar"),
	"toolbar": _("Toolbar"),
	"weekCal": _("Week Calendar"),
}


def _load_dayCal() -> type[CustomizableCalObjType]:
	from scal3.ui_gtk.mainwin_items import dayCal

	return dayCal.CalObj


def _load_labelBox() -> type[CustomizableCalObjType]:
	from scal3.ui_gtk.mainwin_items import labelBox

	return labelBox.CalObj


def _load_monthCal() -> type[CustomizableCalObjType]:
	from scal3.ui_gtk.mainwin_items import monthCal

	return monthCal.CalObj


def _load_monthPBar() -> type[CustomizableCalObjType]:
	from scal3.ui_gtk.mainwin_items import monthPBar

	return monthPBar.CalObj


def _load_seasonPBar() -> type[CustomizableCalObjType]:
	from scal3.ui_gtk.mainwin_items import seasonPBar

	return seasonPBar.CalObj


def _load_yearPBar() -> type[CustomizableCalObjType]:
	from scal3.ui_gtk.mainwin_items import yearPBar

	return yearPBar.CalObj


def _load_toolbar() -> type[CustomizableCalObjType]:
	from scal3.ui_gtk.mainwin_items import toolbar

	return toolbar.CalObj


def _load_weekCal() -> type[CustomizableCalObjType]:
	from scal3.ui_gtk.mainwin_items import weekCal

	return weekCal.CalObj


mainWinItemLoaderByName: dict[str, Callable[[], type[CustomizableCalObjType]]] = {
	"scal3.ui_gtk.mainwin_items.dayCal": _load_dayCal,
	"scal3.ui_gtk.mainwin_items.labelBox": _load_labelBox,
	"scal3.ui_gtk.mainwin_items.monthCal": _load_monthCal,
	"scal3.ui_gtk.mainwin_items.monthPBar": _load_monthPBar,
	"scal3.ui_gtk.mainwin_items.seasonPBar": _load_seasonPBar,
	"scal3.ui_gtk.mainwin_items.yearPBar": _load_yearPBar,
	"scal3.ui_gtk.mainwin_items.toolbar": _load_toolbar,
	"scal3.ui_gtk.mainwin_items.weekCal": _load_weekCal,
}
