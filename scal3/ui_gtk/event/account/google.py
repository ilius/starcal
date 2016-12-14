# -*- coding: utf-8 -*-

from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk.event.account import *

class WidgetClass(BaseWidgetClass):
	def __init__(self, account):
		BaseWidgetClass.__init__(self, account)
		#####
		hbox = gtk.HBox()
		label = gtk.Label(_('Email'))
		label.set_alignment(0, 0.5)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.emailEntry = gtk.Entry()
		pack(hbox, self.emailEntry, 1, 1)
		pack(self, hbox)
	def updateWidget(self):
		BaseWidgetClass.updateWidget(self)
		self.emailEntry.set_text(self.account.email)
	def updateVars(self):
		BaseWidgetClass.updateVars(self)
		self.account.email = self.emailEntry.get_text()

