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
from scal3.ui_gtk.option_ui.base import OptionUI

if typing.TYPE_CHECKING:
	from collections.abc import Sequence

	from scal3.option import Option


__all__ = [
	"ModuleOptionButton",
	"ModuleOptionUI",
]


# rawOption tuple (old legacy design)
# (option: Option, bool,     CHECKBUTTON_TEXT)                 # CheckButton
# (option: Option, list,     LABEL_TEXT, (ITEM1, ITEM2, ...))  # ComboBox
# (option: Option, int,      LABEL_TEXT, MIN, MAX)             # SpinButton
# (option: Option, float,    LABEL_TEXT, MIN, MAX, DIGITS)     # SpinButton
def ModuleOptionUI(
	rawOption: tuple,
	spacing: int = 0,
) -> OptionUI:
	option = rawOption[0]
	t = rawOption[1]
	if t == "bool":
		return CheckModuleOptionUI(
			option=option,
			label=rawOption[2],
			spacing=spacing,
		)
	if t == "list":
		return BasicComboModuleOptionUI(
			option=option,
			label=rawOption[2],
			values=rawOption[3],
			spacing=spacing,
		)
	if t == "dict":
		return AdvancedComboModuleOptionUI(
			option=option,
			label=rawOption[2],
			values=rawOption[3],
			spacing=spacing,
		)
	# if t is "int":
	# 	return IntSpinModuleOptionUI(
	# 		option=option,
	# 		label=rawOption[2],
	# 		minim=rawOption[3],
	# 		maxim=rawOption[4],
	# 		spacing=spacing,
	# 	)
	# if t is "float":
	# 	return FloatSpinModuleOptionUI(
	# 		option=option,
	# 		label=rawOption[2],
	# 		minim=rawOption[3],
	# 		maxim=rawOption[4],
	# 		spacing=spacing,
	# 	)
	raise RuntimeError(f"bad option type {t!r}")


class CheckModuleOptionUI:
	def __init__(
		self,
		option: Option,
		label: str,
		spacing: int = 0,
	) -> None:
		self.option = option
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		w = gtk.CheckButton(label=_(label))
		self.get = w.get_active
		self.set = w.set_active
		pack(hbox, w)
		self._widget = hbox

	def updateVar(self) -> None:
		self.option.v = self.get()

	def updateWidget(self) -> None:
		self.set(self.option.v)

	def getWidget(self) -> gtk.Widget:
		return self._widget


# class IntSpinModuleOptionUI:
# 	def __init__(
# 		self,
# 		option: Option,
# 		label: str,
# 		minim: int,
# 		maxim: int,
# 		spacing: int = 0,
# 	) -> None:
# from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
# 		self.option = option
# 		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
# 		pack(hbox, gtk.Label(label=_(label)))
# 		w = IntSpinButton(minim, maxim)
# 		self.get = w.get_active
# 		self.set = w.set_active
# 		pack(hbox, w)
# 		self._widget = hbox

# 	def updateVar(self) -> None:
# 		self.option.v = self.get()

# 	def updateWidget(self) -> None:
# 		self.set(self.option.v)

# 	def getWidget(self) -> gtk.Widget:
# 		return self._widget


# class FloatSpinModuleOptionUI:
# 	def __init__(
# 		self,
# 		option: Option,
# 		label: str,
# 		minim: float,
# 		maxim: float,
# 		spacing: int = 0,
# 	) -> None:
# from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
# 		self.option = option
# 		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
# 		pack(hbox, gtk.Label(label=_(label)))
# 		w = FloatSpinButton(minim, maxim)
# 		self.get = w.get_active
# 		self.set = w.set_active
# 		pack(hbox, w)
# 		self._widget = hbox

# 	def updateVar(self) -> None:
# 		self.option.v = self.get()

# 	def updateWidget(self) -> None:
# 		self.set(self.option.v)

# 	def getWidget(self) -> gtk.Widget:
# 		return self._widget


class BasicComboModuleOptionUI:
	def __init__(
		self,
		option: Option,
		label: str,
		values: Sequence[str],
		spacing: int = 0,
	) -> None:
		self.option = option
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, gtk.Label(label=_(label)))
		w = gtk.ComboBoxText()  # or RadioButton
		for s in values:
			w.append_text(_(s))
		self.get = w.get_active
		self.set = w.set_active
		pack(hbox, w)
		self._widget = hbox

	def updateVar(self) -> None:
		self.option.v = self.get()

	def updateWidget(self) -> None:
		self.set(self.option.v)

	def getWidget(self) -> gtk.Widget:
		return self._widget


class AdvancedComboModuleOptionUI:
	def __init__(
		self,
		option: Option,
		label: str,
		values: dict[str, str],
		spacing: int = 0,
	) -> None:
		self.option = option
		self.keys = list(values)
		descs = list(values.values())
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, gtk.Label(label=_(label)))
		w = gtk.ComboBoxText()
		self.combo = w
		for s in descs:
			w.append_text(_(s))
		pack(hbox, w)
		self._widget = hbox

	def get(self) -> str:
		return self.keys[self.combo.get_active()]

	def set(self, key: str) -> None:
		index = self.keys.index(key)
		self.combo.set_active(index)

	def updateVar(self) -> None:
		self.option.v = self.get()

	def updateWidget(self) -> None:
		self.set(self.option.v)

	def getWidget(self) -> gtk.Widget:
		return self._widget


# ("button", LABEL, CLICKED_MODULE_NAME, CLICKED_FUNCTION_NAME)
class ModuleOptionButton(OptionUI):
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
