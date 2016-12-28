from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *

from scal3.ui_gtk.event.group.vcsEpochBase \
	import VcsEpochBaseWidgetClass as BaseWidgetClass


class WidgetClass(BaseWidgetClass):
	def __init__(self, group):
		BaseWidgetClass.__init__(self, group)
		####
		hbox = gtk.HBox()
		label = gtk.Label(_('Commit Description'))
		label.set_alignment(0, 0.5)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		##
		self.statCheck = gtk.CheckButton(_('Stat'))
		pack(hbox, self.statCheck)
		##
		pack(hbox, gtk.Label('   '))
		##
		self.authorCheck = gtk.CheckButton(_('Author'))
		pack(hbox, self.authorCheck)
		##
		pack(hbox, gtk.Label('   '))
		##
		self.shortHashCheck = gtk.CheckButton(_('Short Hash'))
		pack(hbox, self.shortHashCheck)
		##
		pack(self, hbox)

	def updateWidget(self):
		BaseWidgetClass.updateWidget(self)
		self.authorCheck.set_active(self.group.showAuthor)
		self.shortHashCheck.set_active(self.group.showShortHash)
		self.statCheck.set_active(self.group.showStat)

	def updateVars(self):
		BaseWidgetClass.updateVars(self)
		self.group.showAuthor = self.authorCheck.get_active()
		self.group.showShortHash = self.shortHashCheck.get_active()
		self.group.showStat = self.statCheck.get_active()
