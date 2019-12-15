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

from scal3 import logger
log = logger.get()

from typing import Optional, Callable, Any, List
from os.path import join, isabs

from scal3.path import *
from scal3.cal_types import calTypes
from scal3 import core
from scal3 import locale_man
from scal3.locale_man import langDict, rtl
from scal3.locale_man import tr as _
from scal3 import startup
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	set_tooltip,
	pixbufFromFile,
)
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	StaticToolBox,
)

from scal3.ui_gtk.pref_utils import PrefItem


def newBox(vertical: bool, homogeneous: bool) -> gtk.Box:
	if vertical:
		box = VBox()
	else:
		box = HBox()
	box.set_homogeneous(homogeneous)
	return box


class FixedSizeOrRatioPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		ratioEnableVarName: str = "",
		fixedLabel: str = "",
		fixedItem: Optional["SpinPrefItem"] = None,
		ratioLabel: str = "",
		ratioItem: Optional["SpinPrefItem"] = None,
		vspacing: int = 0,
		hspacing: int = 0,
		borderWidth: int = 2,
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		if not ratioEnableVarName:
			raise ValueError("ratioEnableVarName is not given")
		if not fixedLabel:
			raise ValueError("fixedLabel is not given")
		if fixedItem is None:
			raise ValueError("fixedItem is not given")
		if not ratioLabel:
			raise ValueError("ratioLanel is not given")
		if ratioItem is None:
			raise ValueError("ratioItem is not given")
		self.obj = obj
		self.ratioEnableVarName = ratioEnableVarName
		self.fixedItem = fixedItem
		self.ratioItem = ratioItem
		self.fixedRadio = gtk.RadioButton(label=fixedLabel)
		self.ratioRadio = gtk.RadioButton(label=ratioLabel, group=self.fixedRadio)
		self._onChangeFunc = onChangeFunc
		#####
		vbox = VBox(spacing=vspacing)
		vbox.set_border_width(borderWidth)
		##
		hbox = HBox(spacing=hspacing)
		pack(hbox, self.fixedRadio)
		pack(hbox, fixedItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		##
		hbox = HBox(spacing=hspacing)
		pack(hbox, self.ratioRadio)
		pack(hbox, ratioItem.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		####
		vbox.show_all()
		self._widget = vbox
		self.updateWidget()
		#####
		fixedItem.getWidget().connect("changed", self.onChange)
		ratioItem.getWidget().connect("changed", self.onChange)
		self.fixedRadio.connect("clicked", self.onChange)
		self.ratioRadio.connect("clicked", self.onChange)

	def updateVar(self) -> None:
		setattr(self.obj, self.ratioEnableVarName, self.ratioRadio.get_active())
		self.fixedItem.updateVar()
		self.ratioItem.updateVar()

	def updateWidget(self) -> None:
		self.ratioRadio.set_active(getattr(self.obj, self.ratioEnableVarName))
		self.fixedItem.updateWidget()
		self.ratioItem.updateWidget()

	def onChange(self, w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class WeekDayCheckListPrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		vertical: bool = False,
		homogeneous: bool = True,
		abbreviateNames: bool = True,
		twoRows: bool = False
	) -> None:
		self.obj = obj
		self.attrName = attrName
		self.vertical = vertical
		self.homogeneous = homogeneous
		self.twoRows = twoRows
		self.start = core.firstWeekDay
		self.buttons = [
			gtk.ToggleButton(label=name)
			for name in
			(core.weekDayNameAb if abbreviateNames else core.weekDayName)
		]
		if self.twoRows:
			self._widget = newBox(not self.vertical, self.homogeneous)
		else:
			self._widget = newBox(self.vertical, self.homogeneous)
		self.updateBoxChildren()

	def updateBoxChildren(self) -> None:
		buttons = self.buttons
		start = self.start
		mainBox = self._widget
		for child in mainBox.get_children():
			mainBox.remove(child)
			for child2 in child.get_children():
				child.remove(child2)
		if self.twoRows:
			box1 = newBox(self.vertical, self.homogeneous)
			box2 = newBox(self.vertical, self.homogeneous)
			pack(mainBox, box1)
			pack(mainBox, box2)
			for i in range(4):
				pack(box1, buttons[(start + i) % 7], 1, 1)
			for i in range(4, 7):
				pack(box2, buttons[(start + i) % 7], 1, 1)
		else:
			for i in range(7):
				pack(mainBox, buttons[(start + i) % 7], 1, 1)
		mainBox.show_all()

	def setStart(self, start: int) -> None:
		self.start = start
		self.updateBoxChildren()

	def get(self) -> List[int]:
		return [
			index
			for index, button in enumerate(self.buttons)
			if button.get_active()
		]

	def set(self, value: List[int]):
		buttons = self.buttons
		for button in buttons:
			button.set_active(False)
		for index in value:
			buttons[index].set_active(True)


"""
class ToolbarIconSizePrefItem(PrefItem):
	def __init__(self, obj, attrName):
		self.obj = obj
		self.attrName = attrName
		####
		self._widget = gtk.ComboBoxText()
		for item in ud.iconSizeList:
			self._widget.append_text(item[0])

	def get(self):
		return ud.iconSizeList[self._widget.get_active()][0]

	def set(self, value):
		for (i, item) in enumerate(ud.iconSizeList):
			if item[0] == value:
				self._widget.set_active(i)
				return
"""

############################################################


class CalTypePrefItem(PrefItem):
	def __init__(
		self,
		obj: Any,
		attrName: str,
		live: bool = False,
		onChangeFunc: Optional[Callable] = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo
		self.obj = obj
		self.attrName = attrName
		self._onChangeFunc = onChangeFunc
		###
		hbox = gtk.HBox()
		pack(hbox, gtk.Label(label=_("Calendar Type") + " "))
		self._combo = CalTypeCombo(hasDefault=True)
		pack(hbox, self._combo)
		self._widget = hbox
		###
		if live:
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			self._combo.connect("changed", self.onClick)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> int:
		return self._combo.get_active()

	def set(self, value: int) -> None:
		self._combo.set_active(value)

	def onClick(self, w):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class LangPrefItem(PrefItem):
	def __init__(self) -> None:
		self.obj = locale_man
		self.attrName = "lang"
		###
		ls = gtk.ListStore(str)
		combo = gtk.ComboBox()
		combo.set_model(ls)
		###
		cell = gtk.CellRendererText()
		pack(combo, cell, True)
		combo.add_attribute(cell, "text", 0)
		###
		self._widget = combo
		self.ls = ls
		self.ls.append([_("System Setting")])
		for (key, langObj) in langDict.items():
			# isinstance(langObj, locale_man.LangData)
			self.ls.append([langObj.name])

	def get(self) -> str:
		i = self._widget.get_active()
		if i == 0:
			return ""
		else:
			return langDict.keyList[i - 1]

	def set(self, value: str) -> None:
		if value == "":
			self._widget.set_active(0)
		else:
			try:
				i = langDict.keyList.index(value)
			except ValueError:
				log.info(f"language {value!r} in not in list!")
				self._widget.set_active(0)
			else:
				self._widget.set_active(i + 1)

	#def updateVar(self):
	#	lang =


class CheckStartupPrefItem(PrefItem):  # FIXME
	def __init__(self) -> None:
		w = gtk.CheckButton(label=_("Run on session startup"))
		set_tooltip(
			w,
			f"Run on startup of Gnome, KDE, Xfce, LXDE, ...\nFile: {startup.comDesk}"
		)
		self._widget = w

	def get(self) -> bool:
		return self._widget.get_active()

	def set(self, value: bool) -> None:
		self._widget.set_active(value)

	def updateVar(self) -> None:
		if self.get():
			if not startup.addStartup():
				self.set(False)
		else:
			try:
				startup.removeStartup()
			except Exception:
				pass

	def updateWidget(self) -> None:
		self.set(
			startup.checkStartup()
		)


class AICalsTreeview(gtk.TreeView):
	def __init__(self) -> None:
		gtk.TreeView.__init__(self)
		self.set_headers_clickable(False)
		self.set_model(gtk.ListStore(str, str))
		###
		self.enable_model_drag_source(
			gdk.ModifierType.BUTTON1_MASK,
			[
				("row", gtk.TargetFlags.SAME_APP, self.dragId),
			],
			gdk.DragAction.MOVE,
		)
		self.enable_model_drag_dest(
			[
				("row", gtk.TargetFlags.SAME_APP, self.dragId),
			],
			gdk.DragAction.MOVE,
		)
		self.connect("drag-data-get", self.dragDataGet)
		self.connect("drag_data_received", self.dragDataReceived)
		####
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(self.title, cell_renderer=cell, text=1)
		col.set_resizable(True)
		self.append_column(col)
		self.set_search_column(1)

	def dragDataGet(
		self,
		treev: gtk.TreeView,
		context: gdk.DragContext,
		selection: gtk.SelectionData,
		dragId: int,
		etime: int,
	) -> bool:
		path, col = treev.get_cursor()
		if path is None:
			return False
		self.dragPath = path
		return True

	def dragDataReceived(
		self,
		treev: gtk.TreeView,
		context: gdk.DragContext,
		x: int,
		y: int,
		selection: gtk.SelectionData,
		dragId: int,
		etime: int,
	) -> None:
		srcTreev = gtk.drag_get_source_widget(context)
		if not isinstance(srcTreev, AICalsTreeview):
			return
		srcDragId = srcTreev.dragId
		model = treev.get_model()
		dest = treev.get_dest_row_at_pos(x, y)
		if srcDragId == self.dragId:
			path, col = treev.get_cursor()
			if path is None:
				return
			i = path[0]
			if dest is None:
				model.move_after(
					model.get_iter(i),
					model.get_iter(len(model) - 1),
				)
			elif dest[1] in (
				gtk.TreeViewDropPosition.BEFORE,
				gtk.TreeViewDropPosition.INTO_OR_BEFORE,
			):
				model.move_before(
					model.get_iter(i),
					model.get_iter(dest[0][0]),
				)
			else:
				model.move_after(
					model.get_iter(i),
					model.get_iter(dest[0][0]),
				)
		else:
			smodel = srcTreev.get_model()
			sIter = smodel.get_iter(srcTreev.dragPath)
			row = [
				smodel.get(sIter, j)[0]
				for j in range(2)
			]
			smodel.remove(sIter)
			if dest is None:
				model.append(row)
			elif dest[1] in (
				gtk.TreeViewDropPosition.BEFORE,
				gtk.TreeViewDropPosition.INTO_OR_BEFORE,
			):
				model.insert_before(
					model.get_iter(dest[0]),
					row,
				)
			else:
				model.insert_after(
					model.get_iter(dest[0]),
					row,
				)

	def makeSwin(self) -> gtk.ScrolledWindow:
		swin = gtk.ScrolledWindow()
		swin.add(self)
		swin.set_policy(gtk.PolicyType.EXTERNAL, gtk.PolicyType.AUTOMATIC)
		# swin.set_min_content_width(200)
		return swin


class ActiveCalsTreeView(AICalsTreeview):
	isActive = True
	title = _("Active")
	dragId = 100


class InactiveCalsTreeView(AICalsTreeview):
	isActive = False
	title = _("Inactive")
	dragId = 101


class AICalsPrefItemToolbar(StaticToolBox):
	def __init__(self, parent):
		StaticToolBox.__init__(
			self,
			parent,
			vertical=True,
		)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size

		# _leftRightAction: "" | "activate" | "inactivate"
		self._leftRightAction = ""

		self.leftRightItem = ToolBoxItem(
			name="left-right",
			imageNameDynamic=True,
			onClick="onLeftRightClick",
			desc=_("Activate/Inactivate"),
			continuousClick=False,
		)
		self.append(self.leftRightItem)
		self.append(ToolBoxItem(
			name="go-up",
			imageName="go-up.svg",
			onClick="onUpClick",
			desc=_("Move up"),
			continuousClick=False,
		))
		self.append(ToolBoxItem(
			name="go-down",
			imageName="go-down.svg",
			onClick="onDownClick",
			desc=_("Move down"),
			continuousClick=False,
		))

	def getLeftRightAction(self):
		return self._leftRightAction

	def setLeftRight(self, isRight: Optional[bool]) -> None:
		tb = self.leftRightItem
		if isRight is None:
			tb.setIconFile("")
			self._leftRightAction = ""
		else:
			tb.setIconFile(
				"go-next.svg" if isRight ^ rtl else "go-previous.svg"
			)
			self._leftRightAction = "inactivate" if isRight else "activate"
		tb.show_all()


class AICalsPrefItem(PrefItem):
	def __init__(self) -> None:
		self._widget = HBox()
		########
		treev = ActiveCalsTreeView()
		treev.connect("row-activated", self.activeTreevRActivate)
		treev.connect("focus-in-event", self.activeTreevFocus)
		treev.get_selection().connect(
			"changed",
			self.activeTreevSelectionChanged,
		)
		###
		pack(self._widget, treev.makeSwin(), 1, 1)
		####
		self.activeTreev = treev
		self.activeTrees = treev.get_model()
		########
		toolbar = AICalsPrefItemToolbar(self)
		toolbar.show_all()
		self.toolbar = toolbar
		pack(self._widget, toolbar)
		########
		treev = InactiveCalsTreeView()
		treev.connect("row-activated", self.inactiveTreevRActivate)
		treev.connect("focus-in-event", self.inactiveTreevFocus)
		treev.get_selection().connect(
			"changed",
			self.inactiveTreevSelectionChanged,
		)
		###
		pack(self._widget, treev.makeSwin(), 1, 1)
		####
		self.inactiveTreev = treev
		self.inactiveTrees = treev.get_model()
		########

	def activeTreevFocus(
		self,
		treev: gtk.TreeView,
		gevent: Optional[gdk.EventFocus] = None,
	) -> None:
		self.toolbar.setLeftRight(True)

	def inactiveTreevFocus(
		self,
		treev: gtk.TreeView,
		gevent: Optional[gdk.EventFocus] = None,
	) -> None:
		self.toolbar.setLeftRight(False)

	def onLeftRightClick(self, obj: Optional[gtk.Button] = None) -> None:
		action = self.toolbar.getLeftRightAction()
		if action == "activate":
			path, col = self.inactiveTreev.get_cursor()
			if path:
				self.activateIndex(path[0])
		elif action == "inactivate":
			if len(self.activeTrees) > 1:
				path, col = self.activeTreev.get_cursor()
				if path:
					self.inactivateIndex(path[0])

	def getCurrentTreeview(self) -> gtk.TreeView:
		action = self.toolbar.getLeftRightAction()
		if action == "inactivate":
			return self.activeTreev
		elif action == "activate":
			return self.inactiveTreev
		else:
			return

	def onUpClick(self, obj: Optional[gtk.Button] = None) -> None:
		treev = self.getCurrentTreeview()
		if not treev:
			return
		path, col = treev.get_cursor()
		if path:
			i = path[0]
			s = treev.get_model()
			if i > 0:
				s.swap(
					s.get_iter(i - 1),
					s.get_iter(i),
				)
				treev.set_cursor(i - 1)

	def onDownClick(self, obj: Optional[gtk.Button] = None) -> None:
		treev = self.getCurrentTreeview()
		if not treev:
			return
		path, col = treev.get_cursor()
		if path:
			i = path[0]
			s = treev.get_model()
			if i < len(s) - 1:
				s.swap(
					s.get_iter(i),
					s.get_iter(i + 1),
				)
				treev.set_cursor(i + 1)

	def inactivateIndex(self, index: int) -> None:
		if len(self.activeTrees) < 2:
			log.warning("You need at least one active calendar type!")
			return
		self.inactiveTrees.prepend(list(self.activeTrees[index]))
		del self.activeTrees[index]
		self.inactiveTreev.set_cursor(0)
		self.activeTreev.set_cursor(min(
			index,
			len(self.activeTrees) - 1
		))
		# set_cursor does not seem to raise exception anymore on invalid index
		self.inactiveTreev.grab_focus()

	def activateIndex(self, index: int) -> None:
		self.activeTrees.append(list(self.inactiveTrees[index]))
		del self.inactiveTrees[index]
		self.activeTreev.set_cursor(len(self.activeTrees) - 1)
		if len(self.inactiveTrees) > 0:
			self.inactiveTreev.set_cursor(min(
				index,
				len(self.inactiveTrees) - 1,
			))
		self.activeTreev.grab_focus()

	def activeTreevSelectionChanged(self, selection: gtk.TreeSelection) -> None:
		if selection.count_selected_rows() > 0:
			self.toolbar.setLeftRight(True)
		else:
			self.toolbar.setLeftRight(None)

	def inactiveTreevSelectionChanged(self, selection: gtk.TreeSelection) -> None:
		if selection.count_selected_rows() > 0:
			self.toolbar.setLeftRight(False)
		else:
			self.toolbar.setLeftRight(None)

	def activeTreevRActivate(
		self,
		treev: gtk.TreeView,
		path: List[int],
		col: gtk.TreeViewColumn,
	) -> None:
		self.inactivateIndex(path[0])

	def inactiveTreevRActivate(
		self,
		treev: gtk.TreeView,
		path: List[int],
		col: gtk.TreeViewColumn,
	):
		self.activateIndex(path[0])

	def get(self) -> Any:
		activeNames = [row[0] for row in self.activeTrees]
		inactiveNames = [row[0] for row in self.inactiveTrees]
		return (activeNames, inactiveNames)

	def updateVar(self) -> None:
		calTypes.activeNames, calTypes.inactiveNames = self.get()
		calTypes.update()

	def updateWidget(self) -> None:
		self.activeTrees.clear()
		self.inactiveTrees.clear()
		##
		for calType in calTypes.active:
			module, ok = calTypes[calType]
			if not ok:
				raise RuntimeError(f"cal type '{calType}' not found")
			self.activeTrees.append([module.name, _(module.desc)])
		##
		for calType in calTypes.inactive:
			module, ok = calTypes[calType]
			if not ok:
				raise RuntimeError(f"cal type '{calType}' not found")
			self.inactiveTrees.append([module.name, _(module.desc)])
