#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import logger
from scal3.ui_gtk.preferences.lang_caltype import PreferencesLanguageCalTypes

log = logger.get()

import typing
from contextlib import suppress
from os.path import isfile, join
from typing import Any

from scal3 import core, locale_man, ui
from scal3.app_info import APP_DESC
from scal3.cal_types import calTypes
from scal3.locale_man import getLocaleFirstWeekDay
from scal3.locale_man import tr as _
from scal3.path import sourceDir, svgDir
from scal3.ui import conf
from scal3.ui_gtk import Dialog, gdk, gtk, pack, pixcache
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_type_option_ui import ModuleOptionButton, ModuleOptionUI
from scal3.ui_gtk.log_pref import LogLevelOptionUI
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.option_ui import (
	CheckColorOptionUI,
	CheckOptionUI,
	ColorOptionUI,
	ComboEntryTextOptionUI,
	FontFamilyOptionUI,
	FontOptionUI,
	ImageFileChooserOptionUI,
	IntSpinOptionUI,
	WidthHeightOptionUI,
)
from scal3.ui_gtk.option_ui_extra import (
	CheckStartupOptionUI,
	WeekDayCheckListOptionUI,
)
from scal3.ui_gtk.preferences.accounts import PreferencesAccountsTab
from scal3.ui_gtk.preferences.plugins import PreferencesPluginsTab
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.utils import (
	dialog_add_button,
	imageFromFile,
	labelImageButton,
	newAlignLabel,
	newHSep,
)

if typing.TYPE_CHECKING:
	from scal3.ui_gtk.option_ui import (
		OptionUI,
	)
	from scal3.ui_gtk.pytypes import StackPageType

__all__ = ["PreferencesWindow"]


class PreferencesWindow(gtk.Window):
	mainGridStyleClass = "preferences-main-grid"

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		return ".preferences-main-grid " + cssTextStyle(
			font=ui.getFont(scale=1.5),
		)

	def __init__(self, transient_for: gtk.Window | None = None) -> None:
		gtk.Window.__init__(self, transient_for=transient_for)
		self.set_title(_("Preferences"))
		self.set_position(gtk.WindowPosition.CENTER)
		self.connect("delete-event", self.onDelete)
		self.connect("key-press-event", self.onKeyPress)
		# self.set_has_separator(False)
		# self.set_skip_taskbar_hint(True)
		# ---
		self.spacing = int(ui.getFont().size)
		self.mainGridSpacing = int(ui.getFont(scale=0.8).size)
		# ---
		self.vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		self.add(self.vbox)
		# ---
		self.buttonbox = MyHButtonBox()
		self.buttonbox.add_button(
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			onClick=self.cancel,
		)
		self.buttonbox.add_button(
			imageName="dialog-ok-apply.svg",
			label=_("_Apply", ctx="window action"),
			onClick=self.apply,
		)
		self.buttonbox.add_button(
			imageName="dialog-ok.svg",
			label=_("_Confirm"),
			onClick=self.ok,
			tooltip=_("Apply and Close", ctx="window action"),
		)
		# okB.grab_default()  # FIXME
		# okB.grab_focus()  # FIXME
		# ----------------------------------------------
		self.loggerOptionUI: LogLevelOptionUI | None = None
		self.localeOptionUIs: list[OptionUI] = []
		self.coreOptionUIs: list[OptionUI] = []
		self.uiOptionUIs: list[OptionUI] = []
		self.gtkOptionUIs: list[OptionUI] = []  # FIXME
		# -----
		self.prefPages: list[StackPageType] = []
		# ----------------------------------------------
		stack = MyStack(
			iconSize=conf.stackIconSize.v,
		)
		stack.setTitleFontSize("large")
		stack.setTitleCentered(True)
		stack.setupWindowTitle(self, _("Preferences"), False)
		self.stack = stack
		# --------------------------------------------------------------------
		self._initPageLangCalTypes()  # Page Language and Calendar Types)
		self._initPageGeneral()  # Page General
		self._initPageAppearance()  # Page Appearance
		self._initPageRegional()  # Page Regional
		self._initPageAdvanced()  # Page Advanced
		self._initPagePlugins()  # Page Plugins
		self._initPageStatusIcon()  # Page Status Icon
		self._initPageAccounts()  # Page Accounts
		# --------------------------------------------------------------------
		rootPageName = "preferences"
		# ---
		mainPages = []
		for page in self.prefPages:
			if page.pageParent:
				continue
			page.pageParent = rootPageName
			page.iconSize = 32
			mainPages.append(page)
		# ----
		colN = 2
		# ----
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		grid.set_row_spacing(self.mainGridSpacing)
		grid.set_column_spacing(self.mainGridSpacing)
		grid.set_border_width(self.mainGridSpacing * 4 // 3)
		# ----
		grid.get_style_context().add_class(self.mainGridStyleClass)
		# ----
		page = mainPages.pop(0)
		button = self.newWideButton(page)
		grid.attach(button, 0, 0, colN, 1)
		# ---
		N = len(mainPages)
		rowN = (N - 1) // colN + 1
		for col_i in range(colN):
			for row_i in range(rowN):
				page_i = col_i * rowN + row_i
				if page_i >= N:
					break
				page = mainPages[page_i]
				button = self.newWideButton(page)
				grid.attach(button, col_i, row_i + 1, 1, 1)
		grid.show_all()
		# ---------------
		pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(pageWidget, grid, True, True)
		page = StackPage()
		page.pagePath = page.pageName = rootPageName
		page.pageWidget = pageWidget
		page.pageExpand = True
		page.pageExpand = True
		stack.addPage(page)
		for page in self.prefPages:
			page.pagePath = page.pageName
			stack.addPage(page)
		# if conf.preferencesPagePath.v:
		# 	self.stack.gotoPage(conf.preferencesPagePath.v)
		# -----------------------
		pack(self.vbox, stack, 1, 1)
		pack(self.vbox, self.buttonbox)
		# ----
		self.vbox.show_all()
		self.vbox.connect("realize", self.onMainVBoxRealize)

	def _initPageLangCalTypes(self) -> None:
		tab = PreferencesLanguageCalTypes(window=self, spacing=self.spacing)
		self.langCalTypesTab = tab
		self.prefPages.append(tab.page)
		self.localeOptionUIs.append(tab.langOption)
		self.coreOptionUIs.append(tab.calsOption)


	def _initPageGeneral(self) -> None:
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=self.spacing)
		vbox.set_border_width(int(self.spacing / 2))
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "general"
		page.pageTitle = _("General")
		page.pageLabel = _("_General")
		page.pageIcon = "preferences-system.svg"
		self.prefPages.append(page)
		item: OptionUI
		# --------------------------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		item = CheckStartupOptionUI()
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------------------------
		item = CheckOptionUI(
			option=conf.showMain,
			label=_("Open main window on start"),
		)
		self.uiOptionUIs.append(item)
		pack(vbox, item.getWidget())
		# ------------------------
		item = CheckOptionUI(
			option=conf.showDesktopWidget,
			label=_("Open desktop widget on start"),
		)
		self.uiOptionUIs.append(item)
		pack(vbox, item.getWidget())
		# --------------------------
		item = CheckOptionUI(
			option=conf.winTaskbar,
			label=_("Window in Taskbar"),
		)
		self.uiOptionUIs.append(item)
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		# -----------
		pack(vbox, hbox)
		# --------------------------
		try:
			import scal3.ui_gtk.starcal_appindicator  # noqa: F401
		except (ImportError, ValueError):
			pass
		else:
			item = CheckOptionUI(
				option=conf.useAppIndicator,
				label=_("Use AppIndicator"),
			)
			self.uiOptionUIs.append(item)
			hbox = gtk.Box(
				orientation=gtk.Orientation.HORIZONTAL,
				spacing=int(self.spacing / 2),
			)
			pack(hbox, item.getWidget())
			pack(hbox, gtk.Label(), 1, 1)
			pack(vbox, hbox)
		# --------------------------
		# hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL,spacing=self.spacing/2)
		# pack(hbox, gtk.Label(label=_("Show Digital Clock:")))
		# pack(hbox, gtk.Label(), 1, 1)
		# #item = CheckOptionUI(
		# #	option=conf.showDigClockTb",
		# #	label=_("On Toolbar"),
		# #)  # FIXME
		# #self.uiOptionUIs.append(item)
		# #pack(hbox, item.getWidget())
		# pack(hbox, gtk.Label(), 1, 1)
		# item = CheckOptionUI(
		# 	option=conf.showDigClockTr,
		# 	label=_("On Status Icon"),
		# 	tooltip="Notification Area",
		# )
		# self.uiOptionUIs.append(item)
		# pack(hbox, item.getWidget())
		# pack(hbox, gtk.Label(), 1, 1)
		# pack(vbox, hbox)

	def _initPageAppearance(self) -> None:
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=self.spacing)
		vbox.set_border_width(self.spacing)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "appearance"
		page.pageTitle = _("Appearance")
		# A is for Apply, P is for Plugins, R is for Regional,
		# C is for Cancel, only "n" is left!
		page.pageLabel = _("Appeara_nce")
		page.pageIcon = "preferences-desktop-theme.png"
		self.prefPages.append(page)
		# --------
		buttonPadding = self.spacing
		padding = int(self.spacing / 2)
		# ---
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		# ---
		customCheckItem = CheckOptionUI(
			option=conf.fontCustomEnable,
			label=_("Application Font"),
		)
		self.uiOptionUIs.append(customCheckItem)
		pack(hbox, customCheckItem.getWidget())
		# ---
		customItem = FontOptionUI(option=conf.fontCustom)
		self.uiOptionUIs.append(customItem)
		pack(hbox, customItem.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		customCheckItem.syncSensitive(customItem.getWidget())
		pack(vbox, hbox, padding=padding)
		item: OptionUI
		# ---------------------------
		item = CheckOptionUI(
			option=conf.buttonIconEnable,
			label=_("Show icons in buttons"),
		)
		self.uiOptionUIs.append(item)
		pack(vbox, item.getWidget())
		# ---------------------------
		item = CheckOptionUI(
			option=conf.useSystemIcons,
			label=_("Use System Icons"),
		)
		self.uiOptionUIs.append(item)
		pack(vbox, item.getWidget())
		# ---------------------------
		item = CheckOptionUI(
			option=conf.oldStyleProgressBar,
			label=_("Old-style Progress Bar"),
		)
		self.uiOptionUIs.append(item)
		pack(vbox, item.getWidget())
		# ------------------------- Theme ---------------------
		pageHBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pageHBox.set_border_width(self.spacing)
		spacing = int(self.spacing / 3)
		# ---
		pageVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Background")))
		item = ColorOptionUI(option=conf.bgColor, useAlpha=True)
		self.uiOptionUIs.append(item)
		self.colorbBg = item.getWidget()  # FIXME
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Border")))
		item = ColorOptionUI(option=conf.borderColor, useAlpha=True)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Cursor")))
		item = ColorOptionUI(option=conf.cursorOutColor, useAlpha=False)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Cursor BG")))
		item = ColorOptionUI(option=conf.cursorBgColor, useAlpha=True)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Today")))
		item = ColorOptionUI(option=conf.todayCellColor, useAlpha=True)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ------
		pack(pageHBox, pageVBox, 1, 1)
		pack(pageHBox, newHSep(), 0, 0)
		pageVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Normal Text")))
		item = ColorOptionUI(option=conf.textColor, useAlpha=False)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Holidays Font")))
		item = ColorOptionUI(option=conf.holidayColor, useAlpha=False)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Inactive Day Font")))
		item = ColorOptionUI(option=conf.inactiveColor, useAlpha=True)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Border Font")))
		item = ColorOptionUI(option=conf.borderTextColor, useAlpha=False)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		pack(pageHBox, pageVBox, 1, 1, padding=int(self.spacing / 2))
		# ----
		page = StackPage()
		page.pageParent = "appearance"
		page.pageWidget = pageHBox
		page.pageName = "colors"
		page.pageTitle = _("Colors") + " - " + _("Appearance")
		page.pageLabel = _("Colors")
		page.pageIcon = "preferences-desktop-color.svg"
		page.pageExpand = False
		self.prefPages.append(page)
		# -----
		appearanceSubPages = [page]
		# -------------------
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		grid.set_row_spacing(buttonPadding)
		for index, page in enumerate(appearanceSubPages):
			grid.attach(self.newWideButton(page), 0, index, 1, 1)
		grid.show_all()
		pack(vbox, grid, padding=padding)

	def _initPageRegional(self) -> None:
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		vbox.set_border_width(5)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "regional"
		page.pageTitle = _("Regional")
		page.pageLabel = _("_Regional")
		page.pageIcon = "preferences-desktop-locale.png"
		self.prefPages.append(page)
		# ------
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		item: OptionUI
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=self.spacing)
		label = gtk.Label(label=_("Date Format"))
		pack(hbox, label)
		sgroup.add_widget(label)
		# pack(hbox, gtk.Label(), 1, 1)
		item = ComboEntryTextOptionUI(
			option=ud.dateFormat,
			items=[
				"%Y/%m/%d",
				"%Y-%m-%d",
				"%y/%m/%d",
				"%y-%m-%d",
				"%OY/%Om/%Od",
				"%OY-%Om-%Od",
				"%m/%d",
				"%m/%d/%Y",
			],
		)
		self.gtkOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# --------------------------------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL,
			spacing=int(self.spacing / 3),
		)
		item = CheckOptionUI(
			option=locale_man.enableNumLocale,
			label=_("Numbers Localization"),
		)
		self.localeOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox, padding=self.spacing)
		# --------------------------------
		pageVBox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=int(self.spacing / 2),
		)
		# ----
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 3)
		)
		pack(hbox, gtk.Label(label=_("First day of week")))
		# item = ComboTextOptionUI(  # FIXME
		self.comboFirstWD = gtk.ComboBoxText()
		for wdName in core.weekDayName:
			self.comboFirstWD.append_text(wdName)
		self.comboFirstWD.append_text(_("Automatic"))
		self.comboFirstWD.connect("changed", self.comboFirstWDChanged)
		pack(hbox, self.comboFirstWD)
		pack(pageVBox, hbox)
		# ---------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 3)
		)
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
		# combo.append_text(_("Automatic"))-- (as Locale)  # FIXME
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox, padding=5)
		self.comboWeekYear = combo
		# ---------
		frame = gtk.Frame()
		frame.set_border_width(10)
		frame.set_label(_("Holidays"))
		item = WeekDayCheckListOptionUI(
			option=core.holidayWeekDays,
			abbreviateNames=False,
			twoRows=True,
		)
		self.coreOptionUIs.append(item)
		self.holiWDItem = item  # Holiday Week Days Item
		itemWidget = item.getWidget()
		assert isinstance(itemWidget, gtk.Container), f"{itemWidget=}"
		itemWidget.set_border_width(10)
		frame.add(itemWidget)
		pack(pageVBox, frame)
		# ------------
		page = StackPage()
		page.pageParent = "regional"
		page.pageWidget = pageVBox
		page.pageName = "regional_week"
		page.pageTitle = _("Week") + " - " + _("Regional")
		page.pageLabel = _("Week-related Settings")
		page.pageIcon = ""
		page.pageExpand = False
		self.prefPages.append(page)
		# -----
		regionalSubPages = [page]
		# --------------------------------------------------
		options = []
		for mod in calTypes:
			if not mod.options:
				continue
			pageVBox = gtk.Box(
				orientation=gtk.Orientation.VERTICAL, spacing=self.spacing
			)
			pageVBox.set_border_width(self.spacing)
			page = StackPage()
			page.pageParent = "regional"
			page.pageWidget = pageVBox
			page.pageName = "regional_" + mod.name
			page.pageTitle = (
				_("{calType} Calendar").format(calType=_(mod.desc, ctx="calendar"))
				+ " - "
				+ _("Regional")
			)
			page.pageLabel = _("{calType} Calendar").format(
				calType=_(mod.desc, ctx="calendar"),
			)
			page.pageExpand = False
			self.prefPages.append(page)
			# -----
			regionalSubPages.append(page)
			optionUI: Any
			for rawOpt in mod.options:
				if rawOpt[0] == "button":
					try:
						optionUI = ModuleOptionButton(rawOpt[1:])
					except Exception:
						log.exception("")
						continue
				else:
					option = getattr(mod, rawOpt[0])
					optionUI = ModuleOptionUI(
						option=option,
						rawOption=rawOpt,
						spacing=self.spacing,
					)
				options.append(optionUI)
				pack(pageVBox, optionUI.getWidget())
			# -----
		# -----
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		# grid.set_row_spacing(self.spacing)
		for index, page in enumerate(regionalSubPages):
			button = self.newWideButton(page)
			button.set_border_width(int(self.spacing * 0.7))
			grid.attach(button, 0, index, 1, 1)
		grid.show_all()
		pack(vbox, grid)
		# ---
		self.moduleOptions = options

	def _initPageAdvanced(self) -> None:
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=self.spacing)
		vbox.set_border_width(int(self.spacing / 2))
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "advanced"
		page.pageTitle = _("Advanced")
		page.pageLabel = _("A_dvanced")
		page.pageIcon = "applications-system.svg"
		self.prefPages.append(page)
		item: OptionUI
		# ------
		item = LogLevelOptionUI()
		self.loggerOptionUI = item
		pack(vbox, item.getWidget())
		# ---
		self.initialLogLevel = logger.logLevel
		# ------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		# pack(hbox, gtk.Label(), 1, 1)
		label = gtk.Label(label=_("Event Time Format"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = ComboEntryTextOptionUI(
			option=conf.eventDayViewTimeFormat,
			items=[
				"HM$",
				"HMS",
				"hMS",
				"hm$",
				"hms",
				"HM",
				"hm",
				"hM",
			],
		)
		item.addDescriptionColumn(
			{
				"HM$": f"05:07:09 {_('or')} 05:07",
				"HMS": f"05:07:09 {_('or')} 05:07:00",
				"hMS": f"05:07:09 {_('or')} 5:07:00",
				"hm$": f"5:7:9 {_('or')} 5:7",
				"hms": f"5:7:9 {_('or')} 5:7:0",
				"HM": "05:07",
				"hm": "5:7",
				"hM": "5:07",
			},
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		# pack(hbox, gtk.Label(), 1, 1)
		label = gtk.Label(label=_("Digital Clock Format"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = ComboEntryTextOptionUI(
			ud.clockFormat,
			items=[
				"%T",
				"%X",
				"%Y/%m/%d - %T",
				"%OY/%Om/%Od - %X",
				"<i>%Y/%m/%d</i> - %T",
				"<b>%T</b>",
				"<b>%X</b>",
				"%H:%M",
				"<b>%H:%M</b>",
				'<span size="smaller">%OY/%Om/%Od</span>,%X'
				'%OY/%Om/%Od,<span color="#ff0000">%X</span>',
				'<span font="bold">%X</span>',
				"%OH:%OM",
				"<b>%OH:%OM</b>",
			],
		)
		self.gtkOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		label = gtk.Label(label=_("Days maximum cache size"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = IntSpinOptionUI(
			option=conf.maxDayCacheSize,
			bounds=(100, 9999),
			step=10,
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(vbox, hbox)
		# ------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		label = gtk.Label(label=_("Horizontal offset for day right-click menu"))
		pack(hbox, label)
		item = IntSpinOptionUI(
			option=conf.cellMenuXOffset,
			bounds=(0, 999),
			step=1,
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(vbox, hbox)
		# ------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		button = labelImageButton(
			label=_("Clear Image Cache"),
			# TODO: _("Clear Image Cache ({size})").format(size=""),
			imageName="sweep.svg",
		)
		button.connect("clicked", self.onClearImageCacheClick)
		pack(hbox, button)
		pack(vbox, hbox)

	def _initPagePlugins(self) -> None:
		tab = PreferencesPluginsTab(spacing=self.spacing, window=self)
		self.pluginsTab = tab
		self.prefPages.append(tab.page)

	def _initPageStatusIcon(self) -> None:
		pageVBox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=int(self.spacing * 0.8),
		)
		pageVBox.set_border_width(self.spacing)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		item: OptionUI
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		label = newAlignLabel(sgroup=sgroup, label=_("Normal Days"))
		pack(hbox, label)
		item = ImageFileChooserOptionUI(
			option=conf.statusIconImage,
			title=_("Select Icon"),
			currentFolder=join(sourceDir, "status-icons"),
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		label = newAlignLabel(sgroup=sgroup, label=_("Holidays"))
		pack(hbox, label)
		item = ImageFileChooserOptionUI(
			option=conf.statusIconImageHoli,
			title=_("Select Icon"),
			currentFolder=join(sourceDir, "status-icons"),
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		checkItem = CheckOptionUI(
			option=conf.statusIconFontFamilyEnable,
			label=_("Change font family to"),
			# tooltip=_("In SVG files"),
		)
		self.uiOptionUIs.append(checkItem)
		# sgroup.add_widget(checkItem.getWidget())
		pack(hbox, checkItem.getWidget())
		item = FontFamilyOptionUI(
			option=conf.statusIconFontFamily,
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		item = CheckOptionUI(
			option=conf.statusIconLocalizeNumber,
			label=_("Localize the number"),
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		item = CheckColorOptionUI(
			CheckOptionUI(
				option=conf.statusIconHolidayFontColorEnable,
				label=_("Holiday font color"),
			),
			ColorOptionUI(
				option=conf.statusIconHolidayFontColor,
			),
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		checkItem = CheckOptionUI(
			option=conf.statusIconFixedSizeEnable,
			label=_("Fixed Size"),
			# tooltip=_(""),
		)
		self.uiOptionUIs.append(checkItem)
		# sgroup.add_widget(checkItem.getWidget())
		pack(hbox, checkItem.getWidget())
		pack(hbox, gtk.Label(label=" "))
		item = WidthHeightOptionUI(
			option=conf.statusIconFixedSizeWH,
			maxim=999,
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		checkItem.syncSensitive(item.getWidget(), reverse=False)
		# --------
		# pluginsTextStatusIcon:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		item = CheckOptionUI(
			option=conf.pluginsTextStatusIcon,
			label=_("Show Plugins Text in Status Icon (for today)"),
		)
		self.uiOptionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# --------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(
			label='<span font_size="small">'
			+ _(
				"To enable/disables events in status icon:\n"
				"Event Manager → Group → Edit → Show in",
			)
			+ "</span>",
		)
		label.set_use_markup(True)
		pack(hbox, label)
		pack(pageVBox, hbox)
		# --------
		page = StackPage()
		page.pageParent = ""
		page.pageWidget = pageVBox
		page.pageName = "statusIcon"
		page.pageTitle = _("Status Icon")
		page.pageLabel = _("Status Icon")
		langExampleIcon = f"status-icon-example-{locale_man.langSh}.svg"
		if isfile(join(svgDir, langExampleIcon)):
			page.pageIcon = langExampleIcon
		else:
			page.pageIcon = "status-icon-example.svg"
		self.prefPages.append(page)

	def _initPageAccounts(self) -> None:
		tab = PreferencesAccountsTab(window=self, spacing=self.spacing)
		self.accountsTab = tab
		self.prefPages.append(tab.page)

	@staticmethod
	def onMainVBoxRealize(_w: gtk.Widget) -> None:
		ud.windowList.updateCSS()

	@staticmethod
	def onClearImageCacheClick(_w: gtk.Widget) -> None:
		pixcache.clearFiles()
		pixcache.clear()

	def onPageButtonClicked(self, _w: gtk.Widget, page: StackPageType) -> None:
		self.stack.gotoPage(page.pagePath)

	def newWideButton(self, page: StackPageType) -> gtk.Button:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=self.spacing)
		hbox.set_border_width(self.spacing)
		label = gtk.Label(label=page.pageLabel)
		label.set_use_underline(True)
		pack(hbox, gtk.Label(), 1, 1)
		iconSize = page.iconSize or self.stack.iconSize()
		if page.pageIcon and conf.buttonIconEnable.v:
			pack(hbox, imageFromFile(page.pageIcon, iconSize))
		pack(hbox, label, 0, 0)
		pack(hbox, gtk.Label(), 1, 1)
		button = gtk.Button()
		button.add(hbox)

		button.connect("clicked", self.onPageButtonClicked, page)
		return button

	def comboFirstWDChanged(self, _combo: gtk.Widget) -> None:
		f = self.comboFirstWD.get_active()  # 0 means Sunday
		if f == 7:  # auto
			with suppress(Exception):
				f = getLocaleFirstWeekDay()
		# core.firstWeekDay.v will be later = f
		self.holiWDItem.setStart(f)

	def onDelete(
		self,
		_widget: gtk.Widget | None = None,
		_data: Any = None,
	) -> bool:
		self.hide()
		return True

	def onKeyPress(self, _arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if gdk.keyval_name(gevent.keyval) == "Escape":
			self.hide()
			return True
		return False

	def ok(self, _w: gtk.Widget) -> None:
		self.hide()

		self.apply()

	def cancel(self, _w: gtk.Widget) -> None:
		self.hide()
		self.updatePrefGui()

	def iterAllOptionUIs(self) -> typing.Iterable[OptionUI]:
		import itertools

		assert self.loggerOptionUI is not None
		return itertools.chain(
			[self.loggerOptionUI],
			self.moduleOptions,
			self.localeOptionUIs,
			self.coreOptionUIs,
			self.uiOptionUIs,
			self.gtkOptionUIs,
		)

	def apply(self, _w: gtk.Widget | None = None) -> None:
		from scal3.ui_gtk.font_utils import gfontDecode

		# log.debug(f"{ui.fontDefault=}")
		ui.fontDefault = gfontDecode(
			ud.settings.get_property("gtk-font-name"),
		)
		# log.debug(f"{ui.fontDefault=}")
		# -----
		conf.preferencesPagePath.v = self.stack.currentPagePath()
		# -----
		# -------------------- Updating pref variables ---------------------
		for option in self.iterAllOptionUIs():
			option.updateVar()
		# Plugin Manager
		self.pluginsTab.apply()
		# ------
		first = self.comboFirstWD.get_active()
		if first == 7:
			core.firstWeekDayAuto.v = True
			with suppress(Exception):
				core.firstWeekDay.v = getLocaleFirstWeekDay()
		else:
			core.firstWeekDayAuto.v = False
			core.firstWeekDay.v = first
		# ------
		weekNumberMode = self.comboWeekYear.get_active()
		# if weekNumberMode == 7:
		# core.weekNumberModeAuto = True
		# core.weekNumberMode = getLocaleWeekNumberMode()
		# else:
		core.weekNumberModeAuto.v = False
		core.weekNumberMode.v = weekNumberMode
		# ------
		ui.cells.clear()  # Very important
		# ^ specially when calTypes.primary will be changed
		# ------
		ud.updateFormatsBin()
		# ---------------------- Saving Preferences -----------------------
		# ------------------- Saving logger config
		assert self.loggerOptionUI is not None
		self.loggerOptionUI.save()
		# ------------------- Saving calendar types config
		for mod in calTypes:
			mod.save()
		# ------------------- Saving locale config
		locale_man.saveConf()
		# ------------------- Saving core config
		core.version.v = core.VERSION
		core.saveConf()
		# ------------------- Saving ui config
		ui.saveConf()
		# ------------------- Saving gtk_ud config
		ud.saveConf()
		# ----------------------- Updating GUI ---------------------------
		ud.windowList.onConfigChange()
		if self.checkNeedRestart():
			d = Dialog(
				title=_("Restart " + APP_DESC),
				transient_for=self,
				modal=True,
				destroy_with_parent=True,
			)
			dialog_add_button(
				d,
				res=gtk.ResponseType.CANCEL,
				imageName="dialog-cancel.svg",
				label=_("_No"),
			)
			d.set_keep_above(True)
			label = gtk.Label(
				label=(
					_(f"Some preferences need restarting {APP_DESC} to apply.")  # noqa: INT001
					+ " "
					+ _("Restart Now?")
				),
			)
			label.set_line_wrap(True)
			vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
			vbox.set_border_width(15)
			pack(vbox, label)
			pack(d.vbox, vbox)
			resBut = dialog_add_button(
				d,
				res=gtk.ResponseType.OK,
				imageName="view-refresh.svg",
				label=_("_Restart"),
			)
			resBut.grab_default()
			d.vbox.set_border_width(5)
			d.resize(400, 150)
			d.vbox.show_all()
			if d.run() == gtk.ResponseType.OK:
				core.restart()
			else:
				d.destroy()

	def checkNeedRestart(self) -> bool:
		if ui.mainWin is None:
			return False
		if ui.checkNeedRestart():
			return True
		return logger.logLevel != self.initialLogLevel

	def refreshAccounts(self) -> None:
		self.accountsTab.refreshAccounts()

	def updatePrefGui(self) -> None:
		# Updating Pref Gui (NOT MAIN GUI)
		for opt in self.iterAllOptionUIs():
			opt.updateWidget()
		# -------------------------------
		if core.firstWeekDayAuto.v:
			self.comboFirstWD.set_active(7)
		else:
			self.comboFirstWD.set_active(core.firstWeekDay.v)
		if core.weekNumberModeAuto.v:
			self.comboWeekYear.set_active(8)
		else:
			self.comboWeekYear.set_active(core.weekNumberMode.v)
		# Plugin Manager
		self.pluginsTab.updateGui()
		# Accounts
		self.refreshAccounts()


if __name__ == "__main__":
	dialog = PreferencesWindow()
	dialog.updatePrefGui()
	dialog.present()
