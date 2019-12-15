#!/usr/bin/env python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *

"""
class MultiValueRule(gtk.Box):
	def __init__(self, rule, ValueWidgetClass):
		from scal3.ui_gtk.utils import labelImageButton
		self.rule = rule
		self.ValueWidgetClass = ValueWidgetClass
		##
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.widgetsBox = HBox()
		pack(self, self.widgetsBox)
		##
		self.removeButton = labelImageButton(
			label=_("_Remove"),
			imageName="list-remove.svg",
		)
		self.removeButton.connect("clicked", self.removeLastWidget)
		##
		self.removeButton.hide()## FIXME

	def removeLastWidget(self, obj=None):

	def addWidget(self, obj=None):
		widget = self.ValueWidgetClass()
"""
