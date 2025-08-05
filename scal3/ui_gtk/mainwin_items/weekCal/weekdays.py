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

from scal3 import core
from scal3.locale_man import tr as _
from scal3.ui import conf

from .column import Column

if TYPE_CHECKING:
	from scal3.ui_gtk.drawing import ImageContext

__all__ = ["WeekDaysColumn"]


class WeekDaysColumn(Column):
	objName = "weekDays"
	desc = _("Week Days")
	widthOption = conf.wcal_weekDays_width
	expandOption = conf.wcal_weekDays_expand
	fontOption = conf.wcalFont_weekDays
	colorizeHolidayText = True
	showCursor = True
	optionsPageSpacing = 20

	def drawColumn(self, cr: ImageContext) -> None:
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[
				[
					(core.getWeekDayN(i), None),
				]
				for i in range(7)
			],
		)
		self.drawCursorFg(cr)

	def getFontPreviewText(self) -> str:  # noqa: PLR6301
		return _(", ").join([_(core.getWeekDayN(i)) for i in range(7)])
