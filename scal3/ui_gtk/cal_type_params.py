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

from scal3 import logger

log = logger.get()

from scal3.cal_types import calTypes
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui.font import getParamsFont
from scal3.ui_gtk import HBox, gtk, pack

__all__ = ["CalTypeParamWidget", "TextParamWidget"]


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
		log.info(f"XAlignComboBox: unexpected {index = }")
		return None

	def set(self, value) -> None:
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

	def set(self, value) -> None:
		if value == "top":
			self.set_active(0)
		elif value == "center":
			self.set_active(1)
		elif value == "buttom":
			self.set_active(2)
		else:
			self.set_active(1)


class TextParamWidget(gtk.Box):
	def __init__(
		self,
		paramName,
		cal,
		params,
		sgroupLabel=None,
		desc=None,
		hasEnable=False,
		hasAlign=False,
		hasAbbreviate=False,
		hasUppercase=False,
		enableTitleLabel="",
		useFrame=False,
	) -> None:
		from scal3.ui_gtk.mywidgets import MyColorButton, MyFontButton
		from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton

		if desc is None:
			raise ValueError("desc is None")
		# ---
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL, spacing=10)
		# ---
		self.set_border_width(5)
		self.paramName = paramName
		self.cal = cal
		self.hasEnable = hasEnable
		self.hasAlign = hasAlign
		self.hasAbbreviate = hasAbbreviate
		self.hasUppercase = hasUppercase
		# ----
		if sgroupLabel is None:
			sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ----
		if not enableTitleLabel and hasEnable:
			enableTitleLabel = _("Enable")
		if hasEnable:
			self.enableCheck = gtk.CheckButton(label=enableTitleLabel)
		# ---
		vbox = self
		if useFrame:
			frame = gtk.Frame()
			vbox = gtk.VBox()
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
		hbox = HBox()
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
		if hasAlign:
			hbox = HBox()
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
		hbox = HBox()
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
		if hasAbbreviate:
			self.abbreviateCheck = gtk.CheckButton(label=_("Abbreviate"))
			pack(vbox, self.abbreviateCheck)
		if hasUppercase:
			self.uppercaseCheck = gtk.CheckButton(label=_("Uppercase"))
			pack(vbox, self.uppercaseCheck)
		# ----
		self.set(params)
		# ----
		self.spinX.connect("changed", self.onChange)
		self.spinY.connect("changed", self.onChange)
		fontb.connect("font-set", self.onChange)
		colorb.connect("color-set", self.onChange)
		if hasEnable:
			self.enableCheck.connect("clicked", self.onChange)
		if hasAlign:
			self.xalignCombo.connect("changed", self.onChange)
			self.yalignCombo.connect("changed", self.onChange)
		if hasAbbreviate:
			self.abbreviateCheck.connect("clicked", self.onChange)
		if hasUppercase:
			self.uppercaseCheck.connect("clicked", self.onChange)

	def get(self):
		params = {
			"pos": (
				self.spinX.get_value(),
				self.spinY.get_value(),
			),
			"font": self.fontb.get_font(),
			"color": self.colorb.get_rgba(),
		}
		if self.hasEnable:
			params["enable"] = self.enableCheck.get_active()
		if self.hasAlign:
			params["xalign"] = self.xalignCombo.get()
			params["yalign"] = self.yalignCombo.get()
		if self.hasAbbreviate:
			params["abbreviate"] = self.abbreviateCheck.get_active()
		if self.hasUppercase:
			params["uppercase"] = self.uppercaseCheck.get_active()
		return params

	def set(self, params) -> None:
		self.spinX.set_value(params["pos"][0])
		self.spinY.set_value(params["pos"][1])
		self.fontb.set_font(getParamsFont(params))
		self.colorb.set_rgba(params["color"])
		if self.hasEnable:
			self.enableCheck.set_active(params.get("enable", True))
		if self.hasAlign:
			self.xalignCombo.set(params.get("xalign", "center"))
			self.yalignCombo.set(params.get("yalign", "center"))
		if self.hasAbbreviate:
			self.abbreviateCheck.set_active(params.get("abbreviate", False))
		if self.hasUppercase:
			self.uppercaseCheck.set_active(params.get("uppercase", False))

	def onChange(self, _obj=None, _event=None) -> None:
		setattr(conf, self.paramName, self.get())
		self.cal.queue_draw()

	def setFontPreviewText(self, text) -> None:
		self.fontb.set_property("preview-text", text)


class CalTypeParamWidget(TextParamWidget):
	def __init__(self, *args, **kwargs) -> None:
		index = kwargs.get("index")
		if index is None:
			raise ValueError("index is None")
		del kwargs["index"]
		self.index = index
		# ----
		calType = kwargs.get("calType")
		if calType is None:
			raise ValueError("calType is None")
		del kwargs["calType"]
		module, ok = calTypes[calType]
		if not ok:
			raise RuntimeError(f"cal type '{calType}' not found")
		kwargs["desc"] = _(module.desc, ctx="calendar")
		# ----
		TextParamWidget.__init__(self, *args, **kwargs)

	def onChange(self, _obj=None, _event=None) -> None:
		typeParams = getattr(conf, self.paramName)
		typeParams[self.index] = self.get()
		self.cal.queue_draw()
