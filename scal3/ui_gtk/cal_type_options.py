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

from typing import TYPE_CHECKING, Any

from scal3 import logger
from scal3.option import ItemOption, ListOption, Option

log = logger.get()

from scal3.cal_types import calTypes
from scal3.locale_man import langHasUppercase
from scal3.locale_man import tr as _
from scal3.ui.font import getOptionsFont
from scal3.ui_gtk import gtk, pack

if TYPE_CHECKING:
	from scal3.ui.pytypes import (
		DayCalTypeDayOptionsDict,
		DayCalTypeWMOptionsDict,
	)
	from scal3.ui_gtk.cal_base import CalBase

__all__ = [
	"DayNumListOptionsWidget",
	"DayNumOptionsWidget",
	"MonthNameListOptionsWidget",
	"WeekDayNameOptionsWidget",
]


class XAlignComboBox(gtk.ComboBoxText):
	def __init__(self) -> None:
		gtk.ComboBoxText.__init__(self)
		# ---
		self.append_text(_("Left"))
		self.append_text(_("Center"))
		self.append_text(_("Right"))
		self.set_active(1)

	def get(self) -> str | None:
		index = self.get_active()
		if index == 0:
			return "left"
		if index == 1:
			return "center"
		if index == 2:
			return "right"
		log.error(f"XAlignComboBox: unexpected {index = }")
		return None

	def set(self, value: str) -> None:
		if value == "left":
			self.set_active(0)
		elif value == "center":
			self.set_active(1)
		elif value == "right":
			self.set_active(2)
		else:
			self.set_active(1)


class YAlignComboBox(gtk.ComboBoxText):
	def __init__(self) -> None:
		gtk.ComboBoxText.__init__(self)
		# ---
		self.append_text(_("Top"))
		self.append_text(_("Center"))
		self.append_text(_("Buttom"))
		self.set_active(1)

	def get(self) -> str | None:
		index = self.get_active()
		if index == 0:
			return "top"
		if index == 1:
			return "center"
		if index == 2:
			return "buttom"
		log.info(f"YAlignComboBox: unexpected {index = }")
		return None

	def set(self, value: str) -> None:
		if value == "top":
			self.set_active(0)
		elif value == "center":
			self.set_active(1)
		elif value == "buttom":
			self.set_active(2)
		else:
			self.set_active(1)


# only used for Day Cal so far
class DayNumOptionsWidget(gtk.Box):
	def __init__(
		self,
		options: Option[DayCalTypeDayOptionsDict],
		cal: CalBase,
		sgroupLabel: gtk.SizeGroup | None = None,
		desc: str | None = None,
		hasEnable: bool = False,
		enableTitleLabel: str = "",
		useFrame: bool = False,
	) -> None:
		from scal3.ui_gtk.mywidgets import MyColorButton, MyFontButton
		from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton

		if desc is None:
			raise ValueError("desc is None")
		# ---
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL, spacing=10)
		# ---
		self.set_border_width(5)
		self.options = options
		self.cal = cal
		self.hasEnable = hasEnable
		# ----
		if sgroupLabel is None:
			sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ----
		if not enableTitleLabel and hasEnable:
			enableTitleLabel = _("Enable")
		if hasEnable:
			self.enableCheck = gtk.CheckButton(label=enableTitleLabel)
		# ---
		vbox: gtk.Box = self
		if useFrame:
			frame = gtk.Frame()
			vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
			vbox.set_border_width(5)
			frame.add(vbox)
			pack(self, frame)
			if hasEnable:
				frame.set_label_widget(self.enableCheck)
			else:
				frame.set_label(enableTitleLabel)
		elif hasEnable:
			pack(vbox, self.enableCheck)
		# ----
		self.set_border_width(5)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Position") + ": ")
		pack(hbox, label)
		sgroupLabel.add_widget(label)
		spin = FloatSpinButton(-999, 999, 1)
		self.spinX = spin
		pack(hbox, spin)
		pack(hbox, gtk.Label(), 1, 1)
		spin = FloatSpinButton(-999, 999, 1)
		self.spinY = spin
		pack(hbox, spin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Alignment") + ": ")
		pack(hbox, label)
		sgroupLabel.add_widget(label)
		# --
		self.xalignCombo = XAlignComboBox()
		pack(hbox, self.xalignCombo)
		# --
		self.yalignCombo = YAlignComboBox()
		pack(hbox, self.yalignCombo)
		# --
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Font") + ": ")
		pack(hbox, label)
		sgroupLabel.add_widget(label)
		# --
		fontb = MyFontButton()
		self.fontb = fontb
		# --
		colorb = MyColorButton()
		self.colorb = colorb
		# --
		pack(hbox, colorb)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, fontb)
		pack(vbox, hbox)
		# ----
		self.localizeCheck = gtk.CheckButton(label=_("Localize"))
		pack(vbox, self.localizeCheck)
		# ----
		self.set(options.v)
		# ----
		self.spinX.connect("changed", self.onChange)
		self.spinY.connect("changed", self.onChange)
		fontb.connect("font-set", self.onChange)
		colorb.connect("color-set", self.onChange)
		if hasEnable:
			self.enableCheck.connect("clicked", self.onChange)
		self.xalignCombo.connect("changed", self.onChange)
		self.yalignCombo.connect("changed", self.onChange)
		self.localizeCheck.connect("clicked", self.onChange)

	def get(self) -> DayCalTypeDayOptionsDict:
		enable = True
		if self.hasEnable:
			enable = self.enableCheck.get_active()
		return {
			"enable": enable,
			"pos": (
				self.spinX.get_value(),
				self.spinY.get_value(),
			),
			"font": self.fontb.getFont(),
			"color": self.colorb.getRGBA(),
			"xalign": self.xalignCombo.get() or "center",
			"yalign": self.yalignCombo.get() or "center",
			"localize": self.localizeCheck.get_active(),
		}

	def set(self, options: DayCalTypeDayOptionsDict) -> None:
		self.spinX.set_value(options["pos"][0])
		self.spinY.set_value(options["pos"][1])
		font = getOptionsFont(options)
		assert font is not None
		self.fontb.setFont(font)
		self.colorb.setRGBA(options["color"])
		if self.hasEnable:
			self.enableCheck.set_active(options.get("enable", True))
		self.xalignCombo.set(options.get("xalign", "center"))
		self.yalignCombo.set(options.get("yalign", "center"))
		self.localizeCheck.set_active(options.get("localize", False))

	def onChange(self, _w: gtk.Widget | None = None, _ge: Any = None) -> None:
		self.options.v = self.get()
		self.cal.w.queue_draw()

	def setFontPreviewText(self, text: str) -> None:
		self.fontb.set_property("preview-text", text)


class DayNumListOptionsWidget(DayNumOptionsWidget):
	def __init__(
		self,
		options: ListOption[DayCalTypeDayOptionsDict],
		index: int,
		calType: int,
		cal: CalBase,
		sgroupLabel: gtk.SizeGroup | None = None,
		hasEnable: bool = False,
		enableTitleLabel: str = "",
		useFrame: bool = False,
	) -> None:
		self.index = index
		# ----
		module = calTypes[calType]
		if module is None:
			raise RuntimeError(f"cal type '{calType}' not found")
		DayNumOptionsWidget.__init__(
			self,
			options=ItemOption(options, index),
			cal=cal,
			sgroupLabel=sgroupLabel,
			desc=_(module.desc, ctx="calendar"),
			hasEnable=hasEnable,
			enableTitleLabel=enableTitleLabel,
			useFrame=useFrame,
		)


# only used for Day Cal so far
class _WeekMonthOptionsWidget(gtk.Box):
	def __init__(
		self,
		options: Option[DayCalTypeWMOptionsDict],
		cal: CalBase,
		sgroupLabel: gtk.SizeGroup | None = None,
		desc: str | None = None,
		hasEnable: bool = False,
		enableTitleLabel: str = "",
		useFrame: bool = False,
	) -> None:
		from scal3.ui_gtk.mywidgets import MyColorButton, MyFontButton
		from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton

		if desc is None:
			raise ValueError("desc is None")
		# ---
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL, spacing=10)
		# ---
		self.set_border_width(5)
		self.options = options
		self.cal = cal
		self.hasEnable = hasEnable
		# ----
		if sgroupLabel is None:
			sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ----
		if not enableTitleLabel and hasEnable:
			enableTitleLabel = _("Enable")
		if hasEnable:
			self.enableCheck = gtk.CheckButton(label=enableTitleLabel)
		# ---
		vbox: gtk.Box = self
		if useFrame:
			frame = gtk.Frame()
			vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
			vbox.set_border_width(5)
			frame.add(vbox)
			pack(self, frame)
			if hasEnable:
				frame.set_label_widget(self.enableCheck)
			else:
				frame.set_label(enableTitleLabel)
		elif hasEnable:
			pack(vbox, self.enableCheck)
		# ----
		self.set_border_width(5)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Position") + ": ")
		pack(hbox, label)
		sgroupLabel.add_widget(label)
		spin = FloatSpinButton(-999, 999, 1)
		self.spinX = spin
		pack(hbox, spin)
		pack(hbox, gtk.Label(), 1, 1)
		spin = FloatSpinButton(-999, 999, 1)
		self.spinY = spin
		pack(hbox, spin)
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Alignment") + ": ")
		pack(hbox, label)
		sgroupLabel.add_widget(label)
		# --
		self.xalignCombo = XAlignComboBox()
		pack(hbox, self.xalignCombo)
		# --
		self.yalignCombo = YAlignComboBox()
		pack(hbox, self.yalignCombo)
		# --
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Font") + ": ")
		pack(hbox, label)
		sgroupLabel.add_widget(label)
		# --
		fontb = MyFontButton()
		self.fontb = fontb
		# --
		colorb = MyColorButton()
		self.colorb = colorb
		# --
		pack(hbox, colorb)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, fontb)
		pack(vbox, hbox)
		# ----
		self.abbreviateCheck = gtk.CheckButton(label=_("Abbreviate"))
		pack(vbox, self.abbreviateCheck)
		self.uppercaseCheck = gtk.CheckButton(label=_("Uppercase"))
		if langHasUppercase:
			pack(vbox, self.uppercaseCheck)
		# ----
		self.set(options.v)
		# ----
		self.spinX.connect("changed", self.onChange)
		self.spinY.connect("changed", self.onChange)
		fontb.connect("font-set", self.onChange)
		colorb.connect("color-set", self.onChange)
		if hasEnable:
			self.enableCheck.connect("clicked", self.onChange)
		self.xalignCombo.connect("changed", self.onChange)
		self.yalignCombo.connect("changed", self.onChange)
		self.abbreviateCheck.connect("clicked", self.onChange)
		self.uppercaseCheck.connect("clicked", self.onChange)

	def get(self) -> DayCalTypeWMOptionsDict:
		enable = True
		if self.hasEnable:
			enable = self.enableCheck.get_active()
		return {
			"enable": enable,
			"pos": (
				self.spinX.get_value(),
				self.spinY.get_value(),
			),
			"font": self.fontb.getFont(),
			"color": self.colorb.getRGBA(),
			"xalign": self.xalignCombo.get() or "center",
			"yalign": self.yalignCombo.get() or "center",
			"abbreviate": self.abbreviateCheck.get_active(),
			"uppercase": self.uppercaseCheck.get_active(),
		}

	def set(self, options: DayCalTypeWMOptionsDict) -> None:
		self.spinX.set_value(options["pos"][0])
		self.spinY.set_value(options["pos"][1])
		font = getOptionsFont(options)
		assert font is not None
		self.fontb.setFont(font)
		self.colorb.setRGBA(options["color"])
		if self.hasEnable:
			self.enableCheck.set_active(options.get("enable", True))
		self.xalignCombo.set(options.get("xalign", "center"))
		self.yalignCombo.set(options.get("yalign", "center"))
		self.abbreviateCheck.set_active(options.get("abbreviate", False))
		self.uppercaseCheck.set_active(options.get("uppercase", False))

	def onChange(self, _w: gtk.Widget | None = None, _ge: Any = None) -> None:
		self.options.v = self.get()
		self.cal.w.queue_draw()

	def setFontPreviewText(self, text: str) -> None:
		self.fontb.set_property("preview-text", text)


class WeekDayNameOptionsWidget(_WeekMonthOptionsWidget):
	pass


class MonthNameListOptionsWidget(_WeekMonthOptionsWidget):
	def __init__(
		self,
		options: ListOption[DayCalTypeWMOptionsDict],
		index: int,
		calType: int,
		cal: CalBase,
		sgroupLabel: gtk.SizeGroup | None = None,
		hasEnable: bool = False,
		enableTitleLabel: str = "",
		useFrame: bool = False,
	) -> None:
		self.index = index
		# ----
		module = calTypes[calType]
		if module is None:
			raise RuntimeError(f"cal type '{calType}' not found")
		_WeekMonthOptionsWidget.__init__(
			self,
			options=ItemOption(options, index),
			cal=cal,
			sgroupLabel=sgroupLabel,
			desc=_(module.desc, ctx="calendar"),
			hasEnable=hasEnable,
			enableTitleLabel=enableTitleLabel,
			useFrame=useFrame,
		)
