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

from scal3.locale_man import tr as _
from scal3.timeline import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui.check import CheckOptionUI
from scal3.ui_gtk.option_ui.spin import (
	FloatSpinOptionUI,
	IntSpinOptionUI,
)
from scal3.ui_gtk.stack import StackPage

if TYPE_CHECKING:
	from scal3.ui_gtk.option_ui.base import OptionUI
	from scal3.ui_gtk.timeline.prefs.types import TimeLineType

__all__ = ["buildButtonsPages"]


def buildButtonsPages(timeLine: TimeLineType) -> list[StackPage]:
	pages: list[StackPage] = []
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageWidget = vbox
	page.pageName = "buttons"
	page.pageTitle = _("Buttons")
	page.pageLabel = _("Buttons")
	page.pageIcon = "configure-toolbars.png"
	pages.append(page)
	# --------------------------
	option: OptionUI

	def updateBasicButtons() -> None:
		timeLine.updateBasicButtons()
		timeLine.w.queue_draw()

	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = IntSpinOptionUI(
		option=conf.basicButtonsSize,
		bounds=(1, 999),
		step=1,
		label=_("Buttons Size"),
		live=True,
		onChangeFunc=updateBasicButtons,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)

	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.basicButtonsSpacing,
		bounds=(0, 999),
		digits=1,
		step=1,
		label=_("Space between buttons"),
		live=True,
		onChangeFunc=updateBasicButtons,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)

	# ----

	def updateMovementButtons() -> None:
		timeLine.updateMovementButtons()
		timeLine.w.queue_draw()

	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = CheckOptionUI(
		option=conf.movementButtonsEnable,
		label=_("Movement Buttons"),
		live=True,
		onChangeFunc=updateMovementButtons,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = IntSpinOptionUI(
		option=conf.movementButtonsSize,
		bounds=(1, 999),
		step=1,
		label=_("Movement Buttons Size"),
		live=True,
		onChangeFunc=updateMovementButtons,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)

	# --------
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.basicButtonsOpacity,
		bounds=(0, 1),
		digits=2,
		step=0.1,
		label=_("Opacity of main buttons"),
		live=True,
		onChangeFunc=updateBasicButtons,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# ---
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movementButtonsOpacity,
		bounds=(0, 1),
		digits=2,
		step=0.1,
		label=_("Opacity of movement buttons"),
		live=True,
		onChangeFunc=updateMovementButtons,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	return pages
