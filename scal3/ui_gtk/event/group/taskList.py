#!/usr/bin/env python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass


class WidgetClass(NormalWidgetClass):
	def __init__(self, group):
		NormalWidgetClass.__init__(self, group)
		###
		hbox = HBox()
		label = gtk.Label(label=_("Default Task Duration"))
		label.set_xalign(0)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.defaultDurationBox = common.DurationInputBox()
		pack(hbox, self.defaultDurationBox)
		pack(self, hbox)
		hbox.show_all()

	def updateWidget(self):## FIXME
		NormalWidgetClass.updateWidget(self)
		self.defaultDurationBox.setDuration(*self.group.defaultDuration)

	def updateVars(self):
		NormalWidgetClass.updateVars(self)
		self.group.defaultDuration = self.defaultDurationBox.getDuration()
