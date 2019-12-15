#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

import sys
import os
from os.path import join, isabs

from typing import Optional, Callable, Any, Union, Tuple, List

from scal3.path import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import set_tooltip, dialog_add_button, newAlignLabel
from scal3.ui_gtk.font_utils import gfontEncode, gfontDecode


from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton


ColorType = Union[Tuple[int, int, int], Tuple[int, int, int, int]]


# (VAR_NAME, bool,     CHECKBUTTON_TEXT)                 ## CheckButton
# (VAR_NAME, list,     LABEL_TEXT, (ITEM1, ITEM2, ...))  ## ComboBox
# (VAR_NAME, int,      LABEL_TEXT, MIN, MAX)             ## SpinButton
# (VAR_NAME, float,    LABEL_TEXT, MIN, MAX, DIGITS)     ## SpinButton
class ModuleOptionItem:
	@classmethod
	def valueString(cls, value: Any) -> str:
		return str(value)

	def __init__(
		self,
		obj: Any,
		opt: Tuple,
	) -> None:
		t = opt[1]
		self.opt = opt ## needed??
		self.obj = obj
		self.type = t
		self.attrName = opt[0]
		hbox = HBox()
		if t == bool:
			w = gtk.CheckButton(label=_(opt[2]))
			self.get = w.get_active
			self.set = w.set_active
		elif t == list:
			pack(hbox, gtk.Label(label=_(opt[2])))
			w = gtk.ComboBoxText()  # or RadioButton
			for s in opt[3]:
				w.append_text(_(s))
			self.get = w.get_active
			self.set = w.set_active
		elif t == int:
			pack(hbox, gtk.Label(label=_(opt[2])))
			w = IntSpinButton(opt[3], opt[4])
			self.get = w.get_value
			self.set = w.set_value
		elif t == float:
			pack(hbox, gtk.Label(label=_(opt[2])))
			w = FloatSpinButton(opt[3], opt[4], opt[5])
			self.get = w.get_value
			self.set = w.set_value
		else:
			raise RuntimeError("bad option type {t!r}")
		pack(hbox, w)
		self._widget = hbox
		####

	def updateVar(self) -> None:
		setattr(
			self.obj,
			self.attrName,
			self.get(),
		)

	def updateWidget(self) -> None:
		self.set(
			getattr(self.obj, self.attrName)
		)

	def getWidget(self) -> gtk.Widget:
		return self._widget


# ("button", LABEL, CLICKED_MODULE_NAME, CLICKED_FUNCTION_NAME)
class ModuleOptionButton:
	@classmethod
	def valueString(cls, value: Any) -> str:
		return str(value)

	def __init__(self, opt: Tuple) -> None:
		funcName = opt[2]
		clickedFunc = getattr(
			__import__(
				f"scal3.ui_gtk.{opt[1]}",
				fromlist=[funcName],
			),
			funcName,
		)
		hbox = HBox()
		button = gtk.Button(label=_(opt[0]))
		button.connect("clicked", clickedFunc)
		pack(hbox, button)
		self._widget = hbox

	def get(self) -> Any:
		return None

	def updateVar(self) -> None:
		pass

	def updateWidget(self) -> None:
		pass

	def getWidget(self) -> gtk.Widget:
		return self._widget


class PrefItem():
	@classmethod
	def valueString(cls, value: Any) -> str:
		return str(value)

	# self.__init__, self.obj, self.attrName, self._widget
	# self.attrName is string, the name of attribute of `self.obj`
	def get(self) -> Any:
		raise NotImplementedError

	def set(self, value: Any) -> None:
		raise NotImplementedError

	def updateVar(self) -> None:
		setattr(
			self.obj,
			self.attrName,
			self.get(),
		)

	def updateWidget(self) -> None:
		self.set(
			getattr(self.obj, self.attrName)
		)

	def getWidget(self) -> gtk.Widget:
		return self._widget


class ComboTextPrefItem(PrefItem):
	@classmethod
	def valueString(cls, value: Any) -> str:
		return self._combo.get_model()[value]

	def __init__(
		self,
		obj: Any,
		attrName: str,
		items: Optional[List[str]] = None,
	) -> None:
		self.obj = obj
		self.attrName = attrName
		combo = gtk.ComboBoxText()
		self._combo = combo
		self._widget = combo
		if items:
			for s in items:
				combo.append_text(s)

	def get(self) -> int:
		return self._widget.get_active()

	def set(self, value: int) -> None:
		self._widget.set_active(value)


class FontFamilyPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		hasAuto: bool = False,
		label: str = "",
		onChangeFunc: Optional[Callable] = None,
	):
		self.obj = obj
		self.attrName = attrName
		self.hasAuto = hasAuto
		self._onChangeFunc = onChangeFunc
		###
		self.fontButton = gtk.FontButton()
		self.fontButton.set_show_size(False)
		self.fontButton.set_level(gtk.FontChooserLevel.FAMILY)
		# set_level: FAMILY, STYLE, SIZE
		self.fontButton.connect("font-set", self.onChange)
		###
		hbox = HBox(spacing=5)
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

	def onFontButtonClick(self, w: gtk.Widget) -> None:
		if not self.hasAuto:
			return
		self.fontRadio.set_active(True)

	def get(self) -> Optional[str]:
		if self.hasAuto and self.autoRadio.get_active():
			return None
		font = gfontDecode(self.fontButton.get_font_name())
		return font[0]

	def set(self, value: Optional[str]) -> None:
		if value is None:
			if self.hasAuto:
				self.autoRadio.set_active(True)
			return
		# now value is not None
		if self.hasAuto:
			self.fontRadio.set_active(True)
		self.fontButton.set_font(gfontEncode((value, False, False, 15)))

	def onChange(self, w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


# TODO: FontStylePrefItem
# get() should return a dict, with keys and values being compatible
# with svg and gtk+css, these keys and values
# 	"font-family"
# 	"font-size"
# 	"font-weight"
# 	"font-style": normal | oblique | italic
# 	"font-variant": normal | small-caps
# 	"font-stretch": ultra-condensed | extra-condensed | condensed |
#		semi-condensed | normal | semi-expanded | expanded |
#		extra-expanded | ultra-expanded

# Constructor can accept argument `attrNameDict: Dict[str, str]`
# with keys being a subset these 6 style keys, and values
# being the attribute/variable names for reading (in updateWidget)
# and storing (in updateVar) the style values
# or maybe we should leave that to the user of class, and just accept
# a `attrName: str` argument like other classes





class ComboEntryTextPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		items: Optional[List[str]] = None,
	):
		"""items is a list of strings"""
		self.obj = obj
		self.attrName = attrName
		w = gtk.ComboBoxText.new_with_entry()
		self._widget = w
		if items:
			for s in items:
				w.append_text(s)

	def get(self) -> str:
		return self._widget.get_child().get_text()

	def set(self, value: str) -> None:
		self._widget.get_child().set_text(value)


class ComboImageTextPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		items: Optional[List[Tuple[str, str]]] = None,
	):
		"""
		items is a list of (imagePath, text) tuples
		"""
		self.obj = obj
		self.attrName = attrName
		###
		ls = gtk.ListStore(GdkPixbuf.Pixbuf, str)
		combo = gtk.ComboBox()
		combo.set_model(ls)
		###
		cell = gtk.CellRendererPixbuf()
		pack(combo, cell, False)
		combo.add_attribute(cell, "pixbuf", 0)
		###
		cell = gtk.CellRendererText()
		pack(combo, cell, True)
		combo.add_attribute(cell, "text", 1)
		###
		self._widget = combo
		self.ls = ls
		if items:
			for (imPath, label) in items:
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


class FontPrefItem(PrefItem):
	@classmethod
	def valueString(cls, value: Any) -> str:
		return gfontEncode(value)

	def __init__(
		self,
		obj: Any,
		attrName: str,
		dragAndDrop: bool = True,
	) -> None:
		from scal3.ui_gtk.mywidgets import MyFontButton
		self.obj = obj
		self.attrName = attrName
		w = MyFontButton(dragAndDrop=dragAndDrop)
		self._widget = w

	def get(self) -> Tuple[str, bool, bool, float]:
		return self._widget.get_font()

	def set(self, value: Optional[Tuple[str, bool, bool, float]]) -> None:
		if value is None:
			return
		self._widget.set_font(value)


class CheckPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		label: str = "",
		tooltip: str = "",
		live: bool = False,
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		self.obj = obj
		self.attrName = attrName
		checkb = gtk.CheckButton(label=label)
		if tooltip:
			set_tooltip(checkb, tooltip)
		self._widget = checkb

		if live:
			self._onChangeFunc = onChangeFunc
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			checkb.connect("clicked", self.onClick)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> bool:
		return self._widget.get_active()

	def set(self, value: bool):
		self._widget.set_active(value)

	def onClick(self, w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

	def syncSensitive(self, widget: gtk.Widget, reverse: bool = False) -> None:
		self._sensitiveWidget = widget
		self._sensitiveReverse = reverse
		self._widget.connect("show", self.syncSensitiveUpdate)
		self._widget.connect("clicked", self.syncSensitiveUpdate)

	def syncSensitiveUpdate(self, myWidget: gtk.Widget) -> None:
		active = myWidget.get_active()
		if self._sensitiveReverse:
			active = not active
		self._sensitiveWidget.set_sensitive(active)


class ColorPrefItem(PrefItem):
	@classmethod
	def valueString(cls, value: Any) -> str:
		if value is None:
			return "None"
		if len(value) == 3:
			return f"rgb{value}"
		if len(value) == 4:
			return f"rgba{value}"
		raise ValueError("unexpected value {value!r}")

	def __init__(
		self,
		obj: Any,
		attrName: str,
		useAlpha: bool = False,
		live: bool = False,
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		from scal3.ui_gtk.mywidgets import MyColorButton
		self.obj = obj
		self.attrName = attrName
		colorb = MyColorButton()
		gtk.ColorChooser.set_use_alpha(colorb, useAlpha)
		# All methods of Gtk.ColorButton are deprecated since version 3.4:
		# Looks like ColorButton itself is deprecated, and should be replaced
		# with something else!!
		self.useAlpha = useAlpha
		self._widget = colorb
		###
		if live:
			self._onChangeFunc = onChangeFunc
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			colorb.connect("color-set", self.onColorSet)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> ColorType:
		return self._widget.get_rgba()

	def set(self, color: Optional[ColorType]) -> None:
		if color is None:
			return
		self._widget.set_rgba(color)

	def onColorSet(self, w: gtk.Widget):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


# combination of CheckPrefItem and ColorPrefItem in a HBox,
# with auto-update / auto-apply, for use in Customize window
class CheckColorPrefItem(PrefItem):
	def __init__(
		self,
		checkItem: CheckPrefItem,
		colorItem: ColorPrefItem,
		checkSizeGroup: Optional[gtk.SizeGroup] = None,
		live: bool = False,
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		self._checkItem = checkItem
		self._colorItem = colorItem
		self.live = live
		self._onChangeFunc = onChangeFunc

		checkb = self._checkItem.getWidget()
		colorb = self._colorItem.getWidget()

		if checkSizeGroup:
			checkSizeGroup.add_widget(checkb)

		hbox = HBox(spacing=3)
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

	def onChange(self, w: gtk.Widget) -> None:
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())
		if self.live:
			self.updateVar()
			if self._onChangeFunc:
				self._onChangeFunc()


# combination of CheckPrefItem and FontPrefItem in a HBox
class CheckFontPrefItem(PrefItem):
	def __init__(
		self,
		checkItem: CheckPrefItem,
		fontItem: FontPrefItem,
		checkSizeGroup: Optional[gtk.SizeGroup] = None,
		vertical: bool = False,
		spacing: int = 3,
		live: bool = False,
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		self._checkItem = checkItem
		self._fontItem = fontItem
		self.live = live
		self._onChangeFunc = onChangeFunc

		checkb = self._checkItem.getWidget()
		fontb = self._fontItem.getWidget()

		if checkSizeGroup:
			checkSizeGroup.add_widget(checkb)

		box = Box(vertical=vertical, spacing=spacing)
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

	def onChange(self, w: gtk.Widget) -> None:
		self._fontItem.getWidget().set_sensitive(self._checkItem.get())
		if self.live:
			self.updateVar()
			if self._onChangeFunc:
				self._onChangeFunc()


class SpinPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		_min: Union[int, float],
		_max: Union[int, float],
		digits: int = 1,
		step: Union[int, float] = 0,
		label: str = "",
		labelSizeGroup: Optional[gtk.SizeGroup] = None,
		unitLabel: str = "",
		live: bool = False,
		onChangeFunc: Optional[Callable] = None,
	):
		self.obj = obj
		self.attrName = attrName
		self._onChangeFunc = onChangeFunc
		##
		if digits == 0:
			spinb = IntSpinButton(_min, _max, step=step)
		else:
			spinb = FloatSpinButton(_min, _max, digits, step=step)
		self._spinb = spinb

		if labelSizeGroup and not label:
			raise ValueError("labelSizeGroup= is passed without label=")

		if label or unitLabel:
			hbox = HBox(spacing=3)
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

	def get(self) -> Union[int, float]:
		return self._spinb.get_value()

	def set(self, value: Union[int, float]) -> None:
		self._spinb.set_value(value)

	# FIXME: updateWidget is triggering onChange func, can we avoid that?
	def onChange(self, w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class TextPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		label: str = "",
		live: bool = False,
		onChangeFunc: Optional[Callable] = None,
	):
		from scal3.ui_gtk.mywidgets import TextFrame
		self.obj = obj
		self.attrName = attrName
		self._onChangeFunc = onChangeFunc
		###
		kwargs = {}
		if live:
			kwargs["onTextChange"] = self.onTextChange
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")
		self.textInput = TextFrame(**kwargs)
		###
		hbox = HBox()
		if label:
			pack(hbox, gtk.Label(label=label))
		pack(hbox, self.textInput, 1, 1)
		hbox.show_all()
		self._widget = hbox
		###
		if live:
			self.updateWidget()

	def get(self) -> str:
		return self.textInput.get_text()

	def set(self, text: str) -> None:
		self.textInput.set_text(text)

	def onTextChange(self, w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class WidthHeightPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		_max: Union[int, float],
	):
		_min = 0
		self.obj = obj
		self.attrName = attrName
		###
		self.widthItem = IntSpinButton(_min, _max)
		self.heightItem = IntSpinButton(_min, _max)
		###
		hbox = self._widget = HBox()
		pack(hbox, gtk.Label(label=_("Width") + ":"))
		pack(hbox, self.widthItem)
		pack(hbox, gtk.Label(label="  "))
		pack(hbox, gtk.Label(label=_("Height") + ":"))
		pack(hbox, self.heightItem)

	def get(self) -> Tuple[int, int]:
		return (
			int(self.widthItem.get_value()),
			int(self.heightItem.get_value()),
		)

	def set(self, value: Tuple[int, int]):
		w, h = value
		self.widthItem.set_value(w)
		self.heightItem.set_value(h)


class FileChooserPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		title: str = "Select File",
		currentFolder: str = "",
		defaultVarName: str = "",
	):
		self.obj = obj
		self.attrName = attrName
		###
		dialog = gtk.FileChooserDialog(
			title=title,
			action=gtk.FileChooserAction.OPEN,
		)
		dialog_add_button(
			dialog,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			dialog,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		w = gtk.FileChooserButton.new_with_dialog(dialog)
		w.set_local_only(True)
		if currentFolder:
			w.set_current_folder(currentFolder)
		###
		self.defaultVarName = defaultVarName
		if defaultVarName:
			dialog_add_button(
				dialog,
				imageName="edit-undo.svg",
				label=_("_Revert"),
				res=gtk.ResponseType.NONE,
				onClick=self.onRevertClick,
			)
		###
		self._widget = w

	def get(self) -> str:
		return self._widget.get_filename()

	def set(self, value: str) -> None:
		self._widget.set_filename(value)

	def onRevertClick(self, button: gtk.Button) -> None:
		defaultValue = getattr(self.obj, self.defaultVarName)
		setattr(
			self.obj,
			self.attrName,
			defaultValue,
		)
		self.set(defaultValue)


class ImageFileChooserPrefItem(FileChooserPrefItem):
	def __init__(self, *args, **kwargs) -> None:
		FileChooserPrefItem.__init__(self, *args, **kwargs)
		self._preview = gtk.Image()
		self._widget.set_preview_widget(self._preview)
		self._widget.set_preview_widget_active(True)
		self._widget.connect("update-preview", self._updatePreview)

	def _updatePreview(self, w: gtk.Widget) -> None:
		from os.path import splitext
		fpath = self._widget.get_preview_filename()
		self._preview.set_from_file(fpath)


class IconChooserPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		label: str = "",
		live: bool = False,
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.icon import IconSelectButton
		self.obj = obj
		self.attrName = attrName
		self._onChangeFunc = onChangeFunc
		hbox = HBox()
		if label:
			pack(hbox, gtk.Label(label=label + "  "))
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(), 1, 1)
		self._widget = hbox
		###
		if live:
			self.updateWidget()
			self.iconSelect.connect("changed", self.onIconChanged)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> str:
		iconPath = self.iconSelect.get_filename()
		direc = join(pixDir, "")
		if iconPath.startswith(direc):
			iconPath = iconPath[len(direc):]
		return iconPath

	def set(self, iconPath: str) -> None:
		if not isabs(iconPath):
			if iconPath.endswith(".svg"):
				iconPath = join(svgDir, iconPath)
			else:
				iconPath = join(pixDir, iconPath)
		self.iconSelect.set_filename(iconPath)

	def onIconChanged(self, widget: gtk.Widget, iconPath: str) -> None:
		if not iconPath:
			self.updateWidget()
		self.updateVar()
		if self._onChangeFunc is not None:
			self._onChangeFunc()


class RadioListPrefItem(PrefItem):
	def __init__(
		self,
		vertical: bool,
		obj: Any,
		attrName: str,
		texts: List[str],
		label: Optional[str] = None,
	) -> None:
		self.num = len(texts)
		self.obj = obj
		self.attrName = attrName
		if vertical:
			box = VBox()
		else:
			box = HBox()
		self._widget = box
		self.radios = [
			gtk.RadioButton(label=_(s))
			for s in texts
		]
		first = self.radios[0]
		if label is not None:
			pack(box, gtk.Label(label=label))
			pack(box, gtk.Label(), 1, 1)
		pack(box, first)
		for r in self.radios[1:]:
			pack(box, gtk.Label(), 1, 1)
			pack(box, r)
			r.set_group(first)
		pack(box, gtk.Label(), 1, 1) ## FIXME

	def get(self) -> Optional[int]:
		for i in range(self.num):
			if self.radios[i].get_active():
				return i

	def set(self, index: int) -> None:
		self.radios[index].set_active(True)


class RadioHListPrefItem(RadioListPrefItem):
	def __init__(self, *args, **kwargs) -> None:
		RadioListPrefItem.__init__(self, False, *args, **kwargs)


class RadioVListPrefItem(RadioListPrefItem):
	def __init__(self, *args, **kwargs) -> None:
		RadioListPrefItem.__init__(self, True, *args, **kwargs)


class ListPrefItem(PrefItem):
	def __init__(
		self,
		vertical: bool,
		obj: Any,
		attrName: str,
		items: Optional[List[PrefItem]] = None,
	) -> None:
		self.obj = obj
		self.attrName = attrName
		if vertical:
			box = VBox()
		else:
			box = HBox()
		if items is None:
			items = []
		for item in items:
			pack(box, item.getWidget())
		self.num = len(items)
		self.items = items
		self._widget = box

	def get(self) -> List[Any]:
		return [
			item.get()
			for item in self.items
		]

	def set(self, valueL: List[Any]):
		for i in range(self.num):
			self.items[i].set(valueL[i])

	def append(self, item: PrefItem) -> None:
		pack(self._widget, Item.getWidget())
		self.items.append(item)


class HListPrefItem(ListPrefItem):
	def __init__(self, *args, **kwargs) -> None:
		ListPrefItem.__init__(self, False, *args, **kwargs)


class VListPrefItem(ListPrefItem):
	def __init__(self, *args, **kwargs) -> None:
		ListPrefItem.__init__(self, True, *args, **kwargs)


class DirectionPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.direction_combo import DirectionComboBox
		###
		self.obj = obj
		self.attrName = attrName
		self._onChangeFunc = onChangeFunc
		###
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Direction")))
		combo = DirectionComboBox()
		self._combo = combo
		pack(hbox, combo)
		combo.connect("changed", self.onComboChange)
		self._widget = hbox
		###
		self.updateWidget()

	def get(self) -> str:
		"""
			returns one of "ltr", "rtl", "auto"
		"""
		return self._combo.getValue()

	def set(self, value: str) -> None:
		"""
			value must be one of "ltr", "rtl", "auto"
		"""
		self._combo.setValue(value)

	def onComboChange(self, w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class JustificationPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		label: str = "",
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.justification_combo import JustificationComboBox
		###
		self.obj = obj
		self.attrName = attrName
		self._onChangeFunc = onChangeFunc
		###
		hbox = HBox(spacing=10)
		if label:
			pack(hbox, gtk.Label(label=label))
		combo = JustificationComboBox()
		self._combo = combo
		pack(hbox, combo)
		combo.connect("changed", self.onComboChange)
		self._widget = hbox
		###
		self.updateWidget()

	def get(self) -> str:
		"""
			returns one of "left", "right", "center", "fill"
		"""
		return self._combo.getValue()

	def set(self, value: str) -> None:
		"""
			value must be one of "left", "right", "center", "fill"
		"""
		self._combo.setValue(value)

	def onComboChange(self, w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()
