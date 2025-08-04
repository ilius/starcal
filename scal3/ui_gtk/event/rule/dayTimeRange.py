from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton


class WidgetClass(gtk.Box):
	def __init__(self, rule):
		self.rule = rule
		###
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		###
		self.startTbox = TimeButton()
		self.endTbox = TimeButton()
		pack(self, self.startTbox)
		pack(self, gtk.Label(label=" " + _("To", ctx="time range") + " "))
		pack(self, self.endTbox)

	def updateWidget(self):
		self.startTbox.set_value(self.rule.dayTimeStart)
		self.endTbox.set_value(self.rule.dayTimeEnd)

	def updateVars(self):
		self.rule.dayTimeStart = self.startTbox.get_value()
		self.rule.dayTimeEnd = self.endTbox.get_value()
