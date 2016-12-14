from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.event.group.vcsBase import VcsBaseWidgetClass


class VcsEpochBaseWidgetClass(VcsBaseWidgetClass):
	def __init__(self, group):
		VcsBaseWidgetClass.__init__(self, group)
		######
		hbox = gtk.HBox()
		label = gtk.Label(_('Show Seconds'))
		label.set_alignment(0, 0.5)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		pack(hbox, label)
		self.showSecondsCheck = gtk.CheckButton('')
		pack(hbox, self.showSecondsCheck)
		pack(self, hbox)
	def updateWidget(self):
		VcsBaseWidgetClass.updateWidget(self)
		self.showSecondsCheck.set_active(self.group.showSeconds)
	def updateVars(self):
		VcsBaseWidgetClass.updateVars(self)
		self.group.showSeconds = self.showSecondsCheck.get_active()

