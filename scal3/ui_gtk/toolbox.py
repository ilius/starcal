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
	pixbufFromFile,
)
from scal3.ui_gtk.icon_mapping import iconNameByImageName
from scal3.ui_gtk.mywidgets.button import ConButtonBase
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj


class BaseToolBoxItem(gtk.Button, ConButtonBase, CustomizableCalObj):
	hasOptions = False

	signals = CustomizableCalObj.signals + [
		("con-clicked", []),
	]

	def show(self) -> None:
		gtk.Button.show_all(self)

	def setVertical(self, vertical: bool) -> None:
		self.vertical = vertical

	# the following methods (do_get_*) are meant to make the button a square
	def do_get_request_mode(self) -> gtk.SizeRequestMode:
		if self.vertical:
			return gtk.SizeRequestMode.HEIGHT_FOR_WIDTH
		return gtk.SizeRequestMode.WIDTH_FOR_HEIGHT

	def do_get_preferred_height_for_width(self, size: int) -> Tuple[int, int]:
		# must return minimum_size, natural_size
		if not self.vertical:
			# self.get_preferred_height() does not work well here, not sure why
			return self.do_get_preferred_width_for_height(size)
		return size, size

	def do_get_preferred_width_for_height(self, size: int) -> Tuple[int, int]:
		# must return minimum_size, natural_size
		if self.vertical:
			return self.get_preferred_width()
		return size, size



@registerSignals
class ToolBoxItem(BaseToolBoxItem):
	def __init__(
		self,
		name: str = "",
		iconName: str = "",
		imageName: str = "",
		imageNameDynamic: bool = False,
		onClick: Union[None, str, Callable] = None,
		desc: str = "",
		shortDesc: str = "",
		enableTooltip: bool = True,
		continuousClick: bool = True,
		onPress: Optional[Union[str, Callable]] = None,
		args: Optional[Tuple[Any]] = None,  # for onClick and onPress
		enable: bool = True,
	) -> None:
		gtk.Button.__init__(self)
		if continuousClick:
			ConButtonBase.__init__(self, button=1)  # only left-click
		######
		# this lines removes the background shadow of button
		# and makes it look like a standard Gtk.ToolButton on a Gtk.ToolBar
		self.set_relief(gtk.ReliefStyle.NONE)
		##
		self.set_focus_on_click(False)
		# self.set_can_default(False)
		# self.set_can_focus(False)
		######
		self._name = name
		self.onClick = onClick
		self.onPress = onPress
		if args is None:
			args = ()
		self.args = args
		self.iconSize = 0
		self.continuousClick = continuousClick
		self.vertical = False
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
		self.imageName = ""
		self.imageNameDynamic = imageNameDynamic
		######
		self.bigPixbuf = None
		self.image = gtk.Image()
		self.image.show()
		self.add(self.image)
		###
		if imageName and not iconName:
			iconName = iconNameByImageName.get(imageName, "")
		self.imageName = imageName
		self.iconName = iconName
		self.preferIconName = False
		######
		self.initVars()
		if enableTooltip:
			set_tooltip(self, desc)
		######
		self.enable = enable

	def build(self):
		"""
			This method must be called after creating instance and calling
			one/many of these methods:
				- setIconName
				- setIconFile
				- setIconSize
				- setPreferIconName
		"""
		imageName = self.imageName
		iconName = self.iconName
		if not (imageName or iconName):
			self.bigPixbuf = None
			if self.image is not None:
				self.image.clear()
			return

		useIconName = bool(iconName)
		if useIconName:
			if self.imageName and not self.preferIconName:
				useIconName = False

		if useIconName:
			self.bigPixbuf = self.render_icon_pixbuf(
				self.iconName,
				gtk.IconSize.DIALOG,
			)
			self._setIconSizeImage(self.iconSize)
		else:
			self.bigPixbuf = pixbufFromFile(self.imageName, size=self.iconSize)
			if self.imageName.endswith(".svg"):
				self.image.set_from_pixbuf(self.bigPixbuf)
			else:
				self._setIconSizeImage(self.iconSize)

	def setIconName(self, iconName: str) -> None:
		self.iconName = iconName

	def setIconFile(self, fname: str) -> None:
		self.imageName = fname

	def setIconSize(self, iconSize: int) -> None:
		self.iconSize = iconSize

	def setPreferIconName(self, preferIconName: bool) -> None:
		self.preferIconName = preferIconName

	def _setIconSizeImage(self, iconSize: int) -> None:
		if self.bigPixbuf is None:
			if self.imageName:
				self.image.set_from_pixbuf(pixbufFromFile(
					self.imageName,
					size=iconSize,
				))
				return
			if self.imageNameDynamic:
				return
			raise RuntimeError(f"bigPixbuf=None, self.imageName={self.imageName}, name={self._name}")
		pixbuf = self.bigPixbuf.scale_simple(
			iconSize,
			iconSize,
			GdkPixbuf.InterpType.BILINEAR,
		)
		self.image.set_from_pixbuf(pixbuf)


@registerSignals
class LabelToolBoxItem(BaseToolBoxItem):
	def __init__(
		self,
		name: str = "",
		onClick: Union[None, str, Callable] = None,
		desc: str = "",
		shortDesc: str = "",
		enableTooltip: bool = True,
		continuousClick: bool = True,
		onPress: Optional[Union[str, Callable]] = None,
		args: Optional[Tuple[Any]] = None,  # for onClick and onPress
	) -> None:
		gtk.Button.__init__(self)
		if continuousClick:
			ConButtonBase.__init__(self, button=1)
		######
		# this lines removes the background shadow of button
		# and makes it look like a standard Gtk.ToolButton on a Gtk.ToolBar
		self.set_relief(gtk.ReliefStyle.NONE)
		##
		self.set_focus_on_click(False)
		# self.set_can_default(False)
		# self.set_can_focus(False)
		######
		self._name = name
		self.onClick = onClick
		self.onPress = onPress
		if args is None:
			args = ()
		self.args = args
		self.continuousClick = continuousClick
		self.vertical = False
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
		self.label = gtk.Label()
		self.add(self.label)
		######
		self.initVars()
		if enableTooltip:
			set_tooltip(self, desc)

	def setIconSize(self, iconSize: int) -> None:
		pass

	def setPreferIconName(self, preferIconName: bool) -> None:
		pass

	def build(self):
		pass

	# the following methods (do_get_*) are overridden to avoid changing size
	# of all icons (or even this icon) when text width changes slightly
	# we assume text height does not change, and the text fits in the square
	def do_get_request_mode(self) -> gtk.SizeRequestMode:
		return gtk.SizeRequestMode.WIDTH_FOR_HEIGHT

	def do_get_preferred_height_for_width(self, size: int) -> Tuple[int, int]:
		# must return minimum_size, natural_size
		return self.do_get_preferred_width_for_height(size)

	def do_get_preferred_width_for_height(self, size: int) -> Tuple[int, int]:
		# must return minimum_size, natural_size
		return size, size


# @registerSignals
class BaseToolBox(gtk.EventBox, CustomizableCalObj):
	# signals = CustomizableCalObj.signals + [
	# 	("popup-main-menu", [int, int, int]),
	# ]
	def __init__(
		self,
		funcOwner: Any,
		vertical: bool = False,
		iconSize: int = 0,
		continuousClick: bool = True,
		buttonBorder: int = 0,
		buttonPadding: int = 0,
	) -> None:
		gtk.EventBox.__init__(self)
		self.vertical = vertical
		self.box = gtk.Box(self, orientation=self.get_orientation())
		self.add(self.box)
		self.box.set_homogeneous(False)
		self.box.show()
		self.funcOwner = funcOwner
		self.preferIconName = ui.useSystemIcons
		if iconSize == 0:
			iconSize = ui.toolbarIconSize
		self.iconSize = iconSize
		self.continuousClick = continuousClick
		self.buttonBorder = buttonBorder
		self.buttonPadding = buttonPadding
		self.initVars()

	def get_orientation(self) -> gtk.Orientation:
		if self.vertical:
			return gtk.Orientation.VERTICAL
		return gtk.Orientation.HORIZONTAL

	def setupItemSignals(self, item: ud.CalObjType) -> None:
		if item.onClick:
			if isinstance(item.onClick, str):
				onClick = getattr(self.funcOwner, item.onClick)
			else:
				onClick = item.onClick
			item.connect("clicked", onClick, *item.args)
			if self.continuousClick and item.continuousClick:
				item.connect("con-clicked", onClick, *item.args)

		if item.onPress:
			if isinstance(item.onPress, str):
				onPress = getattr(self.funcOwner, item.onClick)
			else:
				onPress = item.onPress
			item.connect("button-press-event", onPress, *item.args)


class StaticToolBox(BaseToolBox):
	def __init__(
		self,
		funcOwner: Any,
		vertical: bool = False,
		iconSize: int = 0,
		continuousClick: bool = True,
		buttonBorder: int = 0,
		buttonPadding: int = 0,
	) -> None:
		BaseToolBox.__init__(
			self,
			funcOwner,
			vertical=vertical,
			iconSize=iconSize,
			continuousClick=continuousClick,
			buttonBorder=buttonBorder,
			buttonPadding=buttonPadding
		)

	def getIconSize(self) -> int:
		return self.iconSize

	def append(self, item: BaseToolBoxItem) -> BaseToolBoxItem:
		item.setVertical(self.vertical)
		item.setIconSize(self.iconSize)
		item.setPreferIconName(self.preferIconName)
		item.set_border_width(self.buttonBorder)
		item.build()
		item.onConfigChange(toParent=False)
		self.setupItemSignals(item)
		pack(self.box, item, padding=self.buttonPadding)
		item.show()
		return item



class CustomizableToolBox(StaticToolBox):
	_name = "toolbar"
	desc = _("Toolbar")
	styleList = (
		# Gnome"s naming is not exactly the best here
		# And Gnome"s order of options is also different from Gtk"s enum
		"Icon", # "icons", "Icons only"
		"Text", # "text", "Text only"
		"Text below Icon", # "both", "Text below items"
		"Text beside Icon", # "both-horiz", "Text beside items"
	)
	defaultItems = []
	defaultItemsDict = {}

	def __init__(
		self,
		funcOwner: Any,
		vertical: bool = False,
		iconSize: int = 0,
		continuousClick: bool = True,
	) -> None:
		BaseToolBox.__init__(
			self,
			funcOwner,
			vertical=vertical,
			iconSize=iconSize,
			continuousClick=continuousClick,
		)

		#self.add_events(gdk.EventMask.POINTER_MOTION_MASK)

		# set on setData(), used in getData() to keep compatibility
		self.data = {}

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import CheckPrefItem, SpinPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		###
		optionsWidget = VBox()
		####
		prefItem = CheckPrefItem(
			self,
			"preferIconName",
			label=_("Use System Icons"),
			live=True,
			onChangeFunc=self.updateItems,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		prefItem = SpinPrefItem(
			self,
			"iconSize",
			5, 128,
			digits=1, step=1,
			label=_("Icon Size"),
			live=True,
			onChangeFunc=self.onIconSizeChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		prefItem = SpinPrefItem(
			self,
			"buttonBorder",
			0, 99,
			digits=1, step=1,
			label=_("Buttons Border"),
			live=True,
			onChangeFunc=self.updateItems,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		prefItem = SpinPrefItem(
			self,
			"buttonPadding",
			0, 99,
			digits=1, step=1,
			label=_("Space between buttons"),
			live=True,
			onChangeFunc=self.updateItems,
		)
		pack(optionsWidget, prefItem.getWidget())
		##
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def setPreferIconName(self, preferIconName: bool) -> None:
		self.preferIconName = preferIconName

	def setIconSize(self, size: int) -> None:
		self.iconSize = size

	# this method is for optimization
	# otherwide can be replaced with updateItems
	def onIconSizeChange(self) -> None:
		iconSize = self.iconSize
		for item in self.items:
			item.setIconSize(iconSize)
			item.build()

	def setButtonBorder(self, buttonBorder):
		self.buttonBorder = buttonBorder

	def setButtonPadding(self, padding: int) -> None:
		self.buttonPadding = padding

	def repackAll(self):
		for item in self.items:
			if item.loaded:
				self.box.remove(item)
		for item in self.items:
			if item.loaded:
				pack(self.box, item, item.expand, item.expand)

	def moveItem(self, i, j):
		CustomizableCalObj.moveItem(self, i, j)
		self.repackAll()

	def appendItem(self, item: BaseToolBoxItem) -> None:
		CustomizableCalObj.appendItem(self, item)
		pack(self.box, item)
		if item.enable:
			item.show()

	def updateItems(self):
		"""
			Must be called after creating the instance and calling setData()
			Also after one of the properties (preferIconName, iconSize,
			buttonBorder, buttonPadding) are changed.
			Must be called before onConfigChange()
		"""
		preferIconName = self.preferIconName
		iconSize = self.iconSize
		buttonBorder = self.buttonBorder
		buttonPadding = self.buttonPadding
		for item in self.items:
			item.setPreferIconName(preferIconName)
			item.setIconSize(iconSize)
			item.set_border_width(buttonBorder)
			self.box.set_child_packing(
				child=item,
				expand=False,
				fill=False,
				padding=buttonPadding,
				pack_type=gtk.PackType.START,
			)
			item.build()
			item.onConfigChange(toParent=False)

	def getData(self) -> Dict[str, Any]:
		self.data.update({
			"items": self.getItemsData(),
			"iconSizePixel": self.getIconSize(),
			"buttonBorder": self.buttonBorder,
			"buttonPadding": self.buttonPadding,
			"preferIconName": self.preferIconName,
		})
		return self.data

	def setData(self, data: Dict[str, Any]) -> None:
		self.data = data
		for (name, enable) in data["items"]:
			item = self.defaultItemsDict.get(name)
			if item is None:
				log.info(f"toolbar item {name!r} does not exist")
				continue
			item.enable = enable
			item.setVertical(self.vertical)
			self.setupItemSignals(item)
			self.appendItem(item)
		###
		preferIconName = data.get("preferIconName")
		if preferIconName is not None:
			self.setPreferIconName(preferIconName)
		###
		iconSize = data.get("iconSizePixel")
		if iconSize:
			self.setIconSize(iconSize)
		###
		bb = data.get("buttonBorder", 0)
		self.setButtonBorder(bb)
		###
		padding = data.get("buttonPadding", 0)
		self.setButtonPadding(padding)
		self.optionsWidget = None
		###
		self.updateItems()
