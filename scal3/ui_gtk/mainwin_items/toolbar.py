#!/usr/bin/env python3
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk import gtk_ud as ud

# from scal3.ui_gtk.toolbar import ToolbarItem, CustomizableToolbar
from scal3.ui_gtk.toolbox import (
	ToolBoxItem as ToolbarItem,
	CustomizableToolBox as CustomizableToolbar,
)

class MainMenuToolbarItem(ToolbarItem):
	def __init__(self):
		ToolbarItem.__init__(
			self,
			name="mainMenu",
			iconName="start-here",
			imageName="starcal.svg",
			onClick=None,
			desc=_("Main Menu"),
			continuousClick=False,
			onPress=self.onButtonPress,
			#iconSize=30,  # for svg
			enable=False,
		)
		#self.setIconFile("starcal.svg")

	def getMenuPos(self):
		wcal = self.get_parent().get_parent()
		w = self.get_allocation().width
		h = self.get_allocation().height
		x0, y0 = self.translate_coordinates(wcal, 0, 0)
		return (
			x0 + w // 2,
			y0 + h // 2,
		)

	def onButtonPress(self, widget=None, gevent=None):
		toolbar = self.get_parent()
		x, y = self.translate_coordinates(
			toolbar.get_parent(),
			gevent.x,
			gevent.y,
		)
		toolbar.get_parent().emit(
			"popup-main-menu",
			0,
			x,
			y,
		)


@registerSignals
class CalObj(CustomizableToolbar):
	signals = CustomizableToolbar.signals + [
		("popup-main-menu", [int, int, int]),
	]

	defaultItems = [
		MainMenuToolbarItem(),
		ToolbarItem(
			name="today",
			iconName="gtk-home",
			imageName="go-home.svg",
			onClick="goToday",
			desc="Select Today",
			shortDesc="Today",
			continuousClick=False,
		),
		ToolbarItem(
			name="date",
			iconName="gtk-index",
			imageName="select-date.svg",
			onClick="selectDateShow",
			desc="Select Date...",
			shortDesc="Date",
			continuousClick=False,
		),
		ToolbarItem(
			name="customize",
			iconName="gtk-edit",
			imageName="document-edit.svg",
			onClick="customizeShow",
			continuousClick=False,
		),
		ToolbarItem(
			name="preferences",
			iconName="gtk-preferences",
			imageName="preferences-system.svg",
			onClick="prefShow",
			continuousClick=False,
		),
		ToolbarItem(
			name="add",
			iconName="gtk-add",
			imageName="list-add.svg",
			onClick="eventManShow",
			desc="Event Manager",
			shortDesc="Event",
			continuousClick=False,
		),
		ToolbarItem(
			name="search",
			iconName="gtk-find",
			imageName="",
			onClick="eventSearchShow",
			desc="Search Events",
			shortDesc="Search",
			continuousClick=False,
		),
		ToolbarItem(
			name="export",
			iconName="gtk-convert",
			imageName="export-to-html.svg",
			onClick="onExportClick",
			desc=_("Export to {format}").format(format="HTML"),
			shortDesc="Export",
			continuousClick=False,
		),
		ToolbarItem(
			name="about",
			iconName="gtk-about",
			imageName="dialog-information.svg",
			onClick="aboutShow",
			desc=_("About ") + core.APP_DESC,
			shortDesc="About",
			continuousClick=False,
		),
		ToolbarItem(
			name="quit",
			iconName="gtk-quit",
			imageName="application-exit.svg",
			onClick="quit",
			continuousClick=False,
		),
	]
	defaultItemsDict = {
		item._name: item
		for item in defaultItems
	}

	def __init__(self):
		CustomizableToolbar.__init__(
			self,
			ui.mainWin,
			vertical=False,
			continuousClick=False,
		)
		if not ud.mainToolbarData["items"]:
			ud.mainToolbarData["items"] = [
				(item._name, True) for item in self.defaultItems
			]
		else:
			currentNames = {item[0] for item in ud.mainToolbarData["items"]}
			for name, item in self.defaultItemsDict.items():
				if name not in currentNames:
					ud.mainToolbarData["items"].append((name, False))

		self.setData(ud.mainToolbarData)
		if ui.mainWin:
			self.connect("button-press-event", ui.mainWin.childButtonPress)
			self.connect("popup-main-menu", ui.mainWin.menuMainPopup)

	def updateVars(self):
		CustomizableToolbar.updateVars(self)
		ud.mainToolbarData = self.getData()
