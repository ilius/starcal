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

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from scal3 import core, startup
from scal3.cal_types import calTypes
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.ui_gtk import gdk, gtk, pack
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.option_ui.base import OptionUI
from scal3.ui_gtk.toolbox import ToolBoxItem, VerticalStaticToolBox
from scal3.ui_gtk.utils import set_tooltip

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.option import ListOption, Option, StrDictOption
	from scal3.ui_gtk.option_ui.spin import FloatSpinOptionUI, IntSpinOptionUI

__all__ = [
	"ActiveInactiveCalsOptionUI",
	"CalTypeOptionUI",
	"CheckStartupOptionUI",
	"FixedSizeOrRatioOptionUI",
	"KeyBindingOptionUI",
	"WeekDayCheckListOptionUI",
]


def newBox(vertical: bool, homogeneous: bool) -> gtk.Box:
	if vertical:
		box = gtk.Box(orientation=gtk.Orientation.VERTICAL)
	else:
		box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
	box.set_homogeneous(homogeneous)
	return box


class FixedSizeOrRatioOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		ratioEnableOption: Option[bool] | None,
		fixedLabel: str = "",
		fixedItem: IntSpinOptionUI | None = None,
		ratioLabel: str = "",
		ratioItem: FloatSpinOptionUI | None = None,
		vspacing: int = 0,
		hspacing: int = 0,
		borderWidth: int = 2,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		if not ratioEnableOption:
			raise ValueError("ratioEnableVarName is not given")
		if not fixedLabel:
			raise ValueError("fixedLabel is not given")
		if fixedItem is None:
			raise ValueError("fixedItem is not given")
		if not ratioLabel:
			raise ValueError("ratioLanel is not given")
		if ratioItem is None:
			raise ValueError("ratioItem is not given")
		self.ratioEnableOption = ratioEnableOption
		self.fixedItem = fixedItem
		self.ratioItem = ratioItem
		self.fixedRadio = gtk.RadioButton(label=fixedLabel)
		self.ratioRadio = gtk.RadioButton(label=ratioLabel, group=self.fixedRadio)
		self._onChangeFunc = onChangeFunc
		# -----
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=vspacing)
		vbox.set_border_width(borderWidth)
		# --
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=hspacing)
		pack(hbox, self.fixedRadio)
		pack(hbox, fixedItem.getWidget())
		pack(hbox, gtk.Label(label=_("pixels")))
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		# --
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=hspacing)
		pack(hbox, self.ratioRadio)
		pack(hbox, ratioItem.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		# ----
		vbox.show_all()
		self._widget = vbox
		self.updateWidget()
		# -----
		fixedItem.getWidget().connect("changed", self.onChange)
		ratioItem.getWidget().connect("changed", self.onChange)
		self.fixedRadio.connect("clicked", self.onChange)
		self.ratioRadio.connect("clicked", self.onChange)

	def updateVar(self) -> None:
		self.ratioEnableOption.v = self.ratioRadio.get_active()
		self.fixedItem.updateVar()
		self.ratioItem.updateVar()

	def updateWidget(self) -> None:
		self.ratioRadio.set_active(self.ratioEnableOption.v)
		self.fixedItem.updateWidget()
		self.ratioItem.updateWidget()

	def onChange(self, _w: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class WeekDayCheckListOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: ListOption[int],
		vertical: bool = False,
		homogeneous: bool = True,
		abbreviateNames: bool = True,
		twoRows: bool = False,
	) -> None:
		self.option = option
		self.vertical = vertical
		self.homogeneous = homogeneous
		self.twoRows = twoRows
		self.start = core.firstWeekDay.v
		self.buttons = [
			gtk.ToggleButton(label=name)
			for name in (core.weekDayNameAb if abbreviateNames else core.weekDayName)
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
			if isinstance(child, gtk.Container):
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

	def get(self) -> list[int]:
		return [
			index for index, button in enumerate(self.buttons) if button.get_active()
		]

	def set(self, value: list[int]) -> None:
		buttons = self.buttons
		for button in buttons:
			button.set_active(False)
		for index in value:
			buttons[index].set_active(True)


"""
class ToolbarIconSizeOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(self, option: Option):
		self.option = option
		# ----
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

# ------------------------------------------------------------


class CalTypeOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: Option[int],
		live: bool = False,
		onChangeFunc: Callable[[], None] | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo

		self.option = option
		self._onChangeFunc = onChangeFunc
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Calendar Type") + " "))
		self._combo = CalTypeCombo(hasDefault=True)
		pack(hbox, self._combo)
		self._widget = hbox
		# ---
		if live:
			# updateWidget needs to be called before following connect() calls
			self.updateWidget()
			self._combo.connect("changed", self.onClick)
		elif onChangeFunc is not None:
			raise ValueError("onChangeFunc is given without live=True")

	def get(self) -> int:
		value = self._combo.getActive()
		assert value is not None
		return value

	def set(self, value: int) -> None:
		self._combo.set_active(value)

	def onClick(self, _widegt: gtk.Widget) -> None:
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class CheckStartupOptionUI(OptionUI):  # FIXME
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(self) -> None:
		w = gtk.CheckButton(label=_("Run on session startup"))
		set_tooltip(
			w,
			f"Run on startup of Gnome, KDE, Xfce, LXDE, ...\nFile: {startup.comDesk}",
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
			return

		with suppress(Exception):
			startup.removeStartup()

	def updateWidget(self) -> None:
		self.set(
			startup.checkStartup(),
		)


class ActiveInactveCalsTreeview(gtk.TreeView):
	dragId = 100
	title = ""

	def __init__(self) -> None:
		gtk.TreeView.__init__(self)
		self.set_headers_clickable(False)
		self.listStore = gtk.ListStore(str, str)
		self.set_model(self.listStore)
		# ---
		self.enable_model_drag_source(
			gdk.ModifierType.BUTTON1_MASK,
			[
				gtk.TargetEntry.new("row", gtk.TargetFlags.SAME_APP, self.dragId),
			],
			gdk.DragAction.MOVE,
		)
		self.enable_model_drag_dest(
			[
				gtk.TargetEntry.new("row", gtk.TargetFlags.SAME_APP, self.dragId),
			],
			gdk.DragAction.MOVE,
		)
		self.connect("drag-data-get", self.dragDataGet)
		self.connect("drag_data_received", self.dragDataReceived)
		# ----
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(self.title, cell_renderer=cell, text=1)
		col.set_resizable(True)
		self.append_column(col)
		self.set_search_column(1)

	def dragDataGet(
		self,
		treev: gtk.TreeView,
		_context: gdk.DragContext,
		_selection: gtk.SelectionData,
		_dragId: int,
		_etime: int,
	) -> bool:
		path, _col = treev.get_cursor()
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
		_selection: gtk.SelectionData,
		_dragId: int,
		_etime: int,
	) -> None:
		srcTreev = gtk.drag_get_source_widget(context)
		if not isinstance(srcTreev, ActiveInactveCalsTreeview):
			return
		srcDragId = srcTreev.dragId
		model = self.listStore
		dest = treev.get_dest_row_at_pos(x, y)
		if srcDragId == self.dragId:
			pathObj, _col = treev.get_cursor()
			if pathObj is None:
				return
			path = pathObj.get_indices()
			i = path[0]
			if dest is None:
				model.move_after(
					model.get_iter(str(i)),
					model.get_iter(str(len(model) - 1)),
				)
			elif dest[1] in {
				gtk.TreeViewDropPosition.BEFORE,
				gtk.TreeViewDropPosition.INTO_OR_BEFORE,
			}:
				model.move_before(
					model.get_iter(str(i)),
					model.get_iter(str(dest[0].get_indices()[0])),
				)
			else:
				model.move_after(
					model.get_iter(str(i)),
					model.get_iter(str(dest[0].get_indices()[0])),
				)
		else:
			smodel = srcTreev.listStore
			sIter = smodel.get_iter(srcTreev.dragPath)
			row = [smodel.get(sIter, [str(j)])[0] for j in range(2)]
			smodel.remove(sIter)
			if dest is None:
				model.append(row)
			elif dest[1] in {
				gtk.TreeViewDropPosition.BEFORE,
				gtk.TreeViewDropPosition.INTO_OR_BEFORE,
			}:
				model.insert_before(  # type: ignore[no-untyped-call]
					model.get_iter(dest[0]),
					row,
				)
			else:
				model.insert_after(  # type: ignore[no-untyped-call]
					model.get_iter(dest[0]),
					row,
				)

	def makeSwin(self) -> gtk.ScrolledWindow:
		swin = gtk.ScrolledWindow()
		swin.add(self)
		swin.set_policy(gtk.PolicyType.EXTERNAL, gtk.PolicyType.AUTOMATIC)
		# swin.set_min_content_width(200)
		return swin


class ActiveCalsTreeView(ActiveInactveCalsTreeview):
	isActive = True
	title = _("Active")
	dragId = 101


class InactiveCalsTreeView(ActiveInactveCalsTreeview):
	isActive = False
	title = _("Inactive")
	dragId = 102


class ActiveInactiveCalsOptionUIToolbar(VerticalStaticToolBox):
	def __init__(self, parent: ActiveInactiveCalsOptionUI) -> None:
		VerticalStaticToolBox.__init__(self, parent)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size

		# _leftRightAction: "" | "activate" | "inactivate"
		self._leftRightAction = ""

		self.leftRightItem = ToolBoxItem(
			name="left-right",
			imageNameDynamic=True,
			onClick=parent.onLeftRightClick,
			desc=_("Activate/Inactivate"),
			continuousClick=False,
		)
		self.extend(
			[
				self.leftRightItem,
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick=parent.onUpClick,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick=parent.onDownClick,
					desc=_("Move down"),
					continuousClick=False,
				),
			],
		)

	def getLeftRightAction(self) -> str:
		return self._leftRightAction

	def setLeftRight(self, isRight: bool | None) -> None:
		tb = self.leftRightItem
		if isRight is None:
			tb.setIconFile("")
			self._leftRightAction = ""
		else:
			tb.setIconFile(
				"go-next.svg" if isRight ^ rtl else "go-previous.svg",
			)
			self._leftRightAction = "inactivate" if isRight else "activate"
		tb.build()
		tb.w.show_all()


def treeviewSelect(treev: gtk.TreeView, index: int) -> None:
	path = gtk.TreePath.new_from_indices((index,))
	selection = treev.get_selection()
	# selection.unselect_all()
	selection.select_path(path)
	# col = treev.get_column(0)
	# treev.set_cursor_on_cell(path, col, col.get_cells()[0], False)
	# treev.set_cursor(path, col, False)
	# FIXME: keyboard-selection does not change!!
	# and calling set_cursor unselects it


class ActiveInactiveCalsOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(self) -> None:
		self._widget = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# --------
		activeTreev = ActiveCalsTreeView()
		activeTreev.connect("row-activated", self.activeTreevRActivate)
		activeTreev.connect("focus-in-event", self.activeTreevFocus)
		activeTreev.connect("cursor-changed", self.activeTreevFocus)
		activeTreev.get_selection().connect(
			"changed",
			self.activeTreevSelectionChanged,
		)
		# ---
		pack(self._widget, activeTreev.makeSwin(), 1, 1)
		# ----
		self.activeTreev = activeTreev
		self.activeTrees = activeTreev.listStore
		# --------
		toolbar = ActiveInactiveCalsOptionUIToolbar(self)
		toolbar.w.show_all()
		self.toolbar = toolbar
		pack(self._widget, toolbar.w)
		# --------
		inactiveTreev = InactiveCalsTreeView()
		inactiveTreev.connect("row-activated", self.inactiveTreevRActivate)
		inactiveTreev.connect("focus-in-event", self.inactiveTreevFocus)
		inactiveTreev.connect("cursor-changed", self.inactiveTreevFocus)
		inactiveTreev.get_selection().connect(
			"changed",
			self.inactiveTreevSelectionChanged,
		)
		# ---
		pack(self._widget, inactiveTreev.makeSwin(), 1, 1)
		# ----
		self.inactiveTreev = inactiveTreev
		self.inactiveTrees = inactiveTreev.listStore
		# --------

	def activeTreevFocus(
		self,
		_treev: gtk.TreeView,
		_gevent: gdk.EventFocus | None = None,
	) -> None:
		self.toolbar.setLeftRight(True)
		self.inactiveTreev.get_selection().unselect_all()

	def inactiveTreevFocus(
		self,
		_treev: gtk.TreeView,
		_gevent: gdk.EventFocus | None = None,
	) -> None:
		self.toolbar.setLeftRight(False)
		self.activeTreev.get_selection().unselect_all()

	def onLeftRightClick(self, _obj: gtk.Button | None = None) -> None:
		action = self.toolbar.getLeftRightAction()
		if action == "activate":
			selection = self.inactiveTreev.get_selection()
			model, iter_ = selection.get_selected()
			if iter_:
				self.activateIndex(model.get_path(iter_).get_indices()[0])
		elif action == "inactivate":
			if len(self.activeTrees) > 1:
				selection = self.inactiveTreev.get_selection()
				model, iter_ = selection.get_selected()
				if iter_:
					self.inactivateIndex(model.get_path(iter_).get_indices()[0])

	def getCurrentTreeview(self) -> gtk.TreeView | None:
		action = self.toolbar.getLeftRightAction()
		if action == "inactivate":
			return self.activeTreev
		if action == "activate":
			return self.inactiveTreev
		return None

	def getCurrentTreestore(self) -> gtk.ListStore | None:
		action = self.toolbar.getLeftRightAction()
		if action == "inactivate":
			return self.activeTrees
		if action == "activate":
			return self.inactiveTrees
		return None

	def onUpClick(self, _obj: gtk.Button | None = None) -> None:
		treev = self.getCurrentTreeview()
		if not treev:
			return
		model = self.getCurrentTreestore()
		assert model is not None
		selection = treev.get_selection()
		_model, iter_ = selection.get_selected()
		if not iter_:
			return
		i = model.get_path(iter_).get_indices()[0]
		if i <= 0:
			return
		model.swap(
			model.get_iter(str(i - 1)),
			model.get_iter(str(i)),
		)
		selection.select_path(gtk.TreePath.new_from_indices((i - 1,)))

	def onDownClick(self, _obj: gtk.Button | None = None) -> None:
		treev = self.getCurrentTreeview()
		if not treev:
			return
		model = self.getCurrentTreestore()
		assert model is not None
		selection = treev.get_selection()
		_model, iter_ = selection.get_selected()
		if not iter_:
			return
		i = model.get_path(iter_).get_indices()[0]
		if i >= len(model) - 1:
			return
		model.swap(
			model.get_iter(str(i)),
			model.get_iter(str(i + 1)),
		)
		selection.select_path(gtk.TreePath.new_from_indices((i + 1,)))

	def inactivateIndex(self, index: int) -> None:
		if len(self.activeTrees) < 2:
			log.warning("You need at least one active calendar type!")
			return
		self.inactiveTrees.prepend(list(self.activeTrees[index]))  # type: ignore[call-overload]
		del self.activeTrees[index]
		treeviewSelect(self.inactiveTreev, 0)
		treeviewSelect(
			self.activeTreev,
			min(
				index,
				len(self.activeTrees) - 1,
			),
		)
		self.inactiveTreev.grab_focus()
		self.inactiveTreevFocus(self.inactiveTreev)

	def activateIndex(self, index: int) -> None:
		self.activeTrees.append(list(self.inactiveTrees[index]))  # type: ignore[call-overload]
		del self.inactiveTrees[index]
		treeviewSelect(self.activeTreev, len(self.activeTrees) - 1)
		if len(self.inactiveTrees) > 0:
			treeviewSelect(
				self.inactiveTreev,
				min(
					index,
					len(self.inactiveTrees) - 1,
				),
			)
		self.activeTreev.grab_focus()
		self.activeTreevFocus(self.activeTreev)

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
		_treev: gtk.TreeView,
		path: list[int],
		_col: gtk.TreeViewColumn,
	) -> None:
		self.inactivateIndex(path[0])

	def inactiveTreevRActivate(
		self,
		_treev: gtk.TreeView,
		path: list[int],
		_col: gtk.TreeViewColumn,
	) -> None:
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
		# --
		for calType in calTypes.active:
			module = calTypes[calType]
			if module is None:
				raise RuntimeError(f"cal type '{calType}' not found")
			self.activeTrees.append([module.name, _(module.desc, ctx="calendar")])
		# --
		for calType in calTypes.inactive:
			module = calTypes[calType]
			if module is None:
				raise RuntimeError(f"cal type '{calType}' not found")
			self.inactiveTrees.append([module.name, _(module.desc, ctx="calendar")])


class KeyBindingOptionUI(OptionUI):
	def getWidget(self) -> gtk.Widget:
		return self._widget

	def __init__(
		self,
		option: StrDictOption[str],
		actions: list[str],
		# live: bool = False,
		# onChangeFunc: "Callable] | None" = None,
	) -> None:
		self.option = option
		self.actions = actions
		# ------
		treev = gtk.TreeView()
		treev.set_headers_clickable(True)
		listStore = self.listStore = gtk.ListStore(
			str,  # key
			str,  # action
		)
		treev.set_model(listStore)
		# ---
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Key"), cell_renderer=cell, text=0)
		col.set_property("expand", False)
		treev.append_column(col)
		# ---
		cell = gtk.CellRendererCombo(editable=True)
		actionModel = gtk.ListStore(str)
		for action in actions:
			actionModel.append([action])
		cell.set_property("model", actionModel)
		col = gtk.TreeViewColumn(title=_("Action"), cell_renderer=cell, text=1)
		col.set_property("expand", False)
		treev.append_column(col)
		# ---
		self.treeview = treev
		# ---
		treev.connect("button-press-event", self.onTreeviewButtonPress)
		# ---
		treev.show_all()
		self.treev = treev
		# ---
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		self._widget = swin

	def onMenuModifyKeyClick(self, _w: gtk.Widget, rowIndex: int) -> None:
		trees = self.listStore
		row = trees[rowIndex]
		print(f"Modify Key: {row=}")  # noqa: T201

	# def onMenuDefaultKeyClick(self, menu: gtk.Menu, rowI: int):
	# 	trees = self.listStore
	# 	row = trees[rowI]
	# 	print(f"Default Key: {row=}")

	def onMenuDeleteClick(self, _w: gtk.Widget, rowI: int) -> None:
		trees = self.listStore
		trees.remove(trees.get_iter(str(rowI)))

	def onTreeviewRighButtonPress(
		self,
		rowIndex: int,
		gevent: gdk.EventButton,
	) -> None:
		menu = gtk.Menu()

		# def onModifyKey(w: gtk.Widget) -> None:
		# 	self.onMenuModifyKeyClick(w, rowIndex)

		# menu.add(
		# 	ImageMenuItem(
		# 		label=_("Modify Key"),
		# 		imageName="document-edit.svg",
		# 		func=onModifyKey,
		# 	),
		# )
		# menu.add(ImageMenuItem(
		# 	label=_("Default Key"),
		# 	imageName="edit-undo.svg",
		# 	func=onSetDefaultKey,
		# ))
		# menu.add(gtk.SeparatorMenuItem())
		def onDelete(w: gtk.Widget) -> None:
			self.onMenuDeleteClick(w, rowIndex)

		menu.add(
			ImageMenuItem(
				label=_("Delete", ctx="menu"),
				imageName="edit-delete.svg",
				onActivate=onDelete,
			),
		)
		menu.show_all()
		menu.popup(
			None,
			None,
			None,
			None,
			3,
			gevent.time,
		)

	def onTreeviewButtonPress(
		self,
		_widget: gtk.Widget,
		gevent: gdk.EventButton,
	) -> bool:
		b = gevent.button
		curObj = self.treeview.get_cursor()[0]
		if not curObj:
			return False
		# curObj is gtk.TreePath
		cur = curObj.get_indices()
		rowIndex = cur[0]
		if b == 1:
			pass
		elif b == 3:
			self.onTreeviewRighButtonPress(rowIndex, gevent)
			return True

		return False

	def set(self, keys: dict[str, str]) -> None:
		trees = self.listStore
		trees.clear()
		for key, action in keys.items():
			trees.append([key, action])

	def get(self) -> dict[str, str]:
		trees = self.listStore
		keys: dict[str, str] = {}
		for row in trees:
			if not row[0]:
				continue
			key: str
			action: str
			key, action = row  # type: ignore[misc]
			keys[key] = action
		return keys
