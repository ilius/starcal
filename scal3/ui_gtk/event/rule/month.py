from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.utils import set_tooltip

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def __init__(self, rule) -> None:
		self.rule = rule
		# ---
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		# ---
		self.buttons = []
		calType = self.rule.getCalType()
		for i in range(12):
			b = gtk.ToggleButton(label=_(i + 1))
			set_tooltip(b, locale_man.getMonthName(calType, i + 1))
			pack(self, b)
			self.buttons.append(b)

	def updateWidget(self) -> None:
		monthList = self.rule.getValuesPlain()
		for i in range(12):
			self.buttons[i].set_active((i + 1) in monthList)

	def updateVars(self) -> None:
		monthList = [i + 1 for i in range(12) if self.buttons[i].get_active()]
		self.rule.setValuesPlain(monthList)

	def changeCalType(self, calType) -> None:
		if calType == self.rule.getCalType():
			return
		for i in range(12):
			set_tooltip(
				self.buttons[i],
				locale_man.getMonthName(calType, i + 1),
			)
