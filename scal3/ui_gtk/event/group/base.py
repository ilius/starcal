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
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import getWidgetClass
from scal3.ui_gtk.mywidgets import MyColorButton, TextFrame
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.utils import set_tooltip

if TYPE_CHECKING:
	from scal3.event_lib.groups import EventGroup
	from scal3.event_lib.pytypes import EventGroupType

__all__ = ["BaseWidgetClass"]


def makeGroupWidget(obj: EventGroupType) -> BaseWidgetClass | None:
	"""Obj is an instance of Event, EventRule, EventNotifier or EventGroup."""
	WidgetClass = getWidgetClass(obj)
	if WidgetClass is None:
		return None
	widget: BaseWidgetClass = WidgetClass(obj)  # type: ignore
	widget.show()
	widget.updateWidget()
	return widget


class BaseWidgetClass(gtk.Box):
	userCanAddEvents = True

	def show(self) -> None:
		gtk.Box.show_all(self)

	def __init__(self, group: EventGroup) -> None:
		from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo
		from scal3.ui_gtk.mywidgets.tz_combo import TimeZoneComboBoxEntry

		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.w = self
		self.group = group
		# --------
		self.sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Title"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.titleEntry = gtk.Entry()
		pack(hbox, self.titleEntry, 1, 1)
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Color"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.colorButton = MyColorButton()
		self.colorButton.set_use_alpha(True)  # FIXME
		pack(hbox, self.colorButton)
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Default Icon"))  # FIXME
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Default Calendar Type"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		typeCombo = CalTypeCombo()
		pack(hbox, typeCombo)
		pack(hbox, gtk.Label(), 1, 1)
		self.calTypeCombo = typeCombo
		pack(self, hbox)
		# -----
		self.addStartEndWidgets()
		# -----
		hbox = HBox()
		self.tzCheck = gtk.CheckButton(label=_("Default Time Zone"))
		pack(hbox, self.tzCheck)
		self.sizeGroup.add_widget(self.tzCheck)
		tzCombo = TimeZoneComboBoxEntry()
		pack(hbox, tzCombo)
		pack(hbox, gtk.Label(), 1, 1)
		self.tzCombo = tzCombo
		pack(self, hbox)
		self.tzCheck.connect(
			"clicked",
			lambda check: self.tzCombo.set_sensitive(check.get_active()),
		)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Show in Calendar"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.showInDCalCheck = gtk.CheckButton(label=_("Day"))
		self.showInWCalCheck = gtk.CheckButton(label=_("Week"))
		self.showInMCalCheck = gtk.CheckButton(label=_("Month"))
		pack(hbox, self.showInDCalCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.showInWCalCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.showInMCalCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Show in"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.showInTimeLineCheck = gtk.CheckButton(label=_("Time Line"))
		self.showInStatusIconCheck = gtk.CheckButton(label=_("Status Icon"))
		pack(hbox, self.showInTimeLineCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.showInStatusIconCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Event Cache Size"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.cacheSizeSpin = IntSpinButton(0, 9999)
		pack(hbox, self.cacheSizeSpin)
		pack(self, hbox)
		# -----
		hbox = HBox()
		label = gtk.Label(label=_("Event Text Separator"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.sepInput = TextFrame()
		pack(hbox, self.sepInput, 1, 1)
		pack(self, hbox)
		set_tooltip(
			hbox,
			_(
				"Using to separate Summary and Description when displaying event",
			),
		)
		# -----
		# hbox = HBox()
		# label = gtk.Label(label=_("Enable Notifications"))
		# label.set_xalign(0)
		# pack(hbox, label)
		# self.sizeGroup.add_widget(label)
		# self.notificationEnabledCheck = gtk.CheckButton(label="")
		# pack(hbox, self.notificationEnabledCheck)
		# pack(self, hbox)
		# -----
		# hbox = HBox()
		# label = gtk.Label(label=_("Show Full Event Description"))
		# label.set_xalign(0)
		# pack(hbox, label)
		# self.sizeGroup.add_widget(label)
		# self.showFullEventDescCheck = gtk.CheckButton(label="")
		# pack(hbox, self.showFullEventDescCheck, 1, 1)
		# pack(self, hbox)
		# ---
		self.calTypeCombo.connect(
			"changed",
			self.calTypeComboChanged,
		)  # right place? before updateWidget? FIXME
		# -----
		if self.userCanAddEvents:
			hbox = HBox()
			self.addEventsToBeginningCheck = gtk.CheckButton(
				label=_("Add New Events to Beginning"),
			)
			set_tooltip(
				hbox,  # label or hbox?
				_("Add new events to beginning of event list, not to the end"),
			)
			pack(hbox, self.addEventsToBeginningCheck)
			pack(self, hbox)

	def addStartEndWidgets(self) -> None:
		pass

	def updateWidget(self) -> None:
		self.titleEntry.set_text(self.group.title)
		self.colorButton.setRGBA(self.group.color)
		if self.group.icon:
			self.iconSelect.set_filename(self.group.icon)
		self.calTypeCombo.set_active(self.group.calType)
		# --
		self.tzCheck.set_active(self.group.timeZoneEnable)
		self.tzCombo.set_sensitive(self.group.timeZoneEnable)
		if self.group.timeZone:
			self.tzCombo.set_text(self.group.timeZone)
		# --
		self.showInDCalCheck.set_active(self.group.showInDCal)
		self.showInWCalCheck.set_active(self.group.showInWCal)
		self.showInMCalCheck.set_active(self.group.showInMCal)
		self.showInTimeLineCheck.set_active(self.group.showInTimeLine)
		self.showInStatusIconCheck.set_active(self.group.showInStatusIcon)
		self.cacheSizeSpin.set_value(self.group.eventCacheSize)
		self.sepInput.set_text(self.group.eventTextSep)
		# self.notificationEnabledCheck.set_active(self.group.notificationEnabled)
		# self.showFullEventDescCheck.set_active(self.group.showFullEventDesc)
		if self.userCanAddEvents:
			self.addEventsToBeginningCheck.set_active(self.group.addEventsToBeginning)

	def updateVars(self) -> None:
		self.group.title = self.titleEntry.get_text()
		self.group.color = self.colorButton.getRGBA()
		self.group.icon = self.iconSelect.get_filename()
		calType = self.calTypeCombo.get_active()
		assert calType is not None
		self.group.calType = calType
		# --
		self.group.timeZoneEnable = self.tzCheck.get_active()
		self.group.timeZone = self.tzCombo.get_text()
		# --
		self.group.showInDCal = self.showInDCalCheck.get_active()
		self.group.showInWCal = self.showInWCalCheck.get_active()
		self.group.showInMCal = self.showInMCalCheck.get_active()
		self.group.showInTimeLine = self.showInTimeLineCheck.get_active()
		self.group.showInStatusIcon = self.showInStatusIconCheck.get_active()
		self.group.eventCacheSize = int(self.cacheSizeSpin.get_value())
		self.group.eventTextSep = self.sepInput.get_text()
		# self.group.notificationEnabled = self.notificationEnabledCheck.get_active()
		# FIXME: why does above line cause a seg fault?!
		# self.group.showFullEventDesc = self.showFullEventDescCheck.get_active()
		if self.userCanAddEvents:
			self.group.addEventsToBeginning = (
				self.addEventsToBeginningCheck.get_active()
			)

	def calTypeComboChanged(self, widget: gtk.Widget | None = None) -> None:
		pass
