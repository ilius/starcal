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

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.cal_types import calTypes
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui.font import getOptionsFont
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalBox
from scal3.ui_gtk.mywidgets import MyFontButton

from .base import ColumnBase
from .column import Column

if TYPE_CHECKING:
	from scal3.ui.pytypes import WeekCalDayNumOptionsDict
	from scal3.ui_gtk import gdk
	from scal3.ui_gtk.drawing import ImageContext

	from .pytypes import ColumnParent, WeekCalType

__all__ = ["DaysOfMonthColumnGroup"]


class DaysOfMonthFontButton(MyFontButton):
	styleClass = "daysOfMonthFontButton"

	def __init__(self) -> None:
		MyFontButton.__init__(self, dragAndDrop=True)
		self.get_style_context().add_class(self.styleClass)

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		# make the font of Button smaller by a factor of 0.5
		font = ui.getFont(scale=0.5)
		return (
			"."
			+ DaysOfMonthFontButton.styleClass
			+ " "
			+ cssTextStyle(
				font=font,
			)
		)


class DaysOfMonthCalTypeParamBox(gtk.Box):
	def __init__(
		self,
		wcal: WeekCalType,
		index: int,
		calType: int,
		options: WeekCalDayNumOptionsDict,
		sgroupLabel: gtk.SizeGroup,
		sgroupFont: gtk.SizeGroup,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.wcal = wcal
		self.colParent = wcal
		self.index = index
		self.calType = calType
		# ------
		module = calTypes[calType]
		if module is None:
			raise RuntimeError(f"cal type '{calType}' not found")
		label = gtk.Label(label=_(module.desc, ctx="calendar") + "  ")
		label.set_xalign(0)
		pack(self, label)
		sgroupLabel.add_widget(label)
		# ---
		label = gtk.Label(label=f'<span font-size="small">{_("Font")}</span>')
		label.set_use_markup(True)
		self.fontCheck = gtk.CheckButton()
		self.fontCheck.add(label)
		pack(self, gtk.Label(), 1, 1)
		pack(self, self.fontCheck)
		# ---
		self.fontb = DaysOfMonthFontButton()
		pack(self, self.fontb)
		sgroupFont.add_widget(self.fontb)
		# ----
		self.set(options)
		# ----
		self.fontCheck.connect("clicked", self.onChange)
		self.fontb.connect("font-set", self.onChange)

	def get(self) -> WeekCalDayNumOptionsDict:
		return {
			"font": (self.fontb.getFont() if self.fontCheck.get_active() else None),
		}

	def set(self, data: WeekCalDayNumOptionsDict) -> None:
		font = getOptionsFont(data)
		self.fontCheck.set_active(bool(font))
		if not font:
			font = ui.getFont()
		self.fontb.setFont(font)

	def onChange(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		conf.wcalTypeParams.v[self.index] = self.get()
		self.wcal.w.queue_draw()


class DaysOfMonthColumn(Column):
	colorizeHolidayText = True
	showCursor = True
	widthOption = conf.wcal_daysOfMonth_width
	expandOption = conf.wcal_daysOfMonth_expand

	def __init__(
		self,
		wcal: WeekCalType,
		cgroup: DaysOfMonthColumnGroup,
		calType: int,
		index: int,
	) -> None:
		Column.__init__(self, wcal)
		self.cgroup = cgroup
		self.calType = calType
		self.index = index

	def drawColumn(self, cr: ImageContext) -> None:
		status = self.wcal.status
		assert status is not None
		self.drawBg(cr)
		font = getOptionsFont(conf.wcalTypeParams.v[self.index])
		self.drawTextList(
			cr,
			[
				[
					(
						_(status[i].dates[self.calType][2], calType=self.calType),
						None,
					),
				]
				for i in range(7)
			],
			font=font,
		)
		self.drawCursorFg(cr)


# FIXME: multi-inheritance!
class DaysOfMonthColumnGroup(CustomizableCalBox, ColumnBase):
	objName = "daysOfMonth"
	desc = _("Days of Month")
	optionsPageSpacing = 15

	def __init__(self, wcal: WeekCalType) -> None:
		CustomizableCalBox.__init__(self, vertical=False)
		ColumnBase.__init__(self)
		self.initVars()
		self.wcal = wcal
		self.colParent: ColumnParent = wcal.box
		self.updateCols()
		self.updateDirection()
		self.show()

	def updateDirection(self) -> None:
		self.w.set_direction(ud.textDirDict[conf.wcal_daysOfMonth_dir.v])
		# set_direction does not apply to existing children.
		# that's why we remove children(columns) and add them again
		box = self.box
		columns = box.get_children()
		for col in columns:
			box.remove(col)
		for col in columns:
			pack(box, col, 1, 1)

	def onWidthChange(self) -> None:
		ColumnBase.onWidthChange(self)
		for item in self.items:
			assert isinstance(item, Column), f"{item=}"
			item.onWidthChange()

	def addExtraOptionsWidget(self, optionsWidget: gtk.Box) -> None:
		from scal3.ui_gtk.option_ui.direction import DirectionOptionUI

		# ---
		option = DirectionOptionUI(
			option=conf.wcal_daysOfMonth_dir,
			onChangeFunc=self.updateDirection,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		frame = gtk.Frame()
		frame.set_label(_("Calendars"))
		self.typeOptionsVbox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=self.optionsPageSpacing // 2,
		)
		self.typeOptionsVbox.set_border_width(5)
		frame.add(self.typeOptionsVbox)
		frame.show_all()
		pack(optionsWidget, frame)
		self.updateTypeOptionsWidget()  # FIXME

	# overwrites method from ColumnBase
	def updatePacking(self) -> None:
		ColumnBase.updatePacking(self)
		for item in self.items:
			assert isinstance(item, Column), f"{item=}"
			item.expand = self.expand
			item.updatePacking()

	def getWidth(self) -> int:
		widthOption = self.widthOption
		if widthOption is None:
			raise ValueError("widthProp is None")
		count = len(self.box.get_children())
		return int(count * widthOption.v)

	def updateCols(self) -> None:
		# self.foreach(gtk.DrawingArea.destroy)
		# ^^^ Couses tray icon crash in gnome3
		# self.foreach(lambda child: self.remove(child))
		# ^^^ Couses tray icon crash in gnome3
		# --------
		columns = self.items
		n = len(columns)
		n2 = len(calTypes.active)

		if len(conf.wcalTypeParams.v) < n2:
			while len(conf.wcalTypeParams.v) < n2:
				log.info("appending to wcalTypeParams")
				conf.wcalTypeParams.v.append(
					{
						"font": None,
					},
				)

		if n > n2:
			for i in range(n2, n):
				columns[i].w.destroy()
		elif n < n2:
			for i in range(n, n2):
				col = DaysOfMonthColumn(self.wcal, self, 0, i)
				col.colParent = self.box
				pack(self.box, col.w, 1, 1)
				columns.append(col)
		for i, calType in enumerate(calTypes.active):
			col2 = columns[i]
			assert isinstance(col2, ColumnBase)
			col2.calType = calType
			col2.show()

	def updateTypeOptionsWidget(self) -> None:
		if not hasattr(self, "typeOptionsVbox"):
			return
		vbox = self.typeOptionsVbox
		for child in vbox.get_children():
			child.destroy()
		# ---
		n = len(calTypes.active)
		while len(conf.wcalTypeParams.v) < n:
			conf.wcalTypeParams.v.append(
				{
					"font": None,
				},
			)
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		sgroupFont = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		for i, calType in enumerate(calTypes.active):
			# try:
			options = conf.wcalTypeParams.v[i]
			# except IndexError:
			# --
			hbox = DaysOfMonthCalTypeParamBox(
				self.wcal,
				i,
				calType,
				options,
				sgroupLabel,
				sgroupFont,
			)
			pack(vbox, hbox)
		# ---
		vbox.show_all()

	def onConfigChange(self) -> None:
		super().onConfigChange()
		self.updateCols()
		self.updateTypeOptionsWidget()
