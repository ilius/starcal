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
from scal3.ui_gtk.option_ui.check_mix import CheckColorOptionUI
from scal3.ui_gtk.option_ui.color import ColorOptionUI
from scal3.ui_gtk.option_ui.spin import FloatSpinOptionUI
from scal3.ui_gtk.stack import StackPage

if TYPE_CHECKING:
	from scal3.ui_gtk.option_ui.base import OptionUI
	from scal3.ui_gtk.timeline.prefs.types import TimeLineType

__all__ = ["buildGeneralPages"]


def buildGeneralPages(timeLine: TimeLineType) -> list[StackPage]:
	pages: list[StackPage] = []
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageWidget = vbox
	page.pageName = "general"
	page.pageTitle = _("General")
	page.pageLabel = _("_General")
	page.pageIcon = "preferences-system.svg"
	pages.append(page)
	option: OptionUI
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	pack(hbox, gtk.Label(label=_("Background Color")))
	option = ColorOptionUI(
		option=conf.bgColor,
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	pack(hbox, gtk.Label(label=_("Foreground Color")))
	option = ColorOptionUI(
		option=conf.fgColor,
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.baseFontSize,
		bounds=(0.1, 999),
		digits=1,
		step=1,
		label=_("Base Font Size"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# FIXME: should we update TimeLine on type?! Can make it very slow
	# can even cause freezing TimeLine
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = CheckColorOptionUI(
		CheckOptionUI(
			option=conf.changeHolidayBg,
			label=_("Change Holidays Background"),
		),
		ColorOptionUI(
			option=conf.holidayBgBolor,
			# useAlpha=False,
		),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# -----
	# TODO: changeHolidayBgMinDays
	# TODO: changeHolidayBgMaxDays
	return pages
