from scal3.cal_types import calTypes
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import IdComboBox

class CalTypeCombo(IdComboBox):
	def __init__(self):## , showInactive=True FIXME
		ls = gtk.ListStore(int, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, 'text', 1)
		###
		for i, mod in calTypes.iterIndexModule():
			ls.append([i, _(mod.desc)])

