from scal3.path import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import set_tooltip
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj, CustomizableCalBox


@registerSignals
class WinConButton(gtk.EventBox, CustomizableCalObj):
	expand = False
	imageName = ""
	imageNameFocus = ""
	imageNameInactive = "button-inactive.png"

	def __init__(self, controller, size=23):
		gtk.EventBox.__init__(self)
		self.initVars()
		###
		self.size = size
		self.controller = controller
		CustomizableCalObj.initVars(self)
		self.build()
		###
		if ui.mainWin:
			self.connect("button-press-event", ui.mainWin.childButtonPress)
		###
		self.show_all()

	def onClicked(self, gWin, gevent):
		raise NotImplementedError

	def setImage(self, imName):
		self.im.set_from_file("%s/wm/%s" % (pixDir, imName))

	def setFocus(self, focus):
		self.setImage(self.imageNameFocus if focus else self.imageName)

	def setInactive(self):
		self.setImage(self.imageNameInactive)

	def build(self):
		self.im = gtk.Image()
		self.setFocus(False)
		self.im.set_size_request(self.size, self.size)
		self.add(self.im)
		self.connect("enter-notify-event", self.enterNotify)
		self.connect("leave-notify-event", self.leaveNotify)
		self.connect("button-press-event", self.buttonPress)
		self.connect("button-release-event", self.buttonRelease)
		set_tooltip(self, self.desc)## FIXME

	def enterNotify(self, widget, gevent):
		self.setFocus(True)

	def leaveNotify(self, widget, gevent):
		if self.controller.winFocused:
			self.setFocus(False)
		else:
			self.setInactive()
		return False

	def buttonPress(self, widget, gevent):
		self.setFocus(False)
		return True

	def onClicked(self, gWin, gevent):
		pass

	def buttonRelease(self, button, gevent):
		if gevent.button == 1:
			self.onClicked(self.controller.gWin, gevent)
		return False


class WinConButtonMin(WinConButton):
	_name = "min"
	desc = _("Minimize Window")
	imageName = "button-min.png"
	imageNameFocus = "button-min-focus.png"

	def onClicked(self, gWin, gevent):
		if ui.winTaskbar:
			gWin.iconify()
		else:
			gWin.emit("delete-event", gdk.Event(gevent))


class WinConButtonMax(WinConButton):
	_name = "max"
	desc = _("Maximize Window")
	imageName = "button-max.png"
	imageNameFocus = "button-max-focus.png"

	def onClicked(self, gWin, gevent):
		if gWin.isMaximized:
			gWin.unmaximize()
			gWin.isMaximized = False
		else:
			gWin.maximize()
			gWin.isMaximized = True


class WinConButtonClose(WinConButton):
	_name = "close"
	desc = _("Close Window")
	imageName = "button-close.png"
	imageNameFocus = "button-close-focus.png"

	def onClicked(self, gWin, gevent):
		gWin.emit("delete-event", gdk.Event())


class WinConButtonSep(WinConButton):
	_name = "sep"
	desc = _("Seperator")
	expand = True

	def build(self):
		pass

	def setFocus(self, focus):
		pass

	def setInactive(self):
		pass

## Stick
## Above
## Below


@registerSignals
class CalObj(gtk.HBox, CustomizableCalBox):
	_name = "winContronller"
	desc = _("Window Controller")
	buttonClassList = (
		WinConButtonMin,
		WinConButtonMax,
		WinConButtonClose,
		WinConButtonSep,
	)
	buttonClassDict = {
		cls._name: cls
		for cls in buttonClassList
	}

	def __init__(self):
		gtk.HBox.__init__(self, spacing=ui.winControllerSpacing)
		self.set_property("height-request", 15)
		self.set_direction(gtk.TextDirection.LTR)## FIXME
		self.initVars()
		###########
		for bname, enable in ui.winControllerButtons:
			button = self.buttonClassDict[bname](self)
			button.enable = enable
			self.appendItem(button)
		self.set_property("can-focus", True)
		##################
		self.gWin = ui.mainWin
		if self.gWin:
			self.gWin.winCon = self ## dirty FIXME
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
