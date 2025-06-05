from __future__ import annotations

from typing import Any

from scal3.cal_types import calTypes
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk
from scal3.ui_gtk.utils import IdComboBox

__all__ = ["CalTypeCombo"]


class CalTypeCombo(IdComboBox):
	def __init__(self, hasDefault: bool = False) -> None:  # , showInactive=True FIXME
		ls = gtk.ListStore(int, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		self.set_row_separator_func(self._is_separator, None)
		# ---
		cell = gtk.CellRendererText()
		self.pack_start(cell, expand=True)
		self.add_attribute(cell, "text", 1)
		# ---
		# None is converted to 0 for `int` column, so we use -1 and -2
		if hasDefault:
			ls.append([-1, _("Default Calendar Type")])
			ls.append([-2, None])  # separator

		for i, mod in calTypes.iterIndexModuleActive():
			ls.append([i, _(mod.desc, ctx="calendar")])
		ls.append([-2, None])  # separator

		for i, mod in calTypes.iterIndexModuleInactive():
			ls.append([i, _(mod.desc, ctx="calendar")])

	@staticmethod
	def _is_separator(model: gtk.TreeModel, rowIter: gtk.TreeIter, _data: Any) -> bool:
		return model.get_value(rowIter, 1) is None
