from __future__ import annotations

from scal3 import logger
from scal3.property import Property
from scal3.ui_gtk.pref_utils import FloatSpinPrefItem, IntSpinPrefItem, PrefItem

log = logger.get()

import typing
from typing import Any

from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import GdkPixbuf, VBox, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.icon_mapping import iconNameByImageName
from scal3.ui_gtk.mywidgets.button import ConButtonBase
from scal3.ui_gtk.utils import pixbufFromFile, set_tooltip

if typing.TYPE_CHECKING:
	from collections.abc import Callable, Iterable, Sequence

	from scal3.ui.pytypes import CustomizableToolBoxDict

__all__ = [
	"CustomizableToolBox",
	"LabelToolBoxItem",
	"StaticToolBox",
	"ToolBoxItem",
	"VerticalStaticToolBox",
]


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

	def do_get_preferred_height_for_width(self, size: int) -> tuple[int, int]:
		# must return minimum_size, natural_size
		if not self.vertical:
			# self.get_preferred_height() does not work well here, not sure why
			return self.do_get_preferred_width_for_height(size)
		return size, size

	def do_get_preferred_width_for_height(self, size: int) -> tuple[int, int]:
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
		onClick: str | Callable | None = None,
		desc: str = "",
		shortDesc: str = "",
		enableTooltip: bool = True,
		continuousClick: bool = True,
		onPress: str | Callable | None = None,
		args: Sequence[Any] | None = None,  # for onClick and onPress
		enable: bool = True,
	) -> None:
		gtk.Button.__init__(self)
		if continuousClick:
			ConButtonBase.__init__(self, button=1)  # only left-click
		# ------
		# this lines removes the background shadow of button
		# and makes it look like a standard GtkToolButton on a GtkToolbar
		self.set_relief(gtk.ReliefStyle.NONE)
		# --
		self.set_focus_on_click(False)
		# self.set_can_default(False)
		# self.set_can_focus(False)
		# ------
		self.objName = name
		self.onClick = onClick
		self.onPress = onPress
		if args is None:
			args = ()
		self.args = args
		self.preferIconName = Property(False)
		self.iconSize = Property(conf.toolbarIconSize.v)
		self.continuousClick = continuousClick
		self.vertical = False
		# ------
		if not desc:
			desc = name.capitalize()
		if not shortDesc:
			shortDesc = desc
		# --
		desc = _(desc)
		shortDesc = _(shortDesc)
		self.desc = desc
		# self.shortDesc = shortDesc  # FIXME
		# ------
		self.imageName = ""
		self.imageNameDynamic = imageNameDynamic
		# ------
		self.bigPixbuf = None
		self.image = gtk.Image()
		self.image.show()
		self.add(self.image)
		# ---
		if imageName and not iconName:
			iconName = iconNameByImageName.get(imageName, "")
		self.imageName = imageName
		self.iconName = iconName
		# ------
		self.initVars()
		if enableTooltip:
			set_tooltip(self, desc)
		# ------
		self.enable = enable

	def build(self) -> None:
		"""
		Call this after creating instance and calling one/many of these methods:
		- setIconName
		- setIconFile.
		"""
		imageName = self.imageName
		iconName = self.iconName
		if not (imageName or iconName):
			self.bigPixbuf = None
			if self.image is not None:
				self.image.clear()
			return

		useIconName = bool(iconName)
		if useIconName and self.imageName and not self.preferIconName.v:
			useIconName = False

		if useIconName:
			self.bigPixbuf = self.render_icon_pixbuf(
				self.iconName,
				gtk.IconSize.DIALOG,
			)
			self._setIconImage(self.iconSize.v)
		else:
			self.bigPixbuf = pixbufFromFile(self.imageName, size=self.iconSize.v)
			if self.imageName.endswith(".svg"):
				self.image.set_from_pixbuf(self.bigPixbuf)
			else:
				self._setIconImage(self.iconSize.v)

	def setIconName(self, iconName: str) -> None:
		self.iconName = iconName

	def setIconFile(self, fname: str) -> None:
		self.imageName = fname

	def _setIconImage(self, iconSize: float) -> None:
		if self.bigPixbuf is None:
			if self.imageName:
				self.image.set_from_pixbuf(
					pixbufFromFile(
						self.imageName,
						size=iconSize,
					),
				)
				return
			if self.imageNameDynamic:
				return
			raise RuntimeError(
				f"bigPixbuf=None, self.imageName={self.imageName}, name={self.objName}",
			)
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
		onClick: str | Callable | None = None,
		desc: str = "",
		shortDesc: str = "",
		enableTooltip: bool = True,
		continuousClick: bool = True,
		onPress: str | Callable | None = None,
		args: list[Any] | None = None,  # for onClick and onPress
	) -> None:
		gtk.Button.__init__(self)
		if continuousClick:
			ConButtonBase.__init__(self, button=1)
		# ------
		# this lines removes the background shadow of button
		# and makes it look like a standard GtkToolButton on a GtkToolbar
		self.set_relief(gtk.ReliefStyle.NONE)
		# --
		self.set_focus_on_click(False)
		# self.set_can_default(False)
		# self.set_can_focus(False)
		# ------
		self.objName = name
		self.onClick = onClick
		self.onPress = onPress
		if args is None:
			args = []
		self.args = args
		self.continuousClick = continuousClick
		self.vertical = False
		# ------
		if not desc:
			desc = name.capitalize()
		if not shortDesc:
			shortDesc = desc
		# --
		desc = _(desc)
		shortDesc = _(shortDesc)
		self.desc = desc
		# self.shortDesc = shortDesc  # FIXME
		# ------
		self.label = gtk.Label()
		self.add(self.label)
		# ------
		self.initVars()
		if enableTooltip:
			set_tooltip(self, desc)

	def build(self) -> None:
		pass

	# the following methods (do_get_*) are overridden to avoid changing size
	# of all icons (or even this icon) when text width changes slightly
	# we assume text height does not change, and the text fits in the square
	def do_get_request_mode(self) -> gtk.SizeRequestMode:  # noqa: PLR6301
		return gtk.SizeRequestMode.WIDTH_FOR_HEIGHT

	def do_get_preferred_height_for_width(self, size: int) -> tuple[int, int]:
		# must return minimum_size, natural_size
		return self.do_get_preferred_width_for_height(size)

	def do_get_preferred_width_for_height(  # noqa: PLR6301
		self,
		size: int,
	) -> tuple[int, int]:
		# must return minimum_size, natural_size
		return size, size


# @registerSignals
class BaseToolBox(gtk.EventBox, CustomizableCalObj):
	# signals = CustomizableCalObj.signals + [
	# 	("popup-main-menu", [int, int]),
	# ]
	def __init__(
		self,
		funcOwner: Any,
		iconSize: float = 0,
		continuousClick: bool = True,
		buttonBorder: int = 0,
		buttonPadding: int = 0,
	) -> None:
		assert self.vertical is not None
		gtk.EventBox.__init__(self)
		self.box = gtk.Box()
		self.box.set_orientation(self.get_orientation())
		self.box.set_homogeneous(homogeneous=False)
		self.box.show()
		self.add(self.box)
		self.funcOwner = funcOwner
		self.preferIconName: Property[bool] = conf.useSystemIcons
		self.iconSize: Property[float] = Property(iconSize or conf.toolbarIconSize.v)
		self.continuousClick = continuousClick
		self.buttonBorder = Property(buttonBorder)
		self.buttonPadding = Property(buttonPadding)
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
				onPress = getattr(self.funcOwner, item.onPress)
			else:
				onPress = item.onPress
			item.connect("button-press-event", onPress, *item.args)


class StaticToolBox(BaseToolBox):
	vertical = False

	def __init__(
		self,
		funcOwner: Any,
		iconSize: float = 0,
		continuousClick: bool = True,
		buttonBorder: int = 0,
		buttonPadding: int = 0,
	) -> None:
		BaseToolBox.__init__(
			self,
			funcOwner,
			iconSize=iconSize,
			continuousClick=continuousClick,
			buttonBorder=buttonBorder,
			buttonPadding=buttonPadding,
		)

	def append(self, item: BaseToolBoxItem) -> BaseToolBoxItem:
		item.setVertical(self.vertical)
		item.iconSize = self.iconSize
		item.preferIconName = self.preferIconName
		item.set_border_width(self.buttonBorder.v)
		item.build()
		item.onConfigChange(toParent=False)
		self.setupItemSignals(item)
		pack(self.box, item, padding=self.buttonPadding.v)
		item.show()
		return item

	def extend(self, items: Iterable) -> None:
		for item in items:
			self.append(item)


class VerticalStaticToolBox(StaticToolBox):
	vertical = True


class CustomizableToolBox(StaticToolBox):
	itemListCustomizable = True
	objName = "toolbar"
	desc = _("Toolbar")
	defaultItems: list[ToolBoxItem] = []
	defaultItemsDict: dict[str, ToolBoxItem] = {}

	def __init__(
		self,
		funcOwner: Any,
		iconSize: float = 0,
		continuousClick: bool = True,
	) -> None:
		BaseToolBox.__init__(
			self,
			funcOwner,
			iconSize=iconSize,
			continuousClick=continuousClick,
		)

		# self.add_events(gdk.EventMask.POINTER_MOTION_MASK)

		# set on setDict(), used in getDict() to keep compatibility
		self.data: CustomizableToolBoxDict = {}  # type: ignore[typeddict-item]

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import CheckPrefItem

		if self.optionsWidget:
			return self.optionsWidget
		# ---
		optionsWidget = VBox()
		prefItem: PrefItem
		# ----
		prefItem = CheckPrefItem(
			prop=self.preferIconName,
			label=_("Use System Icons"),
			live=True,
			onChangeFunc=self.updateItems,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ----
		prefItem = FloatSpinPrefItem(
			prop=self.iconSize,
			bounds=(5, 128),
			digits=1,
			step=1,
			label=_("Icon Size"),
			live=True,
			onChangeFunc=self.onIconSizeChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ----
		prefItem = IntSpinPrefItem(
			prop=self.buttonBorder,
			bounds=(0, 99),
			step=1,
			label=_("Buttons Border"),
			live=True,
			onChangeFunc=self.updateItems,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ----
		prefItem = IntSpinPrefItem(
			prop=self.buttonPadding,
			bounds=(0, 99),
			step=1,
			label=_("Space between buttons"),
			live=True,
			onChangeFunc=self.updateItems,
		)
		pack(optionsWidget, prefItem.getWidget())
		# --
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	# this method is for optimization
	# otherwide can be replaced with updateItems
	def onIconSizeChange(self) -> None:
		for item in self.items:
			item.build()

	def repackAll(self) -> None:
		for item in self.items:
			if item.loaded:
				self.box.remove(item)
		for item in self.items:
			if item.loaded:
				pack(self.box, item, item.expand, item.expand)

	def moveItem(self, i: int, j: int) -> None:
		CustomizableCalObj.moveItem(self, i, j)
		self.repackAll()

	def appendItem(self, item: BaseToolBoxItem) -> None:
		CustomizableCalObj.appendItem(self, item)
		self.append(item)
		if item.enable:
			item.show()

	def updateItems(self) -> None:
		"""
		Must be called after creating the instance and calling setDict()
		Also after one of the properties (preferIconName, iconSize,
		buttonBorder, buttonPadding) are changed.
		Must be called before onConfigChange().
		"""
		buttonBorder = self.buttonBorder.v
		buttonPadding = self.buttonPadding.v
		for item in self.items:
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

	def getDict(self) -> CustomizableToolBoxDict:
		self.data.update(
			{
				"items": self.getItemsData(),
				"iconSizePixel": self.iconSize.v,
				"buttonBorder": self.buttonBorder.v,
				"buttonPadding": self.buttonPadding.v,
				"preferIconName": self.preferIconName.v,
			},
		)
		return self.data

	def setDict(self, data: CustomizableToolBoxDict) -> None:
		self.data = data
		for name, enable in data["items"]:
			item = self.defaultItemsDict.get(name)
			if item is None:
				log.info(f"toolbar item {name!r} does not exist")
				continue
			item.enable = enable
			item.setVertical(self.vertical)
			self.setupItemSignals(item)
			self.appendItem(item)
		# ---
		preferIconName = data.get("preferIconName")
		if preferIconName is not None:
			self.preferIconName.v = preferIconName
		# ---
		iconSize = data.get("iconSizePixel")
		if iconSize:
			self.iconSize.v = iconSize
		# ---
		bb = data.get("buttonBorder", 0)
		self.buttonBorder.v = bb
		# ---
		padding = data.get("buttonPadding", 0)
		self.buttonPadding.v = padding
		self.optionsWidget = None
		# ---
		self.updateItems()
