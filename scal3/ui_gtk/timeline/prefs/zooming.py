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
from scal3.ui_gtk.option_ui.spin import FloatSpinOptionUI
from scal3.ui_gtk.stack import StackPage

if TYPE_CHECKING:
	from scal3.ui_gtk.timeline.prefs.types import TimeLineType

__all__ = ["buildZoomingPages"]


def buildZoomingPages(timeLine: TimeLineType) -> list[StackPage]:
	pages: list[StackPage] = []
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageWidget = vbox
	page.pageName = "zooming"
	page.pageTitle = _("Zooming")
	page.pageLabel = _("Zooming")
	page.pageIcon = "zoom-in.svg"
	pages.append(page)
	# --------------------------
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.scrollZoomStep,
		bounds=(1, 9),
		digits=2,
		step=0.1,
		label=_("Zoom Factor by Mouse Scroll"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# ------
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.keyboardZoomStep,
		bounds=(1, 9),
		digits=2,
		step=0.1,
		label=_("Zoom Factor by Keyboard"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	return pages
