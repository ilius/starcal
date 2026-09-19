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
from scal3.ui_gtk.option_ui.color import ColorOptionUI
from scal3.ui_gtk.option_ui.spin import FloatSpinOptionUI, IntSpinOptionUI
from scal3.ui_gtk.stack import StackPage

if TYPE_CHECKING:
	from scal3.ui_gtk.option_ui.base import OptionUI
	from scal3.ui_gtk.timeline.prefs.base import TimeLinePreferencesWindow
	from scal3.ui_gtk.timeline.prefs.types import TimeLineType

__all__ = ["buildIndicatorsPages"]


def buildIndicatorsPages(
	win: TimeLinePreferencesWindow,
	timeLine: TimeLineType,
) -> list[StackPage]:
	pages: list[StackPage] = []
	vboxIndicators = vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageWidget = vbox
	page.pageName = "indicators"
	page.pageTitle = _("Indicators")
	page.pageLabel = _("_Indicators")
	page.pageIcon = "screenruler.png"  # svg image does not look good!
	pages.append(page)
	# --------------------------
	option: OptionUI
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.majorStepMin,
		bounds=(1, 999),
		digits=1,
		step=1,
		label=_("Major Indicator Step (Minimum)"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)
	# FIXME: ValueError: could not convert string to float:
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.minorStepMin,
		bounds=(1, 999),
		digits=1,
		step=1,
		label=_("Minor Indicator Step (Minimum)"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)
	# ---------------
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageParent = "indicators"
	page.pageWidget = vbox
	page.pageName = "indicatorSize"
	page.pageTitle = _("Size of Indicators")
	page.pageLabel = _("Size of Indicators")
	page.pageIcon = "screenruler.png"
	pages.append(page)
	pack(vboxIndicators, win.newWideButton(page), 1, 1)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.baseTickHeight,
		bounds=(0.1, 999),
		digits=1,
		step=1,
		label=_("Base Height"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.baseTickWidth,
		bounds=(0.1, 99),
		digits=2,
		step=1,
		label=_("Base Width"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.maxTickWidth,
		bounds=(0.1, 99),
		digits=1,
		step=1,
		label=_("Maximum Width"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.maxTickHeightRatio,
		bounds=(0.01, 1),
		digits=2,
		step=0.1,
		label=_("Maximum Height"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("of window height")))
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.maxLabelWidth,
		bounds=(1, 999),
		digits=1,
		step=1,
		label=_("Maximum Label Width"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	# -----
	# TODO: labelYRatio
	# -----
	# TODO: yearPrettyPower
	# -----
	# TODO: truncateTickLabel
	# ----------------------------------------------------
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageParent = "indicators"
	page.pageWidget = vbox
	page.pageName = "currentTimeMarker"
	page.pageTitle = _("Current Time Indicator")
	page.pageLabel = _("Current Time Indicator")
	page.pageIcon = "screenruler-redline.png"
	pages.append(page)
	pack(vboxIndicators, win.newWideButton(page), 1, 1)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.currentTimeMarkerHeightRatio,
		bounds=(0.01, 1),
		digits=2,
		step=0.1,
		label=_("Maximum Height"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("of window height")))
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.currentTimeMarkerWidth,
		bounds=(0.1, 99),
		digits=2,
		step=1,
		label=_("Width"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	pack(hbox, gtk.Label(label=_("Color")))
	option = ColorOptionUI(
		option=conf.currentTimeMarkerColor,
		# useAlpha=False,
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# ---------------
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageParent = "indicators"
	page.pageWidget = vbox
	page.pageName = "weekStartIndicator"
	page.pageTitle = _("Week Start Indicators")
	page.pageLabel = _("Week Start Indicators")
	page.pageIcon = ""
	pages.append(page)
	pack(vboxIndicators, win.newWideButton(page), 1, 1)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = CheckOptionUI(
		option=conf.showWeekStart,
		label=_("Show Week Start"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	pack(hbox, gtk.Label(label=_("Color")))
	option = ColorOptionUI(
		option=conf.weekStartTickColor,
		# useAlpha=False,
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = IntSpinOptionUI(
		option=conf.showWeekStartMinDays,
		bounds=(1, 999),
		step=1,
		label=_("Minimum Interval"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("days")))
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = IntSpinOptionUI(
		option=conf.showWeekStartMaxDays,
		bounds=(1, 999),
		step=1,
		label=_("Maximum Interval"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("days")))
	pack(vbox, hbox)
	return pages
