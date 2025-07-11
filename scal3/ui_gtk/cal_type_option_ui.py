#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.
# mypy: ignore-errors

from __future__ import annotations

from scal3 import logger

log = logger.get()

import typing
from typing import Any

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton

if typing.TYPE_CHECKING:
	from scal3.option import Option


__all__ = [
	"ModuleOptionButton",
	"ModuleOptionUI",
]


# (VAR_NAME, bool,     CHECKBUTTON_TEXT)                 # CheckButton
# (VAR_NAME, list,     LABEL_TEXT, (ITEM1, ITEM2, ...))  # ComboBox
# (VAR_NAME, int,      LABEL_TEXT, MIN, MAX)             # SpinButton
# (VAR_NAME, float,    LABEL_TEXT, MIN, MAX, DIGITS)     # SpinButton
class ModuleOptionUI:
	@classmethod
	def valueString(cls, value: Any) -> str:
		return str(value)

	def __init__(
		self,
		option: Option,
		rawOption: tuple,
		spacing: int = 0,
	) -> None:
		self.option = option
		t = rawOption[1]
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		w: gtk.Widget
		if t is bool:
			w = gtk.CheckButton(label=_(rawOption[2]))
			self.get = w.get_active
			self.set = w.set_active
		elif t is list:
			pack(hbox, gtk.Label(label=_(rawOption[2])))
			w = gtk.ComboBoxText()  # or RadioButton
			for s in rawOption[3]:
				w.append_text(_(s))
			self.get = w.get_active
			self.set = w.set_active
		elif t is int:
			pack(hbox, gtk.Label(label=_(rawOption[2])))
			w = IntSpinButton(rawOption[3], rawOption[4])
			self.get = w.get_value
			self.set = w.set_value
		elif t is float:
			pack(hbox, gtk.Label(label=_(rawOption[2])))
			w = FloatSpinButton(rawOption[3], rawOption[4], rawOption[5])
			self.get = w.get_value
			self.set = w.set_value
		else:
			raise RuntimeError(f"bad option type {t!r}")
		pack(hbox, w)
		self._widget = hbox
		# ----

	def updateVar(self) -> None:
		self.option.v = self.get()

	def updateWidget(self) -> None:
		self.set(self.option.v)

	def getWidget(self) -> gtk.Widget:
		return self._widget


# ("button", LABEL, CLICKED_MODULE_NAME, CLICKED_FUNCTION_NAME)
class ModuleOptionButton:
	@classmethod
	def valueString(cls, value: Any) -> str:
		return str(value)

	def __init__(self, opt: tuple) -> None:
		funcName = opt[2]
		clickedFunc = getattr(
			__import__(
				f"scal3.ui_gtk.{opt[1]}",
				fromlist=[funcName],
			),
			funcName,
		)
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		button = gtk.Button(label=_(opt[0]))
		button.connect("clicked", clickedFunc)
		pack(hbox, button)
		self._widget = hbox

	def get(self) -> Any:  # noqa: PLR6301
		return None

	def updateVar(self) -> None:
		pass

	def updateWidget(self) -> None:
		pass

	def getWidget(self) -> gtk.Widget:
		return self._widget
