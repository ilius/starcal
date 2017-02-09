from scal3.cal_types import calTypes
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import IdComboBox


class CalTypeCombo(IdComboBox):
	def __init__(self):## , showInactive=True FIXME
		ls = gtk.ListStore(int, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		self.set_row_separator_func(self._is_separator, None)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, "text", 1)
		###
		for i, mod in calTypes.iterIndexModuleActive():
			ls.append([i, _(mod.desc)])
		ls.append([-1, None])  # separator
		# None is converted to 0 for `int` column, so we use -1
		for i, mod in calTypes.iterIndexModuleInactive():
			ls.append([i, _(mod.desc)])

	def _is_separator(self, model, rowIter, data):
		return model.get_value(rowIter, 1) is None
