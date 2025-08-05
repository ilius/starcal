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

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.option_ui.spin import IntSpinOptionUI

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import Option
	from scal3.ui_gtk.option_ui.base import OptionUI

	from .pytypes import ColumnParent

__all__ = ["ColumnBase", "ColumnDrawingArea"]


class ColumnBase(CustomizableCalObj):
	itemListCustomizable = False
	autoButtonPressHandler = True
	widthOption: Option[int] | None = None
	expandOption: Option[bool] | None = None
	fontOption: Option[str | None] | None = None

	def __init__(self) -> None:
		super().__init__()
		self.colParent: ColumnParent | None = None
		self.calType = 0

	def getFontFamily(self) -> str:
		option = self.fontOption
		if option and option.v:
			return option.v
		return ""

	def onWidthChange(self) -> None:
		# if self.objName:
		# 	self.updatePacking()
		self.w.queue_resize()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI
		from scal3.ui_gtk.option_ui.font import FontFamilyOptionUI

		if self.optionsWidget:
			return self.optionsWidget

		optionsWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=self.optionsPageSpacing,
		)
		option: OptionUI
		# ----
		if self.widthOption is not None:
			widthOption = self.widthOption
			option = IntSpinOptionUI(
				option=widthOption,
				bounds=(1, 999),
				step=1,
				label=_("Width"),
				live=True,
				onChangeFunc=self.onWidthChange,
			)
			pack(optionsWidget, option.getWidget())
		# ----
		if self.expandOption is not None:
			expandOption = self.expandOption
			option = CheckOptionUI(
				option=expandOption,
				label=_("Expand"),
				live=True,
				onChangeFunc=self.onExpandCheckClick,
			)
			pack(optionsWidget, option.getWidget())
		# ----
		if self.fontOption is not None:
			fontOption = self.fontOption
			option = FontFamilyOptionUI(
				option=fontOption,
				hasAuto=True,
				label=_("Font Family"),
				onChangeFunc=self.onFontChange,
			)
			option.updateWidget()  # done inside Live*OptionUI classes
			pack(optionsWidget, option.getWidget())
			previewText = self.getFontPreviewText()
			if previewText:
				option.setPreviewText(previewText)
		# ----
		self.addExtraOptionsWidget(optionsWidget)
		# ----
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def onFontChange(self) -> None:
		self.onDateChange()

	def addExtraOptionsWidget(self, optionsWidget: gtk.Box) -> None:
		pass

	def updatePacking(self) -> None:
		if self.colParent is None:
			return
		self.colParent.set_child_packing(
			self.w,
			self.expand,
			self.expand,
			0,
			gtk.PackType.START,
		)

	def onExpandCheckClick(self) -> None:
		option = self.expandOption
		assert option is not None
		self.expand = option.v
		self.updatePacking()
		self.w.queue_draw()

	def getFontPreviewText(self) -> str:  # noqa: PLR6301
		return ""


class ColumnDrawingArea(gtk.DrawingArea):
	def __init__(self, getWidth: Callable[[], int]) -> None:
		gtk.DrawingArea.__init__(self)
		self.getWidth = getWidth

	def do_get_preferred_width(self) -> tuple[int, int]:
		# must return minimum_size, natural_size
		width = self.getWidth()
		return width, width
