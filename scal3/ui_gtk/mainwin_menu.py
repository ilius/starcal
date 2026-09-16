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
from typing import TYPE_CHECKING

from scal3 import ui
from scal3.cal_types import calTypes
from scal3.locale_man import rtl  # import scal3.locale_man after core
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui.mainmenuitems import menuMainItemDefs
from scal3.ui_gtk import Menu, gtk, popup_menu_at
from scal3.ui_gtk.menuitems import (
	CheckMenuItem,
	ImageMenuItem,
	ResizeMenuItem,
)
from scal3.ui_gtk.starcal_funcs import (
	copyDateGetCallback,
	menuMainPopup,
	onResizeFromMenu,
	yearWheelShow,
)

if TYPE_CHECKING:
	from scal3.ui_gtk import gdk
	from scal3.ui_gtk.mainwin import MainWin
	from scal3.ui_gtk.menuitems import ItemCallback
	from scal3.ui_gtk.pytypes import CustomizableCalObjType
	from scal3.ui_gtk.signals import SignalHandlerType
	from scal3.ui_gtk.starcal_classes import MainWinEventMan

__all__ = ["MainWinMenu"]


class MainWinMenu:
	"""Main menu and cell popup menu building for MainWin."""

	win: gtk.ApplicationWindow
	w: gtk.Widget
	eventMan: MainWinEventMan
	menuMain: gtk.Menu | None
	menuCell: gtk.Menu | None
	menuItemsCallback: dict[str, ItemCallback]

	def __init__(
		self,
		mainWin: MainWin,
		win: gtk.ApplicationWindow,
		w: gtk.Widget,
		eventMan: MainWinEventMan,
	) -> None:
		self.mainWin = mainWin
		self.win = win
		self.w = w
		self.eventMan = eventMan
		self.menuMain = None
		self.menuCell = None
		self.menuItemsCallback = self.createMenuItemsCallback()
		assert sorted(self.menuItemsCallback) == sorted(menuMainItemDefs)

	def createMenuItemsCallback(self) -> dict[str, ItemCallback]:
		mainWin = self.mainWin
		return {
			"onTop": self.onKeepAboveClick,
			"onAllDesktops": self.onStickyClick,
			"today": mainWin.goToday,
			"selectDate": mainWin.selectDateShow,
			"dayInfo": mainWin.dayInfoShowFromMenu,
			"customize": mainWin.customizeShow,
			"preferences": mainWin.prefShow,
			# "addCustomEvent": mainWin.addCustomEvent,
			"dayCalWin": mainWin.dayCalWinShow,
			"eventManager": mainWin.eventManShow,
			"timeLine": mainWin.timeLineShow,
			"yearWheel": yearWheelShow,
			# "weekCal": mainWin.weekCalShow,
			"exportToHtml": mainWin.onExportClick,
			"adjustTime": mainWin.adjustTime,
			"about": mainWin.aboutShow,
			"quit": mainWin.quitFromMenu,
		}

	def cellPopup(
		self,
		_sig: SignalHandlerType,
		x: int,
		y: int,
		item: CustomizableCalObjType,
	) -> None:
		mainWin = self.mainWin
		widget = item.w
		# item.objName is in ("weekCal", "monthCal", ...)
		menu = Menu()
		# ----
		for calType in calTypes.active:
			calTypeDesc = calTypes.getDesc(calType)
			assert calTypeDesc
			menu.add(
				ImageMenuItem(
					label=_("Copy {calType} Date").format(
						calType=_(calTypeDesc, ctx="calendar"),
					),
					imageName="edit-copy.svg",
					onActivate=copyDateGetCallback(calType),
				),
			)
		menu.add(
			ImageMenuItem(
				label=_("Day Info"),
				imageName="info.svg",
				onActivate=mainWin.dayInfoShowFromMenu,
			),
		)
		addToItem = self.eventMan.getEventAddToMenuItem()
		if addToItem is not None:
			menu.add(addToItem)
		self.eventMan.addEditEventCellMenuItems(menu)
		menu.add(gtk.SeparatorMenuItem())
		menu.add(
			ImageMenuItem(
				label=_("Select _Today"),
				imageName="go-home.svg",
				onActivate=mainWin.goToday,
			),
		)
		menu.add(
			ImageMenuItem(
				label=_("Select _Date..."),
				imageName="select-date.svg",
				onActivate=mainWin.selectDateShow,
			),
		)
		# if item.objName in {"weekCal", "monthCal"}:
		# 	isWeek = item.objName == "weekCal"
		# 	calDesc = "Month Calendar" if isWeek else "Week Calendar"
		# 	menu.add(
		# 		ImageMenuItem(
		# 			label=_("Switch to " + calDesc),
		# 			imageName="" if isWeek else "week-calendar.svg",
		# 			onActivate=mainWin.switchWcalMcal,
		# 		),
		# 	)
		menu.add(
			ImageMenuItem(
				label=_("In Time Line"),
				imageName="timeline.svg",
				onActivate=mainWin.timeLineShowSelectedDay,
			),
		)
		if os.path.isfile("/usr/bin/evolution"):  # FIXME
			menu.add(
				ImageMenuItem(
					label=_("In E_volution"),
					imageName="evolution.png",
					onActivate=ui.cells.current.dayOpenEvolution,
				),
			)
		# ----
		moreMenu = Menu()
		moreMenu.add(
			ImageMenuItem(
				label=_("_Customize"),
				imageName="document-edit.svg",
				onActivate=mainWin.customizeShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Preferences"),
				imageName="preferences-system.svg",
				onActivate=mainWin.prefShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Event Manager"),
				imageName="list-add.svg",
				onActivate=mainWin.eventManShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("Year Wheel"),
				imageName="year-wheel.svg",
				onActivate=yearWheelShow,
			),
		)  # icon? FIXME
		moreMenu.add(
			ImageMenuItem(
				label=_("Day Calendar (Desktop Widget)"),
				imageName="starcal.svg",
				onActivate=mainWin.dayCalWinShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("Export to {format}").format(format="HTML"),
				imageName="export-to-html.svg",
				onActivate=mainWin.onExportClick,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_About"),
				imageName="dialog-information.svg",
				onActivate=mainWin.aboutShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Quit"),
				imageName="application-exit.svg",
				onActivate=mainWin.onQuitClick,
			),
		)
		# --
		moreMenu.show_all()
		moreItem = ImageMenuItem(label=_("More"))
		moreItem.set_submenu(moreMenu)
		# moreItem.show_all()
		menu.add(moreItem)
		# ----
		menu.show_all()
		self.menuCell = menu
		popup_menu_at(menu, widget, x, y, root=self.w, rtl=rtl)
		ui.updateFocusTime()

	def onResizeFromMenu(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		return onResizeFromMenu(self.menuMain, self.win, gevent)

	# TODO: customize list of main menu items (disable/enable/re-order)
	def mainCreate(self) -> gtk.Menu:
		if self.menuMain:
			return self.menuMain
		menu = gtk.Menu(reserve_toggle_size=False)
		# ----
		menu.add(
			ResizeMenuItem(
				label=_("Resize"),
				onButtonPress=self.onResizeFromMenu,
			)
		)
		for name, itemDict in menuMainItemDefs.items():
			menu.add(
				itemDict["cls"](
					label=itemDict["label"],
					onActivate=self.menuItemsCallback[name],
					**itemDict["args"],
				)
			)
		# -------
		menu.show_all()
		self.menuMain = menu
		return menu

	# handler for "popup-main-menu" signal
	def mainPopup(
		self,
		_sig: SignalHandlerType,
		x: int,
		y: int,
		item: CustomizableCalObjType,
	) -> None:
		menuMainPopup(self.w, self.mainCreate, x, y, item)

	def destroyMenus(self) -> None:
		if self.menuMain:
			self.menuMain.destroy()
			self.menuMain = None
		if self.menuCell:
			self.menuCell.destroy()
			self.menuCell = None

	def onKeepAboveClick(self, check: gtk.Widget) -> None:
		assert isinstance(check, CheckMenuItem)
		act = check.get_active()
		self.win.set_keep_above(act)
		conf.winKeepAbove.v = act
		ui.saveLiveConf()

	def onStickyClick(self, check: gtk.Widget) -> None:
		assert isinstance(check, CheckMenuItem)
		if check.get_active():
			self.win.stick()
			conf.winSticky.v = True
		else:
			self.win.unstick()
			conf.winSticky.v = False
		ui.saveLiveConf()
