from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.cal_types import jd_to
from scal3.event_lib.menstrual import (
	observationFlowLabels,
	observationMucusLabels,
	observationOpkLabels,
	observationRecordedByLabels,
)
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton

if TYPE_CHECKING:
	from scal3.event_lib.menstrual import MenstrualObservationEvent

__all__ = ["WidgetClass"]

recordedByNames = list(observationRecordedByLabels)
recordedByLabels = list(observationRecordedByLabels.values())
flowNames = list(observationFlowLabels)
flowLabels = list(observationFlowLabels.values())
mucusNames = list(observationMucusLabels)
mucusLabels = list(observationMucusLabels.values())
opkNames = list(observationOpkLabels)
opkLabels = list(observationOpkLabels.values())


def _comboIndex(names: list[str], value: str) -> int:
	if value in names:
		return names.index(value)
	return 0


class WidgetClass(common.WidgetClass):
	_event: MenstrualObservationEvent

	def __init__(self, event: MenstrualObservationEvent) -> None:
		common.WidgetClass.__init__(self, event)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Date")))
		self.dateInput = DateButton()
		pack(hbox, self.dateInput)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Recorded By")))
		self.recordedByCombo = gtk.ComboBoxText()
		for label in recordedByLabels:
			self.recordedByCombo.append_text(label)
		pack(hbox, self.recordedByCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Flow")))
		self.flowCombo = gtk.ComboBoxText()
		for label in flowLabels:
			self.flowCombo.append_text(label)
		pack(hbox, self.flowCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Cervical Mucus")))
		self.mucusCombo = gtk.ComboBoxText()
		for label in mucusLabels:
			self.mucusCombo.append_text(label)
		pack(hbox, self.mucusCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Basal Body Temperature (°C)")))
		self.bbtInput = FloatSpinButton(34.0, 42.0, 1, 0.1)
		pack(hbox, self.bbtInput)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Ovulation Predictor Kit")))
		self.opkCombo = gtk.ComboBoxText()
		for label in opkLabels:
			self.opkCombo.append_text(label)
		pack(hbox, self.opkCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ---
		self.sexCheck = gtk.CheckButton(label=_("Intercourse occurred"))
		pack(self, self.sexCheck)
		# ---
		self.setExpandDescription(True)

	def setExpandDescription(self, expand: bool) -> None:
		for child in self.get_children():
			if isinstance(child, gtk.Frame):
				child.set_vexpand(expand)

	def updateWidget(self) -> None:
		common.WidgetClass.updateWidget(self)
		event = self._event
		self.dateInput.setDate(jd_to(event.getJd(), event.calType))
		self.recordedByCombo.set_active(
			_comboIndex(recordedByNames, event.recordedBy),
		)
		self.flowCombo.set_active(_comboIndex(flowNames, event.flow))
		self.mucusCombo.set_active(_comboIndex(mucusNames, event.mucus))
		self.bbtInput.set_value(event.bbt if event.bbt is not None else 0.0)
		self.opkCombo.set_active(_comboIndex(opkNames, event.opk))
		self.sexCheck.set_active(event.sex)

	def updateVars(self) -> None:
		common.WidgetClass.updateVars(self)
		event = self._event
		event.setJd(self.dateInput.get_jd(event.calType))
		event.recordedBy = recordedByNames[self.recordedByCombo.get_active()]
		event.flow = flowNames[self.flowCombo.get_active()]
		event.mucus = mucusNames[self.mucusCombo.get_active()]
		bbt = self.bbtInput.get_value()
		event.bbt = bbt if bbt > 0 else None
		event.opk = opkNames[self.opkCombo.get_active()]
		event.sex = self.sexCheck.get_active()

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		self.dateInput.changeCalType(self._event.calType, newCalType)
		self._event.calType = newCalType
