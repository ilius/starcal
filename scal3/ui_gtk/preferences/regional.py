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

from contextlib import suppress

from scal3 import logger

log = logger.get()

import typing
from typing import Any

from scal3 import core, locale_man
from scal3.cal_types import calTypes
from scal3.locale_man import getLocaleFirstWeekDay
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_type_option_ui import ModuleOptionButton, ModuleOptionUI
from scal3.ui_gtk.option_ui import CheckOptionUI, ComboEntryTextOptionUI
from scal3.ui_gtk.option_ui_extra import WeekDayCheckListOptionUI
from scal3.ui_gtk.stack import StackPage

if typing.TYPE_CHECKING:
	from scal3.ui_gtk.option_ui import OptionUI

__all__ = ["PreferencesRegionalTab"]


class PreferencesRegionalTab:
	def __init__(self, spacing: int) -> None:
		self.optionUIs: list[OptionUI] = []
		##
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		self.vbox = vbox
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "regional"
		page.pageTitle = _("Regional")
		page.pageLabel = _("_Regional")
		page.pageIcon = "preferences-desktop-locale.png"
		self.prefPages = [page]
		# ------
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		item: OptionUI
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		label = gtk.Label(label=_("Date Format"))
		pack(hbox, label)
		sgroup.add_widget(label)
		# pack(hbox, gtk.Label(), 1, 1)
		item = ComboEntryTextOptionUI(
			option=ud.dateFormat,
			items=[
				"%Y/%m/%d",
				"%Y-%m-%d",
				"%y/%m/%d",
				"%y-%m-%d",
				"%OY/%Om/%Od",
				"%OY-%Om-%Od",
				"%m/%d",
				"%m/%d/%Y",
			],
		)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# --------------------------------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL,
			spacing=int(spacing / 3),
		)
		item = CheckOptionUI(
			option=locale_man.enableNumLocale,
			label=_("Numbers Localization"),
		)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox, padding=spacing)
		# --------------------------------
		pageVBox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=int(spacing / 2),
		)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=int(spacing / 3))
		pack(hbox, gtk.Label(label=_("First day of week")))
		# item = ComboTextOptionUI(  # FIXME
		self.comboFirstWD = gtk.ComboBoxText()
		for wdName in core.weekDayName:
			self.comboFirstWD.append_text(wdName)
		self.comboFirstWD.append_text(_("Automatic"))
		self.comboFirstWD.connect("changed", self.comboFirstWDChanged)
		pack(hbox, self.comboFirstWD)
		pack(pageVBox, hbox)
		# ---------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=int(spacing / 3))
		pack(hbox, gtk.Label(label=_("First week of year containts")))
		combo = gtk.ComboBoxText()
		texts = [
			_("First {weekDay} of year").format(weekDay=name)
			for name in core.weekDayName
		] + [
			_("First day of year"),
		]
		texts[4] += " (ISO 8601)"  # FIXME
		for text in texts:
			combo.append_text(text)
		# combo.append_text(_("Automatic"))-- (as Locale)  # FIXME
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox, padding=5)
		self.comboWeekYear = combo
		# ---------
		frame = gtk.Frame()
		frame.set_border_width(10)
		frame.set_label(_("Holidays"))
		item = WeekDayCheckListOptionUI(
			option=core.holidayWeekDays,
			abbreviateNames=False,
			twoRows=True,
		)
		self.optionUIs.append(item)
		self.holiWDItem = item  # Holiday Week Days Item
		itemWidget = item.getWidget()
		assert isinstance(itemWidget, gtk.Container), f"{itemWidget=}"
		itemWidget.set_border_width(10)
		frame.add(itemWidget)
		pack(pageVBox, frame)
		# ------------
		page = StackPage()
		page.pageParent = "regional"
		page.pageWidget = pageVBox
		page.pageName = "regional_week"
		page.pageTitle = _("Week") + " - " + _("Regional")
		page.pageLabel = _("Week-related Settings")
		page.pageIcon = ""
		page.pageExpand = False
		self.prefPages.append(page)
		# -----
		self.subPages = [page]
		# --------------------------------------------------
		options = []
		for mod in calTypes:
			if not mod.options:
				continue
			pageVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=spacing)
			pageVBox.set_border_width(spacing)
			page = StackPage()
			page.pageParent = "regional"
			page.pageWidget = pageVBox
			page.pageName = "regional_" + mod.name
			page.pageTitle = (
				_("{calType} Calendar").format(calType=_(mod.desc, ctx="calendar"))
				+ " - "
				+ _("Regional")
			)
			page.pageLabel = _("{calType} Calendar").format(
				calType=_(mod.desc, ctx="calendar"),
			)
			page.pageExpand = False
			self.prefPages.append(page)
			# -----
			self.subPages.append(page)
			optionUI: Any
			for rawOpt in mod.options:
				if rawOpt[0] == "button":
					try:
						optionUI = ModuleOptionButton(rawOpt[1:])
					except Exception:
						log.exception("")
						continue
				else:
					option = getattr(mod, rawOpt[0])
					optionUI = ModuleOptionUI(
						option=option,
						rawOption=rawOpt,
						spacing=spacing,
					)
				options.append(optionUI)
				pack(pageVBox, optionUI.getWidget())
			# -----
		# ---
		self.moduleOptionUIs = options

	def apply(self) -> None:
		first = self.comboFirstWD.get_active()
		if first == 7:
			core.firstWeekDayAuto.v = True
			with suppress(Exception):
				core.firstWeekDay.v = getLocaleFirstWeekDay()
		else:
			core.firstWeekDayAuto.v = False
			core.firstWeekDay.v = first

		weekNumberMode = self.comboWeekYear.get_active()
		# if weekNumberMode == 7:
		# core.weekNumberModeAuto = True
		# core.weekNumberMode = getLocaleWeekNumberMode()
		# else:
		core.weekNumberModeAuto.v = False
		core.weekNumberMode.v = weekNumberMode

	def updatePrefGui(self) -> None:
		if core.firstWeekDayAuto.v:
			self.comboFirstWD.set_active(7)
		else:
			self.comboFirstWD.set_active(core.firstWeekDay.v)
		if core.weekNumberModeAuto.v:
			self.comboWeekYear.set_active(8)
		else:
			self.comboWeekYear.set_active(core.weekNumberMode.v)

	def comboFirstWDChanged(self, _combo: gtk.Widget) -> None:
		f = self.comboFirstWD.get_active()  # 0 means Sunday
		if f == 7:  # auto
			with suppress(Exception):
				f = getLocaleFirstWeekDay()
		# core.firstWeekDay.v will be later = f
		self.holiWDItem.setStart(f)
