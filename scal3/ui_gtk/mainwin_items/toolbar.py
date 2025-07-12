from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.app_info import APP_DESC
from scal3.locale_man import tr as _
from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.gtk_ud import commonSignals
from scal3.ui_gtk.signals import SignalHandlerBase, registerSignals
from scal3.ui_gtk.toolbox import CustomizableToolBox, ToolBoxItem

if TYPE_CHECKING:
	from scal3.ui_gtk.starcal_types import MainWinType

__all__ = ["CalObj"]


@registerSignals
class MainMenuToolBoxItemSignalHandler(SignalHandlerBase):
	signals = commonSignals + [
		("popup-main-menu", [int, int]),
	]


class MainMenuToolBoxItem(ToolBoxItem):
	Sig = MainMenuToolBoxItemSignalHandler

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

	def onButtonPress(
		self,
		_widget: gtk.Widget,
		gevent: gdk.EventButton,
	) -> None:
		self.s.emit(
			"popup-main-menu",
			gevent.x,
			gevent.y,
		)


class CalObj(CustomizableToolBox):
	itemHaveOptions = False
	desc = _("Toolbar (Horizontal)")

	def __init__(self, win: MainWinType) -> None:
		CustomizableToolBox.__init__(
			self,
			win,
			continuousClick=False,
		)
		self.win = win
		self.mainMenuItem = MainMenuToolBoxItem()
		self.defaultItems = [
			self.mainMenuItem,
			ToolBoxItem(
				name="today",
				iconName="gtk-home",
				imageName="go-home.svg",
				onClick=win.goToday,
				desc="Select Today",
				shortDesc="Today",
				continuousClick=False,
			),
			ToolBoxItem(
				name="date",
				iconName="gtk-index",
				imageName="select-date.svg",
				onClick=win.selectDateShow,
				desc="Select Date...",
				shortDesc="Date",
				continuousClick=False,
			),
			ToolBoxItem(
				name="customize",
				iconName="gtk-edit",
				imageName="document-edit.svg",
				onClick=win.customizeShow,
				continuousClick=False,
			),
			ToolBoxItem(
				name="preferences",
				iconName="gtk-preferences",
				imageName="preferences-system.svg",
				onClick=win.prefShow,
				continuousClick=False,
			),
			ToolBoxItem(
				name="add",
				iconName="gtk-add",
				imageName="list-add.svg",
				onClick=win.eventManShow,
				desc="Event Manager",
				shortDesc="Event",
				continuousClick=False,
			),
			ToolBoxItem(
				name="search",
				iconName="gtk-find",
				imageName="system-search.svg",
				onClick=win.eventSearchShow,
				desc="Search Events",
				shortDesc="Search",
				continuousClick=False,
			),
			ToolBoxItem(
				name="export",
				iconName="gtk-convert",
				imageName="export-to-html.svg",
				onClick=win.onExportClick,
				desc=_("Export to {format}").format(format="HTML"),
				shortDesc="Export",
				continuousClick=False,
			),
			ToolBoxItem(
				name="about",
				iconName="gtk-about",
				imageName="dialog-information.svg",
				onClick=win.aboutShow,
				desc=_("About ") + APP_DESC,
				shortDesc="About",
				continuousClick=False,
			),
			ToolBoxItem(
				name="quit",
				iconName="gtk-quit",
				imageName="application-exit.svg",
				onClick=win.onQuitClick,
				continuousClick=False,
			),
		]
		self.defaultItemsDict = {item.objName: item for item in self.defaultItems}

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
			self.mainMenuItem.s.connect(
				"popup-main-menu",
				win.menuMainPopup,
				self.mainMenuItem,
			)

	def updateVars(self) -> None:
		CustomizableToolBox.updateVars(self)
		ud.mainToolbarData = self.getDict()
