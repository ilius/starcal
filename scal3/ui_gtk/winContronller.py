from __future__ import annotations

import os
from os.path import join
from typing import TYPE_CHECKING, Protocol

from scal3 import ui
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.path import svgDir
from scal3.ui import conf
from scal3.ui_gtk import gdk, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.customize import CustomizableCalBox
from scal3.ui_gtk.option_ui import IntSpinOptionUI, OptionUI
from scal3.ui_gtk.utils import pixbufFromFile, set_tooltip

if TYPE_CHECKING:
	from collections.abc import Iterator

	from scal3.ui_gtk.signals import SignalHandlerType

__all__ = ["CalObj"]

themeFileSet = {
	"close-focus-light.svg",
	"close-focus.svg",
	"close-inactive-light.svg",
	"close-inactive.svg",
	"close-light.svg",
	"close-press-light.svg",
	"close-press.svg",
	"close.svg",
	"left-focus-light.svg",
	"left-focus.svg",
	"left-inactive-light.svg",
	"left-inactive.svg",
	"left-light.svg",
	"left-press-light.svg",
	"left-press.svg",
	"left.svg",
	"maximize-focus-light.svg",
	"maximize-focus.svg",
	"maximize-inactive-light.svg",
	"maximize-inactive.svg",
	"maximize-light.svg",
	"maximize-press-light.svg",
	"maximize-press.svg",
	"maximize.svg",
	"minimize-focus-light.svg",
	"minimize-focus.svg",
	"minimize-inactive-light.svg",
	"minimize-inactive.svg",
	"minimize-light.svg",
	"minimize-press-light.svg",
	"minimize-press.svg",
	"minimize.svg",
	"right-focus-light.svg",
	"right-focus.svg",
	"right-inactive-light.svg",
	"right-inactive.svg",
	"right-light.svg",
	"right-press-light.svg",
	"right-press.svg",
	"right.svg",
}


class MainWinType(Protocol):
	win: gtk.ApplicationWindow
	s: SignalHandlerType

	def childButtonPress(
		self,
		widget: gtk.Widget,  # noqa: ARG002
		gevent: gdk.EventButton,
	) -> bool: ...
	def toggleMinimized(self, gevent: gdk.EventButton) -> None: ...
	def toggleMaximized(self, _ge: gdk.EventButton) -> None: ...
	def toggleWidthMaximized(self, _ge: gdk.EventButton) -> None: ...


class WinConButton(CustomizableCalObj):
	hasOptions = False
	expand = False

	imageName = ""
	imageNameFocus = ""
	imageNameInactive = ""
	imageNamePress = ""

	def __init__(self, controller: CalObj) -> None:
		super().__init__()
		self.ebox = gtk.EventBox()
		self.w: gtk.Widget = self.ebox
		self.ebox.set_border_width(conf.winControllerBorder.v)
		self.initVars()
		# ---
		self.controller = controller
		self.build()
		# ---
		win = controller.parentWin
		if win:
			self.w.connect("button-press-event", win.childButtonPress)
		# ---
		self.w.show_all()

	def setImage(self, imName: str) -> None:
		if self.controller.light:
			imName += "-light"
		self.im.set_from_pixbuf(
			pixbufFromFile(
				join(
					"wm",
					conf.winControllerTheme.v,
					imName + ".svg",
				),
				conf.winControllerIconSize.v,
			),
		)

	def setFocus(self, focus: bool) -> None:
		self.setImage(self.imageNameFocus if focus else self.imageName)

	def setInactive(self) -> None:
		if not self.imageNameInactive:
			return
		self.setImage(self.imageNameInactive)

	def setPressed(self) -> None:
		self.setImage(
			self.imageNamePress
			if conf.winControllerPressState.v
			else self.imageNameFocus,
		)

	def build(self) -> None:
		self.im = gtk.Image()
		self.setFocus(False)
		box = self.ebox
		box.add(self.im)
		box.connect("enter-notify-event", self.enterNotify)
		box.connect("leave-notify-event", self.leaveNotify)
		box.connect("button-press-event", self.onButtonPress)
		box.connect("button-release-event", self.onButtonRelease)
		set_tooltip(self.w, self.desc)  # FIXME

	def enterNotify(self, _w: gtk.Widget, _ge: gdk.EventMotion) -> None:
		self.setFocus(True)

	def leaveNotify(self, _w: gtk.Widget, _ge: gdk.EventMotion) -> bool:
		if self.controller.winFocused:
			self.setFocus(False)
		else:
			self.setInactive()
		return False

	def onButtonPress(self, _w: gtk.Widget, _ge: gdk.EventButton) -> bool:
		self.setPressed()
		return True

	def onClick(self, win: MainWinType, gevent: gdk.EventButton) -> None:
		pass

	def onRightClick(self, win: MainWinType, gevent: gdk.EventButton) -> None:
		pass

	def onButtonRelease(self, _b: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if gevent.button == 1:
			self.onClick(self.controller.parentWin, gevent)
			return True
		if gevent.button == 3:
			self.onRightClick(self.controller.parentWin, gevent)
			return True
		return False


class WinConButtonMin(WinConButton):
	objName = "min"
	desc = _("Minimize Window")
	imageName = "minimize"
	imageNameFocus = "minimize-focus"
	imageNameInactive = "minimize-inactive"
	imageNamePress = "minimize-press"

	def onClick(self, win: MainWinType, gevent: gdk.EventButton) -> None:  # noqa: PLR6301
		win.toggleMinimized(gevent)


class WinConButtonMax(WinConButton):
	objName = "max"
	desc = _("Maximize Window")
	imageName = "maximize"
	imageNameFocus = "maximize-focus"
	imageNameInactive = "maximize-inactive"
	imageNamePress = "maximize-press"

	def onClick(self, win: MainWinType, gevent: gdk.EventButton) -> None:  # noqa: PLR6301
		win.toggleMaximized(gevent)

	def onRightClick(self, win: MainWinType, gevent: gdk.EventButton) -> None:  # noqa: PLR6301
		win.toggleWidthMaximized(gevent)


class WinConButtonClose(WinConButton):
	objName = "close"
	desc = _("Close Window")
	imageName = "close"
	imageNameFocus = "close-focus"
	imageNameInactive = "close-inactive"
	imageNamePress = "close-press"

	def onClick(self, win: MainWinType, _ge: gdk.EventButton) -> None:  # noqa: PLR6301
		win.win.emit("delete-event", gdk.Event())


class WinConButtonRightPanel(WinConButton):
	objName = "rightPanel"
	desc = _("Show Right Panel")

	def __init__(self, controller: CalObj) -> None:
		direc = "left" if rtl else "right"
		self.imageName = direc
		self.imageNameFocus = f"{direc}-focus"
		self.imageNameInactive = f"{direc}-inactive"
		self.imageNamePress = f"{direc}-press"
		WinConButton.__init__(self, controller)

	def onClick(self, win: MainWinType, _ge: gdk.EventButton) -> None:  # noqa: PLR6301
		win.s.emit("toggle-right-panel")


class WinConButtonSep(WinConButton):
	objName = "sep"
	desc = _("Separator")
	expand = True

	def build(self) -> None:
		pass

	def setFocus(self, focus: bool) -> None:
		pass

	def setInactive(self) -> None:
		pass


# Stick
# Above
# Below


class CalObj(CustomizableCalBox):
	vertical = False
	hasOptions = True
	itemHaveOptions = False
	objName = "winContronller"
	desc = _("Window Controller")
	buttonClassList = (
		WinConButtonMin,
		WinConButtonMax,
		WinConButtonClose,
		WinConButtonSep,
		WinConButtonRightPanel,
	)
	buttonClassDict = {cls.objName: cls for cls in buttonClassList}

	def __init__(self, win: MainWinType) -> None:
		CustomizableCalBox.__init__(self, vertical=False)
		self.parentWin = win
		self.box.set_spacing(conf.winControllerSpacing.v)
		self.w.set_direction(gtk.TextDirection.LTR)  # FIXME
		self.initVars()
		# -----------
		# passing `self` to ud.hasLightTheme does not work!
		self.light = ud.hasLightTheme(win.win)
		# -----------
		for bname, enable in conf.winControllerButtons.v:
			button = self.buttonClassDict[bname](self)
			button.enable = enable
			self.appendItem(button)
		self.w.set_property("can-focus", True)
		# ------------------
		# if win:
		# 	win.winCon = self  # dirty FIXME REMOVE
		# gWin.connect("focus-in-event", self.windowFocusIn)
		# gWin.connect("focus-out-event", self.windowFocusOut)
		self.winFocused = True

	@property
	def buttons(self) -> Iterator[WinConButton]:
		for b in self.items:
			assert isinstance(b, WinConButton), f"{b=}"
			yield b

	def windowFocusIn(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> bool:
		for b in self.buttons:
			b.setFocus(False)
		self.winFocused = True
		return False

	def windowFocusOut(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> bool:
		for b in self.buttons:
			b.setInactive()
		self.winFocused = False
		return False

	def updateVars(self) -> None:
		CustomizableCalBox.updateVars(self)
		conf.winControllerButtons.v = self.getItemsData()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui import (
			CheckOptionUI,
			ComboTextOptionUI,
		)

		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		option: OptionUI
		# ----
		option = ComboTextOptionUI(
			option=conf.winControllerTheme,
			items=ui.winControllerThemeList,
			label=_("Theme"),
			live=True,
			onChangeFunc=self.updateTheme,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		option = IntSpinOptionUI(
			option=conf.winControllerIconSize,
			bounds=(5, 128),
			step=1,
			label=_("Icon Size"),
			live=True,
			onChangeFunc=self.updateButtons,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		option = IntSpinOptionUI(
			option=conf.winControllerBorder,
			bounds=(0, 99),
			step=1,
			label=_("Buttons Border"),
			live=True,
			onChangeFunc=self.onButtonBorderChange,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		option = IntSpinOptionUI(
			option=conf.winControllerSpacing,
			bounds=(0, 99),
			step=1,
			label=_("Space between buttons"),
			live=True,
			onChangeFunc=self.onButtonPaddingChange,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		option = CheckOptionUI(
			option=conf.winControllerPressState,
			label=_("Change icon on button press"),
			live=True,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def updateTheme(self) -> None:  # noqa: PLR6301
		name = conf.winControllerTheme.v
		dirPath = join(svgDir, "wm", name)
		fileSet = set(os.listdir(dirPath))
		if fileSet == themeFileSet:
			return
		print(fileSet)
		missingFiles = themeFileSet - fileSet
		extraFiles = fileSet - themeFileSet
		if missingFiles:
			print(f"Missing svg files: {missingFiles}")
		if extraFiles:
			print(f"Extra svg files: {extraFiles}")

	def updateButtons(self) -> None:
		for item in self.buttons:
			item.setFocus(False)

	def onButtonBorderChange(self) -> None:
		for item in self.buttons:
			item.ebox.set_border_width(conf.winControllerBorder.v)
		self.updateButtons()

	def onButtonPaddingChange(self) -> None:
		self.box.set_spacing(conf.winControllerSpacing.v)
		self.updateButtons()
