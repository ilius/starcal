#!/usr/bin/env python3

from typing import Optional

from scal3.path import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import set_tooltip, pixbufFromFile
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj, CustomizableCalBox
from scal3.ui_gtk import gtk_ud as ud


@registerSignals
class WinConButton(gtk.EventBox, CustomizableCalObj):
	hasOptions = False
	expand = False

	imageName = ""
	imageNameFocus = ""
	imageNameInactive = ""

	def __init__(self, controller):
		gtk.EventBox.__init__(self)
		self.set_border_width(ui.winControllerBorder)
		self.initVars()
		###
		self.controller = controller
		CustomizableCalObj.initVars(self)
		self.build()
		###
		if controller.win:
			self.connect("button-press-event", controller.win.childButtonPress)
		###
		self.show_all()

	def onClick(self, gWin, gevent):
		raise NotImplementedError

	def setImage(self, imName):
		if self.controller.light:
			imName += "-light"
		self.im.set_from_pixbuf(pixbufFromFile(
			join(
				"wm",
				ui.winControllerTheme,
				imName + ".svg"
			),
			ui.winControllerIconSize,
		))

	def setFocus(self, focus):
		self.setImage(self.imageNameFocus if focus else self.imageName)

	def setInactive(self):
		if not self.imageNameInactive:
			return
		self.setImage(self.imageNameInactive)

	def build(self):
		self.im = gtk.Image()
		self.setFocus(False)
		self.add(self.im)
		self.connect("enter-notify-event", self.enterNotify)
		self.connect("leave-notify-event", self.leaveNotify)
		self.connect("button-press-event", self.onButtonPress)
		self.connect("button-release-event", self.onButtonRelease)
		set_tooltip(self, self.desc)## FIXME

	def enterNotify(self, widget, gevent):
		self.setFocus(True)

	def leaveNotify(self, widget, gevent):
		if self.controller.winFocused:
			self.setFocus(False)
		else:
			self.setInactive()
		return False

	def onButtonPress(self, widget, gevent):
		self.setFocus(False)
		return True

	def onClick(self, gWin, gevent):
		pass

	def onRightClick(self, gWin, gevent):
		pass

	def onButtonRelease(self, button, gevent):
		if gevent.button == 1:
			self.onClick(self.controller.win, gevent)
			return True
		elif gevent.button == 3:
			self.onRightClick(self.controller.win, gevent)
			return True
		return False


class WinConButtonMin(WinConButton):
	_name = "min"
	desc = _("Minimize Window")
	imageName = "minimize"
	imageNameFocus = "minimize-focus"
	imageNameInactive = "minimize-inactive"

	def onClick(self, gWin, gevent):
		gWin.toggleMinimized(gevent)


class WinConButtonMax(WinConButton):
	_name = "max"
	desc = _("Maximize Window")
	imageName = "maximize"
	imageNameFocus = "maximize-focus"
	imageNameInactive = "maximize-inactive"

	def onClick(self, gWin, gevent):
		gWin.toggleMaximized(gevent)

	def onRightClick(self, gWin, gevent):
		gWin.toggleWidthMaximized(gevent)



class WinConButtonClose(WinConButton):
	_name = "close"
	desc = _("Close Window")
	imageName = "close"
	imageNameFocus = "close-focus"
	imageNameInactive = "close-inactive"

	def onClick(self, gWin, gevent):
		gWin.emit("delete-event", gdk.Event())


class WinConButtonRightPanel(WinConButton):
	_name = "rightPanel"
	desc = _("Show Right Panel")
	
	def __init__(self, controller):
		direc = "left" if rtl else "right"
		self.imageName = f"{direc}"
		self.imageNameFocus = f"{direc}-focus"
		self.imageNameInactive = f"{direc}-inactive"
		WinConButton.__init__(self, controller)

	def onClick(self, gWin, gevent):
		gWin.emit("toggle-right-panel")


class WinConButtonSep(WinConButton):
	_name = "sep"
	desc = _("Separator")
	expand = True

	def build(self):
		pass

	def setFocus(self, focus):
		pass

	def setInactive(self):
		pass

# Stick
# Above
# Below


@registerSignals
class CalObj(gtk.Box, CustomizableCalBox):
	hasOptions = True
	_name = "winContronller"
	desc = _("Window Controller")
	buttonClassList = (
		WinConButtonMin,
		WinConButtonMax,
		WinConButtonClose,
		WinConButtonSep,
		WinConButtonRightPanel,
	)
	buttonClassDict = {
		cls._name: cls
		for cls in buttonClassList
	}

	def __init__(self, win):
		self.win = win
		gtk.Box.__init__(
			self,
			orientation=gtk.Orientation.HORIZONTAL,
			spacing=ui.winControllerSpacing,
		)
		self.set_spacing(ui.winControllerSpacing)
		self.set_direction(gtk.TextDirection.LTR)## FIXME
		self.initVars()
		###########
		# passing `self` to ud.hasLightTheme does not work!
		self.light = ud.hasLightTheme(win)
		###########
		for bname, enable in ui.winControllerButtons:
			button = self.buttonClassDict[bname](self)
			button.enable = enable
			self.appendItem(button)
		self.set_property("can-focus", True)
		##################
		if win:
			win.winCon = self  # dirty FIXME
		##gWin.connect("focus-in-event", self.windowFocusIn)
		##gWin.connect("focus-out-event", self.windowFocusOut)
		self.winFocused = True

	def windowFocusIn(self, widget=None, event=None):
		for b in self.items:
			b.setFocus(False)
		self.winFocused = True
		return False

	def windowFocusOut(self, widget=None, event=None):
		for b in self.items:
			b.setInactive()
		self.winFocused = False
		return False

	def updateVars(self):
		CustomizableCalBox.updateVars(self)
		ui.winControllerButtons = self.getItemsData()

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import SpinPrefItem, ComboTextPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = VBox()
		####
		prefItem = ComboTextPrefItem(
			ui,
			"winControllerTheme",
			items=ui.winControllerThemeList,
			label=_("Theme"),
			live=True,
			onChangeFunc=self.updateTheme,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		prefItem = SpinPrefItem(
			ui,
			"winControllerIconSize",
			5, 128,
			digits=1, step=1,  # noqa: FURB120
			label=_("Icon Size"),
			live=True,
			onChangeFunc=self.updateButtons,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		prefItem = SpinPrefItem(
			ui,
			"winControllerBorder",
			0, 99,
			digits=1, step=1,  # noqa: FURB120
			label=_("Buttons Border"),
			live=True,
			onChangeFunc=self.onButtonBorderChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		prefItem = SpinPrefItem(
			ui,
			"winControllerSpacing",
			0, 99,
			digits=1, step=1,  # noqa: FURB120
			label=_("Space between buttons"),
			live=True,
			onChangeFunc=self.onButtonPaddingChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def updateTheme(self):
		pass

	def updateButtons(self):
		for item in self.items:
			item.setFocus(False)

	def onButtonBorderChange(self) -> None:
		for item in self.items:
			item.set_border_width(ui.winControllerBorder)
		self.updateButtons()

	def onButtonPaddingChange(self) -> None:
		self.set_spacing(ui.winControllerSpacing)
		self.updateButtons()
