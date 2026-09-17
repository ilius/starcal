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

from typing import TYPE_CHECKING

from scal3 import core
from scal3.cal_types import calTypes
from scal3.locale_man import langHasUppercase, langSh
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.cal_type_options import (
	MonthNameListOptionsWidget,
	WeekDayNameOptionsWidget,
)
from scal3.ui_gtk.customize import newSubPageButton
from scal3.ui_gtk.option_ui.spin import FloatSpinOptionUI, IntSpinOptionUI
from scal3.ui_gtk.stack import StackPage

if TYPE_CHECKING:
	from scal3.ui_gtk.day_cal.cal import DayCal
	from scal3.ui_gtk.option_ui.base import OptionUI
	from scal3.ui_gtk.pytypes import StackPageType

__all__ = ["DayCalOptions"]


class DayCalOptions:
	"""Options widget building for DayCal."""

	def __init__(self, dayCal: DayCal) -> None:
		self.dayCal = dayCal
		self.optionsWidget: gtk.Widget | None = None
		self.subPages: list[StackPageType] | None = None
		self.buttons1: list[gtk.Button] = []
		self.dayMonthOptionsVbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)

	def updateTypeOptionsWidget(self) -> list[StackPageType]:
		from scal3.ui_gtk.cal_type_options import DayNumListOptionsWidget

		dayCal = self.dayCal
		monthOptions = dayCal.getMonthOptions(allCalTypes=True)
		vbox = self.dayMonthOptionsVbox
		for child in vbox.get_children():
			child.destroy()
		# ---
		subPages: list[StackPageType] = []
		# ---
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		assert dayCal.dayOptions
		assert dayCal.monthOptions
		for index, calType in enumerate(calTypes.active):
			module = calTypes[calType]
			if module is None:
				raise RuntimeError(f"cal type '{calType}' not found")
			calTypeDesc = _("{calType} Calendar").format(
				calType=_(module.desc, ctx="calendar"),
			)
			# --
			pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
			# ---
			dayWidget = DayNumListOptionsWidget(
				options=dayCal.dayOptions,
				index=index,
				calType=calType,
				cal=dayCal,
				sgroupLabel=sgroupLabel,
				hasEnable=True,
				enableTitleLabel=_("Day of Month"),
				useFrame=True,
			)
			pack(pageWidget, dayWidget)
			# ---
			monthWidget = MonthNameListOptionsWidget(
				options=dayCal.monthOptions,
				index=index,
				calType=calType,
				cal=dayCal,
				sgroupLabel=sgroupLabel,
				hasEnable=True,
				enableTitleLabel=_("Month Name"),
				useFrame=True,
			)
			monthWidget.show_all()
			page = StackPage()
			page.pageWidget = monthWidget
			page.pageName = module.name + "." + "month"
			page.pageParent = module.name
			page.pageTitle = _("Month Name") + " - " + calTypeDesc
			page.pageLabel = _("Month Name")
			page.pageExpand = False
			subPages.append(page)
			pack(pageWidget, newSubPageButton(dayCal.s, page), padding=4)
			# ---
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = module.name
			page.pageTitle = calTypeDesc
			page.pageLabel = calTypeDesc
			page.pageExpand = False
			subPages.append(page)
			self.buttons1.append(newSubPageButton(dayCal.s, page))
			# ---
			c = dayCal.getCell()
			dayWidget.setFontPreviewText(
				_(c.dates[calType][2], calType=calTypes.primary),
			)
			monthWidget.setFontPreviewText(
				dayCal.getMonthName(c, calType, monthOptions[index]),
			)
		# ---
		vbox.show_all()
		return subPages

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI
		from scal3.ui_gtk.option_ui.color import ColorOptionUI

		dayCal = self.dayCal
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		subPages = []
		option: OptionUI
		# ---
		buttons1: list[gtk.Button] = []
		buttons2: list[gtk.Button] = []
		self.buttons1 = buttons1
		# ----
		if dayCal.backgroundColor:
			option = ColorOptionUI(
				option=dayCal.backgroundColor,
				live=True,
				onChangeFunc=dayCal.getWidget().queue_draw,
			)
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
			pack(hbox, gtk.Label(label=_("Background") + ": "))
			pack(hbox, option.getWidget())
			pack(hbox, gtk.Label(), 1, 1)
			pack(optionsWidget, hbox)
		# --------
		pack(optionsWidget, self.dayMonthOptionsVbox)
		subPages += self.updateTypeOptionsWidget()
		# ----
		pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
		page = StackPage()
		page.pageWidget = pageWidget
		page.pageName = "buttons"
		page.pageTitle = _("Buttons")
		page.pageLabel = _("Buttons")
		page.pageExpand = False
		subPages.append(page)
		buttons2.append(newSubPageButton(dayCal.s, page))
		# ---
		if dayCal.widgetButtonsEnable:
			option = CheckOptionUI(
				option=dayCal.widgetButtonsEnable,
				label=_("Widget Buttons"),
				live=True,
				onChangeFunc=dayCal.getWidget().queue_draw,
			)
			pack(pageWidget, option.getWidget())
		if dayCal.widgetButtonsSize:
			option = IntSpinOptionUI(
				option=dayCal.widgetButtonsSize,
				bounds=(0, 99),
				step=1,
				label=_("Widget Buttons Size"),
				live=True,
				onChangeFunc=dayCal.getWidget().queue_draw,
			)
			pack(pageWidget, option.getWidget())
		if dayCal.widgetButtonsOpacity:
			option = FloatSpinOptionUI(
				option=dayCal.widgetButtonsOpacity,
				bounds=(0, 1),
				digits=2,
				step=0.1,
				label=_("Widget Buttons Opacity"),
				live=True,
				onChangeFunc=dayCal.getWidget().queue_draw,
			)
			pack(pageWidget, option.getWidget())
		if dayCal.navButtonsEnable:
			option = CheckOptionUI(
				option=dayCal.navButtonsEnable,
				label=_("Navigation buttons"),
				live=True,
				onChangeFunc=dayCal.getWidget().queue_draw,
			)
			pack(pageWidget, option.getWidget())
		pageWidget.show_all()
		# -----
		if dayCal.weekdayOptions:
			pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
			# ---
			weekdayWidget = WeekDayNameOptionsWidget(
				options=dayCal.weekdayOptions,
				cal=dayCal,
				# sgroupLabel=None,
				desc=_("Week Day"),
				hasEnable=True,
			)
			pack(pageWidget, weekdayWidget)
			# ---
			if dayCal.weekdayLocalize and langSh != "en":
				option = CheckOptionUI(
					option=dayCal.weekdayLocalize,
					label=_("Localize"),
					live=True,
					onChangeFunc=dayCal.getWidget().queue_draw,
				)
				pack(pageWidget, option.getWidget())
			if dayCal.weekdayAbbreviate:
				option = CheckOptionUI(
					option=dayCal.weekdayAbbreviate,
					label=_("Abbreviate"),
					live=True,
					onChangeFunc=dayCal.getWidget().queue_draw,
				)
				pack(pageWidget, option.getWidget())
			if langHasUppercase and dayCal.weekdayUppercase:
				option = CheckOptionUI(
					option=dayCal.weekdayUppercase,
					label=_("Uppercase"),
					live=True,
					onChangeFunc=dayCal.getWidget().queue_draw,
				)
				pack(pageWidget, option.getWidget())
			# ---
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = "weekday"
			page.pageTitle = _("Week Day")
			page.pageLabel = _("Week Day")
			page.pageExpand = False
			subPages.append(page)
			buttons2.append(newSubPageButton(dayCal.s, page))
			# ---
			c = dayCal.getCell()
			text = core.getWeekDayAuto(
				c.weekDay,
				localize=dayCal.getWeekdayLocalize(),
				abbreviate=dayCal.getWeekdayAbbreviate(),
				relative=False,
			)
			weekdayWidget.setFontPreviewText(text)
		# --------
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "events"
		page.pageTitle = _("Events")
		page.pageLabel = _("Events")
		page.pageExpand = False
		subPages.append(page)
		buttons2.append(newSubPageButton(dayCal.s, page))
		# ---
		if dayCal.eventIconSize:
			option = IntSpinOptionUI(
				option=dayCal.eventIconSize,
				bounds=(5, 999),
				step=1,
				label=_("Icon Size"),
				live=True,
				onChangeFunc=dayCal.getWidget().queue_draw,
			)
			pack(vbox, option.getWidget())
		# ---
		if dayCal.eventTotalSizeRatio:
			option = FloatSpinOptionUI(
				option=dayCal.eventTotalSizeRatio,
				bounds=(0, 1),
				digits=3,
				step=0.01,
				label=_("Total Size Ratio"),
				live=True,
				onChangeFunc=dayCal.getWidget().queue_draw,
			)
			pack(vbox, option.getWidget())
		# ----
		if dayCal.seasonPieEnable:
			pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = "seasonPie"
			page.pageTitle = _("Season Pie")
			page.pageLabel = _("Season Pie")
			page.pageExpand = False
			subPages.append(page)
			buttons2.append(newSubPageButton(dayCal.s, page))
			# ---
			option = CheckOptionUI(
				option=dayCal.seasonPieEnable,
				label=_("Season Pie"),
				live=True,
				onChangeFunc=dayCal.getWidget().queue_draw,
			)
			pack(pageWidget, option.getWidget())
			# ---
			frame = gtk.Frame()
			frame.set_border_width(5)
			frame.set_label(_("Colors"))
			grid = gtk.Grid()
			grid.set_row_spacing(5)
			grid.set_column_spacing(5)
			grid.set_row_spacing(3)
			grid.set_border_width(5)
			frame.add(grid)
			pack(pageWidget, frame)
			assert dayCal.seasonPieColors is not None
			for index, season in enumerate(("Spring", "Summer", "Autumn", "Winter")):
				hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
				label = gtk.Label(label=_(season))
				label.set_xalign(0)
				option = ColorOptionUI(
					option=dayCal.seasonPieColors[season],
					useAlpha=True,
					live=True,
					onChangeFunc=dayCal.getWidget().queue_draw,
				)
				row_index = int(index / 2)
				column_index = index % 2 * 3
				grid.attach(
					label,
					column_index,
					row_index,
					1,
					1,
				)
				grid.attach(
					option.getWidget(),
					column_index + 1,
					row_index,
					1,
					1,
				)
				dummyLabel = gtk.Label()
				dummyLabel.set_hexpand(True)
				grid.attach(
					dummyLabel,
					column_index + 2,
					row_index,
					1,
					1,
				)
			pageWidget.show_all()
		# ----
		for buttons in (buttons1, buttons2):
			grid = gtk.Grid()
			grid.set_row_homogeneous(True)
			grid.set_column_homogeneous(True)
			grid.set_row_spacing(5)
			grid.set_column_spacing(5)
			for index, button in enumerate(buttons):
				grid.attach(
					button,
					index % 2,
					index // 2,
					1,
					1,
				)
			grid.show_all()
			pack(optionsWidget, grid, padding=5)
		# ---
		vbox.show_all()
		# --------
		self.subPages = subPages
		self.optionsWidget = optionsWidget
		# ---
		optionsWidget.show_all()
		return optionsWidget

	def getSubPages(self) -> list[StackPageType]:
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		assert self.subPages is not None
		return self.subPages
