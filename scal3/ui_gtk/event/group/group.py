from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.core import jd_to
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event.account import AccountCombo, AccountGroupBox
from scal3.ui_gtk.event.group.base import BaseWidgetClass
from scal3.ui_gtk.mywidgets.expander import ExpanderFrame
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton

if TYPE_CHECKING:
	from scal3.event_lib.groups import EventGroup

__all__ = ["WidgetClass"]


class WidgetClass(BaseWidgetClass):
	def addStartEndWidgets(self) -> None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Start"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.startDateInput = DateButton()
		pack(hbox, self.startDateInput)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("End"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
		pack(self, hbox)

	def __init__(self, group: EventGroup) -> None:
		BaseWidgetClass.__init__(self, group)
		# ------
		exp = ExpanderFrame(
			label=_("Online Service"),
		)
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		exp.add(vbox)
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		self.onlineServiceExpander = exp
		# --
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Account"))
		label.set_xalign(0)
		pack(hbox, label)
		sizeGroup.add_widget(label)  # FIXME
		self.accountCombo = AccountCombo()
		pack(hbox, self.accountCombo)
		pack(vbox, hbox)
		# --
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Remote Group"))
		label.set_xalign(0)
		pack(hbox, label)
		sizeGroup.add_widget(label)  # FIXME
		accountGroupBox = AccountGroupBox(self.accountCombo)
		pack(hbox, accountGroupBox, 1, 1)
		pack(vbox, hbox)
		self.accountGroupCombo = accountGroupBox.combo
		# --
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.syncCheck = gtk.CheckButton(label=_("Synchronization Interval"))
		pack(hbox, self.syncCheck)
		sizeGroup.add_widget(self.syncCheck)
		self.syncIntervalInput = common.DurationInputBox()
		pack(hbox, self.syncIntervalInput)
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		self.syncCheck.connect(
			"clicked",
			lambda check: self.syncIntervalInput.set_sensitive(check.get_active()),
		)
		# --
		pack(self, exp)

	def updateWidget(self) -> None:
		BaseWidgetClass.updateWidget(self)
		self.startDateInput.set_value(
			jd_to(
				self.group.startJd,
				self.group.calType,
			),
		)
		self.endDateInput.set_value(
			jd_to(
				self.group.endJd,
				self.group.calType,
			),
		)
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

		self.onlineServiceExpander.set_expanded(False)

	def updateVars(self) -> None:
		BaseWidgetClass.updateVars(self)
		self.group.startJd = self.startDateInput.get_jd(self.group.calType)
		self.group.endJd = self.endDateInput.get_jd(self.group.calType)
		# ---
		self.group.remoteIds = None
		aid = self.accountCombo.getActive()
		if aid:
			gid = self.accountGroupCombo.getGroupId()
			if gid:
				self.group.remoteIds = aid, gid
		self.group.remoteSyncEnable = self.syncCheck.get_active()
		self.group.remoteSyncDuration = self.syncIntervalInput.getDuration()

	def calTypeComboChanged(
		self,
		widget: gtk.Widget | None = None,  # noqa: ARG002
	) -> None:
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		self.startDateInput.changeCalType(self.group.calType, newCalType)
		self.endDateInput.changeCalType(self.group.calType, newCalType)
		self.group.calType = newCalType
