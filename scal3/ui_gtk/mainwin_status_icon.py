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
from os.path import join
from time import localtime
from typing import TYPE_CHECKING

from scal3 import logger

log = logger.get()

from scal3 import core, locale_man, ui
from scal3.cal_types import calTypes, convert
from scal3.color_utils import rgbToHtmlColor
from scal3.locale_man import tr as _
from scal3.path import pixDir
from scal3.ui import conf
from scal3.ui_gtk import GdkPixbuf, Menu, gtk
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.starcal_funcs import (
	copyCurrentDate,
	copyCurrentDateTime,
	getStatusIconTooltip,
	yearWheelShow,
)
from scal3.ui_gtk.status_icon_backend import create_status_icon

if TYPE_CHECKING:
	from typing import Any

	from scal3.ui_gtk.mainwin import MainWin
	from scal3.ui_gtk.starcal_types import OptWidget

__all__ = ["MainWinStatusIcon"]


class MainWinStatusIcon:
	"""Status-icon / tray icon handling for MainWin."""

	win: gtk.ApplicationWindow
	w: gtk.Widget
	statusIconMode: int
	sicon: Any | None
	xfceApplet: Any | None
	statusIconPopupMenu: gtk.Menu | None

	def __init__(
		self,
		mainWin: MainWin,
		win: gtk.ApplicationWindow,
		w: gtk.Widget,
		statusIconMode: int,
	) -> None:
		self.mainWin = mainWin
		self.win = win
		self.w = w
		self.statusIconMode = statusIconMode
		self.statusIconPopupMenu = None
		self.sicon = create_status_icon(mainWin, statusIconMode)
		if statusIconMode == 3:
			self.xfceApplet = self.sicon
		elif statusIconMode == 2:
			# serve the xfce applet next to the tray/status icon
			from scal3.ui_gtk.starcal_xfce_applet import XfceAppletStatusIcon

			self.xfceApplet = XfceAppletStatusIcon(mainWin)
		else:
			self.xfceApplet = None

	def getMainWinMenuItem(self) -> gtk.MenuItem:
		item = gtk.MenuItem(label=_("Main Window"))
		item.connect("activate", self.mainWin.onStatusIconClick)
		return item

	def popupItems(self) -> list[gtk.MenuItem]:
		mainWin = self.mainWin
		return [
			ImageMenuItem(
				label=_("Copy Date and _Time"),
				imageName="edit-copy.svg",
				onActivate=copyCurrentDateTime,
			),
			ImageMenuItem(
				label=_("Copy _Date"),
				imageName="edit-copy.svg",
				onActivate=copyCurrentDate,
			),
			ImageMenuItem(
				label=_("Ad_just System Time"),
				imageName="preferences-system.svg",
				onActivate=mainWin.adjustTime,
			),
			# ImageMenuItem(
			# 	label=_("_Add Event"),
			# 	imageName="list-add.svg",
			# 	onActivate=ui.addCustomEvent,
			# ),  # FIXME
			ImageMenuItem(
				label=_("Export to {format}").format(format="HTML"),
				imageName="export-to-html.svg",
				onActivate=mainWin.onExportClickStatusIcon,
			),
			ImageMenuItem(
				label=_("_Preferences"),
				imageName="preferences-system.svg",
				onActivate=mainWin.prefShow,
			),
			ImageMenuItem(
				label=_("_Event Manager"),
				imageName="list-add.svg",
				onActivate=mainWin.eventManShow,
			),
			ImageMenuItem(
				label=_("Time Line"),
				imageName="timeline.svg",
				onActivate=mainWin.timeLineShow,
			),
			ImageMenuItem(
				label=_("Year Wheel"),
				imageName="year-wheel.svg",
				onActivate=yearWheelShow,
			),
			ImageMenuItem(
				label=_("_About"),
				imageName="dialog-information.svg",
				onActivate=mainWin.aboutShow,
			),
			gtk.SeparatorMenuItem(),
			ImageMenuItem(
				label=_("_Quit"),
				imageName="application-exit.svg",
				onActivate=mainWin.onQuitClick,
			),
		]

	def popup(self, sicon: gtk.StatusIcon, button: int, etime: int) -> None:
		assert isinstance(self.sicon, gtk.StatusIcon), f"{self.sicon=}"
		menu = Menu()
		if os.sep == "\\":
			from scal3.ui_gtk.windows import setupMenuHideOnLeave

			setupMenuHideOnLeave(menu)
		items = self.popupItems()
		# items.insert(0, self.getMainWinMenuItem())-- FIXME
		get_pos_func = None
		y1 = 0
		geo = sicon.get_geometry()
		# Previously geo was None on windows
		# and on Linux it had `geo.index(1)` (not sure about the type)
		# Now it's tuple on both Linux and windows
		if geo is None:
			items.reverse()
		elif isinstance(geo, tuple):
			# geo == (True, screen, area, orientation)
			y1 = geo[2].y
		else:
			y1 = geo.index(1)
		try:  # new gi versions
			y = gtk.StatusIcon.position_menu(menu, 0, 0, self.sicon)[1]  # type: ignore[call-arg, arg-type]
		except TypeError:  # old gi versions
			y = gtk.StatusIcon.position_menu(menu, self.sicon)[1]
		if y1 > 0 and y < y1:  # taskbar is on bottom
			items.reverse()
		get_pos_func = gtk.StatusIcon.position_menu
		for item in items:
			menu.add(item)
		menu.show_all()
		# log.debug("statusIconPopup", button, etime)
		self._keepMenu(menu)
		menu.popup(None, None, get_pos_func, self.sicon, button, etime)
		# self.sicon.do_popup_menu(self.sicon, button, etime)
		ui.updateFocusTime()

	def _keepMenu(self, menu: gtk.Menu) -> None:
		# keep a reference so the menu is not garbage-collected while shown
		self.statusIconPopupMenu = menu
		menu.connect("deactivate", self._onMenuDeactivate)

	def _onMenuDeactivate(self, menu: gtk.Menu) -> None:
		if getattr(self, "statusIconPopupMenu", None) is menu:
			self.statusIconPopupMenu = None

	def popupAtPointer(self, button: int = 3) -> None:
		menu = Menu()
		if os.sep == "\\":
			from scal3.ui_gtk.windows import setupMenuHideOnLeave

			setupMenuHideOnLeave(menu)
		for item in self.popupItems():
			menu.add(item)
		menu.show_all()
		self._keepMenu(menu)
		menu.popup(
			None,
			None,
			None,
			None,
			button,
			gtk.get_current_event_time(),
		)
		ui.updateFocusTime()

	def updateIcon(self, ddate: tuple[int, int, int]) -> None:  # FIXME
		from scal3.utils import toBytes

		assert self.sicon is not None

		imagePath = (
			conf.statusIconImageHoli.v
			if ui.cells.today.holiday
			else conf.statusIconImage.v
		)
		ext = os.path.splitext(imagePath)[1].lstrip(".").lower()
		with open(imagePath, "rb") as fp:
			data = fp.read()
		if ext == "svg":
			if conf.statusIconLocalizeNumber.v:
				dayNum = locale_man.numEncode(
					ddate[2],
					localeMode="calendar",
				)
			else:
				dayNum = str(ddate[2])
			style: list[tuple[str, Any]] = []
			if conf.statusIconFontFamilyEnable.v:
				family = conf.statusIconFontFamily.v or ui.getFont().family
				style.append(("font-family", family))
			if (
				conf.statusIconHolidayFontColorEnable.v
				and conf.statusIconHolidayFontColor.v
				and ui.cells.today.holiday
			):
				style.append(
					("fill", rgbToHtmlColor(conf.statusIconHolidayFontColor.v)),
				)
			if style:
				styleStr = "".join([f"{key}:{value};" for key, value in style])
				dayNum = f'<tspan style="{styleStr}">{dayNum}</tspan>'
			data = data.replace(
				b"TX",
				toBytes(dayNum),
			)
		loader = GdkPixbuf.PixbufLoader.new_with_type(ext)
		if conf.statusIconFixedSizeEnable.v:
			try:
				width, height = conf.statusIconFixedSizeWH.v
				loader.set_size(width, height)
			except Exception:
				log.exception("")
		try:
			loader.write(data)
		finally:
			loader.close()
		pixbuf = loader.get_pixbuf()
		assert pixbuf is not None

		# alternative way:
		# stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
		# pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)

		self.sicon.set_from_pixbuf(pixbuf)
		if self.xfceApplet is not None and self.xfceApplet is not self.sicon:
			self.xfceApplet.set_from_pixbuf(pixbuf)

	def updateTooltip(self) -> None:
		try:
			sicon = self.sicon
		except AttributeError:
			return
		tooltip = getStatusIconTooltip()
		if sicon is not None:
			sicon.set_tooltip_text(tooltip)
		try:
			xfceApplet = self.xfceApplet
		except AttributeError:
			return
		if xfceApplet is not None and xfceApplet is not sicon:
			xfceApplet.set_tooltip_text(tooltip)

	def update(
		self,
		gdate: tuple[int, int, int] | None = None,
		checkStatusIconMode: bool = True,
	) -> None:
		if self.sicon is None:
			return
		if checkStatusIconMode and self.statusIconMode < 1:
			return
		if gdate is None:
			gdate = localtime()[:3]
		if calTypes.primary == core.GREGORIAN:
			ddate = gdate
		else:
			ddate = convert(
				gdate[0],
				gdate[1],
				gdate[2],
				core.GREGORIAN,
				calTypes.primary,
			)
		# -------
		placeholder = join(pixDir, "starcal-24.png")
		if self.sicon is not None:
			self.sicon.set_from_file(placeholder)
		if self.xfceApplet is not None and self.xfceApplet is not self.sicon:
			self.xfceApplet.set_from_file(placeholder)
		self.updateIcon(ddate)
		# -------
		self.updateTooltip()

	def onClick(self, _w: OptWidget = None) -> None:
		if self.w.get_property("visible"):
			# conf.winX.v, conf.winY.v = self.w.get_position()
			# FIXME: ^ gives bad position sometimes
			# liveConfChanged()
			# log.debug(conf.winX.v, conf.winY.v)
			self.mainWin.hide()
		else:
			self.win.move(conf.winX.v, conf.winY.v)
			# every calling of .hide() and .present(), makes dialog not on top
			# (forgets being on top)
			self.win.set_keep_above(conf.winKeepAbove.v)
			if conf.winSticky.v:
				self.win.stick()
			self.win.deiconify()
			self.win.present()
			self.mainWin.focusIn()
			# in LXDE, the window was not focused without self.focusIn()
			# while worked in Xfce and GNOME.

	"""
	def updateToolbarClock(self):
		if conf.showDigClockTb.v:
			if self.clock is None:
				from scal3.ui_gtk.mywidgets.clock import FClockLabel
				self.clock = FClockLabel(ud.clockFormat)
				pack(self.toolbBox, self.clock)
				self.clock.show()
			else:
				self.clock.format = ud.clockFormat
		else:
			if self.clock is not None:
				self.clock.destroy()
				self.clock = None

	def updateStatusIconClock(self, checkStatusIconMode=True):
		if checkStatusIconMode and self.statusIconMode!=2:
			return
		if conf.showDigClockTr.v:
			if self.clockTr is None:
				from scal3.ui_gtk.mywidgets.clock import FClockLabel
				self.clockTr = FClockLabel(ud.clockFormat)
				try:
					pack(self.statusIconHbox, self.clockTr)
				except AttributeError:
					self.clockTr.destroy()
					self.clockTr = None
				else:
					self.clockTr.show()
			else:
				self.clockTr.format = ud.clockFormat
		else:
			if self.clockTr is not None:
				self.clockTr.destroy()
				self.clockTr = None
	"""
