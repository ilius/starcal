from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton

if TYPE_CHECKING:
	from scal3.event_lib.menstrual import MenstrualCycleGroup

__all__ = ["WidgetClass"]

windowModeNames = ["fixed", "oginoKnaus"]
windowModeLabels = [
	_("Fixed (based on estimated ovulation)"),
	_("Knaus-Ogino (irregular cycles)"),
]


class WidgetClass(NormalWidgetClass):
	"""Group editor with the cycle settings on a separate stack page."""

	group: MenstrualCycleGroup

	def __init__(self, group: MenstrualCycleGroup) -> None:
		NormalWidgetClass.__init__(self, group)
		# --- cycle settings go on the group-type-specific settings page ---
		self._addSettingsWidgets(self.typeBox)

	def _addSettingsWidgets(self, box: gtk.Box) -> None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Person Name")))
		self.personNameEntry = gtk.Entry()
		pack(hbox, self.personNameEntry, 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Cycle Length (Days)")))
		self.cycleLengthSpin = IntSpinButton(15, 60)
		pack(hbox, self.cycleLengthSpin)
		self.cycleLengthAutoCheck = gtk.CheckButton(label=_("Auto from records"))
		pack(hbox, self.cycleLengthAutoCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Luteal Phase (Days)")))
		self.lutealPhaseSpin = IntSpinButton(8, 20)
		pack(hbox, self.lutealPhaseSpin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Period Length (Days)")))
		self.periodLengthSpin = IntSpinButton(1, 12)
		pack(hbox, self.periodLengthSpin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Fertile Window Mode")))
		self.windowModeCombo = gtk.ComboBoxText()
		for label in windowModeLabels:
			self.windowModeCombo.append_text(label)
		pack(hbox, self.windowModeCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Min Cycle (Days)")))
		self.minCycleSpin = IntSpinButton(15, 60)
		pack(hbox, self.minCycleSpin)
		pack(hbox, gtk.Label(label=_("Max Cycle (Days)")))
		self.maxCycleSpin = IntSpinButton(15, 60)
		pack(hbox, self.maxCycleSpin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.showPeriodPredictCheck = gtk.CheckButton(label=_("Show Predicted Periods"))
		pack(hbox, self.showPeriodPredictCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.showFertileCheck = gtk.CheckButton(label=_("Show Fertile Window"))
		pack(hbox, self.showFertileCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.showOvulationCheck = gtk.CheckButton(label=_("Show Ovulation Day"))
		pack(hbox, self.showOvulationCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Cycle Viability Factor")))
		self.viabilityFactorInput = FloatSpinButton(0.0, 1.0, 2, 0.05)
		pack(hbox, self.viabilityFactorInput)
		pack(hbox, gtk.Label(), 1, 1)
		pack(box, hbox)
		# ---
		self.windowModeCombo.connect(
			"changed",
			self.windowModeChanged,
		)

	def windowModeChanged(self, _combo: gtk.ComboBoxText | None = None) -> None:
		ogino = windowModeNames[self.windowModeCombo.get_active()] == "oginoKnaus"
		self.minCycleSpin.set_sensitive(ogino)
		self.maxCycleSpin.set_sensitive(ogino)

	def updateWidget(self) -> None:
		NormalWidgetClass.updateWidget(self)
		group = self.group
		self.personNameEntry.set_text(group.personName)
		self.cycleLengthSpin.set_value(group.cycleLength)
		self.cycleLengthAutoCheck.set_active(group.cycleLengthAuto)
		self.lutealPhaseSpin.set_value(group.lutealPhase)
		self.periodLengthSpin.set_value(group.periodLength)
		self.windowModeCombo.set_active(
			windowModeNames.index(group.windowMode),
		)
		self.minCycleSpin.set_value(group.minCycle)
		self.maxCycleSpin.set_value(group.maxCycle)
		self.showPeriodPredictCheck.set_active(group.showPeriodPredict)
		self.showFertileCheck.set_active(group.showFertile)
		self.showOvulationCheck.set_active(group.showOvulation)
		self.viabilityFactorInput.set_value(group.viabilityFactor)
		self.windowModeChanged()

	def updateVars(self) -> None:
		NormalWidgetClass.updateVars(self)
		group = self.group
		group.personName = self.personNameEntry.get_text()
		group.cycleLength = self.cycleLengthSpin.get_value()
		group.cycleLengthAuto = self.cycleLengthAutoCheck.get_active()
		group.lutealPhase = self.lutealPhaseSpin.get_value()
		group.periodLength = self.periodLengthSpin.get_value()
		group.windowMode = windowModeNames[self.windowModeCombo.get_active()]
		group.minCycle = self.minCycleSpin.get_value()
		group.maxCycle = self.maxCycleSpin.get_value()
		group.showPeriodPredict = self.showPeriodPredictCheck.get_active()
		group.showFertile = self.showFertileCheck.get_active()
		group.showOvulation = self.showOvulationCheck.get_active()
		group.viabilityFactor = self.viabilityFactorInput.get_value()
