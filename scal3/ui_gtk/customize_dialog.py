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
from scal3.ui import conf

log = logger.get()


from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import GdkPixbuf, HBox, VBox, gdk, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj, newSubPageButton
from scal3.ui_gtk.pref_utils import CheckPrefItem
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.toolbox import (
	StaticToolBox,
	ToolBoxItem,
)
from scal3.ui_gtk.tree_utils import tree_path_split
from scal3.ui_gtk.utils import (
	dialog_add_button,
	pixbufFromFile,
	showInfo,
)

__all__ = ["CustomizeWindow"]


class CustomizeWindowItemsToolbar(StaticToolBox):
	def __init__(self, parent, onClickArgs):
		StaticToolBox.__init__(
			self,
			parent,
			vertical=True,
		)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		self.extend(
			[
				ToolBoxItem(
					name="goto-top",
					imageName="go-top.svg",
					onClick="onTopClick",
					desc=_("Move to top"),
					continuousClick=False,
					args=onClickArgs,
				),
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick="onUpClick",
					desc=_("Move up"),
					continuousClick=False,
					args=onClickArgs,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick="onDownClick",
					desc=_("Move down"),
					continuousClick=False,
					args=onClickArgs,
				),
				ToolBoxItem(
					name="goto-bottom",
					imageName="go-bottom.svg",
					onClick="onBottomClick",
					desc=_("Move to bottom"),
					continuousClick=False,
					args=onClickArgs,
				),
			],
		)


class CustomizeWindow(gtk.Dialog):
	def __init__(self, item: CustomizableCalObj, scrolled=True, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
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
		self.connect("delete-event", self.onSaveClick)
		dialog_add_button(
			self,
			imageName="document-save.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
			onClick=self.onSaveClick,
		)
		# should we save on Escape? or when clicking the X (close) button?
		# ---
		self.itemByPagePath = {}
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
	def itemPixbuf(item):
		if not item.enable:
			return None
		if item.hasOptions or (item.itemListCustomizable and item.items):
			return pixbufFromFile("document-edit.svg", conf.treeIconSize.v)
		return None

	def newItemList(
		self,
		parentPagePath: str,
		parentItem: CustomizableCalObj,
		scrolled=False,
	) -> tuple[gtk.TreeView, gtk.Box]:
		# column 0: bool: enable
		# column 1: str: unique pagePath (dot separated)
		# column 2: str: desc
		# column 3: Pixbuf: settings icon
		model = gtk.ListStore(bool, str, str, GdkPixbuf.Pixbuf)
		treev = gtk.TreeView(model=model)
		if parentItem.itemListSeparatePage:
			treev.pagePath = parentPagePath + ".items"
		else:
			treev.pagePath = parentPagePath
		self.itemByPagePath[treev.pagePath] = parentItem
		# --
		treev.set_headers_visible(False)
		treev.connect("button-press-event", self.onTreeviewButtonPress)
		treev.connect("row-activated", self.rowActivated)
		# ------
		cell = gtk.CellRendererToggle()
		col = gtk.TreeViewColumn(title="", cell_renderer=cell, active=0)
		col.set_property("expand", False)
		cell.connect("toggled", self.onEnableCellToggle, treev)
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
			model.append(
				[
					item.enable,
					parentPagePath + "." + item.objName,
					item.desc,
					self.itemPixbuf(item),
				],
			)
		# ---
		hbox = HBox()
		vbox_l = VBox()
		if scrolled:
			swin = gtk.ScrolledWindow()
			swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
			swin.add(treev)
			pack(vbox_l, swin, 1, 1)
		else:
			pack(vbox_l, treev, 1, 1)
		pack(hbox, vbox_l, 1, 1)
		# ---
		toolbar = CustomizeWindowItemsToolbar(parent=self, onClickArgs=(treev,))
		# ---
		pack(hbox, toolbar)
		# ---
		vbox = VBox(spacing=10)
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

	def vboxSizeRequest(self, _widget=None, _req=None):
		self.resize(self.get_size()[0], 1)

	def onTopClick(self, _button, treev):
		item = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		cur = treev.get_cursor()[0]
		if not cur:
			return
		i = cur[-1]

		assert len(cur) == 1, f"unexpected {cur = }"

		if i <= 0 or i >= len(model):
			gdk.beep()
			return
		# ---
		item.moveItem(i, 0)
		model.prepend(list(model[i]))
		model.remove(model.get_iter(i + 1))
		treev.set_cursor(0)

	def onUpClick(self, _button, treev):
		item = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		cur = treev.get_cursor()[0]
		if not cur:
			return
		i = cur[-1]

		assert len(cur) == 1, f"unexpected {cur = }"

		if i <= 0 or i >= len(model):
			gdk.beep()
			return
		# ---
		item.moveItem(i, i - 1)
		model.swap(model.get_iter(i - 1), model.get_iter(i))
		treev.set_cursor(i - 1)

	def onDownClick(self, _button, treev):
		item = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		cur = treev.get_cursor()[0]
		if not cur:
			return
		i = cur[-1]

		assert len(cur) == 1, f"unexpected {cur = }"

		if i < 0 or i >= len(model) - 1:
			gdk.beep()
			return
		# ---
		item.moveItem(i + 1, i)
		model.swap(model.get_iter(i), model.get_iter(i + 1))
		treev.set_cursor(i + 1)

	def onBottomClick(self, _button, treev):
		item = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		cur = treev.get_cursor()[0]
		if not cur:
			return
		i = cur[-1]

		assert len(cur) == 1, f"unexpected {cur = }"

		if i < 0 or i >= len(model) - 1:
			gdk.beep()
			return
		# ---
		item.moveItem(i, len(model) - 1)
		model.append(list(model[i]))
		model.remove(model.get_iter(i))
		treev.set_cursor(len(model) - 1)

	def _addPageItemsTree(self, page):
		pagePath = page.pagePath
		item = page.pageItem

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

	def addPageObj(self, page):
		pagePath = page.pagePath
		title = page.pageTitle
		item = page.pageItem
		log.debug(f"addPageObj: {page.pagePath=}, {page.pageParent=}, {item.objName=}")

		if self.stack.hasPage(pagePath):
			return

		if item.enableParam:
			hbox = HBox(spacing=10)
			prefItem = CheckPrefItem(
				prop=item.enableParam,
				label=_("Enable"),
				live=True,
				onChangeFunc=item.onEnableCheckClick,
			)
			pack(hbox, prefItem.getWidget())
			pack(page.pageWidget, hbox, 0, 0)
			item.enablePrefItem = prefItem

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
		item.connect("goto-page", self.gotoPageCallback)

	def _addPage(
		self,
		pagePath: str,
		parentPagePath: str,
		parentItem: CustomizableCalObj,
		itemIndex: int,
	):
		item = parentItem.items[itemIndex]

		title = item.desc
		if parentItem.objName != "mainWin":
			title = title + " - " + parentItem.desc

		page = StackPage()
		page.pageName = pagePath.split(".")[-1]
		page.pagePath = pagePath
		page.pageParent = parentPagePath
		page.pageWidget = VBox(spacing=item.optionsPageSpacing)
		page.pageTitle = title
		page.pageExpand = True
		page.pageExpand = True
		page.pageItem = item

		self.addPageObj(page)

		return page

	def gotoPageCallback(self, _item, pagePath):
		self.stack.gotoPage(pagePath)

	def onTreeviewButtonPress(self, treev, gevent):
		if gevent.button != 1:
			return False
		pos_t = treev.get_path_at_pos(int(gevent.x), int(gevent.y))
		if not pos_t:
			return False
		# pos_t == path, col, xRel, yRel
		path = pos_t[0]
		col = pos_t[1]
		cell = col.get_cells()[0]
		if isinstance(cell, gtk.CellRendererPixbuf):
			self.rowActivated(treev, path, col)
		return False

	def rowActivated(
		self,
		treev: gtk.TreeView,
		path: gtk.TreePath,
		_col: gtk.TreeViewColumn,
	):
		parentPagePath = treev.pagePath
		parentItem = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		itemIter = model.get_iter(path)
		pagePath = model.get_value(itemIter, 1)
		itemIndex = tree_path_split(path)[0]
		item = parentItem.items[itemIndex]

		log.debug(f"rowActivated: {pagePath=}, {itemIndex=}, {parentPagePath=}")
		if parentItem.isWrapper:
			parentItem = parentItem.getWidget()
		# print(f"rowActivated: {pagePath=}, {parentPagePath=}")

		# if none of the items in list have any settings, we can toggle-enable instead
		if not parentItem.itemHaveOptions:
			self.enableCellToggle(treev, item.enable, itemIndex)
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
	def loadItem(parentItem, itemIndex):
		item = parentItem.items[itemIndex]
		if not item.loaded:
			item = item.getLoadedObj()
			if item is None:
				return
			parentItem.replaceItem(itemIndex, item)
			parentItem.insertItemWidget(itemIndex)
		item.onConfigChange()
		item.onDateChange()
		return item

	def onEnableCellToggle(self, cell, path, treev):
		itemIndex = tree_path_split(path)[0]
		self.enableCellToggle(treev, cell.get_active(), itemIndex)

	def enableCellToggle(self, treev: gtk.TreeView, active: bool, itemIndex: int):
		active = not active
		path = (itemIndex,)
		model = treev.get_model()
		itr = model.get_iter(path)
		model.set_value(itr, 0, active)
		parentItem = self.itemByPagePath[treev.pagePath]
		item = parentItem.items[itemIndex]
		assert parentItem.items[itemIndex] == item
		# ---
		if active:
			item = self.loadItem(parentItem, itemIndex)
			if item is None:
				return
		item.enable = active
		model.set_value(itr, 3, self.itemPixbuf(item))
		item.showHide()
		# calling item.onConfigChange() causes labelBox not to hide when unchecked

	def updateMainPanelTreeEnableChecks(self):
		pass
		# FIXME: called from MainWin
		# treev = self.treev_root
		# model = treev.get_model()
		# for i, item in enumerate(self.mainPanelItem.items):
		# 	model.set_value(
		# 		model.get_iter((i,)),
		# 		0,
		# 		item.enable,
		# 	)

	def save(self):
		item = self.rootItem
		item.updateVars()
		conf.ud__wcalToolbarData.v = ud.wcalToolbarData
		conf.ud__mainToolbarData.v = ud.mainToolbarData
		conf.customizePagePath.v = self.stack.currentPagePath()
		ui.saveConfCustomize()
		# data = item.getData()-- remove? FIXME

	def onSaveClick(self, _button=None, _event=None):
		self.save()
		self.hide()
		return True
