from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import core
from scal3.locale_man import tr as _
from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.gtk_ud import commonSignals
from scal3.ui_gtk.signals import SignalHandlerBase, registerSignals
from scal3.ui_gtk.toolbox import CustomizableToolBox, ToolBoxItem

if TYPE_CHECKING:
	from scal3.ui_gtk.starcal import MainWin

__all__ = ["CalObj"]


class MainMenuToolBoxItem(ToolBoxItem):
	def __init__(self) -> None:
		ToolBoxItem.__init__(
			self,
			name="mainMenu",
			iconName="start-here",
			imageName="starcal.svg",
			desc=_("Main Menu"),
			continuousClick=False,
			onPress=self.onButtonPress,
			# iconSize=30,  # for svg
			enable=False,
		)
		# self.setIconFile("starcal.svg")

	def getMenuPos(self) -> tuple[int, int]:
		parent = self.w.get_parent()
		assert parent is not None
		wcal = parent.get_parent()
		assert wcal is not None
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		coords = self.w.translate_coordinates(wcal, 0, 0)
		assert coords is not None
		x0, y0 = coords
		return (
			x0 + w // 2,
			y0 + h // 2,
		)

	def onButtonPress(
		self,
		_widget: gtk.Widget,
		gevent: gdk.EventButton,
	) -> None:
		toolbar = self.w.get_parent()
		assert toolbar is not None
		wcal = toolbar.get_parent()
		assert wcal is not None
		coords = self.w.translate_coordinates(
			wcal,
			int(gevent.x),
			int(gevent.y),
		)
		assert coords is not None
		x, y = coords
		wcal.emit(
			"popup-main-menu",
			x,
			y,
		)


@registerSignals
class SignalHandler(SignalHandlerBase):
	signals = commonSignals + [
		("popup-main-menu", [int, int]),
	]


class CalObj(CustomizableToolBox):
	Sig = SignalHandler
	itemHaveOptions = False
	desc = _("Toolbar (Horizontal)")

	defaultItems = [
		MainMenuToolBoxItem(),
		ToolBoxItem(
			name="today",
			iconName="gtk-home",
			imageName="go-home.svg",
			onClick="goToday",
			desc="Select Today",
			shortDesc="Today",
			continuousClick=False,
		),
		ToolBoxItem(
			name="date",
			iconName="gtk-index",
			imageName="select-date.svg",
			onClick="selectDateShow",
			desc="Select Date...",
			shortDesc="Date",
			continuousClick=False,
		),
		ToolBoxItem(
			name="customize",
			iconName="gtk-edit",
			imageName="document-edit.svg",
			onClick="customizeShow",
			continuousClick=False,
		),
		ToolBoxItem(
			name="preferences",
			iconName="gtk-preferences",
			imageName="preferences-system.svg",
			onClick="prefShow",
			continuousClick=False,
		),
		ToolBoxItem(
			name="add",
			iconName="gtk-add",
			imageName="list-add.svg",
			onClick="eventManShow",
			desc="Event Manager",
			shortDesc="Event",
			continuousClick=False,
		),
		ToolBoxItem(
			name="search",
			iconName="gtk-find",
			imageName="system-search.svg",
			onClick="eventSearchShow",
			desc="Search Events",
			shortDesc="Search",
			continuousClick=False,
		),
		ToolBoxItem(
			name="export",
			iconName="gtk-convert",
			imageName="export-to-html.svg",
			onClick="onExportClick",
			desc=_("Export to {format}").format(format="HTML"),
			shortDesc="Export",
			continuousClick=False,
		),
		ToolBoxItem(
			name="about",
			iconName="gtk-about",
			imageName="dialog-information.svg",
			onClick="aboutShow",
			desc=_("About ") + core.APP_DESC,
			shortDesc="About",
			continuousClick=False,
		),
		ToolBoxItem(
			name="quit",
			iconName="gtk-quit",
			imageName="application-exit.svg",
			onClick="quit",
			continuousClick=False,
		),
	]
	defaultItemsDict = {item.objName: item for item in defaultItems}

	def __init__(self, win: MainWin) -> None:
		CustomizableToolBox.__init__(
			self,
			win,
			continuousClick=False,
		)
		self.win = win
		if not ud.mainToolbarData["items"]:
			ud.mainToolbarData["items"] = [
				(item.objName, True) for item in self.defaultItems
			]
		else:
			currentNames = {item[0] for item in ud.mainToolbarData["items"]}
			for name in self.defaultItemsDict:
				if name not in currentNames:
					ud.mainToolbarData["items"].append((name, False))

		self.setDict(ud.mainToolbarData)
		if win:
			self.w.connect("button-press-event", win.childButtonPress)
			self.s.connect("popup-main-menu", win.menuMainPopup)

	def updateVars(self) -> None:
		CustomizableToolBox.updateVars(self)
		ud.mainToolbarData = self.getDict()
