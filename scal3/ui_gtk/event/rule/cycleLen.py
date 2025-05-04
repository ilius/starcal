from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def __init__(self, rule) -> None:
		self.rule = rule
		# ---
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		spin = IntSpinButton(0, 9999)
		pack(self, spin)
		self.spin = spin
		# --
		pack(self, gtk.Label(label=" " + _("days and") + " "))
		tbox = TimeButton()
		pack(self, tbox)
		self.tbox = tbox

	def updateWidget(self) -> None:
		self.spin.set_value(self.rule.days)
		self.tbox.set_value(self.rule.extraTime)

	def updateVars(self) -> None:
		self.rule.days = self.spin.get_value()
		self.rule.extraTime = self.tbox.get_value()
