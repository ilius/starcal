from __future__ import annotations

from scal3.core import jd_to
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event.group.base import BaseWidgetClass
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton

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
		pack(self.mainBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("End"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
		pack(self.mainBox, hbox)

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

	def updateVars(self) -> None:
		BaseWidgetClass.updateVars(self)
		self.group.startJd = self.startDateInput.get_jd(self.group.calType)
		self.group.endJd = self.endDateInput.get_jd(self.group.calType)

	def calTypeComboChanged(
		self,
		widget: gtk.Widget | None = None,  # noqa: ARG002
	) -> None:
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		self.startDateInput.changeCalType(self.group.calType, newCalType)
		self.endDateInput.changeCalType(self.group.calType, newCalType)
		self.group.calType = newCalType
