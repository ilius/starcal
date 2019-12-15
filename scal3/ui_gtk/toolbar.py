#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

from time import time as now

from typing import Optional, Tuple, Dict, Union, Callable, Any

from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import (
	set_tooltip,
	imageFromIconName,
	imageFromFile,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.pref_utils import PrefItem


# Gnome's naming is not exactly the best here
# And Gnome's order of options is also different from Gtk"s enum
toolbarStyleList = (
	"Icon",  # "icons", "Icons only"
	"Text",  # "text", "Text only"
	"Text below Icon",  # "both", "Text below items"
	"Text beside Icon",  # "both-horiz", "Text beside items"
)


@registerSignals
class ToolbarItem(gtk.ToolButton, CustomizableCalObj):
	hasOptions = False

	def __init__(
		self,
		name: str = "",
		iconName: str = "",
		imageName: str = "",
		onClick: Union[str, Callable] = None,
		desc: str = "",
		shortDesc: str = "",
		enableTooltip: bool = True,
		labelOnly: bool = False,
		continuousClick: bool = True,
		onPress: Optional[Union[str, Callable]] = None,
		args: Optional[Tuple[Any]] = None,  # for onClick and onPress
		iconSize: int = 26,
		enable: bool = True,
	) -> None:
		# log.debug("ToolbarItem", name, iconName, onClick, desc, text)
		self._name = name
		self.onClick = onClick
		self.onPress = onPress
		if args is None:
			args = ()
		self.args = args
		self.continuousClick = continuousClick
		self.iconSize = iconSize
		######
		if not desc:
			desc = name.capitalize()
		if not shortDesc:
			shortDesc = desc
		##
		desc = _(desc)
		shortDesc = _(shortDesc)
		self.desc = desc
		# self.shortDesc = shortDesc  # FIXME
		######
		gtk.ToolButton.__init__(self)
		if labelOnly:
			self.label = gtk.Label()
			self.set_property("label-widget", self.label)
		elif imageName:
			self.set_icon_widget(imageFromFile(
				imageName,
				size=iconSize,
			))
		elif iconName:
			self.set_icon_widget(imageFromIconName(
				iconName,
				gtk.IconSize.DIALOG,
			))
		self.set_label(shortDesc)
		#self.shortDesc = shortDesc## FIXME
		self.initVars()
		if enableTooltip:
			set_tooltip(self, desc)## FIXME
		self.set_is_important(True)## FIXME
		###
		self.enable = enable

	def setIconFile(self, fname: str) -> None:
		from scal3.ui_gtk.utils import imageFromFile
		self.set_property(
			"label-widget",
			imageFromFile(fname, self.iconSize),
		)

	def show(self):
		self.show_all()


class ToolbarStylePrefItem(PrefItem):
	def __init__(
		self,
		obj: "CustomizableToolbar",
		attrName: str,
		label: str = "",
		onChangeFunc: Optional[Callable] = None,
	):
		self.obj = obj  # because of PrefItem
		self.attrName = attrName
		self._onChangeFunc = onChangeFunc
		###
		hbox = HBox()
		if label:
			pack(hbox, gtk.Label(label=label))
		self.combo = gtk.ComboBoxText()
		for item in toolbarStyleList:
			self.combo.append_text(_(item))
		pack(hbox, self.combo)
		self._widget = hbox
		###
		self.combo.connect("changed", self.onComboChange)
		###
		self.updateWidget()

	def get(self) -> str:
		return toolbarStyleList[self.combo.get_active()]

	def set(self, styleName: str) -> None:
		self.combo.set_active(toolbarStyleList.index(styleName))

	def onComboChange(self, w):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class ToolbarIconSizePrefItem(PrefItem):
	def __init__(
		self,
		obj: "CustomizableToolbar",
		attrName: str,
		label: str = "",
		onChangeFunc: Optional[Callable] = None,
	):
		self.obj = obj  # because of PrefItem
		self.attrName = attrName
		self._onChangeFunc = onChangeFunc
		###
		hbox = HBox()
		if label:
			pack(hbox, gtk.Label(label=label))
		self.combo = gtk.ComboBoxText()
		for name, value in ud.iconSizeList:
			self.combo.append_text(_(name))
		pack(hbox, self.combo)
		self._widget = hbox
		###
		self.combo.connect("changed", self.onComboChange)
		###
		self.updateWidget()

	def get(self) -> str:
		return ud.iconSizeList[self.combo.get_active()][0]

	def set(self, sizeName: str) -> None:
		self.combo.set_active(ud.iconSizeNames.index(sizeName))

	def onComboChange(self, w):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()



#@registerSignals
class CustomizableToolbar(gtk.Toolbar, CustomizableCalObj):
	_name = "toolbar"
	desc = _("Toolbar")
	#signals = CustomizableCalObj.signals + [
	#	("popup-main-menu", [int, int, int]),
	#]
	defaultItems = []
	defaultItemsDict = {}

	def __init__(
		self,
		funcOwner: Any,
		vertical: bool = False,
		continuousClick: bool = True,
	) -> None:
		gtk.Toolbar.__init__(self)
		self.funcOwner = funcOwner
		self.set_orientation(
			gtk.Orientation.VERTICAL if vertical
			else gtk.Orientation.HORIZONTAL
		)
		self.add_events(gdk.EventMask.POINTER_MOTION_MASK)
		self.continuousClick = continuousClick
		self.remain = False
		self.lastPressTime = 0
		self.initVars()
		##
		self.iconSizeName = "Button"
		self.styleName = "Icon"
		self.buttonBorder = 0
		# log.debug("toolbar state", self.get_state()## STATE_NORMAL)
		#self.set_state(gtk.StateType.ACTIVE)## FIXME
		#self.set_property("border-width", 0)
		#style = self.get_style()
		#style.border_width = 10
		#self.set_style(style)

		# set on setData(), used in getData() to keep compatibility
		self.data = {}

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import SpinPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		###
		optionsWidget = VBox()
		##
		prefItem = ToolbarStylePrefItem(
			self,
			"styleName",
			label=_("Style"),
			onChangeFunc=self.onStyleNameChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		##
		prefItem = ToolbarIconSizePrefItem(
			self,
			"iconSizeName",
			label=_("Icon Size"),
			onChangeFunc=self.onIconSizeNameChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		##
		prefItem = SpinPrefItem(
			self,
			"buttonBorder",
			0, 99,
			digits=1, step=1,
			label=_("Buttons Border"),
			live=True,
			onChangeFunc=self.onButtonBorderChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		##
		optionsWidget.show_all()
		optionsWidget = optionsWidget
		return optionsWidget

	def getIconSizeName(self) -> str:
		return self.iconSizeName

	def setIconSizeName(self, iconSizeName: str) -> None:
		self.iconSizeName = iconSizeName
		self.onIconSizeNameChange()

	def onIconSizeNameChange(self):
		self.set_icon_size(ud.iconSizeDict[self.iconSizeName])
		# gtk.Toolbar.set_icon_size was previously Deprecated
		# but it's not Deprecated now? FIXME

	def getButtonBorder(self):
		return self.buttonBorder

	def setButtonBorder(self, buttonBorder: int) -> None:
		self.buttonBorder = buttonBorder
		self.onButtonBorderChange()

	def onButtonBorderChange(self):
		buttonBorder = self.buttonBorder
		for item in self.items:
			item.set_border_width(buttonBorder)

	def moveItem(self, i: int, j: int) -> None:
		button = self.items[i]
		self.remove(button)
		self.insert(button, j)
		self.items.insert(j, self.items.pop(i))

	#def insertItem(self, item, pos):
	#	CustomizableCalObj.insertItem(self, pos, item)
	#	gtk.Toolbar.insert(self, item, pos)
	#	item.show()

	def appendItem(self, item: ud.CalObjType) -> None:
		CustomizableCalObj.appendItem(self, item)
		gtk.Toolbar.insert(self, item, -1)
		if item.enable:
			item.show()

	def getStyleName(self) -> str:
		return self.styleName

	def setStyleName(self, styleName: str) -> None:
		self.styleName = styleName
		self.onStyleNameChange()
		
	def onStyleNameChange(self):
		style = toolbarStyleList.index(self.styleName)
		self.set_style(style)
		# self.showHide()  # FIXME

	def getData(self) -> Dict[str, Any]:
		self.data.update({
			"items": self.getItemsData(),
			"iconSize": self.getIconSizeName(),
			"style": self.getStyleName(),
			"buttonsBorder": self.getButtonBorder(),
		})
		return self.data

	def setupItemSignals(self, item: ud.CalObjType) -> None:
		if item.onClick:
			if isinstance(item.onClick, str):
				onClick = getattr(self.funcOwner, item.onClick)
			else:
				onClick = item.onClick
			if self.continuousClick and item.continuousClick:
				child = item.get_child()
				child.connect("button-press-event", lambda obj, ev: self.itemPress(onClick, item.args))
				child.connect("button-release-event", self.onItemButtonRelease)
			else:
				item.connect("clicked", onClick, *item.args)

		if item.onPress:
			if isinstance(item.onPress, str):
				onPress = getattr(self.funcOwner, item.onPress)
			else:
				onPress = item.onPress
			child = item.get_child()
			child.connect("button-press-event", onPress, *item.args)

	def setData(self, data: Dict[str, Any]) -> None:
		self.data = data
		newItemNames = set()
		for (name, enable) in data["items"]:
			item = self.defaultItemsDict.get(name)
			if item is None:
				log.info(f"toolbar item {name!r} does not exist")
				continue
			item.enable = enable
			self.setupItemSignals(item)
			self.appendItem(item)
			newItemNames.add(name)
		for item in self.defaultItems:
			if item._name not in newItemNames:
				self.setupItemSignals(item)
				self.appendItem(item)
		###
		iconSize = data.get("iconSize")
		if iconSize is not None:
			self.setIconSizeName(iconSize)
		###
		self.setStyleName(data.get("style", "Icon"))
		self.setButtonBorder(data.get("buttonsBorder", 0))
		###
		self.optionsWidget = None

	def itemPress(self, func, args: "Tuple[Any]"):
		if self.remain:
			# log.debug(f"itemPress: skip: remain={self.remain}")
			return
		if now() - self.lastPressTime < ui.timeout_repeat * 0.01:
			# log.debug(f"itemPress: skip: delta = {now()-self.lastPressTime}")
			return
		# log.debug(
		#	"itemPress:",
		#	now() - self.lastPressTime,
		#	">=",
		#	ui.timeout_repeat * 0.01,
		#)
		self.lastPressTime = now()
		self.remain = True
		func(*args)
		timeout_add(ui.timeout_initial, self.itemPressRemain, func, args)

	def itemPressRemain(self, func, args: "Tuple[Any]"):
		if not self.remain:
			return
		if now() - self.lastPressTime < ui.timeout_repeat * 0.001:
			return
		# log.debug(
		#	"itemPressRemain:",
		#	now() - self.lastPressTime,
		#	">=",
		#	ui.timeout_repeat * 0.001,
		#)
		func(*args)
		timeout_add(ui.timeout_repeat, self.itemPressRemain, func)

	def onItemButtonRelease(self, widget, event=None):
		# log.debug("------------------------ onItemButtonRelease")
		self.remain = False
