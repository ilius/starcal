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

import typing

from scal3 import timeline
from scal3.locale_man import tr as _
from scal3.timeline import conf
from scal3.ui import conf as uiconf
from scal3.ui_gtk import HBox, VBox, gdk, gtk, pack
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.pref_utils import (
	CheckColorPrefItem,
	CheckPrefItem,
	ColorPrefItem,
	FloatSpinPrefItem,
	IntSpinPrefItem,
	PrefItem,
)
from scal3.ui_gtk.pref_utils_extra import KeyBindingPrefItem
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.utils import imageFromFile

__all__ = ["TimeLinePreferencesWindow"]


class TimeLineType(typing.Protocol):
	def queue_draw(self) -> None: ...

	def updateBasicButtons(self) -> None: ...

	def updateMovementButtons(self) -> None: ...


class TimeLinePreferencesWindow(gtk.Window):
	def __init__(self, timeLine: TimeLineType, **kwargs) -> None:
		gtk.Window.__init__(self, **kwargs)
		self.set_title(_("Time Line Preferences"))
		self.set_position(gtk.WindowPosition.CENTER)
		self.connect("delete-event", self.onDelete)
		self.connect("key-press-event", self.onKeyPress)
		# self.set_has_separator(False)
		# self.set_skip_taskbar_hint(True)
		# ---
		self.vbox = VBox()
		self.add(self.vbox)
		# ---
		self.buttonbox = MyHButtonBox()
		# self.buttonbox.add_button(
		# 	imageName="dialog-cancel.svg",
		# 	label=_("Cancel"),
		# 	onClick=self.onCancelClick,
		# )
		# self.buttonbox.add_button(
		# 	imageName="dialog-ok-apply.svg",
		# 	label=_("_Apply", ctx="window action"),
		# 	onClick=self.onApplyClick,
		# )
		self.buttonbox.add_button(
			imageName="document-save.svg",
			label=_("_Save"),
			onClick=self.onSaveClick,
			tooltip=_("Save Preferences"),
		)
		# -------
		self.prefPages = []
		# ----------------------------------------------------
		stack = MyStack(
			iconSize=uiconf.stackIconSize.v,
		)
		stack.setTitleFontSize("large")
		stack.setTitleCentered(True)
		stack.setupWindowTitle(self, _("Time Line Preferences"), False)
		self.stack = stack
		# ----------------------------------------------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "general"
		page.pageTitle = _("General")
		page.pageLabel = _("_General")
		page.pageIcon = "preferences-system.svg"
		self.prefPages.append(page)
		prefItem: PrefItem
		# -----
		hbox = HBox(spacing=5)
		pack(hbox, gtk.Label(label=_("Background Color")))
		prefItem = ColorPrefItem(
			prop=conf.bgColor,
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		pack(hbox, gtk.Label(label=_("Foreground Color")))
		prefItem = ColorPrefItem(
			prop=conf.fgColor,
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.baseFontSize,
			bounds=(0.1, 999),
			digits=1,
			step=1,
			label=_("Base Font Size"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# FIXME: should we update TimeLine on type?! Can make it very slow
		# can even cause freezing TimeLine
		# -----
		hbox = HBox(spacing=5)
		prefItem = CheckColorPrefItem(
			CheckPrefItem(
				prop=conf.changeHolidayBg,
				label=_("Change Holidays Background"),
			),
			ColorPrefItem(
				prop=conf.holidayBgBolor,
				# useAlpha=False,
			),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# -----
		# TODO: changeHolidayBgMinDays
		# TODO: changeHolidayBgMaxDays
		# ----------------------------------------------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "buttons"
		page.pageTitle = _("Buttons")
		page.pageLabel = _("Buttons")
		page.pageIcon = "configure-toolbars.png"
		self.prefPages.append(page)
		# --------------------------

		def updateBasicButtons() -> None:
			timeLine.updateBasicButtons()
			timeLine.queue_draw()

		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.basicButtonsSize,
			bounds=(1, 999),
			digits=1,
			step=1,
			label=_("Buttons Size"),
			live=True,
			onChangeFunc=updateBasicButtons,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)

		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.basicButtonsSpacing,
			bounds=(0, 999),
			digits=1,
			step=1,
			label=_("Space between buttons"),
			live=True,
			onChangeFunc=updateBasicButtons,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)

		# ----

		def updateMovementButtons() -> None:
			timeLine.updateMovementButtons()
			timeLine.queue_draw()

		hbox = HBox(spacing=5)
		prefItem = CheckPrefItem(
			prop=conf.movementButtonsEnable,
			label=_("Movement Buttons"),
			live=True,
			onChangeFunc=updateMovementButtons,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movementButtonsSize,
			bounds=(1, 999),
			digits=1,
			step=1,
			label=_("Movement Buttons Size"),
			live=True,
			onChangeFunc=updateMovementButtons,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)

		# --------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.basicButtonsOpacity,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Opacity of main buttons"),
			live=True,
			onChangeFunc=updateBasicButtons,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# ---
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movementButtonsOpacity,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Opacity of movement buttons"),
			live=True,
			onChangeFunc=updateMovementButtons,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# ----------------------------------------------------
		vboxIndicators = vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "indicators"
		page.pageTitle = _("Indicators")
		page.pageLabel = _("_Indicators")
		page.pageIcon = "screenruler.png"  # svg image does not look good!
		self.prefPages.append(page)
		# --------------------------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.majorStepMin,
			bounds=(1, 999),
			digits=1,
			step=1,
			label=_("Major Indicator Step (Minimum)"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# FIXME: ValueError: could not convert string to float:
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.minorStepMin,
			bounds=(1, 999),
			digits=1,
			step=1,
			label=_("Minor Indicator Step (Minimum)"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# ---------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageParent = "indicators"
		page.pageWidget = vbox
		page.pageName = "indicatorSize"
		page.pageTitle = _("Size of Indicators")
		page.pageLabel = _("Size of Indicators")
		page.pageIcon = "screenruler.png"
		self.prefPages.append(page)
		pack(vboxIndicators, self.newWideButton(page), 1, 1)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.baseTickHeight,
			bounds=(0.1, 999),
			digits=1,
			step=1,
			label=_("Base Height"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.baseTickWidth,
			bounds=(0.1, 99),
			digits=2,
			step=1,
			label=_("Base Width"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.maxTickWidth,
			bounds=(0.1, 99),
			digits=1,
			step=1,
			label=_("Maximum Width"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.maxTickHeightRatio,
			bounds=(0.01, 1),
			digits=2,
			step=0.1,
			label=_("Maximum Height"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("of window height")))
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.maxLabelWidth,
			bounds=(1, 999),
			digits=1,
			step=1,
			label=_("Maximum Label Width"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		hbox = HBox(spacing=5)
		# -----
		# TODO: labelYRatio
		# -----
		# TODO: yearPrettyPower
		# -----
		# TODO: truncateTickLabel
		# ----------------------------------------------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageParent = "indicators"
		page.pageWidget = vbox
		page.pageName = "currentTimeMarker"
		page.pageTitle = _("Current Time Indicator")
		page.pageLabel = _("Current Time Indicator")
		page.pageIcon = "screenruler-redline.png"
		self.prefPages.append(page)
		pack(vboxIndicators, self.newWideButton(page), 1, 1)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.currentTimeMarkerHeightRatio,
			bounds=(0.01, 1),
			digits=2,
			step=0.1,
			label=_("Maximum Height"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("of window height")))
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.currentTimeMarkerWidth,
			bounds=(0.1, 99),
			digits=2,
			step=1,
			label=_("Width"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		pack(hbox, gtk.Label(label=_("Color")))
		prefItem = ColorPrefItem(
			prop=conf.currentTimeMarkerColor,
			# useAlpha=False,
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# ---------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageParent = "indicators"
		page.pageWidget = vbox
		page.pageName = "weekStartIndicator"
		page.pageTitle = _("Week Start Indicators")
		page.pageLabel = _("Week Start Indicators")
		page.pageIcon = ""
		self.prefPages.append(page)
		pack(vboxIndicators, self.newWideButton(page), 1, 1)
		# -----
		hbox = HBox(spacing=5)
		prefItem = CheckPrefItem(
			prop=conf.showWeekStart,
			label=_("Show Week Start"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		pack(hbox, gtk.Label(label=_("Color")))
		prefItem = ColorPrefItem(
			prop=conf.weekStartTickColor,
			# useAlpha=False,
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = IntSpinPrefItem(
			prop=conf.showWeekStartMinDays,
			bounds=(1, 999),
			step=1,
			label=_("Minimum Interval"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("days")))
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = IntSpinPrefItem(
			prop=conf.showWeekStartMaxDays,
			bounds=(1, 999),
			step=1,
			label=_("Maximum Interval"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("days")))
		pack(vbox, hbox)
		# ----------------------------------------------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "events"
		page.pageTitle = _("Events")
		page.pageLabel = _("Events")
		page.pageIcon = "view-calendar-timeline.svg"
		self.prefPages.append(page)
		# --------------------------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.boxLineWidth,
			bounds=(0, 99),
			digits=1,
			step=1,
			label=_("Border Line Width"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.boxInnerAlpha,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Inner Opacity"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.boxEditBorderWidth,
			bounds=(0, 999),
			digits=1,
			step=1,
			label=_("Editing Border Width"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.boxEditInnerLineWidth,
			bounds=(0, 99),
			digits=1,
			step=1,
			label=_("Editing Inner Line Width"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.boxEditHelperLineWidth,
			bounds=(0, 99),
			digits=1,
			step=1,
			label=_("Editing Helper Line Width"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=5)
		prefItem = CheckPrefItem(
			prop=conf.boxReverseGravity,
			label=_("Reverse Gravity"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# ------
		# TODO: boxSkipPixelLimit = 0.1  # pixel
		# TODO: rotateBoxLabel = -1
		# ----------------------------------------------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "movement"
		page.pageTitle = _("Movement")
		page.pageLabel = _("Movement")
		page.pageIcon = "movement.svg"
		self.prefPages.append(page)
		# --------------------------
		hbox = HBox(spacing=5)
		noAnimVBox = gtk.VBox()
		animVBox = gtk.VBox()

		animation = conf.enableAnimation.v

		noAnimVBox.set_sensitive(not animation)
		animVBox.set_sensitive(animation)

		def enableAnimationChanged() -> None:
			noAnimVBox.set_sensitive(not animation)
			animVBox.set_sensitive(animation)
			timeLine.queue_draw()

		prefItem = CheckPrefItem(
			prop=conf.enableAnimation,
			label=_("Animation"),
			live=True,
			onChangeFunc=enableAnimationChanged,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# ------
		frame = gtk.Frame(label=_("Without Animation"))

		noAnimVBox.set_border_width(3)
		frame.add(noAnimVBox)
		pack(vbox, frame)
		# ---
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingStaticStepMouse,
			bounds=(0.1, 9999),
			digits=1,
			step=1,
			label=_("Step with mouse scroll"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(noAnimVBox, hbox)
		# ---
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingStaticStepKeyboard,
			bounds=(0.1, 9999),
			digits=1,
			step=1,
			label=_("Step with keyboard"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(noAnimVBox, hbox)
		# ---
		pack(vbox, animVBox)
		# ---------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageParent = "movement"
		page.pageWidget = vbox
		page.pageName = "movementAnimation"
		page.pageTitle = _("Animation Settings")
		page.pageLabel = _("Animation Settings")
		page.pageIcon = "movement.svg"
		self.prefPages.append(page)
		pack(animVBox, self.newWideButton(page), 1, 1)
		# -----------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingInitialVelocity,
			bounds=(0, 9999),
			digits=1,
			step=1,
			label=_("Initial Velocity"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixel/second")))
		pack(vbox, hbox)
		# ---
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingMaxVelocity,
			bounds=(0.1, 9999),
			digits=1,
			step=1,
			label=_("Maximum Velocity"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixel/second")))
		pack(vbox, hbox)
		# ---
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingHandForceMouse,
			bounds=(0.1, 9999),
			digits=1,
			step=1,
			label=_("Acceleration with mouse"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(
			hbox,
			gtk.Label(
				label=_("pixel/second<sup>2</sup>"),
				use_markup=True,
			),
		)
		pack(vbox, hbox)
		# ---
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingHandForceKeyboard,
			bounds=(0.1, 9999),
			digits=1,
			step=1,
			label=_("Acceleration with keyboard"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(
			hbox,
			gtk.Label(
				label=_("pixel/second<sup>2</sup>"),
				use_markup=True,
			),
		)
		pack(vbox, hbox)
		# ---
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingHandForceKeyboardSmall,
			bounds=(0.1, 9999),
			digits=1,
			step=1,
			label=_("Acceleration with keyboard (with Shift)"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(
			hbox,
			gtk.Label(
				label=_("pixel/second<sup>2</sup>"),
				use_markup=True,
			),
		)
		pack(vbox, hbox)
		# ---
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingHandForceButton,
			bounds=(0.1, 9999),
			digits=1,
			step=1,
			label=_("Acceleration with buttons"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(
			hbox,
			gtk.Label(
				label=_("pixel/second<sup>2</sup>"),
				use_markup=True,
			),
		)
		pack(vbox, hbox)
		# -----
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.movingFrictionForce,
			bounds=(0, 9999),
			digits=1,
			step=1,
			label=_("Friction Acceleration"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
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
		# ----------------------------------------------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "zooming"
		page.pageTitle = _("Zooming")
		page.pageLabel = _("Zooming")
		page.pageIcon = "zoom-in.svg"
		self.prefPages.append(page)
		# --------------------------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.scrollZoomStep,
			bounds=(1, 9),
			digits=2,
			step=0.1,
			label=_("Zoom Factor by Mouse Scroll"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=5)
		prefItem = FloatSpinPrefItem(
			prop=conf.keyboardZoomStep,
			bounds=(1, 9),
			digits=2,
			step=0.1,
			label=_("Zoom Factor by Keyboard"),
			live=True,
			onChangeFunc=timeLine.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(vbox, hbox)
		# ----------------------------------------------------
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "keys"
		page.pageTitle = _("Keys")
		page.pageLabel = _("Keys")
		page.pageIcon = "configure-shortcuts.png"
		self.prefPages.append(page)
		# -----
		prefItem = KeyBindingPrefItem(
			prop=conf.keys,
			actions=sorted(conf.keys.v.values()),
		)
		prefItem.updateWidget()
		pack(vbox, prefItem.getWidget(), 1, 1)
		# --------------------------------------------------------------------
		rootPagePath = "root"
		# ---
		mainPages = []
		for page in self.prefPages:
			if page.pageParent:
				page.pagePath = page.pageParent + "." + page.pageName
				continue
			page.pageParent = rootPagePath
			page.pagePath = page.pageName
			mainPages.append(page)
		# ----
		colN = 2
		# ----
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		grid.set_row_spacing(15)
		grid.set_column_spacing(15)
		grid.set_border_width(20)
		# ----
		self.defaultWidget = None
		firstPageDoubleSize = len(mainPages) % 2 == 1
		if firstPageDoubleSize:
			page = mainPages.pop(0)
			button = self.newWideButton(page)
			grid.attach(button, 0, 0, colN, 1)
			self.defaultWidget = button
		# ---
		N = len(mainPages)
		colBN = (N - 1) // colN + 1
		for col_i in range(colN):
			for row_i in range(colBN):
				page_i = col_i * colBN + row_i
				if page_i >= N:
					break
				page = mainPages[page_i]
				button = self.newWideButton(page)
				grid.attach(button, col_i, row_i + 1, 1, 1)
				if page_i == 0 and not firstPageDoubleSize:
					self.defaultWidget = button
		grid.show_all()
		# ---------------
		page = StackPage()
		page.pagePath = rootPagePath
		page.pageWidget = grid
		page.pageExpand = True
		page.pageExpand = True
		stack.addPage(page)
		for page in self.prefPages:
			stack.addPage(page)
		# -----------------------
		pack(self.vbox, stack, 1, 1)
		pack(self.vbox, self.buttonbox)
		# ----
		self.vbox.show_all()

	def gotoPageClicked(self, _b: gtk.Widget, page: StackPage) -> None:
		self.stack.gotoPage(page.pagePath)

	def newWideButton(self, page: StackPage) -> gtk.Widget:
		hbox = HBox(spacing=10)
		hbox.set_border_width(10)
		label = gtk.Label(label=page.pageLabel)
		label.set_use_underline(True)
		pack(hbox, gtk.Label(), 1, 1)
		if page.pageIcon and uiconf.buttonIconEnable.v:
			pack(hbox, imageFromFile(page.pageIcon, self.stack.iconSize()))
		pack(hbox, label, 0, 0)
		pack(hbox, gtk.Label(), 1, 1)
		button = gtk.Button()
		button.add(hbox)
		button.connect("clicked", self.gotoPageClicked, page)
		return button

	def onDelete(
		self,
		_widget: gtk.Widget | None = None,
		_data: typing.Any = None,
	) -> bool:
		self.hide()
		return True

	def onSaveClick(self, _w: gtk.Widget | None = None) -> bool:
		self.hide()
		timeline.saveConf()
		return True

	def onKeyPress(self, _arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if gdk.keyval_name(gevent.keyval) == "Escape":
			self.hide()
			return True
		return False
