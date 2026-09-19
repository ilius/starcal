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
from scal3.ui_gtk.option_ui.spin import FloatSpinOptionUI
from scal3.ui_gtk.stack import StackPage

if TYPE_CHECKING:
	from scal3.ui_gtk.option_ui.base import OptionUI
	from scal3.ui_gtk.timeline.prefs.base import TimeLinePreferencesWindow
	from scal3.ui_gtk.timeline.prefs.types import TimeLineType

__all__ = ["buildMovementPages"]


def buildMovementPages(
	win: TimeLinePreferencesWindow,
	timeLine: TimeLineType,
) -> list[StackPage]:
	pages: list[StackPage] = []
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageWidget = vbox
	page.pageName = "movement"
	page.pageTitle = _("Movement")
	page.pageLabel = _("Movement")
	page.pageIcon = "movement.svg"
	pages.append(page)
	# --------------------------
	option: OptionUI
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	noAnimVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
	animVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)

	animation = conf.enableAnimation.v

	noAnimVBox.set_sensitive(not animation)
	animVBox.set_sensitive(animation)

	def enableAnimationChanged() -> None:
		noAnimVBox.set_sensitive(not animation)
		animVBox.set_sensitive(animation)
		timeLine.w.queue_draw()

	option = CheckOptionUI(
		option=conf.enableAnimation,
		label=_("Animation"),
		live=True,
		onChangeFunc=enableAnimationChanged,
	)
	pack(hbox, option.getWidget())
	pack(vbox, hbox)
	# ------
	frame = gtk.Frame(label=_("Without Animation"))

	noAnimVBox.set_border_width(3)
	frame.add(noAnimVBox)
	pack(vbox, frame)
	# ---
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingStaticStepMouse,
		bounds=(0.1, 9999),
		digits=1,
		step=1,
		label=_("Step with mouse scroll"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(noAnimVBox, hbox)
	# ---
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingStaticStepKeyboard,
		bounds=(0.1, 9999),
		digits=1,
		step=1,
		label=_("Step with keyboard"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixels")))
	pack(noAnimVBox, hbox)
	# ---
	pack(vbox, animVBox)
	# ---------------
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageParent = "movement"
	page.pageWidget = vbox
	page.pageName = "movementAnimation"
	page.pageTitle = _("Animation Settings")
	page.pageLabel = _("Animation Settings")
	page.pageIcon = "movement.svg"
	pages.append(page)
	pack(animVBox, win.newWideButton(page), 1, 1)
	# -----------
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingInitialVelocity,
		bounds=(0, 9999),
		digits=1,
		step=1,
		label=_("Initial Velocity"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixel/second")))
	pack(vbox, hbox)
	# ---
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingMaxVelocity,
		bounds=(0.1, 9999),
		digits=1,
		step=1,
		label=_("Maximum Velocity"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(hbox, gtk.Label(label=_("pixel/second")))
	pack(vbox, hbox)
	# ---
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingHandForceMouse,
		bounds=(0.1, 9999),
		digits=1,
		step=1,
		label=_("Acceleration with mouse"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(
		hbox,
		gtk.Label(
			label=_("pixel/second<sup>2</sup>"),
			use_markup=True,
		),
	)
	pack(vbox, hbox)
	# ---
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingHandForceKeyboard,
		bounds=(0.1, 9999),
		digits=1,
		step=1,
		label=_("Acceleration with keyboard"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(
		hbox,
		gtk.Label(
			label=_("pixel/second<sup>2</sup>"),
			use_markup=True,
		),
	)
	pack(vbox, hbox)
	# ---
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingHandForceKeyboardSmall,
		bounds=(0.1, 9999),
		digits=1,
		step=1,
		label=_("Acceleration with keyboard (with Shift)"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(
		hbox,
		gtk.Label(
			label=_("pixel/second<sup>2</sup>"),
			use_markup=True,
		),
	)
	pack(vbox, hbox)
	# ---
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingHandForceButton,
		bounds=(0.1, 9999),
		digits=1,
		step=1,
		label=_("Acceleration with buttons"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(
		hbox,
		gtk.Label(
			label=_("pixel/second<sup>2</sup>"),
			use_markup=True,
		),
	)
	pack(vbox, hbox)
	# -----
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
	option = FloatSpinOptionUI(
		option=conf.movingFrictionForce,
		bounds=(0, 9999),
		digits=1,
		step=1,
		label=_("Friction Acceleration"),
		live=True,
		onChangeFunc=timeLine.w.queue_draw,
	)
	pack(hbox, option.getWidget())
	pack(
		hbox,
		gtk.Label(
			label=_("pixel/second<sup>2</sup>"),
			use_markup=True,
		),
	)
	pack(vbox, hbox)
	# -----
	# TODO: movingKeyTimeoutFirst
	# TODO: movingKeyTimeout
	return pages
