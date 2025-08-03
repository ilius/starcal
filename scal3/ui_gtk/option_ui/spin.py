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

from __future__ import annotations

from scal3 import logger

log = logger.get()

import typing

from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.option_ui.base import OptionUI
from scal3.ui_gtk.utils import newAlignLabel

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import Option

__all__ = ["FloatSpinOptionUI", "IntSpinOptionUI"]


class IntSpinOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[int],
		bounds: tuple[int, int],
		step: int = 0,
		label: str = "",
		labelSizeGroup: gtk.SizeGroup | None = None,
		unitLabel: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		minim, maxim = bounds
		self.option = option
		self._onChangeFunc = onChangeFunc
		# --
		spinb = IntSpinButton(minim, maxim, step=step)
		self._spinb = spinb

		if labelSizeGroup and not label:
			raise ValueError("labelSizeGroup= is passed without label=")

		if label or unitLabel:
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=3)
			pack(hbox, newAlignLabel(sgroup=labelSizeGroup, label=label))
			pack(hbox, spinb)
			if unitLabel:
				pack(hbox, gtk.Label(label=unitLabel))
			self._widget = hbox
		else:
			self._widget = spinb

		if live:
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			spinb.connect("changed", self.onChange)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> int:
		return self._spinb.get_value()

	def set(self, value: int) -> None:
		self._spinb.set_value(value)

	# FIXME: updateWidget is triggering onChange func, can we avoid that?
	def onChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class FloatSpinOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[float],
		bounds: tuple[float, float],
		digits: int = 1,
		step: float = 0,
		label: str = "",
		labelSizeGroup: gtk.SizeGroup | None = None,
		unitLabel: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		minim, maxim = bounds
		self.option = option
		self._onChangeFunc = onChangeFunc
		# --
		spinb = FloatSpinButton(minim, maxim, digits, step=step)
		self._spinb = spinb

		if labelSizeGroup and not label:
			raise ValueError("labelSizeGroup= is passed without label=")

		if label or unitLabel:
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=3)
			pack(hbox, newAlignLabel(sgroup=labelSizeGroup, label=label))
			pack(hbox, spinb)
			if unitLabel:
				pack(hbox, gtk.Label(label=unitLabel))
			self._widget = hbox
		else:
			self._widget = spinb

		if live:
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			spinb.connect("changed", self.onChange)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> float:
		return self._spinb.get_value()

	def set(self, value: float) -> None:
		self._spinb.set_value(value)

	# FIXME: updateWidget is triggering onChange func, can we avoid that?
	def onChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()
