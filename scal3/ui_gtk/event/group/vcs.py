#!/usr/bin/env python3
from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *

from scal3.ui_gtk.event.group.vcsEpochBase \
	import VcsEpochBaseWidgetClass as BaseWidgetClass


class WidgetClass(BaseWidgetClass):
	def __init__(self, group):
		BaseWidgetClass.__init__(self, group)
		####
		hbox = HBox()
		label = gtk.Label(label=_("Commit Description"))
		label.set_xalign(0)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		##
		self.statCheck = gtk.CheckButton(label=_("Stat"))
		pack(hbox, self.statCheck)
		##
		pack(hbox, gtk.Label(label="   "))
		##
		self.authorCheck = gtk.CheckButton(label=_("Author"))
		pack(hbox, self.authorCheck)
		##
		pack(hbox, gtk.Label(label="   "))
		##
		self.shortHashCheck = gtk.CheckButton(label=_("Short Hash"))
		pack(hbox, self.shortHashCheck)
		##
		hbox.show_all()
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
