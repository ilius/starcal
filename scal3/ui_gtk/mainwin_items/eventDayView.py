from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *

from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.event.occurrence_view import DayOccurrenceView


#@registerSignals
class CalObj(DayOccurrenceView, CustomizableCalObj):  # FIXME
	def __init__(self):
		DayOccurrenceView.__init__(self)
		self.maxHeight = ui.eventViewMaxHeight

	def optionsWidgetCreate(self):
		from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
		if self.optionsWidget:
			return
		self.optionsWidget = gtk.HBox()
		###
		hbox = gtk.HBox()
		spin = IntSpinButton(1, 9999)
		spin.set_value(ui.eventViewMaxHeight)
		spin.connect("changed", self.heightSpinChanged)
		pack(hbox, gtk.Label(_("Maximum Height")))
		pack(hbox, spin)
		pack(self.optionsWidget, hbox)
		###
		self.optionsWidget.show_all()

	def heightSpinChanged(self, spin):
		v = spin.get_value()
		self.maxHeight = ui.eventViewMaxHeight = v
		self.queue_resize()
