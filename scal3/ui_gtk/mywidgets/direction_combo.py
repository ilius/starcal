from scal3.locale_man import tr as _

from scal3.ui_gtk import *


class DirectionComboBox(gtk.ComboBox):
	keys = ['ltr', 'rtl', 'auto']
	descs = [
		_('Left to Right'),
		_('Right to Left'),
		_('Auto'),
	]

	def __init__(self):
		ls = gtk.ListStore(str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, 'text', 0)
		###
		for d in self.descs:
			ls.append([d])
		self.set_active(0)

	def getValue(self):
		return self.keys[self.get_active()]

	def setValue(self, value):
		self.set_active(self.keys.index(value))
