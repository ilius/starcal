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

from scal3.path import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import set_tooltip, dialog_add_button


from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton


# (VAR_NAME, bool,     CHECKBUTTON_TEXT)                 ## CheckButton
# (VAR_NAME, list,     LABEL_TEXT, (ITEM1, ITEM2, ...))  ## ComboBox
# (VAR_NAME, int,      LABEL_TEXT, MIN, MAX)             ## SpinButton
# (VAR_NAME, float,    LABEL_TEXT, MIN, MAX, DIGITS)     ## SpinButton
class ModuleOptionItem:
	def __init__(self, module, opt):
		t = opt[1]
		self.opt = opt ## needed??
		self.module = module
		self.type = t
		self.var_name = opt[0]
		hbox = gtk.HBox()
		if t == bool:
			w = gtk.CheckButton(_(opt[2]))
			self.get_value = w.get_active
			self.set_value = w.set_active
		elif t == list:
			pack(hbox, gtk.Label(_(opt[2])))
			w = gtk.ComboBoxText()  # or RadioButton
			for s in opt[3]:
				w.append_text(_(s))
			self.get_value = w.get_active
			self.set_value = w.set_active
		elif t == int:
			pack(hbox, gtk.Label(_(opt[2])))
			w = IntSpinButton(opt[3], opt[4])
			self.get_value = w.get_value
			self.set_value = w.set_value
		elif t == float:
			pack(hbox, gtk.Label(_(opt[2])))
			w = FloatSpinButton(opt[3], opt[4], opt[5])
			self.get_value = w.get_value
			self.set_value = w.set_value
		else:
			raise RuntimeError("bad option type \"%s\"" % t)
		pack(hbox, w)
		self._widget = hbox
		####

	def updateVar(self):
		setattr(
			self.module,
			self.var_name,
			self.get_value(),
		)

	def updateWidget(self):
		self.set_value(
			getattr(self.module, self.var_name)
		)

	def getWidget(self):
		return self._widget

# ("button", LABEL, CLICKED_MODULE_NAME, CLICKED_FUNCTION_NAME)
class ModuleOptionButton:
	def __init__(self, opt):
		funcName = opt[2]
		clickedFunc = getattr(
			__import__(
				"scal3.ui_gtk.%s" % opt[1],
				fromlist=[funcName],
			),
			funcName,
		)
		hbox = gtk.HBox()
		button = gtk.Button(_(opt[0]))
		button.connect("clicked", clickedFunc)
		pack(hbox, button)
		self._widget = hbox

	def updateVar(self):
		pass

	def updateWidget(self):
		pass

	def getWidget(self):
		return self._widget

class PrefItem():
	# self.__init__, self.module, self.varName, self._widget
	# self.varName an string containing the name of variable
	# set self.module is None if varName is name of a global variable
	# in this module
	def get(self):
		raise NotImplementedError

	def set(self, value):
		raise NotImplementedError

	def updateVar(self):
		setattr(
			self.module,
			self.varName,
			self.get(),
		)

	def updateWidget(self):
		self.set(
			getattr(self.module, self.varName)
		)

	def getWidget(self):
		return self._widget

class ComboTextPrefItem(PrefItem):
	def makeWidget(self):
		return gtk.ComboBoxText()

	def __init__(self, module, varName, items=[]):## items is a list of strings
		self.module = module
		self.varName = varName
		w = self.makeWidget()
		self._widget = w
		for s in items:
			w.append_text(s)

	def get(self):
		return self._widget.get_active()

	def set(self, value):
		self._widget.set_active(value)


class FontFamilyPrefItem(ComboTextPrefItem):
	def makeWidget(self):
		from scal3.ui_gtk.mywidgets.font_family_combo import FontFamilyCombo
		return FontFamilyCombo(True)

	def get(self):
		return self._widget.get_value()

	def set(self, value):
		self._widget.set_value(value)


class ComboEntryTextPrefItem(PrefItem):
	def __init__(self, module, varName, items=[]):
		"""items is a list of strings"""
		self.module = module
		self.varName = varName
		w = gtk.ComboBoxText.new_with_entry()
		self._widget = w
		for s in items:
			w.append_text(s)

	def get(self):
		return self._widget.get_child().get_text()

	def set(self, value):
		self._widget.get_child().set_text(value)


class ComboImageTextPrefItem(PrefItem):
	def __init__(self, module, varName, items=[]):
		"""
		items is a list of (imagePath, text) tuples
		"""
		self.module = module
		self.varName = varName
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
		for (imPath, label) in items:
			self.append(imPath, label)

	def get(self):
		return self._widget.get_active()

	def set(self, value):
		self._widget.set_active(value)

	def append(self, imPath, label):
		if imPath:
			if not isabs(imPath):
				imPath = join(pixDir, imPath)
			pix = GdkPixbuf.Pixbuf.new_from_file(imPath)
		else:
			pix = None
		self.ls.append([pix, label])


class FontPrefItem(PrefItem):  # FIXME
	def __init__(self, module, varName, parent):
		from scal3.ui_gtk.mywidgets import MyFontButton
		self.module = module
		self.varName = varName
		w = MyFontButton(parent)
		self._widget = w

	def get(self):
		return self._widget.get_font_name()  # FIXME

	def set(self, value):
		self._widget.set_font_name(value)


class CheckPrefItem(PrefItem):
	def __init__(self, module, varName, label="", tooltip=""):
		self.module = module
		self.varName = varName
		w = gtk.CheckButton(label)
		if tooltip:
			set_tooltip(w, tooltip)
		self._widget = w

	def get(self):
		return self._widget.get_active()

	def set(self, value):
		self._widget.set_active(value)

	def syncSensitive(self, widget, reverse=False):
		self._sensitiveWidget = widget
		self._sensitiveReverse = reverse
		self._widget.connect("show", self.syncSensitiveUpdate)
		self._widget.connect("clicked", self.syncSensitiveUpdate)

	def syncSensitiveUpdate(self, myWidget):
		active = myWidget.get_active()
		if self._sensitiveReverse:
			active = not active
		self._sensitiveWidget.set_sensitive(active)


class LiveCheckPrefItem(CheckPrefItem):
	def __init__(self, module, varName, label="", tooltip="", onChangeFunc: "Optional[Callable]" = None):
		CheckPrefItem.__init__(self, module, varName, label=label, tooltip=tooltip)
		self._onChangeFunc = onChangeFunc
		# updateWidget needs to be called before following connect() calls
		self.updateWidget()
		self._widget.connect("clicked", self.onClicked)

	def onClicked(self, w):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

class ColorPrefItem(PrefItem):
	def __init__(self, module, varName, useAlpha=False):
		from scal3.ui_gtk.mywidgets import MyColorButton
		self.module = module
		self.varName = varName
		w = MyColorButton()
		w.set_use_alpha(useAlpha)
		self.useAlpha = useAlpha
		self._widget = w

	def get(self):
		#if self.useAlpha:
		alpha = self._widget.get_alpha()
		if alpha is None:
			return self._widget.get_color()
		else:
			return self._widget.get_color() + (alpha,)

	def set(self, color):
		if self.useAlpha:
			if len(color) == 3:
				self._widget.set_color(color)
				self._widget.set_alpha(255)
			elif len(color) == 4:
				self._widget.set_color(color[:3])
				self._widget.set_alpha(color[3])
			else:
				raise ValueError
		else:
			self._widget.set_color(color)


class LiveColorPrefItem(ColorPrefItem):
	def __init__(self, module, varName, useAlpha=False, onChangeFunc: "Optional[Callable]" = None):
		ColorPrefItem.__init__(self, module, varName, useAlpha=useAlpha)
		self._onChangeFunc = onChangeFunc
		# updateWidget needs to be called before following connect() calls
		self.updateWidget()
		self._widget.connect("color-set", self.onColorSet)

	def onColorSet(self, w):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


# combination of CheckPrefItem and ColorPrefItem in a HBox, with auto-update / auto-apply, for use in Customize window
class LiveCheckColorPrefItem(PrefItem):
	def __init__(self, checkItem: CheckPrefItem, colorItem: ColorPrefItem, onChangeFunc: "Optional[Callable]" = None):
		self._checkItem = checkItem
		self._colorItem = colorItem
		self._onChangeFunc = onChangeFunc

		checkb = self._checkItem.getWidget()
		colorb = self._colorItem.getWidget()

		hbox = gtk.HBox(spacing=3)
		pack(hbox, checkb)
		pack(hbox, colorb)
		self._widget = hbox

		# updateWidget needs to be called before following connect() calls
		self.updateWidget()

		checkb.connect("clicked", self.onChange)
		colorb.connect("color-set", self.onChange)

	def updateVar(self):
		self._checkItem.updateVar()
		self._colorItem.updateVar()

	def updateWidget(self):
		# FIXME: this func is triggering onChange func, can we avoid that?
		self._checkItem.updateWidget()
		self._colorItem.updateWidget()
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())

	def onChange(self, w):
		self.updateVar()
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())
		if self._onChangeFunc:
			self._onChangeFunc()


class SpinPrefItem(PrefItem):
	def __init__(self, module, varName, _min, _max, digits=1):
		self.module = module
		self.varName = varName
		if digits == 0:
			w = IntSpinButton(_min, _max)
		else:
			w = FloatSpinButton(_min, _max, digits)
		self._widget = w

	def get(self):
		return self._widget.get_value()

	def set(self, value):
		self._widget.set_value(value)


class LiveLabelSpinPrefItem(PrefItem):
	def __init__(self, label: str, spinItem: SpinPrefItem, onChangeFunc: "Optional[Callable]" = None):
		self._spinItem = spinItem
		self._onChangeFunc = onChangeFunc

		spinb = self._spinItem.getWidget()

		hbox = gtk.HBox(spacing=3)
		pack(hbox, gtk.Label(label))
		pack(hbox, spinb)
		self._widget = hbox

		# updateWidget needs to be called before following connect() calls
		self.updateWidget()

		spinb.connect("changed", self.onChange)

	def updateVar(self):
		self._spinItem.updateVar()

	def updateWidget(self):
		# FIXME: this func is triggering onChange func, can we avoid that?
		self._spinItem.updateWidget()

	def onChange(self, w):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class WidthHeightPrefItem(PrefItem):
	def __init__(self, module, varName, _max):
		_min = 0
		self.module = module
		self.varName = varName
		###
		self.widthItem = IntSpinButton(_min, _max)
		self.heightItem = IntSpinButton(_min, _max)
		###
		hbox = self._widget = gtk.HBox()
		pack(hbox, gtk.Label(_("Width") + ":"))
		pack(hbox, self.widthItem)
		pack(hbox, gtk.Label("  "))
		pack(hbox, gtk.Label(_("Height") + ":"))
		pack(hbox, self.heightItem)

	def get(self):
		return (
			int(self.widthItem.get_value()),
			int(self.heightItem.get_value()),
		)

	def set(self, value):
		w, h = value
		self.widthItem.set_value(w)
		self.heightItem.set_value(h)


class FileChooserPrefItem(PrefItem):
	def __init__(
		self,
		module,
		varName,
		title="Select File",
		currentFolder="",
		defaultVarName=None,
	):
		self.module = module
		self.varName = varName
		###
		dialog = gtk.FileChooserDialog(
			title,
			action=gtk.FileChooserAction.OPEN,
		)
		dialog_add_button(
			dialog,
			gtk.STOCK_CANCEL,
			_("_Cancel"),
			gtk.ResponseType.CANCEL,
			None,
		)
		dialog_add_button(
			dialog,
			gtk.STOCK_OK,
			_("_OK"),
			gtk.ResponseType.OK,
			None,
		)
		w = gtk.FileChooserButton(dialog)
		w.set_local_only(True)
		if currentFolder:
			w.set_current_folder(currentFolder)
		###
		self.defaultVarName = defaultVarName
		if defaultVarName:
			dialog_add_button(
				dialog,
				gtk.STOCK_UNDO,
				_("_Revert"),
				gtk.ResponseType.NONE,
				self.revertClicked,
			)
		###
		self._widget = w

	def get(self):
		return self._widget.get_filename()

	def set(self, value):
		self._widget.set_filename(value)

	def revertClicked(self, button):
		defaultValue = getattr(self.module, self.defaultVarName)
		setattr(
			self.module,
			self.varName,
			defaultValue,
		)
		self.set(defaultValue)


class RadioListPrefItem(PrefItem):
	def __init__(self, vertical, module, varName, texts, label=None):
		self.num = len(texts)
		self.module = module
		self.varName = varName
		if vertical:
			box = gtk.VBox()
		else:
			box = gtk.HBox()
		self._widget = box
		self.radios = [
			gtk.RadioButton(label=_(s))
			for s in texts
		]
		first = self.radios[0]
		if label is not None:
			pack(box, gtk.Label(label))
			pack(box, gtk.Label(""), 1, 1)
		pack(box, first)
		for r in self.radios[1:]:
			pack(box, gtk.Label(""), 1, 1)
			pack(box, r)
			r.set_group(first)
		pack(box, gtk.Label(""), 1, 1) ## FIXME

	def get(self):
		for i in range(self.num):
			if self.radios[i].get_active():
				return i

	def set(self, index):
		self.radios[index].set_active(True)


class RadioHListPrefItem(RadioListPrefItem):
	def __init__(self, *args, **kwargs):
		RadioListPrefItem.__init__(self, False, *args, **kwargs)


class RadioVListPrefItem(RadioListPrefItem):
	def __init__(self, *args, **kwargs):
		RadioListPrefItem.__init__(self, True, *args, **kwargs)


class ListPrefItem(PrefItem):
	def __init__(self, vertical, module, varName, items=[]):
		self.module = module
		self.varName = varName
		if vertical:
			box = gtk.VBox()
		else:
			box = gtk.HBox()
		for item in items:
			pack(box, Item.getWidget())
		self.num = len(items)
		self.items = items
		self._widget = box

	def get(self):
		return [
			item.get()
			for item in self.items
		]

	def set(self, valueL):
		for i in range(self.num):
			self.items[i].set(valueL[i])

	def append(self, item):
		pack(self._widget, Item.getWidget())
		self.items.append(item)


class HListPrefItem(ListPrefItem):
	def __init__(self, *args, **kwargs):
		ListPrefItem.__init__(self, False, *args, **kwargs)


class VListPrefItem(ListPrefItem):
	def __init__(self, *args, **kwargs):
		ListPrefItem.__init__(self, True, *args, **kwargs)

