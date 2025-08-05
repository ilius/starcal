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

from scal3 import logger

log = logger.get()

from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk
from scal3.ui_gtk.cal_obj_base import commonSignals
from scal3.ui_gtk.customize import CustomizableCalBox, DummyCalObj
from scal3.ui_gtk.mainwin_items import mainWinItemsDesc
from scal3.ui_gtk.signals import SignalHandlerBase, registerSignals
from scal3.ui_gtk.starcal_funcs import prefUpdateBgColor

if TYPE_CHECKING:
	from scal3.ui_gtk import gdk
	from scal3.ui_gtk.pytypes import CalObjType
	from scal3.ui_gtk.starcal_types import MainWinType, OptWidget

__all__ = ["MainWinVbox", "SignalHandler"]


class MainWinVbox(CustomizableCalBox):
	vertical = True
	objName = "mainPanel"
	desc = _("Main Panel")
	itemListCustomizable = True
	myKeys: set[str] = {
		"down",
		"end",
		"f10",
		"home",
		"i",
		"j",
		"k",
		"left",
		"m",
		"menu",
		"n",
		"p",
		"page_down",
		"page_up",
		"right",
		"space",
		"t",
		"up",
	}

	def __init__(self, win: MainWinType) -> None:
		CustomizableCalBox.__init__(self, vertical=True)
		self.parentWin = win
		self.initVars()

	def connectItem(self, item: CalObjType) -> None:
		super().connectItem(item)
		win = self.parentWin
		signalNames = {sigTup[0] for sigTup in item.s.signals}
		if "popup-cell-menu" in signalNames:
			item.s.connect("popup-cell-menu", win.menuCellPopup, item)
		if "popup-main-menu" in signalNames:
			item.s.connect("popup-main-menu", win.menuMainPopup, item)
		if "pref-update-bg-color" in signalNames:
			item.s.connect("pref-update-bg-color", prefUpdateBgColor)
		if "day-info" in signalNames:
			item.s.connect("day-info", win.dayInfoShow)

	def createItems(self) -> None:
		win = self.parentWin
		itemsPkg = "scal3.ui_gtk.mainwin_items"

		for name, enable in conf.mainWinItems.v:
			if name in {"winContronller", "statusBar"}:
				log.warning(f"Skipping main win item {name!r}")
				continue
			# log.debug(name, enable)
			if not enable:
				self.appendItem(
					DummyCalObj(name, mainWinItemsDesc[name], itemsPkg, True),  # type: ignore[arg-type]
				)
				continue

			try:
				module = __import__(
					f"{itemsPkg}.{name}",
					fromlist=["CalObj"],
				)
				CalObj = module.CalObj
			except RuntimeError:
				raise
			except Exception as e:
				log.error(f"error importing mainWinItem {name}")
				log.exception("")
				if os.getenv("STARCAL_DEV") == "1":
					raise e from None
				continue
			# try:
			item = CalObj(win)
			# except Exception as e:
			# 	log.error(f"creating {CalObj} instance at {module}: {e}")
			# 	raise
			item.enable = enable
			self.appendItem(item)

	def updateVars(self) -> None:
		CustomizableCalBox.updateVars(self)
		conf.mainWinItems.v = self.getItemsData()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		CustomizableCalBox.onKeyPress(self, arg, gevent)
		return True  # FIXME

	# def switchWcalMcal(self, customizeWindow: CustomizeWindow) -> None:
	# 	wi = None
	# 	mi = None
	# 	wcalEnabled = True
	# 	for i, item in enumerate(self.items):
	# 		if item.objName == "weekCal":
	# 			wi = i
	# 			wcalEnabled = item.enable
	# 		elif item.objName == "monthCal":
	# 			mi = i
	# 			wcalEnabled = False
	# 	if wi is None or mi is None:
	# 		log.error(f"weekCal index: {wi}, monthCal index: {mi}")
	# 		return

	# 	customizeWindow.loadItem(self, wi, enable=not wcalEnabled)
	# 	customizeWindow.loadItem(self, mi, enable=wcalEnabled)

	# 	# FIXME
	# 	# self.reorder_child(wcal, mi)
	# 	# self.reorder_child(mcal, wi)
	# 	# self.items[wi], self.items[mi] = mcal, wcal
	# 	self.showHide()
	# 	self.broadcastDateChange()

	def getOptionsWidget(self) -> OptWidget:
		if self.optionsWidget is not None:
			return self.optionsWidget
		self.optionsWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL, spacing=self.optionsPageSpacing
		)
		return self.optionsWidget


@registerSignals
class SignalHandler(SignalHandlerBase):
	signals = commonSignals + [
		("toggle-right-panel", []),
	]
