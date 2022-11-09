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

from typing import Tuple

from scal3.path import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3 import ui

from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	set_tooltip,
	dialog_add_button,
	showInfo,
	pixbufFromFile,
)
from scal3.ui_gtk.tree_utils import tree_path_split
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.customize import newSubPageButton
from scal3.ui_gtk.pref_utils import CheckPrefItem
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	StaticToolBox,
)


class CustomizeWindowItemsToolbar(StaticToolBox):
	def __init__(self, parent, onClickArgs):
		StaticToolBox.__init__(
			self,
			parent,
			vertical=True,
		)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		self.extend([
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
		])




class CustomizeWindow(gtk.Dialog):
	def __init__(self, item: "CustomizableCalObj", scrolled=True, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.vbox.set_border_width(10)
		##
		self.stack = MyStack(
			headerSpacing=10,
			iconSize=ui.stackIconSize,
		)
		pack(self.vbox, self.stack, 1, 1)
		##
		self.set_title(_("Customize"))
		#self.set_has_separator(False)## not in gtk3
		self.connect("delete-event", self.onSaveClick)
		dialog_add_button(
			self,
			imageName="document-save.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
			onClick=self.onSaveClick,
		)
		# should we save on Escape? or when clicking the X (close) button?
		###
		self.itemByPagePath = {}
		self.rootItem = item
		###
		rootPagePath = "mainWin"
		rootPage = StackPage()
		rootPage.pagePath = rootPagePath
		rootPage.pageWidget = item.getOptionsButtonBox()
		rootPage.pageExpand = True
		rootPage.pageExpand = True
		rootPage.pageItem = item
		self.stack.addPage(rootPage)

		for page in item.getSubPages():
			if page.pageItem is None:
				raise ValueError(f"pageItem=None, {page.pagePath=}")
			if not page.pageName:
				raise ValueError(f"pageName empty, {page=}")
			page.pageParent = rootPagePath
			page.pagePath = rootPagePath + "." + page.pageName
			self.addPageObj(page)
		###
		if ui.customizePagePath:
			self.stack.tryToGotoPage(ui.customizePagePath)
		###
		self.vbox.connect("size-allocate", self.vboxSizeRequest)
		self.vbox.show_all()
		###
		if scrolled:
			# self.resize does not work
			self.vbox.set_size_request(300, 450)

	def itemPixbuf(self, item):
		if not item.enable:
			return None
		if item.hasOptions or (item.itemListCustomizable and item.items):
			return pixbufFromFile("document-edit.svg", ui.treeIconSize)
		return None

	def newItemList(
		self,
		parentPagePath: str,
		parentItem: "CustomizableCalObj",
		scrolled=False,
	) -> Tuple[gtk.TreeView, gtk.Box]:
		# column 0: bool: enable
		# column 1: str: unique pagePath (dot separated)
		# column 2: str: desc
		# column 3: Pixbuf: settings icon
		model = gtk.ListStore(bool, str, str, GdkPixbuf.Pixbuf)
		treev = gtk.TreeView(model=model)
		if parentItem.itemsPageEnable:
			treev.pagePath = parentPagePath + ".items"
		else:
			treev.pagePath = parentPagePath
		self.itemByPagePath[treev.pagePath] = parentItem
		##
		treev.set_headers_visible(False)
		treev.connect("button-press-event", self.onTreeviewButtonPress)
		treev.connect("row-activated", self.rowActivated)
		######
		cell = gtk.CellRendererToggle()
		col = gtk.TreeViewColumn(title="", cell_renderer=cell, active=0)
		col.set_property("expand", False)
		cell.connect("toggled", self.enableCellToggled, treev)
		treev.append_column(col)
		#####
		col = gtk.TreeViewColumn(
			title="Widget",
			cell_renderer=gtk.CellRendererText(),
			text=2,
		)
		col.set_property("expand", True)
		treev.append_column(col)
		#####
		col = gtk.TreeViewColumn(
			title="S",
			cell_renderer=gtk.CellRendererPixbuf(),
			pixbuf=3,
		)
		col.set_property("expand", False)
		treev.append_column(col)
		#####
		anyItemHasOptions = False
		for item in parentItem.items:
			if not item.customizable:
				continue
			if item.hasOptions:
				anyItemHasOptions = True
			if not item._name:
				raise ValueError(f"{item._name = }")
			model.append([
				item.enable,
				parentPagePath + "." + item._name,
				item.desc,
				self.itemPixbuf(item),
			])
		###
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
		###
		toolbar = CustomizeWindowItemsToolbar(
			self,
			(treev,)
		)
		###
		pack(hbox, toolbar)
		###
		vbox = VBox(spacing=10)
		if anyItemHasOptions:
			label = gtk.Label(
				label=(
					"<span font_size=\"xx-small\">" +
					_("Double-click on each row to see its settings") +
					"</span>"
				),
			)
			label.set_use_markup(True)
			pack(vbox, label)
		pack(vbox, hbox, 1, 1)
		###
		return treev, vbox

	def vboxSizeRequest(self, widget, req):
		self.resize(self.get_size()[0], 1)

	def onTopClick(self, button, treev):
		item = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		cur = treev.get_cursor()[0]
		if not cur:
			return
		i = cur[-1]

		if len(cur) != 1:
			raise RuntimeError(f"unexpected {cur = }")

		if i <= 0 or i >= len(model):
			gdk.beep()
			return
		###
		item.moveItem(i, 0)
		model.prepend(list(model[i]))
		model.remove(model.get_iter(i + 1))
		treev.set_cursor(0)

	def onUpClick(self, button, treev):
		item = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		cur = treev.get_cursor()[0]
		if not cur:
			return
		i = cur[-1]

		if len(cur) != 1:
			raise RuntimeError(f"unexpected {cur = }")

		if i <= 0 or i >= len(model):
			gdk.beep()
			return
		###
		item.moveItem(i, i - 1)
		model.swap(model.get_iter(i - 1), model.get_iter(i))
		treev.set_cursor(i - 1)

	def onDownClick(self, button, treev):
		item = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		cur = treev.get_cursor()[0]
		if not cur:
			return
		i = cur[-1]

		if len(cur) != 1:
			raise RuntimeError(f"unexpected {cur = }")

		if i < 0 or i >= len(model) - 1:
			gdk.beep()
			return
		###
		item.moveItem(i + 1, i)
		model.swap(model.get_iter(i), model.get_iter(i + 1))
		treev.set_cursor(i + 1)

	def onBottomClick(self, button, treev):
		item = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		cur = treev.get_cursor()[0]
		if not cur:
			return
		i = cur[-1]

		if len(cur) != 1:
			raise RuntimeError(f"unexpected {cur = }")

		if i < 0 or i >= len(model) - 1:
			gdk.beep()
			return
		###
		item.moveItem(i, len(model) - 1)
		model.append(list(model[i]))
		model.remove(model.get_iter(i))
		treev.set_cursor(len(model) - 1)

	def _addPageItemsTree(self, page):
		pagePath = page.pagePath
		item = page.pageItem

		childrenTreev, childrenBox = self.newItemList(
			pagePath,
			item,
			scrolled=True,
		)
		childrenBox.show_all()

		if not item.itemsPageEnable:
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
		pack(page.pageWidget, newSubPageButton(
			item,
			itemsPage,
			borderWidth=item.itemsPageButtonBorder,
		))

	def addPageObj(self, page):
		pagePath = page.pagePath
		parentPagePath = page.pageParent
		title = page.pageTitle
		item = page.pageItem
		log.debug(f"addPageObj: {page.pagePath=}, {page.pageParent=}, {item._name=}")

		if self.stack.hasPage(pagePath):
			return

		if item.enableParam:
			hbox = HBox(spacing=10)
			prefItem = CheckPrefItem(
				ui,
				item.enableParam,
				_("Enable"),
				live=True,
				onChangeFunc=item.onEnableCheckClick,
			)
			pack(hbox, prefItem.getWidget())
			pack(page.pageWidget, hbox, 0, 0)

		if item.itemListCustomizable and item.items:
			self._addPageItemsTree(page)

		if item.hasOptions:
			optionsWidget = item.getOptionsWidget()
			if optionsWidget is None:
				raise ValueError(f"{item.hasOptions=} but {optionsWidget=}")
			pack(page.pageWidget, optionsWidget, 0, 0)

		log.debug(
			f"adding page {page.pagePath} to stack, {page.pageWidget=}"
			f" (parent={page.pageWidget.get_parent()})"
		)
		self.stack.addPage(page) # FIXME: crashes here

		for page in item.getSubPages():
			if not (page.pagePath and page.pageParent):
				if not page.pageName:
					raise ValueError(f"pageName empty, {page=}")
				page.pagePath = pagePath + "." + page.pageName
				page.pageParent = ".".join(
					[pagePath] + page.pageName.split(".")[:-1]
				)

			page.pageTitle = page.pageTitle + " - " + title
			self.stack.addPage(page)
		item.connect("goto-page", self.gotoPageCallback)

	def _addPage(
		self,
		pagePath: str,
		parentPagePath: str,
		parentItem: "CustomizableCalObj",
		itemIndex: int,
	):
		item = parentItem.items[itemIndex]

		title = item.desc
		if parentItem._name != "mainWin":
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

	def gotoPageCallback(self, item, pagePath):
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
		col: gtk.TreeViewColumn,
	):
		parentPagePath = treev.pagePath
		parentItem = self.itemByPagePath[treev.pagePath]
		model = treev.get_model()
		itemIter = model.get_iter(path)
		pagePath = model.get_value(itemIter, 1)
		itemIndex = tree_path_split(path)[0]
		item = parentItem.items[itemIndex]
		if not item.enable:
			msg = _(
				"{item} is disabled.\n"
				"Check the checkbox if you want to enable it."
			).format(item=item.desc)
			showInfo(msg, transient_for=self)
			return
		log.debug(f"rowActivated: {pagePath=}, {itemIndex=}, {parentPagePath=}")
		if parentItem.isWrapper:
			parentItem = parentItem.getWidget()
		# print(f"rowActivated: {pagePath=}, {parentPagePath=}")
		page = self._addPage(pagePath, parentPagePath, parentItem, itemIndex)
		self.stack.gotoPage(page.pagePath)

	def loadItem(self, parentItem, itemIndex):
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

	def enableCellToggled(self, cell, path, treev):
		model = treev.get_model()
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 0, active)
		parentItem = self.itemByPagePath[treev.pagePath]
		itemIndex = tree_path_split(path)[0]
		item = parentItem.items[itemIndex]
		assert parentItem.items[itemIndex] == item
		###
		if active:
			item = self.loadItem(parentItem, itemIndex)
			if item is None:
				return
		item.enable = active
		model.set_value(itr, 3, self.itemPixbuf(item))
		item.showHide()
		item.onConfigChange()

	def updateMainPanelTreeEnableChecks(self):
		pass
		# FIXME: called from MainWin
		#treev = self.treev_root
		#model = treev.get_model()
		#for i, item in enumerate(self.mainPanelItem.items):
		#	model.set_value(
		#		model.get_iter((i,)),
		#		0,
		#		item.enable,
		#	)

	def save(self):
		item = self.rootItem
		item.updateVars()
		ui.ud__wcalToolbarData = ud.wcalToolbarData
		ui.ud__mainToolbarData = ud.mainToolbarData
		ui.customizePagePath = self.stack.currentPagePath()
		ui.saveConfCustomize()
		#data = item.getData()## remove? FIXME

	def onSaveClick(self, button=None, event=None):
		self.save()
		self.hide()
		return True
