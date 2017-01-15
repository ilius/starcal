from os.path import join

from scal3.path import rootDir
from scal3.json_utils import jsonToOrderedData
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *


class TimeZoneComboBoxEntry(gtk.HBox):
	def __init__(self):
		from natz.tree import getZoneInfoTree
		gtk.HBox.__init__(self)
		model = gtk.TreeStore(str, bool)
		self.c = gtk.ComboBoxText.new_with_entry()
		pack(self, self.c, 1, 1)
		#gtk.ComboBoxText.__init__(self)
		self.c.set_model(model)
		self.c.set_entry_text_column(0)
		first_cell = self.c.get_cells()[0]
		self.c.add_attribute(first_cell, "text", 0)
		self.c.add_attribute(first_cell, "sensitive", 1)
		self.c.connect("changed", self.onChanged)
		child = self.c.get_child()
		child.set_text(str(core.localTz))
		#self.set_text(str(core.localTz)) ## FIXME
		###
		self.get_text = child.get_text
		#self.get_text = self.c.get_active_text ## FIXME
		self.set_text = child.set_text
		#####
		recentIter = model.append(None, [
			_("Recent..."),
			False,
		])
		for tz_name in ui.localTzHist:
			model.append(recentIter, [tz_name, True])
		###
		self.appendOrderedDict(
			None,
			getZoneInfoTree(),
		)

	def appendOrderedDict(self, parentIter, dct):
		model = self.c.get_model()
		for key, value in dct.items():
			if isinstance(value, dict):
				itr = model.append(parentIter, [key, False])
				self.appendOrderedDict(itr, value)
			else:
				itr = model.append(parentIter, [key, True])

	def onChanged(self, widget):
		model = self.c.get_model()
		itr = self.c.get_active_iter()
		if itr is None:
			return
		path = model.get_path(itr)
		parts = []
		if path[0] == 0:
			text = model.get(itr, 0)[0]
		else:
			for i in range(len(path)):
				parts.append(
					model.get(
						model.get_iter(path[:i + 1]),
						0,
					)[0]
				)
			text = "/".join(parts)
		self.set_text(text)
