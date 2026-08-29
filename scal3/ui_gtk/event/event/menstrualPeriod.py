from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.cal_types import jd_to
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton

if TYPE_CHECKING:
	from scal3.event_lib.menstrual import MenstrualPeriodEvent

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	_event: MenstrualPeriodEvent

	def __init__(self, event: MenstrualPeriodEvent) -> None:
		common.WidgetClass.__init__(self, event)
		# ---
		self.predictedLabel = gtk.Label(
			label=_("Predicted period, managed by the group")
		)
		self.predictedLabel.set_xalign(0)
		pack(self, self.predictedLabel)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Period Start Date")))
		self.dateInput = DateButton()
		pack(hbox, self.dateInput)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Measured Cycle Length (Days)")))
		self.cycleSpin = IntSpinButton(1, 90)
		pack(hbox, self.cycleSpin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.ovulCheck = gtk.CheckButton(label=_("Ovulation Day Override"))
		pack(hbox, self.ovulCheck)
		self.ovulDateInput = DateButton()
		pack(hbox, self.ovulDateInput)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		self.ovulCheck.connect(
			"clicked",
			lambda check: self.ovulDateInput.set_sensitive(check.get_active()),
		)

	def updateWidget(self) -> None:
		common.WidgetClass.updateWidget(self)
		event = self._event
		predicted = event.predicted
		self.predictedLabel.set_visible(predicted)
		self.dateInput.set_visible(not predicted)
		self.dateInput.setDate(jd_to(event.getJd(), event.calType))
		self.cycleSpin.set_sensitive(not predicted)
		self.cycleSpin.set_value(event.actualCycle or 0)
		override = event.ovulationOverride
		self.ovulCheck.set_active(override is not None)
		self.ovulCheck.set_sensitive(not predicted)
		self.ovulDateInput.set_sensitive(override is not None)
		self.ovulDateInput.setDate(
			jd_to(override or event.getJd(), event.calType),
		)

	def updateVars(self) -> None:
		common.WidgetClass.updateVars(self)
		event = self._event
		if not event.predicted:
			event.setJd(self.dateInput.get_jd(event.calType))
			cycle = self.cycleSpin.get_value()
			event.actualCycle = cycle if cycle > 0 else None
			if self.ovulCheck.get_active():
				event.ovulationOverride = self.ovulDateInput.get_jd(event.calType)
			else:
				event.ovulationOverride = None

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		self.dateInput.changeCalType(self._event.calType, newCalType)
		self.ovulDateInput.changeCalType(self._event.calType, newCalType)
		self._event.calType = newCalType
