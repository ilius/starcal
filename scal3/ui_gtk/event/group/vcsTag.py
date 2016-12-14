from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.event.group.vcsEpochBase import VcsEpochBaseWidgetClass as BaseWidgetClass


class WidgetClass(BaseWidgetClass):
	def __init__(self, group):
		BaseWidgetClass.__init__(self, group)
		####
		hbox = gtk.HBox()
		label = gtk.Label(_('Tag Description'))
		label.set_alignment(0, 0.5)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		##
		self.statCheck = gtk.CheckButton(_('Stat'))
		pack(hbox, self.statCheck)
		##
		pack(self, hbox)
	def updateWidget(self):
		BaseWidgetClass.updateWidget(self)
		self.statCheck.set_active(self.group.showStat)
	def updateVars(self):
		BaseWidgetClass.updateVars(self)
		self.group.showStat = self.statCheck.get_active()






