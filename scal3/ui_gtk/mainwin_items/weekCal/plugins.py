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
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import pack

from .column import Column

if TYPE_CHECKING:
	from scal3.color_utils import ColorType
	from scal3.ui_gtk import gtk
	from scal3.ui_gtk.drawing import ImageContext

__all__ = ["PluginsTextColumn"]


class PluginsTextColumn(Column):
	objName = "pluginsText"
	desc = _("Plugins Text")
	fontOption = conf.wcalFont_pluginsText
	expand = True
	truncateText = False
	optionsPageSpacing = 20

	def getTextListByIndex(self, i: int) -> list[tuple[str, ColorType | None]]:
		status = self.wcal.status
		assert status is not None
		return [
			(line, None)
			for line in status[i]
			.getPluginsText(
				firstLineOnly=conf.wcal_pluginsText_firstLineOnly.v,
			)
			.split("\n")
		]

	def drawColumn(self, cr: ImageContext) -> None:
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[self.getTextListByIndex(i) for i in range(7)],
		)

	def addExtraOptionsWidget(self, optionsWidget: gtk.Box) -> None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI

		# -----
		option = CheckOptionUI(
			option=conf.wcal_pluginsText_firstLineOnly,
			label=_("Only first line of text"),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(optionsWidget, option.getWidget())

	def getFontPreviewText(self) -> str:  # noqa: PLR6301
		for occurData in ui.cells.current.getPluginsData():
			return occurData[1].replace("\n", " ")
		return ""
