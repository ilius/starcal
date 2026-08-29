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
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.customize import newSubPageButton
from scal3.ui_gtk.event import common, getWidgetClass
from scal3.ui_gtk.event.account import AccountCombo, AccountGroupBox
from scal3.ui_gtk.mywidgets import MyColorButton, TextFrame
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.signals import SignalHandlerBase, registerSignals
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.utils import set_tooltip

if TYPE_CHECKING:
	from scal3.event_lib.group import EventGroup
	from scal3.event_lib.pytypes import EventGroupType

__all__ = ["BaseWidgetClass", "makeGroupWidget"]


def makeGroupWidget(obj: EventGroupType) -> BaseWidgetClass | None:
	"""Obj is an instance of Event, EventRule, EventNotifier or EventGroup."""
	WidgetClass = getWidgetClass(obj)
	if WidgetClass is None:
		return None
	widget: BaseWidgetClass = WidgetClass(obj)  # type: ignore[arg-type, assignment]
	widget.show()
	widget.updateWidget()
	return widget


@registerSignals
class GroupSubPageSignalHandler(SignalHandlerBase):
	signals = [("goto-page", [str])]


class BaseWidgetClass(gtk.Box):
	userCanAddEvents = True

	mainPagePath = "main"
	onlinePagePath = "main.online"
	typePagePath = "main.settings"
	onlinePageLabel = "Online Service"

	def show(self) -> None:
		self._finalizeSubPages()
		gtk.Box.show_all(self)

	def __init__(self, group: EventGroup) -> None:
		from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo
		from scal3.ui_gtk.mywidgets.tz_combo import TimeZoneComboBoxEntry

		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.w = self
		self.group = group
		# --------
		self.stack = MyStack()
		pack(self, self.stack, 1, 1)
		# --------
		self.sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		self.typeSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		self.onlineSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# --------
		self.mainBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		mainPage = StackPage()
		mainPage.pagePath = self.mainPagePath
		mainPage.pageWidget = self.mainBox
		self.stack.addPage(mainPage)
		# --------
		self.typeBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		self.onlineBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		self._subPagesFinalized = False
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Title"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.titleEntry = gtk.Entry()
		pack(hbox, self.titleEntry, 1, 1)
		pack(self.mainBox, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Color"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.colorButton = MyColorButton()
		self.colorButton.set_use_alpha(True)  # FIXME
		pack(hbox, self.colorButton)
		pack(self.mainBox, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Default Icon"))  # FIXME
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(self.mainBox, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Default Calendar Type"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		typeCombo = CalTypeCombo()
		pack(hbox, typeCombo)
		pack(hbox, gtk.Label(), 1, 1)
		self.calTypeCombo = typeCombo
		pack(self.mainBox, hbox)
		# -----
		self.addStartEndWidgets()
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.tzCheck = gtk.CheckButton(label=_("Default Time Zone"))
		pack(hbox, self.tzCheck)
		self.sizeGroup.add_widget(self.tzCheck)
		tzCombo = TimeZoneComboBoxEntry()
		pack(hbox, tzCombo)
		pack(hbox, gtk.Label(), 1, 1)
		self.tzCombo = tzCombo
		pack(self.mainBox, hbox)
		self.tzCheck.connect(
			"clicked",
			lambda check: self.tzCombo.set_sensitive(check.get_active()),
		)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
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
		pack(self.mainBox, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
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
		pack(self.mainBox, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Event Cache Size"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.cacheSizeSpin = IntSpinButton(0, 9999)
		pack(hbox, self.cacheSizeSpin)
		pack(self.mainBox, hbox)
		# -----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Event Text Separator"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.sepInput = TextFrame()
		pack(hbox, self.sepInput, 1, 1)
		pack(self.mainBox, hbox)
		set_tooltip(
			hbox,
			_(
				"Using to separate Summary and Description when displaying event",
			),
		)
		# -----
		# hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# label = gtk.Label(label=_("Enable Notifications"))
		# label.set_xalign(0)
		# pack(hbox, label)
		# self.sizeGroup.add_widget(label)
		# self.notificationEnabledCheck = gtk.CheckButton(label="")
		# pack(hbox, self.notificationEnabledCheck)
		# pack(self, hbox)
		# -----
		# hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
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
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
			self.addEventsToBeginningCheck = gtk.CheckButton(
				label=_("Add New Events to Beginning"),
			)
			set_tooltip(
				hbox,  # label or hbox?
				_("Add new events to beginning of event list, not to the end"),
			)
			pack(hbox, self.addEventsToBeginningCheck)
			pack(self.mainBox, hbox)
		# ------ Online Service settings (sub-page)
		self._addOnlineServiceWidgets()

	def _addOnlineServiceWidgets(self) -> None:
		sizeGroup = self.onlineSizeGroup
		# --
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Account"))
		label.set_xalign(0)
		pack(hbox, label)
		sizeGroup.add_widget(label)
		self.accountCombo = AccountCombo()
		pack(hbox, self.accountCombo)
		pack(self.onlineBox, hbox)
		# --
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Remote Group"))
		label.set_xalign(0)
		pack(hbox, label)
		sizeGroup.add_widget(label)
		accountGroupBox = AccountGroupBox(self.accountCombo)
		pack(hbox, accountGroupBox, 1, 1)
		pack(self.onlineBox, hbox)
		self.accountGroupCombo = accountGroupBox.combo
		# --
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.syncCheck = gtk.CheckButton(label=_("Synchronization Interval"))
		pack(hbox, self.syncCheck)
		sizeGroup.add_widget(self.syncCheck)
		self.syncIntervalInput = common.DurationInputBox()
		pack(hbox, self.syncIntervalInput)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.onlineBox, hbox)
		self.syncCheck.connect(
			"clicked",
			lambda check: self.syncIntervalInput.set_sensitive(check.get_active()),
		)

	def addStartEndWidgets(self) -> None:
		pass

	def _finalizeSubPages(self) -> None:
		if self._subPagesFinalized:
			return
		self._subPagesFinalized = True
		if self.onlineBox.get_children():
			self._addSubPage(
				self.onlineBox,
				self.onlinePagePath,
				_(self.onlinePageLabel),
			)
		if self.typeBox.get_children():
			self._addSubPage(
				self.typeBox,
				self.typePagePath,
				_("{groupType} Setting").format(groupType=self.group.desc),
			)

	def _addSubPage(
		self,
		box: gtk.Box,
		pagePath: str,
		pageLabel: str,
	) -> None:
		page = StackPage()
		page.pagePath = pagePath
		page.pageParent = self.mainPagePath
		page.pageLabel = pageLabel
		page.pageTitle = pageLabel
		page.pageWidget = box
		sig = GroupSubPageSignalHandler()
		sig.connect("goto-page", self.gotoPage)
		pack(self.mainBox, newSubPageButton(sig, page), False, False)
		self.stack.addPage(page)

	def gotoPage(self, _sig: object, pagePath: str) -> None:
		self.stack.gotoPage(pagePath)

	def updateWidget(self) -> None:
		self.titleEntry.set_text(self.group.title)
		self.colorButton.setRGBA(self.group.color)
		if self.group.icon:
			self.iconSelect.set_filename(self.group.icon)
		self.calTypeCombo.setActive(self.group.calType)
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
		# ---
		if self.group.remoteIds:
			aid, gid = self.group.remoteIds
		else:
			aid, gid = None, None
		self.accountCombo.setActive(aid)
		self.accountGroupCombo.setGroupId(gid)
		self.syncCheck.set_active(self.group.remoteSyncEnable)
		self.syncIntervalInput.set_sensitive(self.group.remoteSyncEnable)

		value, unit = self.group.remoteSyncDuration
		self.syncIntervalInput.setDuration(value, unit)

	def updateVars(self) -> None:
		self.group.title = self.titleEntry.get_text()
		self.group.color = self.colorButton.getRGBA()
		self.group.icon = self.iconSelect.get_filename()
		calType = self.calTypeCombo.getActive()
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
		# ---
		self.group.remoteIds = None
		aid = self.accountCombo.getActive()
		if aid:
			gid = self.accountGroupCombo.getGroupId()
			if gid:
				self.group.remoteIds = aid, gid
		self.group.remoteSyncEnable = self.syncCheck.get_active()
		self.group.remoteSyncDuration = self.syncIntervalInput.getDuration()

	def calTypeComboChanged(self, widget: gtk.Widget | None = None) -> None:
		pass
