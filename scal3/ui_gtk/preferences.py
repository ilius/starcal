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

from time import localtime

import sys
import os
from os.path import join

from scal3.path import *
from scal3.cal_types import calTypes
from scal3 import core
from scal3 import locale_man
from scal3.locale_man import langSh
from scal3.locale_man import tr as _
from scal3 import plugin_man
from scal3 import ui
from scal3.ui_gtk import *
from scal3.ui_gtk.utils import *
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.pref_utils import *
from scal3.ui_gtk.pref_utils_extra import *
from scal3.ui_gtk.log_pref import LogLevelPrefItem
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	StaticToolBox,
)


class PreferencesPluginsToolbar(StaticToolBox):
	def __init__(self, parent):
		StaticToolBox.__init__(
			self,
			parent,
			vertical=True,
			buttonBorder=0,
			buttonPadding=0,
		)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		self.append(ToolBoxItem(
			name="goto-top",
			imageName="go-top.svg",
			onClick="plugTreeviewTop",
			desc=_("Move to top"),
			continuousClick=False,
		))
		self.append(ToolBoxItem(
			name="go-up",
			imageName="go-up.svg",
			onClick="plugTreeviewUp",
			desc=_("Move up"),
			continuousClick=False,
		))
		self.append(ToolBoxItem(
			name="go-down",
			imageName="go-down.svg",
			onClick="plugTreeviewDown",
			desc=_("Move down"),
			continuousClick=False,
		))
		self.append(ToolBoxItem(
			name="goto-bottom",
			imageName="go-bottom.svg",
			onClick="plugTreeviewBottom",
			desc=_("Move to bottom"),
			continuousClick=False,
		))
		self.buttonAdd = self.append(ToolBoxItem(
			name="add",
			imageName="list-add.svg",
			onClick="onPlugAddClick",
			desc=_("Add"),
			continuousClick=False,
		))
		self.buttonAdd.set_sensitive(False)
		self.append(ToolBoxItem(
			name="delete",
			imageName="edit-delete.svg",
			onClick="onPlugDeleteClick",
			desc=_("Delete"),
			continuousClick=False,
		))

	def setCanAdd(self, canAdd: bool):
		self.buttonAdd.set_sensitive(canAdd)


class PreferencesWindow(gtk.Window):
	def __init__(self, **kwargs):
		from math import ceil
		##
		gtk.Window.__init__(self, **kwargs)
		self.set_title(_("Preferences"))
		self.set_position(gtk.WindowPosition.CENTER)
		self.connect("delete-event", self.onDelete)
		self.connect("key-press-event", self.onKeyPress)
		# self.set_has_separator(False)
		# self.set_skip_taskbar_hint(True)
		###
		self.vbox = VBox()
		self.add(self.vbox)
		###
		self.buttonbox = MyHButtonBox()
		self.buttonbox.add_button(
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			onClick=self.cancel,
		)
		self.buttonbox.add_button(
			imageName="dialog-ok-apply.svg",
			label=_("_Apply"),
			onClick=self.apply,
		)
		okB = self.buttonbox.add_button(
			imageName="dialog-ok.svg",
			label=_("_OK"),
			onClick=self.ok,
			tooltip=_("Apply and Close"),
		)
		# okB.grab_default()  # FIXME
		# okB.grab_focus()  # FIXME
		##############################################
		self.loggerPrefItem = None
		self.localePrefItems = []
		self.corePrefItems = []
		self.uiPrefItems = []
		self.gtkPrefItems = []  # FIXME
		#####
		self.prefPages = []
		##############################################
		stack = MyStack(
			iconSize=ui.stackIconSize,
		)
		stack.setTitleFontSize("large")
		stack.setTitleCentered(True)
		stack.setupWindowTitle(self, _("Preferences"), False)
		self.stack = stack
		# ############### Page 0 (Language and Calendar Types) ################
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "lang_calTypes"
		page.pageTitle = _("Language and Calendar Types")
		page.pageLabel = _("_Language and Calendar Types")
		page.pageIcon = "preferences-desktop-locale.png"
		self.prefPages.append(page)
		##########################
		hbox = HBox(spacing=3)
		pack(hbox, gtk.Label(label=_("Language")))
		itemLang = LangPrefItem()
		self.localePrefItems.append(itemLang)
		###
		pack(hbox, itemLang.getWidget())
		if langSh != "en":
			pack(hbox, gtk.Label(label="Language"))
		pack(vbox, hbox)
		##########################
		hbox = HBox()
		frame = gtk.Frame()
		frame.set_label(_("Calendar Types"))
		itemCals = AICalsPrefItem()
		self.corePrefItems.append(itemCals)
		itemCalsWidget = itemCals.getWidget()
		itemCalsWidget.set_border_width(10)
		frame.add(itemCalsWidget)
		pack(hbox, frame, 1, 1)
		hbox.set_border_width(5)
		frame.set_border_width(0)
		pack(vbox, hbox, 1, 1)
		# ############################## Page 1 (General) #####################
		vbox = VBox()
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "general"
		page.pageTitle = _("General")
		page.pageLabel = _("_General")
		page.pageIcon = "preferences-system.svg"
		self.prefPages.append(page)
		##########################
		hbox = HBox(spacing=3)
		item = CheckStartupPrefItem()
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		########################
		item = CheckPrefItem(
			ui,
			"showMain",
			_("Open main window on start"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		########################
		item = CheckPrefItem(
			ui,
			"showDesktopWidget",
			_("Open desktop widget on start"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		##########################
		item = CheckPrefItem(
			ui,
			"winTaskbar",
			_("Window in Taskbar"),
		)
		self.uiPrefItems.append(item)
		hbox = HBox(spacing=3)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		###########
		pack(vbox, hbox)
		##########################
		try:
			import scal3.ui_gtk.starcal_appindicator
		except (ImportError, ValueError):
			pass
		else:
			item = CheckPrefItem(
				ui,
				"useAppIndicator",
				_("Use AppIndicator"),
			)
			self.uiPrefItems.append(item)
			hbox = HBox(spacing=3)
			pack(hbox, item.getWidget())
			pack(hbox, gtk.Label(), 1, 1)
			pack(vbox, hbox)
		##########################
		# hbox = HBox(spacing=3)
		# pack(hbox, gtk.Label(label=_("Show Digital Clock:")))
		# pack(hbox, gtk.Label(), 1, 1)
		# #item = CheckPrefItem(
		# #	ui,
		# #	"showDigClockTb",
		# #	_("On Toolbar"),
		# #)  # FIXME
		# #self.uiPrefItems.append(item)
		# #pack(hbox, item.getWidget())
		# pack(hbox, gtk.Label(), 1, 1)
		# item = CheckPrefItem(
		# 	ui,
		# 	"showDigClockTr",
		# 	_("On Status Icon"),
		# 	"Notification Area",
		# )
		# self.uiPrefItems.append(item)
		# pack(hbox, item.getWidget())
		# pack(hbox, gtk.Label(), 1, 1)
		# pack(vbox, hbox)
		# ############################## Page 2 (Appearance) ##################
		vbox = VBox(spacing=0)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "appearance"
		page.pageTitle = _("Appearance")
		# A is for Apply, P is for Plugins, R is for Regional,
		# C is for Cancel, only "n" is left!
		page.pageLabel = _("Appeara_nce")
		page.pageIcon = "preferences-desktop-theme.png"
		self.prefPages.append(page)
		########
		buttonPadding = 7
		padding = 5
		###
		hbox = HBox(spacing=2)
		###
		customCheckItem = CheckPrefItem(
			ui,
			"fontCustomEnable",
			_("Application Font"),
		)
		self.uiPrefItems.append(customCheckItem)
		pack(hbox, customCheckItem.getWidget())
		###
		customItem = FontPrefItem(ui, "fontCustom", dragAndDrop=True)
		self.uiPrefItems.append(customItem)
		pack(hbox, customItem.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		customCheckItem.syncSensitive(customItem.getWidget())
		pack(vbox, hbox, padding=padding)
		###########################
		item = CheckPrefItem(
			ui,
			"buttonIconEnable",
			_("Show icons in buttons"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		###########################
		item = CheckPrefItem(
			ui,
			"useSystemIcons",
			_("Use System Icons"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		# ######################### Theme #####################
		pageHBox = HBox()
		pageHBox.set_border_width(10)
		spacing = 3
		###
		pageVBox = VBox()
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		###
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Background")))
		item = ColorPrefItem(ui, "bgColor", True)
		self.uiPrefItems.append(item)
		self.colorbBg = item.getWidget()  # FIXME
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		###
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Border")))
		item = ColorPrefItem(ui, "borderColor", True)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		###
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Cursor")))
		item = ColorPrefItem(ui, "cursorOutColor", False)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		###
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Cursor BG")))
		item = ColorPrefItem(ui, "cursorBgColor", True)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		###
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Today")))
		item = ColorPrefItem(ui, "todayCellColor", True)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		######
		pack(pageHBox, pageVBox, 1, 1)
		pack(pageHBox, newHSep(), 0, 0)
		pageVBox = VBox()
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		######
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Normal Text")))
		item = ColorPrefItem(ui, "textColor", False)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		###
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Holidays Font")))
		item = ColorPrefItem(ui, "holidayColor", False)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		###
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Inactive Day Font")))
		item = ColorPrefItem(ui, "inactiveColor", True)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		####
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Border Font")))
		item = ColorPrefItem(ui, "borderTextColor", False)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		####
		pack(pageHBox, pageVBox, 1, 1, padding=5)
		####
		page = StackPage()
		page.pageParent = "appearance"
		page.pageWidget = pageHBox
		page.pageName = "colors"
		page.pageTitle = _("Colors") + " - " + _("Appearance")
		page.pageLabel = _("Colors")
		page.pageIcon = "preferences-desktop-color.svg"
		page.pageExpand = False
		self.prefPages.append(page)
		#####
		appearanceSubPages = [page]
		###################
		pageVBox = VBox(spacing=10)
		pageVBox.set_border_width(10)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		hbox = HBox(spacing=1)
		label = newAlignLabel(sgroup=sgroup, label=_("Normal Days"))
		pack(hbox, label)
		item = ImageFileChooserPrefItem(
			ui,
			"statusIconImage",
			title=_("Select Icon"),
			currentFolder=join(sourceDir, "status-icons"),
			defaultVarName="statusIconImageDefault",
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		####
		hbox = HBox(spacing=1)
		label = newAlignLabel(sgroup=sgroup, label=_("Holidays"))
		pack(hbox, label)
		item = ImageFileChooserPrefItem(
			ui,
			"statusIconImageHoli",
			title=_("Select Icon"),
			currentFolder=join(sourceDir, "status-icons"),
			defaultVarName="statusIconImageHoliDefault",
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		####
		hbox = HBox(spacing=1)
		checkItem = CheckPrefItem(
			ui,
			"statusIconFontFamilyEnable",
			label=_("Change font family to"),
			# tooltip=_("In SVG files"),
		)
		self.uiPrefItems.append(checkItem)
		# sgroup.add_widget(checkItem.getWidget())
		pack(hbox, checkItem.getWidget())
		item = FontFamilyPrefItem(
			ui,
			"statusIconFontFamily",
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		####
		hbox = HBox(spacing=1)
		item = CheckColorPrefItem(
			CheckPrefItem(
				ui,
				"statusIconHolidayFontColorEnable",
				label=_("Holiday font color"),
			),
			ColorPrefItem(
				ui,
				"statusIconHolidayFontColor",
			),
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		####
		hbox = HBox(spacing=1)
		checkItem = CheckPrefItem(
			ui,
			"statusIconFixedSizeEnable",
			label=_("Fixed Size"),
			# tooltip=_(""),
		)
		self.uiPrefItems.append(checkItem)
		# sgroup.add_widget(checkItem.getWidget())
		pack(hbox, checkItem.getWidget())
		pack(hbox, gtk.Label(label=" "))
		item = WidthHeightPrefItem(
			ui,
			"statusIconFixedSizeWH",
			999,
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		########
		checkItem.syncSensitive(item.getWidget(), reverse=False)
		####
		page = StackPage()
		page.pageParent = "appearance"
		page.pageWidget = pageVBox
		page.pageName = "statusIcon"
		page.pageTitle = _("Status Icon") + " - " + _("Appearance")
		page.pageLabel = _("Status Icon")
		page.pageIcon = ""
		self.prefPages.append(page)
		#####
		appearanceSubPages.append(page)
		###############
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		grid.set_row_spacing(buttonPadding)
		for index, page in enumerate(appearanceSubPages):
			grid.attach(self.newWideButton(page), 0, index, 1, 1)
		grid.show_all()
		pack(vbox, grid, padding=padding)
		# ############################## Page 3 (Regional) ###################
		vbox = VBox()
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "regional"
		page.pageTitle = _("Regional")
		page.pageLabel = _("_Regional")
		page.pageIcon = "preferences-desktop-locale.png"
		self.prefPages.append(page)
		######
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		buttonPadding = 3
		######
		hbox = HBox(spacing=10)
		label = gtk.Label(label=_("Date Format"))
		pack(hbox, label)
		sgroup.add_widget(label)
		# pack(hbox, gtk.Label(), 1, 1)
		item = ComboEntryTextPrefItem(ud, "dateFormat", (
			"%Y/%m/%d",
			"%Y-%m-%d",
			"%y/%m/%d",
			"%y-%m-%d",
			"%OY/%Om/%Od",
			"%OY-%Om-%Od",
			"%m/%d",
			"%m/%d/%Y",
		))
		self.gtkPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		################################
		hbox = HBox(spacing=3)
		item = CheckPrefItem(
			locale_man,
			"enableNumLocale",
			_("Numbers Localization"),
		)
		self.localePrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox, padding=10)
		################################
		pageVBox = VBox(spacing=5)
		####
		hbox = HBox(spacing=3)
		pack(hbox, gtk.Label(label=_("First day of week")))
		# item = ComboTextPrefItem(  # FIXME
		self.comboFirstWD = gtk.ComboBoxText()
		for item in core.weekDayName:
			self.comboFirstWD.append_text(item)
		self.comboFirstWD.append_text(_("Automatic"))
		self.comboFirstWD.connect("changed", self.comboFirstWDChanged)
		pack(hbox, self.comboFirstWD)
		pack(pageVBox, hbox)
		#########
		hbox = HBox(spacing=3)
		pack(hbox, gtk.Label(label=_("First week of year containts")))
		combo = gtk.ComboBoxText()
		texts = [
			_("First {weekDay} of year").format(weekDay=name)
			for name in core.weekDayName
		] + [
			_("First day of year"),
		]
		texts[4] += " (ISO 8601)"  # FIXME
		for text in texts:
			combo.append_text(text)
		# combo.append_text(_("Automatic"))## (as Locale)  # FIXME
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox, padding=5)
		self.comboWeekYear = combo
		#########
		frame = gtk.Frame()
		frame.set_border_width(10)
		frame.set_label(_("Holidays"))
		item = WeekDayCheckListPrefItem(
			core,
			"holidayWeekDays",
			abbreviateNames=False,
			twoRows=True,
		)
		self.corePrefItems.append(item)
		self.holiWDItem = item  # Holiday Week Days Item
		itemWidget = item.getWidget()
		itemWidget.set_border_width(10)
		frame.add(itemWidget)
		pack(pageVBox, frame)
		############
		page = StackPage()
		page.pageParent = "regional"
		page.pageWidget = pageVBox
		page.pageName = "regional_week"
		page.pageTitle = _("Week") + " - " + _("Regional")
		page.pageLabel = _("Week-related Settings")
		page.pageIcon = ""
		page.pageExpand = False
		self.prefPages.append(page)
		#####
		regionalSubPages = [page]
		##################################################
		options = []
		for mod in calTypes:
			if not mod.options:
				continue
			pageVBox = VBox(spacing=10)
			page = StackPage()
			page.pageParent = "regional"
			page.pageWidget = pageVBox
			page.pageName = "regional_" + mod.name
			page.pageTitle = (
				_("{calType} Calendar").format(calType=_(mod.desc)) +
				" - " +
				_("Regional")
			)
			page.pageLabel = _("{calType} Calendar").format(
				calType=_(mod.desc),
			)
			page.pageExpand = False
			self.prefPages.append(page)
			#####
			regionalSubPages.append(page)
			for opt in mod.options:
				if opt[0] == "button":
					try:
						optl = ModuleOptionButton(opt[1:])
					except Exception:
						log.exception("")
						continue
				else:
					optl = ModuleOptionItem(mod, opt)
				options.append(optl)
				pack(pageVBox, optl.getWidget())
			#####
		#####
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		grid.set_row_spacing(4)
		for index, page in enumerate(regionalSubPages):
			grid.attach(self.newWideButton(page), 0, index, 1, 1)
		grid.show_all()
		pack(vbox, grid)
		###
		self.moduleOptions = options
		# ############################## Page 4 (Advanced) ###################
		vbox = VBox(spacing=10)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "advanced"
		page.pageTitle = _("Advanced")
		page.pageLabel = _("A_dvanced")
		page.pageIcon = "applications-system.svg"
		self.prefPages.append(page)
		######
		item = LogLevelPrefItem()
		self.loggerPrefItem = item
		pack(vbox, item.getWidget())
		######
		hbox = HBox(spacing=5)
		# pack(hbox, gtk.Label(), 1, 1)
		label = gtk.Label(label=_("Event Time Format"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = ComboEntryTextPrefItem(ui, "eventDayViewTimeFormat", (
			"HM$",
			"HMS",
			"hMS",
			"hm$",
			"hms",
			"HM",
			"hm",
			"hM",
		))
		item.addDescriptionColumn({
			"HM$": f"05:07:09 {_('or')} 05:07",
			"HMS": f"05:07:09 {_('or')} 05:07:00",
			"hMS": f"05:07:09 {_('or')} 5:07:00",
			"hm$": f"5:7:9 {_('or')} 5:7",
			"hms": f"5:7:9 {_('or')} 5:7:0",
			"HM": f"05:07",
			"hm": f"5:7",
			"hM": f"5:07",
		})
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		######
		hbox = HBox(spacing=5)
		# pack(hbox, gtk.Label(), 1, 1)
		label = gtk.Label(label=_("Digital Clock Format"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = ComboEntryTextPrefItem(ud, "clockFormat", (
			"%T",
			"%X",
			"%Y/%m/%d - %T",
			"%OY/%Om/%Od - %X",
			"<i>%Y/%m/%d</i> - %T",
			"<b>%T</b>",
			"<b>%X</b>",
			"%H:%M",
			"<b>%H:%M</b>",
			"<span size=\"smaller\">%OY/%Om/%Od</span>,%X"
			"%OY/%Om/%Od,<span color=\"#ff0000\">%X</span>",
			"<span font=\"bold\">%X</span>",
			"%OH:%OM",
			"<b>%OH:%OM</b>",
		))
		self.gtkPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		######
		hbox = HBox(spacing=5)
		label = gtk.Label(label=_("Days maximum cache size"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = SpinPrefItem(ui, "maxDayCacheSize", 100, 9999, digits=0, step=10)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(vbox, hbox)
		######
		hbox = HBox(spacing=5)
		label = gtk.Label(label=_("Horizontal offset for day right-click menu"))
		pack(hbox, label)
		item = SpinPrefItem(ui, "cellMenuXOffset", 0, 999, digits=0, step=1)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(vbox, hbox)
		######
		hbox = HBox(spacing=5)
		button = labelImageButton(
			label=_("Clear Image Cache"),
			# TODO: _("Clear Image Cache ({size})").format(size=""),
			imageName="sweep.svg",
		)
		button.connect("clicked", self.onClearImageCacheClick)
		pack(hbox, button)
		pack(vbox, hbox)
		# ############################## Page 5 (Plugins) ####################
		vbox = VBox()
		page = StackPage()
		vbox.set_border_width(5)
		page.pageWidget = vbox
		page.pageName = "plugins"
		page.pageTitle = _("Plugins")
		page.pageLabel = _("_Plugins")
		page.pageIcon = "preferences-plugin.svg"
		self.prefPages.append(page)
		#####
		# pluginsTextStatusIcon:
		hbox = HBox()
		item = CheckPrefItem(
			ui,
			"pluginsTextStatusIcon",
			_("Show in Status Icon (for today)"),
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox)
		#####
		treev = gtk.TreeView()
		treev.set_headers_clickable(True)
		treeModel = gtk.ListStore(
			int,  # index
			bool,  # enable
			bool,  # show_date
			str,  # title
		)
		treev.set_model(treeModel)
		treev.enable_model_drag_source(
			gdk.ModifierType.BUTTON1_MASK,
			[
				("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.enable_model_drag_dest(
			[
				("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.connect("drag_data_received", self.plugTreevDragReceived)
		treev.get_selection().connect("changed", self.plugTreevCursorChanged)
		treev.connect("row-activated", self.plugTreevRActivate)
		treev.connect("button-press-event", self.plugTreevButtonPress)
		###
		# treev.drag_source_add_text_targets()
		# treev.drag_source_add_uri_targets()
		# treev.drag_source_unset()
		###
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(
			gtk.PolicyType.AUTOMATIC,
			gtk.PolicyType.AUTOMATIC,
		)
		######
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.plugTreeviewCellToggled)
		titleLabel = gtk.Label(
			label="<span size='small'>" + _("Enable") + "</span>",
			use_markup=True,
		)
		titleLabel.show()
		col = gtk.TreeViewColumn(cell_renderer=cell)
		col.set_widget(titleLabel)
		col.add_attribute(cell, "active", 1)
		# cell.set_active(False)
		col.set_resizable(True)
		col.set_property("expand", False)
		treev.append_column(col)
		######
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.plugTreeviewCellToggled2)
		titleLabel = gtk.Label(
			label="<span size='xx-small'>" + _("Show\nDate") + "</span>",
			use_markup=True,
		)
		titleLabel.show()
		col = gtk.TreeViewColumn(cell_renderer=cell)
		col.set_widget(titleLabel)
		col.add_attribute(cell, "active", 2)
		# cell.set_active(False)
		col.set_resizable(True)
		col.set_property("expand", False)
		treev.append_column(col)
		######
		# cell = gtk.CellRendererText()
		# col = gtk.TreeViewColumn(title=_("File Name"), cell_renderer=cell, text=2)
		# col.set_resizable(True)
		# treev.append_column(col)
		# treev.set_search_column(1)
		######
		cell = gtk.CellRendererText()
		# cell.set_property("wrap-mode", gtk.WrapMode.WORD)
		# cell.set_property("editable", True)
		# cell.set_property("wrap-width", 200)
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=3)
		# treev.connect("draw", self.plugTreevExpose)
		# self.plugTitleCell = cell
		# self.plugTitleCol = col
		# col.set_resizable(True)## No need!
		col.set_property("expand", True)
		treev.append_column(col)
		######
		# for i in xrange(len(core.plugIndex)):
		# 	x = core.plugIndex[i]
		# 	treeModel.append([x[0], x[1], x[2], core.allPlugList[x[0]].title])
		######
		self.plugTreeview = treev
		#######################
		hbox = HBox()
		vboxPlug = VBox()
		pack(vboxPlug, swin, 1, 1)
		pack(hbox, vboxPlug, 1, 1)
		###
		hboxBut = HBox()
		###
		button = labelImageButton(
			label=_("_About Plugin"),
			imageName="dialog-information.svg",
		)
		button.set_sensitive(False)
		button.connect("clicked", self.onPlugAboutClick)
		self.plugButtonAbout = button
		pack(hboxBut, button)
		pack(hboxBut, gtk.Label(), 1, 1)
		###
		button = labelImageButton(
			label=_("C_onfigure Plugin"),
			imageName="preferences-system.svg",
		)
		button.set_sensitive(False)
		button.connect("clicked", self.onPlugConfClick)
		self.plugButtonConf = button
		pack(hboxBut, button)
		pack(hboxBut, gtk.Label(), 1, 1)
		###
		pack(vboxPlug, hboxBut)
		###
		toolbar = PreferencesPluginsToolbar(self)
		pack(hbox, toolbar)
		self.pluginsToolbar = toolbar
		#####
		"""
		vpan = gtk.VPaned()
		vpan.add1(hbox)
		vbox2 = VBox()
		pack(vbox2, gtk.Label(label="Test Label"))
		vpan.add2(vbox2)
		vpan.set_position(100)
		pack(vbox, vpan)
		"""
		pack(vbox, hbox, 1, 1)
		##########################
		d = gtk.Dialog(transient_for=self)
		d.set_transient_for(self)
		# dialog.set_transient_for(parent) makes the window on top of parent
		# and at the center point of parent
		# but if you call dialog.show() or dialog.present(), the parent is
		# still active(clickabel widgets) before closing child "dialog"
		# you may call dialog.run() to realy make it transient for parent
		# d.set_has_separator(False)
		d.connect("delete-event", self.plugAddDialogClose)
		d.set_title(_("Add Plugin"))
		###
		dialog_add_button(
			d,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
			onClick=self.plugAddDialogClose,
		)
		dialog_add_button(
			d,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
			onClick=self.plugAddDialogOK,
		)
		###
		treev = gtk.TreeView()
		treeModel = gtk.ListStore(str)
		treev.set_model(treeModel)
		# treev.enable_model_drag_source(
		# 	gdk.ModifierType.BUTTON1_MASK,
		# 	[("", 0, 0, 0)],
		# 	gdk.DragAction.MOVE,
		# )  # FIXME
		# treev.enable_model_drag_dest(
		# 	[("", 0, 0, 0)],
		# 	gdk.DragAction.MOVE,
		# )  # FIXME
		treev.connect("drag_data_received", self.plugTreevDragReceived)
		treev.connect("row-activated", self.plugAddTreevRActivate)
		####
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=0)
		# col.set_resizable(True)# no need when have only one column!
		treev.append_column(col)
		####
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(d.vbox, swin, 1, 1)
		d.vbox.show_all()
		self.plugAddDialog = d
		self.plugAddTreeview = treev
		self.plugAddTreeModel = treeModel
		#############
		# treev.set_resize_mode(gtk.RESIZE_IMMEDIATE)
		# self.plugAddItems = []
		# ##################################### Page 6 (Accounts)
		vbox = VBox()
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "accounts"
		page.pageTitle = _("Accounts")
		page.pageLabel = _("Accounts")
		page.pageIcon = "applications-development-web.png"
		self.prefPages.append(page)
		#####
		treev = gtk.TreeView()
		treev.set_headers_clickable(True)
		treeModel = gtk.ListStore(int, bool, str)  # id (hidden), enable, title
		treev.set_model(treeModel)
		treev.enable_model_drag_source(
			gdk.ModifierType.BUTTON1_MASK,
			[
				("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.enable_model_drag_dest(
			[
				("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.connect("row-activated", self.accountsTreevRActivate)
		treev.connect("button-press-event", self.accountsTreevButtonPress)
		###
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		######
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.accountsTreeviewCellToggled)
		col = gtk.TreeViewColumn(title=_("Enable"), cell_renderer=cell)
		col.add_attribute(cell, "active", 1)
		# cell.set_active(False)
		col.set_resizable(True)
		col.set_property("expand", False)
		treev.append_column(col)
		######
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=2)
		col.set_property("expand", True)
		treev.append_column(col)
		######
		self.accountsTreeview = treev
		self.accountsTreeModel = treeModel
		#######################
		hbox = HBox()
		vboxPlug = VBox()
		pack(vboxPlug, swin, 1, 1)
		pack(hbox, vboxPlug, 1, 1)
		#####
		toolbar = StaticToolBox(self, vertical=True)
		#####
		toolbar.append(ToolBoxItem(
			name="register",
			imageName="starcal.svg",
			onClick="onAccountsRegisterClick",
			desc=_("Register at StarCalendar.net"),
			continuousClick=False,
		))
		######
		toolbar.append(ToolBoxItem(
			name="add",
			imageName="list-add.svg",
			onClick="onAccountsAddClick",
			desc=_("Add"),
			continuousClick=False,
		))
		######
		toolbar.append(ToolBoxItem(
			name="edit",
			imageName="document-edit.svg",
			onClick="onAccountsEditClick",
			desc=_("Edit"),
			continuousClick=False,
		))
		######
		toolbar.append(ToolBoxItem(
			name="delete",
			imageName="edit-delete.svg",
			onClick="onAccountsDeleteClick",
			desc=_("Delete"),
			continuousClick=False,
		))
		######
		toolbar.append(ToolBoxItem(
			name="moveUp",
			imageName="go-up.svg",
			onClick="onAccountsUpClick",
			desc=_("Move up"),
			continuousClick=False,
		))
		######
		toolbar.append(ToolBoxItem(
			name="moveDown",
			imageName="go-down.svg",
			onClick="onAccountsDownClick",
			desc=_("Move down"),
			continuousClick=False,
		))
		###########
		pack(hbox, toolbar)
		pack(vbox, hbox, 1, 1)
		####################################################################
		rootPageName = "preferences"
		###
		mainPages = []
		for page in self.prefPages:
			if page.pageParent:
				continue
			page.pageParent = rootPageName
			mainPages.append(page)
		####
		colN = 2
		####
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		grid.set_row_spacing(15)
		grid.set_column_spacing(15)
		grid.set_border_width(20)
		####
		page = mainPages.pop(0)
		button = self.newWideButton(page)
		grid.attach(button, 0, 0, colN, 1)
		self.defaultWidget = button
		###
		N = len(mainPages)
		colBN = int(ceil(N / colN))
		for col_i in range(colN):
			colVBox = VBox(spacing=10)
			for row_i in range(colBN):
				page_i = col_i * colBN + row_i
				if page_i >= N:
					break
				page = mainPages[page_i]
				button = self.newWideButton(page)
				grid.attach(button, col_i, row_i + 1, 1, 1)
		grid.show_all()
		###############
		page = StackPage()
		page.pageName = rootPageName
		page.pageWidget = grid
		page.pageExpand = True
		page.pageExpand = True
		stack.addPage(page)
		for page in self.prefPages:
			stack.addPage(page)
		if ui.preferencesPageName:
			self.stack.gotoPage(ui.preferencesPageName)
		#######################
		pack(self.vbox, stack, 1, 1)
		pack(self.vbox, self.buttonbox)
		####
		self.vbox.show_all()

	def onClearImageCacheClick(self, button):
		pixcache.clearFiles()
		pixcache.clear()

	def gotoPageCallback(self, pageName):
		def callback(*args):
			self.stack.gotoPage(pageName)
		return callback

	def newWideButton(self, page: StackPage):
		hbox = HBox(spacing=10)
		hbox.set_border_width(10)
		label = gtk.Label(label=page.pageLabel)
		label.set_use_underline(True)
		pack(hbox, gtk.Label(), 1, 1)
		if page.pageIcon and ui.buttonIconEnable:
			pack(hbox, imageFromFile(page.pageIcon, self.stack.iconSize()))
		pack(hbox, label, 0, 0)
		pack(hbox, gtk.Label(), 1, 1)
		button = gtk.Button()
		button.add(hbox)
		button.connect("clicked", self.gotoPageCallback(page.pageName))
		return button

	def comboFirstWDChanged(self, combo):
		f = self.comboFirstWD.get_active()  # 0 means Sunday
		if f == 7:  # auto
			try:
				f = core.getLocaleFirstWeekDay()
			except Exception:
				pass
		# core.firstWeekDay will be later = f
		self.holiWDItem.setStart(f)

	def onDelete(self, obj=None, data=None):
		self.hide()
		return True

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		if gdk.keyval_name(gevent.keyval) == "Escape":
			self.hide()
			return True
		return False

	def ok(self, widget):
		self.hide()

		self.apply()

	def cancel(self, widget=None):
		self.hide()
		self.updatePrefGui()
		return True

	def iterAllPrefItems(self):
		import itertools
		return itertools.chain(
			[self.loggerPrefItem],
			self.moduleOptions,
			self.localePrefItems,
			self.corePrefItems,
			self.uiPrefItems,
			self.gtkPrefItems,
		)

	def loadPlugin(self, plug: "BasePlugin", plugI: int) -> "BasePlugin":
		plug = plugin_man.loadPlugin(plug.file, enable=True)
		if plug:
			assert plug.loaded
		core.allPlugList[plugI] = plug
		return plug

	def apply(self, widget=None):
		from scal3.ui_gtk.font_utils import gfontDecode
		# log.debug(f"fontDefault = {ui.fontDefault!r}")
		ui.fontDefault = gfontDecode(
			ud.settings.get_property("gtk-font-name")
		)
		# log.debug(f"fontDefault = {ui.fontDefault!r}")
		#####
		ui.preferencesPageName = self.stack.currentPageName()
		#####
		# #################### Updating pref variables #####################
		for prefItem in self.iterAllPrefItems():
			prefItem.updateVar()
		# ##### Plugin Manager
		index = []
		for row in self.plugTreeview.get_model():
			plugI = row[0]
			enable = row[1]
			show_date = row[2]
			index.append(plugI)
			plug = core.allPlugList[plugI]
			if plug.loaded:
				try:
					plug.enable = enable
					plug.show_date = show_date
				except NameError:
					core.log.exception("")
					log.info(i, core.plugIndex)
			elif enable:
				plug = self.loadPlugin(plug, plugI)
		core.plugIndex = index
		core.updatePlugins()
		######
		first = self.comboFirstWD.get_active()
		if first == 7:
			core.firstWeekDayAuto = True
			try:
				core.firstWeekDay = core.getLocaleFirstWeekDay()
			except Exception:
				pass
		else:
			core.firstWeekDayAuto = False
			core.firstWeekDay = first
		######
		weekNumberMode = self.comboWeekYear.get_active()
		if weekNumberMode == 8:
			core.weekNumberModeAuto = True
			core.weekNumberMode = core.getLocaleweekNumberMode()
		else:
			core.weekNumberModeAuto = False
			core.weekNumberMode = weekNumberMode
		######
		ui.cellCache.clear()  # Very important
		# ^ specially when calTypes.primary will be changed
		######
		ud.updateFormatsBin()
		# ###################### Saving Preferences #######################
		# ################### Saving logger config
		self.loggerPrefItem.save()
		# ################### Saving calendar types config
		for mod in calTypes:
			mod.save()
		# ################### Saving locale config
		locale_man.saveConf()
		# ################### Saving core config
		core.version = core.VERSION
		core.saveConf()
		del core.version
		# ################### Saving ui config
		ui.saveConf()
		# ################### Saving gtk_ud config
		ud.saveConf()
		# ####################### Updating GUI ###########################
		ud.windowList.onConfigChange()
		if ui.mainWin:
			if ui.checkNeedRestart():
				d = gtk.Dialog(
					title=_("Restart " + core.APP_DESC),
					transient_for=self,
					modal=True,
					destroy_with_parent=True,
				)
				dialog_add_button(
					d,
					imageName="dialog-cancel.svg",
					label=_("Cancel"),
					res=gtk.ResponseType.CANCEL,
				)
				d.set_keep_above(True)
				label = gtk.Label(label=_(
					f"Some preferences need restarting {core.APP_DESC} to apply."
				))
				label.set_line_wrap(True)
				vbox = VBox()
				vbox.set_border_width(15)
				pack(vbox, label)
				pack(d.vbox, vbox)
				resBut = dialog_add_button(
					d,
					imageName="view-refresh.svg",
					label=_("_Restart"),
					res=gtk.ResponseType.OK,
				)
				resBut.grab_default()
				d.vbox.set_border_width(5)
				d.resize(400, 150)
				d.vbox.show_all()
				if d.run() == gtk.ResponseType.OK:
					core.restart()
				else:
					d.destroy()

	def refreshAccounts(self):
		self.accountsTreeModel.clear()
		for account in ui.eventAccounts:
			self.accountsTreeModel.append([
				account.id,
				account.enable,
				account.title,
			])

	def updatePrefGui(self):  # Updating Pref Gui (NOT MAIN GUI)
		for opt in self.iterAllPrefItems():
			opt.updateWidget()
		###############################
		if core.firstWeekDayAuto:
			self.comboFirstWD.set_active(7)
		else:
			self.comboFirstWD.set_active(core.firstWeekDay)
		if core.weekNumberModeAuto:
			self.comboWeekYear.set_active(8)
		else:
			self.comboWeekYear.set_active(core.weekNumberMode)
		# #### Plugin Manager
		model = self.plugTreeview.get_model()
		model.clear()
		for row in core.getPluginsTable():
			model.append(row)
		self.plugAddItems = []
		self.plugAddTreeModel.clear()
		for (i, title) in core.getDeletedPluginsTable():
			self.plugAddItems.append(i)
			self.plugAddTreeModel.append([title])
			self.pluginsToolbar.setCanAdd(True)
		# #### Accounts
		self.refreshAccounts()

	# def plugTreevExpose(self, widget, gevent):
	# 	self.plugTitleCell.set_property(
	# 		"wrap-width",
	# 		self.plugTitleCol.get_width() + 2
	# 	)

	def plugTreevCursorChanged(self, selection=None):
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		model = self.plugTreeview.get_model()
		j = model[i][0]
		plug = core.allPlugList[j]
		self.plugButtonAbout.set_sensitive(bool(plug.about))
		self.plugButtonConf.set_sensitive(plug.hasConfig)

	def onPlugAboutClick(self, obj=None):
		from scal3.ui_gtk.about import AboutDialog
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		model = self.plugTreeview.get_model()
		j = model[i][0]
		plug = core.allPlugList[j]
		if hasattr(plug, "open_about"):
			return plug.open_about()
		if plug.about is None:
			return
		about = AboutDialog(
			name="",  # FIXME
			title=_("About Plugin"),  # _("About ") + plug.title
			authors=plug.authors,
			comments=plug.about,
		)
		about.set_transient_for(self)
		about.connect("delete-event", lambda w, e: w.destroy())
		about.connect("response", lambda w, e: w.destroy())
		# about.set_resizable(True)
		# about.vbox.show_all()  # OR about.vbox.show_all() ; about.run()
		openWindow(about)  # FIXME

	def onPlugConfClick(self, obj=None):
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		model = self.plugTreeview.get_model()
		j = model[i][0]
		plug = core.allPlugList[j]
		if not plug.hasConfig:
			return
		plug.open_configure()

	def onPlugExportToIcsClick(self, menu, plug):
		from scal3.ui_gtk.export import ExportToIcsDialog
		ExportToIcsDialog(plug.exportToIcs, plug.title).run()

	def plugTreevRActivate(self, treev, path, col):
		if col.get_title() == _("Title"):  # FIXME
			self.onPlugAboutClick(None)

	def plugTreevButtonPress(self, widget, gevent):
		b = gevent.button
		if b == 3:
			cur = self.plugTreeview.get_cursor()[0]
			if cur:
				i = cur[0]
				j = self.plugTreeview.get_model()[i][0]
				plug = core.allPlugList[j]
				menu = Menu()
				##
				item = ImageMenuItem(
					_("_About"),
					imageName="dialog-information.svg",
					func=self.onPlugAboutClick,
				)
				item.set_sensitive(bool(plug.about))
				menu.add(item)
				##
				item = ImageMenuItem(
					_("_Configure"),
					imageName="preferences-system.svg",
					func=self.onPlugConfClick,
				)
				item.set_sensitive(plug.hasConfig)
				menu.add(item)
				##
				menu.add(ImageMenuItem(
					_("Export to {format}").format(format="iCalendar"),
					imageName="text-calendar-ics.png",
					func=self.onPlugExportToIcsClick,
					args=(plug,),
				))
				##
				menu.show_all()
				self.tmpMenu = menu
				menu.popup(None, None, None, None, 3, gevent.time)
			return True
		return False

	def onPlugAddClick(self, button):
		# FIXME
		# Reize window to show all texts
		# self.plugAddTreeview.columns_autosize()  # FIXME
		x, y, w, h = self.plugAddTreeview.get_column(0).cell_get_size()
		# log.debug(x, y, w, h)
		self.plugAddDialog.resize(
			w + 30,
			75 + 30 * len(self.plugAddTreeModel),
		)
		###############
		self.plugAddDialog.run()
		self.pluginsToolbar.setCanAdd(len(self.plugAddItems) > 0)

	def plugAddDialogClose(self, obj, gevent=None):
		self.plugAddDialog.hide()
		return True

	def plugTreeviewCellToggled(self, cell, path):
		model = self.plugTreeview.get_model()
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 1, active)
		if active:
			plugI = model[path[0]][0]
			plug = core.allPlugList[plugI]
			if not plug.loaded:
				plug = self.loadPlugin(plug, plugI)
			self.plugTreevCursorChanged()

	def plugTreeviewCellToggled2(self, cell, path):
		model = self.plugTreeview.get_model()
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 2, active)

	def plugTreeviewTop(self, button):
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		t = self.plugTreeview.get_model()
		if i <= 0 or i >= len(t):
			gdk.beep()
			return
		t.prepend(list(t[i]))
		t.remove(t.get_iter(i + 1))
		self.plugTreeview.set_cursor(0)

	def plugTreeviewBottom(self, button):
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		t = self.plugTreeview.get_model()
		if i < 0 or i >= len(t) - 1:
			gdk.beep()
			return
		t.append(list(t[i]))
		t.remove(t.get_iter(i))
		self.plugTreeview.set_cursor(len(t) - 1)

	def plugTreeviewUp(self, button):
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		t = self.plugTreeview.get_model()
		if i <= 0 or i >= len(t):
			gdk.beep()
			return
		t.swap(t.get_iter(i - 1), t.get_iter(i))
		self.plugTreeview.set_cursor(i - 1)

	def plugTreeviewDown(self, button):
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		t = self.plugTreeview.get_model()
		if i < 0 or i >= len(t) - 1:
			gdk.beep()
			return
		t.swap(t.get_iter(i), t.get_iter(i + 1))
		self.plugTreeview.set_cursor(i + 1)

	def plugTreevDragReceived(self, treev, context, x, y, selec, info, etime):
		t = treev.get_model()  # self.plugAddTreeModel
		cur = treev.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		dest = treev.get_dest_row_at_pos(x, y)
		if dest is None:
			t.move_after(
				t.get_iter(i),
				t.get_iter(len(t) - 1),
			)
		elif dest[1] in (
			gtk.TreeViewDropPosition.BEFORE,
			gtk.TreeViewDropPosition.INTO_OR_BEFORE,
		):
			t.move_before(
				t.get_iter(i),
				t.get_iter(dest[0][0]),
			)
		else:
			t.move_after(
				t.get_iter(i),
				t.get_iter(dest[0][0]),
			)

	def onPlugDeleteClick(self, button):
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		t = self.plugTreeview.get_model()
		n = len(t)
		if i < 0 or i >= n:
			gdk.beep()
			return
		j = t[i][0]
		t.remove(t.get_iter(i))
		# j is index of deleted plugin
		self.plugAddItems.append(j)
		title = core.allPlugList[j].title
		self.plugAddTreeModel.append([title])
		log.debug(f"deleting {title}")
		self.pluginsToolbar.setCanAdd(True)
		if n > 1:
			self.plugTreeview.set_cursor(min(n - 2, i))

	def plugAddDialogOK(self, obj):
		cur = self.plugAddTreeview.get_cursor()[0]
		if cur is None:
			gdk.beep()
			return
		i = cur[0]
		j = self.plugAddItems[i]
		cur2 = self.plugTreeview.get_cursor()[0]
		if cur2 is None:
			pos = len(self.plugTreeview.get_model())
		else:
			pos = cur2[0] + 1
		self.plugTreeview.get_model().insert(pos, [
			j,
			True,
			False,
			core.allPlugList[j].title,
		])
		self.plugAddTreeModel.remove(self.plugAddTreeModel.get_iter(i))
		self.plugAddItems.pop(i)
		self.plugAddDialog.hide()
		self.plugTreeview.set_cursor(pos)  # pos == -1 ## FIXME

	def plugAddTreevRActivate(self, treev, path, col):
		self.plugAddDialogOK(None)  # FIXME

	def editAccount(self, index):
		from scal3.ui_gtk.event.account_op import AccountEditorDialog
		accountId = self.accountsTreeModel[index][0]
		account = ui.eventAccounts[accountId]
		if not account.loaded:
			showError(_("Account must be enabled before editing"), transient_for=self)
			return
		account = AccountEditorDialog(account, transient_for=self).run()
		if account is None:
			return
		account.save()
		ui.eventAccounts.save()
		self.accountsTreeModel[index][2] = account.title

	def onAccountsEditClick(self, button):
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur[0]
		self.editAccount(index)

	def onAccountsRegisterClick(self, button):
		from scal3.ui_gtk.event.register_starcal import StarCalendarRegisterDialog
		win = StarCalendarRegisterDialog(transient_for=self)
		win.present()

	def onAccountsAddClick(self, button):
		from scal3.ui_gtk.event.account_op import AccountEditorDialog
		account = AccountEditorDialog(transient_for=self).run()
		if account is None:
			return
		account.save()
		ui.eventAccounts.append(account)
		ui.eventAccounts.save()
		self.accountsTreeModel.append([
			account.id,
			account.enable,
			account.title,
		])
		###
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		error = account.fetchGroups()
		if error:
			log.error(error)
			return
		account.save()

	def onAccountsDeleteClick(self, button):
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur[0]
		accountId = self.accountsTreeModel[index][0]
		account = ui.eventAccounts[accountId]
		if not confirm(
			_("Do you want to delete account \"{accountTitle}\"").format(
				accountTitle=account.title,
			),
			transient_for=self,
		):
			return
		ui.eventAccounts.delete(account)
		ui.eventAccounts.save()
		del self.accountsTreeModel[index]

	def onAccountsUpClick(self, button):
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur[0]
		t = self.accountsTreeModel
		if index <= 0 or index >= len(t):
			gdk.beep()
			return
		ui.eventAccounts.moveUp(index)
		ui.eventAccounts.save()
		t.swap(
			t.get_iter(index - 1),
			t.get_iter(index),
		)
		self.accountsTreeview.set_cursor(index - 1)

	def onAccountsDownClick(self, button):
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur[0]
		t = self.accountsTreeModel
		if index < 0 or index >= len(t) - 1:
			gdk.beep()
			return
		ui.eventAccounts.moveDown(index)
		ui.eventAccounts.save()
		t.swap(t.get_iter(index), t.get_iter(index + 1))
		self.accountsTreeview.set_cursor(index + 1)

	def accountsTreevRActivate(self, treev, path, col):
		index = path[0]
		self.editAccount(index)

	def accountsTreevButtonPress(self, widget, gevent):
		b = gevent.button
		if b == 3:
			cur = self.accountsTreeview.get_cursor()[0]
			if cur:
				index = cur[0]
				accountId = self.accountsTreeModel[index][0]
				account = ui.eventAccounts[accountId]
				menu = Menu()
				##
				# FIXME
				##
				# menu.show_all()
				# self.tmpMenu = menu
				# menu.popup(None, None, None, None, 3, gevent.time)
			return True
		return False

	def accountsTreeviewCellToggled(self, cell, path):
		index = int(path)
		active = not cell.get_active()
		###
		accountId = self.accountsTreeModel[index][0]
		account = ui.eventAccounts[accountId]
		if not account.loaded:  # it's a dummy account
			if active:
				account = ui.eventAccounts.replaceDummyObj(account)
				if account is None:
					return
		account.enable = active
		account.save()
		###
		self.accountsTreeModel[index][1] = active


if __name__ == "__main__":
	dialog = PreferencesWindow(0)
	dialog.updatePrefGui()
	dialog.run()
