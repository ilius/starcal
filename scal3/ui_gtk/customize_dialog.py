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

from typing import TYPE_CHECKING, Any, Protocol

from scal3 import logger
from scal3.ui import conf
from scal3.ui_gtk.layout import WinLayoutObj

log = logger.get()

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, GdkPixbuf, gdk, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj, DummyCalObj, newSubPageButton
from scal3.ui_gtk.pref_utils import CheckPrefItem
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	VerticalStaticToolBox,
)
from scal3.ui_gtk.utils import (
	dialog_add_button,
	pixbufFromFile,
	showInfo,
)

if TYPE_CHECKING:
	from scal3.ui_gtk.layout import WinLayoutBox
	from scal3.ui_gtk.signals import SignalHandlerType

__all__ = ["CustomizeWindow"]


class CustomizeToolbarOwner(Protocol):
	def onTopClick(self, w: gtk.Widget, treev: gtk.TreeView, pagePath: str) -> None: ...
	def onUpClick(self, w: gtk.Widget, treev: gtk.TreeView, pagePath: str) -> None: ...
	def onDownClick(
		self, w: gtk.Widget, treev: gtk.TreeView, pagePath: str
	) -> None: ...
	def onBottomClick(
		self, w: gtk.Widget, treev: gtk.TreeView, pagePath: str
	) -> None: ...


class CustomizeWindowItemsToolbar(VerticalStaticToolBox):
	def __init__(
		self,
		owner: CustomizeToolbarOwner,
		treeview: gtk.TreeView,
		pagePath: str,
	) -> None:
		VerticalStaticToolBox.__init__(self, owner)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size

		def onTopClick(w: gtk.Widget) -> None:
			owner.onTopClick(w, treeview, pagePath)

		def onUpClick(w: gtk.Widget) -> None:
			owner.onUpClick(w, treeview, pagePath)

		def onDownClick(w: gtk.Widget) -> None:
			owner.onDownClick(w, treeview, pagePath)

		def onBottomClick(w: gtk.Widget) -> None:
			owner.onBottomClick(w, treeview, pagePath)

		self.extend(
			[
				ToolBoxItem(
					name="goto-top",
					imageName="go-top.svg",
					onClick=onTopClick,
					desc=_("Move to top"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick=onUpClick,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick=onDownClick,
					desc=_("Move down"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="goto-bottom",
					imageName="go-bottom.svg",
					onClick=onBottomClick,
					desc=_("Move to bottom"),
					continuousClick=False,
				),
			],
		)


class CustomizeWindow(Dialog):
	def __init__(
		self,
		item: WinLayoutBox,
		scrolled: bool = True,
		transient_for: gtk.Window | None = None,
	) -> None:
		Dialog.__init__(self, transient_for=transient_for)
		self.vbox.set_border_width(10)
		# --
		self.stack = MyStack(
			headerSpacing=10,
			iconSize=conf.stackIconSize.v,
		)
		pack(self.vbox, self.stack, 1, 1)
		# --
		self.set_title(_("Customize"))
		# self.set_has_separator(False)-- not in gtk3
		self.connect("delete-event", self.onDeleteEvent)
		dialog_add_button(
			self,
			res=gtk.ResponseType.OK,
			imageName="document-save.svg",
			label=_("_Save"),
			onClick=self.onSaveClick,
		)
		# should we save on Escape? or when clicking the X (close) button?
		# ---
		self.itemByPagePath: dict[str, CustomizableCalObj] = {}
		self.enableParamByPagePath: dict[str, CheckPrefItem] = {}
		self.rootItem = item
		# ---
		rootPagePath = "mainWin"
		rootPage = StackPage()
		rootPage.pagePath = rootPagePath
		rootPage.pageWidget = item.getOptionsButtonBox()
		rootPage.pageExpand = True
		rootPage.pageExpand = True
		rootPage.pageItem = item
		self.stack.addPage(rootPage)

		for page in item.getSubPages():
			assert page.pageItem is not None, f"{page=}"
			assert page.pageName, f"{page=}"
			page.pageParent = rootPagePath
			page.pagePath = rootPagePath + "." + page.pageName
			self.addPageObj(page)
		# ---
		if conf.customizePagePath.v:
			self.stack.tryToGotoPage(conf.customizePagePath.v)
		# ---
		self.vbox.connect("size-allocate", self.vboxSizeRequest)
		self.vbox.show_all()
		# ---
		if scrolled:
			# self.resize does not work
			self.vbox.set_size_request(300, 450)

	@staticmethod
	def itemPixbuf(item: CustomizableCalObj) -> GdkPixbuf.Pixbuf | None:
		if not item.enable:
			return None
		if item.hasOptions or (item.itemListCustomizable and item.items):
			return pixbufFromFile("document-edit.svg", conf.treeIconSize.v)
		return None

	def newItemList(
		self,
		parentPagePath: str,
		parentItem: CustomizableCalObj,
		scrolled: bool = False,
	) -> tuple[gtk.TreeView, gtk.Box]:
		# column 0: bool: enable
		# column 1: str: unique pagePath (dot separated)
		# column 2: str: desc
		# column 3: Pixbuf: settings icon
		model = gtk.ListStore(bool, str, str, GdkPixbuf.Pixbuf)
		treev = gtk.TreeView(model=model)
		pagePath = parentPagePath
		if parentItem.itemListSeparatePage:
			pagePath = parentPagePath + ".items"
		assert pagePath not in self.itemByPagePath, (
			f"{pagePath=}, {self.itemByPagePath.keys()=}"
		)
		self.itemByPagePath[pagePath] = parentItem
		# --
		treev.set_headers_visible(False)
		treev.connect("button-press-event", self.onTreeviewButtonPress, pagePath)
		treev.connect("row-activated", self.rowActivated, pagePath)
		# ------
		cell = gtk.CellRendererToggle()
		col = gtk.TreeViewColumn(title="", cell_renderer=cell, active=0)
		col.set_property("expand", False)
		cell.connect("toggled", self.onEnableCellToggle, treev, pagePath)
		treev.append_column(col)
		# -----
		col = gtk.TreeViewColumn(
			title="Widget",
			cell_renderer=gtk.CellRendererText(),
			text=2,
		)
		col.set_property("expand", True)
		treev.append_column(col)
		# -----
		col = gtk.TreeViewColumn(
			title="S",
			cell_renderer=gtk.CellRendererPixbuf(),
			pixbuf=3,
		)
		col.set_property("expand", False)
		treev.append_column(col)
		# -----
		for item in parentItem.items:
			if not item.customizable:
				continue
			assert item.objName, f"{item = }"
			assert isinstance(item, CustomizableCalObj | DummyCalObj), f"{item = }"
			model.append(
				[
					item.enable,
					parentPagePath + "." + item.objName,
					item.desc,
					self.itemPixbuf(item),
				],
			)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		vbox_l = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		if scrolled:
			swin = gtk.ScrolledWindow()
			swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
			swin.add(treev)
			pack(vbox_l, swin, 1, 1)
		else:
			pack(vbox_l, treev, 1, 1)
		pack(hbox, vbox_l, 1, 1)
		# ---
		toolbar = CustomizeWindowItemsToolbar(
			owner=self,
			treeview=treev,
			pagePath=pagePath,
		)
		# ---
		pack(hbox, toolbar.w)
		# ---
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		if parentItem.itemHaveOptions:
			label = gtk.Label(
				label=(
					'<span font_size="xx-small">'
					+ _("Double-click on each row to see its settings")
					+ "</span>"
				),
			)
			label.set_use_markup(True)
			pack(vbox, label)
		pack(vbox, hbox, 1, 1)
		# ---
		return treev, vbox

	def vboxSizeRequest(self, _w: gtk.Widget | None = None, _req: Any = None) -> None:
		self.resize(self.get_size()[0], 1)

	def onTopClick(self, _w: gtk.Widget, treev: gtk.TreeView, pagePath: str) -> None:
		item = self.itemByPagePath[pagePath]
		model = treev.get_model()
		assert isinstance(model, gtk.ListStore), f"{model=}"
		curObj = treev.get_cursor()[0]
		if not curObj:
			return
		cur = curObj.get_indices()
		i = cur[-1]

		assert len(cur) == 1, f"unexpected {cur = }"

		if i <= 0 or i >= len(model):
			gdk.beep()
			return
		# ---
		item.moveItem(i, 0)
		model.prepend(list(model[i]))  # type: ignore[call-overload]
		model.remove(model.get_iter(str(i + 1)))
		treev.set_cursor(0)  # type: ignore[arg-type]

	def onUpClick(self, _w: gtk.Widget, treev: gtk.TreeView, pagePath: str) -> None:
		item = self.itemByPagePath[pagePath]
		model = treev.get_model()
		assert isinstance(model, gtk.ListStore), f"{model=}"
		curObj = treev.get_cursor()[0]
		if not curObj:
			return
		cur = curObj.get_indices()
		i = cur[-1]

		assert len(cur) == 1, f"unexpected {cur = }"

		if i <= 0 or i >= len(model):
			gdk.beep()
			return
		# ---
		item.moveItem(i, i - 1)
		model.swap(model.get_iter(str(i - 1)), model.get_iter(str(i)))
		treev.set_cursor(i - 1)  # type: ignore[arg-type]

	def onDownClick(self, _w: gtk.Widget, treev: gtk.TreeView, pagePath: str) -> None:
		item = self.itemByPagePath[pagePath]
		model = treev.get_model()
		assert isinstance(model, gtk.ListStore), f"{model=}"
		curObj = treev.get_cursor()[0]
		if not curObj:
			return
		cur = curObj.get_indices()
		i = cur[-1]

		assert len(cur) == 1, f"unexpected {cur = }"

		if i < 0 or i >= len(model) - 1:
			gdk.beep()
			return
		# ---
		item.moveItem(i + 1, i)
		model.swap(model.get_iter(str(i)), model.get_iter(str(i + 1)))
		treev.set_cursor(i + 1)  # type: ignore[arg-type]

	def onBottomClick(self, _w: gtk.Widget, treev: gtk.TreeView, pagePath: str) -> None:
		item = self.itemByPagePath[pagePath]
		model = treev.get_model()
		assert isinstance(model, gtk.ListStore), f"{model=}"
		curObj = treev.get_cursor()[0]
		if not curObj:
			return
		cur = curObj.get_indices()
		i = cur[-1]

		assert len(cur) == 1, f"unexpected {cur = }"

		if i < 0 or i >= len(model) - 1:
			gdk.beep()
			return
		# ---
		item.moveItem(i, len(model) - 1)
		model.append(list(model[i]))  # type: ignore[call-overload]
		model.remove(model.get_iter(str(i)))
		treev.set_cursor(len(model) - 1)  # type: ignore[arg-type]

	def _addPageItemsTree(self, page: StackPage) -> None:
		pagePath = page.pagePath
		item = page.pageItem
		assert item is not None
		assert page.pageWidget is not None

		_childrenTreev, childrenBox = self.newItemList(
			pagePath,
			item,
			scrolled=True,
		)
		childrenBox.show_all()

		if not item.itemListSeparatePage:
			pack(page.pageWidget, childrenBox, 1, 1)
			return

		itemsPagePath = pagePath + ".items"
		itemsPage = StackPage()
		itemsPage.pageWidget = childrenBox
		itemsPage.pageParent = pagePath
		itemsPage.pagePath = itemsPagePath
		itemsPage.pageTitle = item.itemsPageTitle + " - " + page.pageTitle
		itemsPage.pageLabel = item.itemsPageTitle
		itemsPage.pageExpand = True
		self.stack.addPage(itemsPage)
		pack(
			page.pageWidget,
			newSubPageButton(
				item,
				itemsPage,
				borderWidth=item.itemsPageButtonBorder,
			),
		)

	def addPageObj(self, page: StackPage) -> None:
		pagePath = page.pagePath
		title = page.pageTitle
		item = page.pageItem
		assert item is not None
		assert page.pageWidget is not None
		log.debug(f"addPageObj: {page.pagePath=}, {page.pageParent=}, {item.objName=}")

		if self.stack.hasPage(pagePath):
			return

		if item.enableParam:
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
			prefItem = CheckPrefItem(
				prop=item.enableParam,
				label=_("Enable"),
				live=True,
				onChangeFunc=item.onEnableCheckClick,
			)
			pack(hbox, prefItem.getWidget())
			pack(page.pageWidget, hbox, 0, 0)
			self.enableParamByPagePath[pagePath] = prefItem

		if item.itemListCustomizable and item.items:
			self._addPageItemsTree(page)

		if item.hasOptions:
			optionsWidget = item.getOptionsWidget()
			assert optionsWidget is not None, f"{item.hasOptions=} but {optionsWidget=}"
			pack(page.pageWidget, optionsWidget, 0, 0)

		log.debug(
			f"adding page {page.pagePath} to stack, {page.pageWidget=}"
			f" (parent={page.pageWidget.get_parent()})",
		)
		self.stack.addPage(page)  # FIXME: crashes here

		for page2 in item.getSubPages():
			if not (page2.pagePath and page2.pageParent):
				assert page2.pageName, f"{page2=}"
				page2.pagePath = pagePath + "." + page2.pageName
				page2.pageParent = ".".join(
					[pagePath] + page2.pageName.split(".")[:-1],
				)

			page2.pageTitle = page2.pageTitle + " - " + title
			self.stack.addPage(page2)
		item.s.connect("goto-page", self.gotoPageCallback)

	def _addPage(
		self,
		pagePath: str,
		parentPagePath: str,
		parentItem: CustomizableCalObj,
		itemIndex: int,
	) -> StackPage:
		item = parentItem.items[itemIndex]
		assert isinstance(item, CustomizableCalObj), f"{item=}"

		title = item.desc
		if parentItem.objName != "mainWin":
			title = title + " - " + parentItem.desc

		page = StackPage()
		page.pageName = pagePath.split(".", maxsplit=1)[-1]
		page.pagePath = pagePath
		page.pageParent = parentPagePath
		page.pageWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=item.optionsPageSpacing,
		)
		page.pageTitle = title
		page.pageExpand = True
		page.pageExpand = True
		page.pageItem = item

		self.addPageObj(page)

		return page

	def gotoPageCallback(self, _sig: SignalHandlerType, pagePath: str) -> None:
		self.stack.gotoPage(pagePath)

	def onTreeviewButtonPress(
		self,
		treev: gtk.TreeView,
		gevent: gdk.EventButton,
		pagePath: str,
	) -> bool:
		if gevent.button != 1:
			return False
		pos_t = treev.get_path_at_pos(int(gevent.x), int(gevent.y))
		if not pos_t:
			return False
		# pos_t == path, col, xRel, yRel
		path = pos_t[0]
		col = pos_t[1]
		assert col is not None
		assert path is not None
		cell = col.get_cells()[0]
		if isinstance(cell, gtk.CellRendererPixbuf):
			self.rowActivated(treev, path, col, pagePath)
		return False

	def rowActivated(
		self,
		treev: gtk.TreeView,
		path: gtk.TreePath,
		_col: gtk.TreeViewColumn,
		parentPagePath: str,
	) -> None:
		parentItem = self.itemByPagePath[parentPagePath]
		model = treev.get_model()
		assert isinstance(model, gtk.ListStore), f"{model=}"
		itemIter = model.get_iter(path)
		pagePath = model.get_value(itemIter, 1)
		itemIndex = path.get_indices()[0]
		item = parentItem.items[itemIndex]

		log.debug(f"rowActivated: {pagePath=}, {itemIndex=}, {parentPagePath=}")
		if isinstance(parentItem, WinLayoutObj):  # if parentItem.isWrapper
			parentWidget = parentItem.getItem()
			assert isinstance(parentWidget, CustomizableCalObj), f"{parentWidget=}"
			parentItem = parentWidget

		# if none of the items in list have any settings, we can toggle-enable instead
		if not parentItem.itemHaveOptions:
			self.enableCellToggle(treev, item.enable, itemIndex, pagePath)
			return

		if not item.enable:
			msg = _(
				"{item} is disabled.\nCheck the checkbox if you want to enable it.",
			).format(item=item.desc)
			showInfo(msg, transient_for=self)
			return

		page = self._addPage(pagePath, parentPagePath, parentItem, itemIndex)
		self.stack.gotoPage(page.pagePath)

	@staticmethod
	def loadItem(
		parentItem: CustomizableCalObj,
		itemIndex: int,
		enable: bool | None = None,
	) -> CustomizableCalObj | None:
		item = parentItem.items[itemIndex]
		if item.loaded:
			if enable is not None:
				item.enable = enable
		else:
			item = item.getLoadedObj()
			if item is None:
				return None
			if enable is not None:
				item.enable = enable
			parentItem.replaceItem(itemIndex, item)
			parentItem.insertItemWidget(itemIndex)
		item.onConfigChange()
		item.broadcastDateChange()
		return item

	def onEnableCellToggle(
		self,
		cell: gtk.CellRendererToggle,
		pathStr: str,
		treev: gtk.TreeView,
		pagePath: str,
	) -> None:
		itemIndex = int(pathStr)
		self.enableCellToggle(treev, cell.get_active(), itemIndex, pagePath)

	def enableCellToggle(
		self,
		treev: gtk.TreeView,
		active: bool,
		itemIndex: int,
		pagePath: str,
	) -> None:
		active = not active
		model = treev.get_model()
		assert isinstance(model, gtk.ListStore), f"{model=}"
		itr = model.get_iter(str(itemIndex))
		model.set_value(itr, 0, active)
		parentItem = self.itemByPagePath[pagePath]
		item = parentItem.items[itemIndex]
		assert parentItem.items[itemIndex] == item
		# ---
		if active:
			itemNew = self.loadItem(parentItem, itemIndex, enable=active)
			if itemNew is None:
				return
			item = itemNew
		item.enable = active
		model.set_value(itr, 3, self.itemPixbuf(item))
		item.showHide()
		# calling item.onConfigChange() causes labelBox not to hide when unchecked

	def updateMainPanelTreeEnableChecks(self) -> None:
		pass
		# FIXME: called from MainWin
		# treev = self.treev_root
		# model = self._listStore
		# for i, item in enumerate(self.mainPanelItem.items):
		# 	model.set_value(
		# 		model.get_iter((i,)),
		# 		0,
		# 		item.enable,
		# 	)

	def save(self) -> None:
		item = self.rootItem
		item.updateVars()
		conf.ud__wcalToolbarData.v = ud.wcalToolbarData
		conf.ud__mainToolbarData.v = ud.mainToolbarData
		conf.customizePagePath.v = self.stack.currentPagePath()
		ui.saveConfCustomize()
		# data = item.getDict()-- remove? FIXME

	def onDeleteEvent(self, _w: gtk.Widget, _ge: gdk.Event) -> bool:
		self.save()
		self.hide()
		return True

	def onSaveClick(self, _w: gtk.Widget) -> None:
		self.save()
		self.hide()
