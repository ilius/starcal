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
from scal3.font import Font
from scal3.ui_gtk.mywidgets import MyFontButton

log = logger.get()

import typing
from os.path import isabs, join
from typing import Any

from scal3.locale_man import tr as _
from scal3.path import pixDir, svgDir
from scal3.ui_gtk import GdkPixbuf, getOrientation, gtk, pack
from scal3.ui_gtk.font_utils import gfontDecode, gfontEncode
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.utils import (
	dialog_add_button,
	newAlignLabel,
	set_tooltip,
)

if typing.TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.color_utils import ColorType
	from scal3.property import ListProperty, Property

__all__ = [
	"CheckColorOptionUI",
	"CheckFontOptionUI",
	"CheckOptionUI",
	"ColorOptionUI",
	"ComboEntryTextOptionUI",
	"ComboImageTextOptionUI",
	"ComboTextOptionUI",
	"DirectionOptionUI",
	"FileChooserOptionUI",
	"FloatSpinOptionUI",
	"FontFamilyOptionUI",
	"FontOptionUI",
	"HListOptionUI",
	"IconChooserOptionUI",
	"ImageFileChooserOptionUI",
	"IntSpinOptionUI",
	"JustificationOptionUI",
	"ListOptionUI",
	"OptionUI",
	"RadioHListOptionUI",
	"RadioListOptionUI",
	"RadioVListOptionUI",
	"TextOptionUI",
	"VListOptionUI",
	"WidthHeightOptionUI",
]


class OptionUI:
	prop: Property[Any]
	# def __new__(cls, *args, **kwargs):
	# print("OptionUI:", args, kwargs)
	# obj = object.__new__(cls)
	# return obj

	@classmethod
	def valueString(cls, value: Any) -> str:
		return str(value)

	def get(self) -> Any:
		raise NotImplementedError

	def set(self, value: Any) -> None:
		raise NotImplementedError

	def updateVar(self) -> None:
		self.prop.v = self.get()

	def updateWidget(self) -> None:
		self.set(self.prop.v)

	def getWidget(self) -> gtk.Widget:
		raise NotImplementedError


class ComboTextOptionUI(OptionUI):
	# valueString is not used anywhere!
	# and I was using self here!
	# @classmethod
	# def valueString(cls, value: Any) -> str:
	# 	return self._combo.get_model()[value]

	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str],
		items: list[str],
		label: str = "",
		labelSizeGroup: gtk.SizeGroup | None = None,
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self.prop = prop
		combo = gtk.ComboBoxText()
		self._combo = combo
		self._items = items
		if items:
			for s in items:
				combo.append_text(s)

		self._widget: gtk.Widget
		if label:
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=3)
			pack(hbox, newAlignLabel(sgroup=labelSizeGroup, label=label))
			pack(hbox, combo)
			self._widget = hbox
		else:
			self._widget = combo

		if live:
			self._onChangeFunc = onChangeFunc
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			combo.connect("changed", self.onChange)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def onChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

	def get(self) -> str:
		return self._combo.get_active_text() or ""

	def set(self, value: str) -> None:
		self._combo.set_active(self._items.index(value))


class FontFamilyOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str] | Property[str | None],
		hasAuto: bool = False,
		label: str = "",
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self.prop = prop
		self.hasAuto = hasAuto
		self._onChangeFunc = onChangeFunc
		# ---
		self.fontButton = MyFontButton()
		self.fontButton.set_show_size(False)
		if gtk.MINOR_VERSION >= 24:
			self.fontButton.set_level(gtk.FontChooserLevel.FAMILY)
		# set_level: FAMILY, STYLE, SIZE
		self.fontButton.connect("font-set", self.onChange)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		if label:
			pack(hbox, gtk.Label(label=label))
		if hasAuto:
			self.fontRadio = gtk.RadioButton()
			self.autoRadio = gtk.RadioButton(
				label=_("Auto"),
				group=self.fontRadio,
			)
			pack(hbox, self.fontRadio)
			pack(hbox, self.fontButton)
			pack(hbox, self.autoRadio, padding=5)
			self.fontButton.connect("clicked", self.onFontButtonClick)
			self.fontRadio.connect("clicked", self.onChange)
			self.autoRadio.connect("clicked", self.onChange)
		else:
			pack(hbox, self.fontButton)
		hbox.show_all()
		self._widget = hbox

	def onFontButtonClick(self, _w: gtk.Widget) -> None:
		if not self.hasAuto:
			return
		self.fontRadio.set_active(True)

	def get(self) -> str | None:
		if self.hasAuto and self.autoRadio.get_active():
			return None
		font = gfontDecode(self.fontButton.get_font_name())
		return font.family

	def set(self, value: str | None) -> None:
		if value is None:
			if self.hasAuto:
				self.autoRadio.set_active(True)
			return
		# now value is not None
		if self.hasAuto:
			self.fontRadio.set_active(True)
		self.fontButton.setFont(Font(family=value, size=15))

	def onChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

	def setPreviewText(self, text: str) -> None:
		self.fontButton.set_property("preview-text", text)


# TODO: FontStyleOptionUI
# get() should return a dict, with keys and values being compatible
# with svg and gtk+css, these keys and values
# 	"font-family"
# 	"font-size"
# 	"font-weight"
# 	"font-style": normal | oblique | italic
# 	"font-variant": normal | small-caps
# 	"font-stretch": ultra-condensed | extra-condensed | condensed |
# 		semi-condensed | normal | semi-expanded | expanded |
# 		extra-expanded | ultra-expanded

# Constructor can accept argument `propDict: dict[str, Property]`
# with keys being a subset these 6 style keys, and values
# being the attribute/variable names for reading (in updateWidget)
# and storing (in updateVar) the style values
# or maybe we should leave that to the user of class, and just accept
# a `prop: Property` argument like other classes


class ComboEntryTextOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str],
		items: list[str] | None = None,
	) -> None:
		"""Items is a list of strings."""
		self.prop = prop
		w = gtk.ComboBoxText.new_with_entry()
		self._widget = w
		if items:
			for s in items:
				w.append_text(s)

	def get(self) -> str:
		child = self._widget.get_child()
		assert isinstance(child, gtk.Entry), f"{child=}"
		return child.get_text()

	def set(self, value: str) -> None:
		child = self._widget.get_child()
		assert isinstance(child, gtk.Entry), f"{child=}"
		child.set_text(value)

	def addDescriptionColumn(self, descByValue: dict[str, str]) -> None:
		w = self._widget
		cell = gtk.CellRendererText()
		w.pack_start(cell, expand=True)
		w.add_attribute(cell, "text", 1)
		ls = w.get_model()
		for row in ls:
			row[1] = descByValue.get(row[0], "")


class ComboImageTextOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[int],
		items: list[tuple[str, str]] | None = None,
	) -> None:
		"""Items is a list of (imagePath, text) tuples."""
		self.prop = prop
		# ---
		ls = gtk.ListStore(GdkPixbuf.Pixbuf, str)
		combo = gtk.ComboBox()
		combo.set_model(ls)
		cell: gtk.CellRenderer
		# ---
		cell = gtk.CellRendererPixbuf()
		combo.pack_start(cell, expand=False)
		combo.add_attribute(cell, "pixbuf", 0)
		# ---
		cell = gtk.CellRendererText()
		combo.pack_start(cell, expand=True)
		combo.add_attribute(cell, "text", 1)
		# ---
		self._widget = combo
		self.ls = ls
		if items:
			for imPath, label in items:
				self.append(imPath, label)

	def get(self) -> int:
		return self._widget.get_active()

	def set(self, value: int) -> None:
		self._widget.set_active(value)

	def append(self, imPath: str, label: str) -> None:
		if imPath:
			if not isabs(imPath):
				imPath = join(pixDir, imPath)
			pix = GdkPixbuf.Pixbuf.new_from_file(imPath)
		else:
			pix = None
		self.ls.append([pix, label])


class FontOptionUI(OptionUI):
	@classmethod
	def valueString(cls, value: Any) -> str:
		return gfontEncode(value)

	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[Font | None],
		dragAndDrop: bool = True,
		previewText: str = "",
	) -> None:
		from scal3.ui_gtk.mywidgets import MyFontButton

		self.prop = prop
		w = MyFontButton(dragAndDrop=dragAndDrop)
		self._widget = w
		if previewText:
			self.setPreviewText(previewText)

	def get(self) -> Font:
		return self._widget.getFont()

	def set(self, value: Font | None) -> None:
		if value is None:
			return
		self._widget.setFont(value)

	def setPreviewText(self, text: str) -> None:
		self._widget.set_preview_text(text)
		# self._widget.set_property("preview-text", text)


class CheckOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[bool],
		label: str = "",
		tooltip: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self.prop = prop
		checkb = gtk.CheckButton(label=label)
		if tooltip:
			set_tooltip(checkb, tooltip)
		self._widget = checkb
		self._checkButton = checkb

		if live:
			self._onChangeFunc = onChangeFunc
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			checkb.connect("clicked", self.onClick)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> bool:
		return self._widget.get_active()

	def set(self, value: bool) -> None:
		self._widget.set_active(value)

	def onClick(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

	def syncSensitive(self, widget: gtk.Widget, reverse: bool = False) -> None:
		self._sensitiveWidget = widget
		self._sensitiveReverse = reverse
		self._widget.connect("show", self.syncSensitiveUpdate)
		self._widget.connect("clicked", self.syncSensitiveUpdate)

	def syncSensitiveUpdate(self, _widget: gtk.Widget) -> None:
		active = self._checkButton.get_active()
		if self._sensitiveReverse:
			active = not active
		self._sensitiveWidget.set_sensitive(active)


# All methods of Gtk.ColorButton are deprecated since version 3.4:
# Looks like ColorButton itself is deprecated, and should be replaced
# with something else!!


class ColorOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	@classmethod
	def valueString(cls, value: Any) -> str:
		if value is None:
			return "None"
		if len(value) == 3:
			return f"rgb{value}"
		if len(value) == 4:
			return f"rgba{value}"
		raise ValueError(f"unexpected value {value!r}")

	def __init__(
		self,
		prop: Property[ColorType] | Property[ColorType | None],
		useAlpha: bool = False,
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets import MyColorButton

		self.prop = prop
		colorb = MyColorButton()
		gtk.ColorChooser.set_use_alpha(colorb, useAlpha)
		self.useAlpha = useAlpha
		self._widget = colorb
		# ---
		if live:
			self._onChangeFunc = onChangeFunc
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			colorb.connect("color-set", self.onColorSet)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> ColorType:
		return self._widget.getRGBA()

	def set(self, color: ColorType | None) -> None:
		if color is None:
			return
		self._widget.setRGBA(color)

	def onColorSet(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


# class OptionalColorOptionUI(ColorOptionUI):
# 	def __init__(
# 		self,
# 		prop: Property[ColorType | None],
# 		useAlpha: bool = False,
# 		live: bool = False,
# 		onChangeFunc: Callable | None = None,
# 	) -> None:


# combination of CheckOptionUI and ColorOptionUI in a HBox,
# with auto-update / auto-apply, for use in Customize window
class CheckColorOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		checkItem: CheckOptionUI,
		colorItem: ColorOptionUI,
		checkSizeGroup: gtk.SizeGroup | None = None,
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self._checkItem = checkItem
		self._colorItem = colorItem
		self.live = live
		self._onChangeFunc = onChangeFunc

		checkb = self._checkItem.getWidget()
		colorb = self._colorItem.getWidget()

		if checkSizeGroup:
			checkSizeGroup.add_widget(checkb)

		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=3)
		pack(hbox, checkb)
		pack(hbox, colorb)
		self._widget = hbox

		if live:
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")
		checkb.connect("clicked", self.onChange)
		colorb.connect("color-set", self.onChange)

	def updateVar(self) -> None:
		self._checkItem.updateVar()
		self._colorItem.updateVar()

	def updateWidget(self) -> None:
		# FIXME: this func is triggering onChange func, can we avoid that?
		self._checkItem.updateWidget()
		self._colorItem.updateWidget()
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())

	def onChange(self, _w: gtk.Widget) -> None:
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())
		if self.live:
			self.updateVar()
			if self._onChangeFunc:
				self._onChangeFunc()


# combination of CheckOptionUI and FontOptionUI in a HBox
class CheckFontOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		checkItem: CheckOptionUI,
		fontItem: FontOptionUI,
		checkSizeGroup: gtk.SizeGroup | None = None,
		vertical: bool = False,
		spacing: int = 3,
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		self._checkItem = checkItem
		self._fontItem = fontItem
		self.live = live
		self._onChangeFunc = onChangeFunc

		checkb = self._checkItem.getWidget()
		fontb = self._fontItem.getWidget()

		if checkSizeGroup:
			checkSizeGroup.add_widget(checkb)

		box = gtk.Box(orientation=getOrientation(vertical), spacing=spacing)
		pack(box, checkb)
		pack(box, fontb)
		self._widget = box

		if live:
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")
		checkb.connect("clicked", self.onChange)
		fontb.connect("font-set", self.onChange)

	def updateVar(self) -> None:
		self._checkItem.updateVar()
		self._fontItem.updateVar()

	def updateWidget(self) -> None:
		# FIXME: this func is triggering onChange func, can we avoid that?
		self._checkItem.updateWidget()
		self._fontItem.updateWidget()
		self._fontItem.getWidget().set_sensitive(self._checkItem.get())

	def onChange(self, _w: gtk.Widget) -> None:
		self._fontItem.getWidget().set_sensitive(self._checkItem.get())
		if self.live:
			self.updateVar()
			if self._onChangeFunc:
				self._onChangeFunc()


class IntSpinOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[int],
		bounds: tuple[int, int],
		step: int = 0,
		label: str = "",
		labelSizeGroup: gtk.SizeGroup | None = None,
		unitLabel: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		minim, maxim = bounds
		self.prop = prop
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
		prop: Property[float],
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
		self.prop = prop
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


class TextOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str],
		label: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets import TextFrame

		self.prop = prop
		self._onChangeFunc = onChangeFunc
		# ---
		kwargs = {}
		if live:
			kwargs["onTextChange"] = self.onTextChange
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")
		self.textInput = TextFrame(**kwargs)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		if label:
			pack(hbox, gtk.Label(label=label))
		pack(hbox, self.textInput, 1, 1)
		hbox.show_all()
		self._widget = hbox
		# ---
		if live:
			self.updateWidget()

	def get(self) -> str:
		return self.textInput.get_text()

	def set(self, text: str) -> None:
		self.textInput.set_text(text)

	def onTextChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class WidthHeightOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[tuple[int, int]],
		maxim: int,
	) -> None:
		minim = 0
		self.prop = prop
		# ---
		self.widthItem = IntSpinButton(minim, maxim)
		self.heightItem = IntSpinButton(minim, maxim)
		# ---
		hbox = self._widget = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Width") + ":"))
		pack(hbox, self.widthItem)
		pack(hbox, gtk.Label(label="  "))
		pack(hbox, gtk.Label(label=_("Height") + ":"))
		pack(hbox, self.heightItem)

	def get(self) -> tuple[int, int]:
		return (
			int(self.widthItem.get_value()),
			int(self.heightItem.get_value()),
		)

	def set(self, value: tuple[int, int]) -> None:
		w, h = value
		self.widthItem.set_value(w)
		self.heightItem.set_value(h)


class FileChooserOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str],
		title: str = "Select File",
		currentFolder: str = "",
	) -> None:
		self.prop = prop
		# ---
		dialog = gtk.FileChooserDialog(
			title=title,
			action=gtk.FileChooserAction.OPEN,
		)
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
		)
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Choose"),
		)
		w = gtk.FileChooserButton.new_with_dialog(dialog)
		w.set_local_only(True)
		if currentFolder:
			w.set_current_folder(currentFolder)
		# ---
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.NONE,
			imageName="edit-undo.svg",
			label=_("_Revert"),
			onClick=self.onRevertClick,
		)
		# ---
		self._widget = w
		self._fcb = w

	def get(self) -> str:
		return self._fcb.get_filename() or ""

	def set(self, value: str) -> None:
		self._fcb.set_filename(value)

	def onRevertClick(self, _w: gtk.Widget) -> None:
		defaultValue = self.prop.default()
		self.prop.v = defaultValue
		self.set(defaultValue)


class ImageFileChooserOptionUI(FileChooserOptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str],
		title: str = "Select File",
		currentFolder: str = "",
	) -> None:
		FileChooserOptionUI.__init__(
			self,
			prop=prop,
			title=title,
			currentFolder=currentFolder,
		)
		self._preview = gtk.Image()
		self._widget.set_preview_widget(self._preview)
		self._widget.set_preview_widget_active(True)
		self._widget.connect("update-preview", self._updatePreview)

	def _updatePreview(self, _w: gtk.Widget) -> None:
		fpath = self._widget.get_preview_filename()
		self._preview.set_from_file(fpath)


class IconChooserOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str],
		label: str = "",
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.icon import IconSelectButton

		self.prop = prop
		self._onChangeFunc = onChangeFunc
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		if label:
			pack(hbox, gtk.Label(label=label + "  "))
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(), 1, 1)
		self._widget = hbox
		# ---
		if live:
			self.updateWidget()
			self.iconSelect.connect("changed", self.onIconChanged)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> str:
		return self.iconSelect.get_filename().removeprefix(join(pixDir, ""))

	def set(self, iconPath: str) -> None:
		if not isabs(iconPath):
			if iconPath.endswith(".svg"):
				iconPath = join(svgDir, iconPath)
			else:
				iconPath = join(pixDir, iconPath)
		self.iconSelect.set_filename(iconPath)

	def onIconChanged(self, _w: gtk.Widget, iconPath: str) -> None:
		if not iconPath:
			self.updateWidget()
		self.updateVar()
		if self._onChangeFunc is not None:
			self._onChangeFunc()


class RadioListOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		vertical: bool,
		prop: Property[int | None],
		texts: list[str],
		label: str | None = None,
	) -> None:
		self.num = len(texts)
		self.prop = prop
		if vertical:
			box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		else:
			box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self._widget = box
		self.radios = [gtk.RadioButton(label=_(s)) for s in texts]
		first = self.radios[0]
		if label is not None:
			pack(box, gtk.Label(label=label))
			pack(box, gtk.Label(), 1, 1)
		pack(box, first)
		for r in self.radios[1:]:
			pack(box, gtk.Label(), 1, 1)
			pack(box, r)
			r.join_group(first)
		pack(box, gtk.Label(), 1, 1)  # FIXME

	def get(self) -> int | None:
		for i in range(self.num):
			if self.radios[i].get_active():
				return i
		return None

	def set(self, index: int) -> None:
		self.radios[index].set_active(True)


class RadioHListOptionUI(RadioListOptionUI):
	def __init__(
		self,
		prop: Property[int | None],
		texts: list[str],
		label: str | None = None,
	) -> None:
		RadioListOptionUI.__init__(
			self,
			vertical=False,
			prop=prop,
			texts=texts,
			label=label,
		)


class RadioVListOptionUI(RadioListOptionUI):
	def __init__(
		self,
		prop: Property[int | None],
		texts: list[str],
		label: str | None = None,
	) -> None:
		RadioListOptionUI.__init__(
			self,
			vertical=True,
			prop=prop,
			texts=texts,
			label=label,
		)


class ListOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		vertical: bool,
		prop: ListProperty[Any],
		items: list[OptionUI] | None = None,
	) -> None:
		self.prop = prop
		if vertical:
			box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		else:
			box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		if items is None:
			items = []
		for item in items:
			pack(box, item.getWidget())
		self.num = len(items)
		self.items = items
		self._widget = box

	def get(self) -> list[Any]:
		return [item.get() for item in self.items]

	def set(self, valueL: list[Any]) -> None:
		for i in range(self.num):
			self.items[i].set(valueL[i])

	def append(self, item: OptionUI) -> None:
		pack(self._widget, item.getWidget())
		self.items.append(item)


class HListOptionUI(ListOptionUI):
	def __init__(
		self,
		prop: ListProperty[Any],
		items: list[OptionUI] | None = None,
	) -> None:
		ListOptionUI.__init__(
			self,
			vertical=False,
			prop=prop,
			items=items,
		)


class VListOptionUI(ListOptionUI):
	def __init__(
		self,
		prop: ListProperty[Any],
		items: list[OptionUI] | None = None,
	) -> None:
		ListOptionUI.__init__(
			self,
			vertical=True,
			prop=prop,
			items=items,
		)


class DirectionOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str],
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.direction_combo import DirectionComboBox

		# ---
		self.prop = prop
		self._onChangeFunc = onChangeFunc
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Direction")))
		combo = DirectionComboBox()
		self._combo = combo
		pack(hbox, combo)
		combo.connect("changed", self.onComboChange)
		self._widget = hbox
		# ---
		self.updateWidget()

	def get(self) -> str:
		"""Returns one of "ltr", "rtl", "auto"."""
		return self._combo.getValue()

	def set(self, value: str) -> None:
		"""Value must be one of "ltr", "rtl", "auto"."""
		self._combo.setValue(value)

	def onComboChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class JustificationOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		prop: Property[str],
		label: str = "",
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.justification_combo import JustificationComboBox

		# ---
		self.prop = prop
		self._onChangeFunc = onChangeFunc
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
		if label:
			pack(hbox, gtk.Label(label=label))
		combo = JustificationComboBox()
		self._combo = combo
		pack(hbox, combo)
		combo.connect("changed", self.onComboChange)
		self._widget = hbox
		# ---
		self.updateWidget()

	def get(self) -> str:
		"""Returns one of "left", "right", "center", "fill"."""
		return self._combo.getValue()

	def set(self, value: str) -> None:
		"""Value must be one of "left", "right", "center", "fill"."""
		self._combo.setValue(value)

	def onComboChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()
