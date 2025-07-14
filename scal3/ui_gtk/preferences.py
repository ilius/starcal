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
from scal3.app_info import APP_DESC
from scal3.ui_gtk.cal_type_option_ui import ModuleOptionButton, ModuleOptionUI

log = logger.get()

import typing
from contextlib import suppress
from os.path import isfile, join

from scal3 import core, locale_man, plugin_man, ui
from scal3.cal_types import calTypes
from scal3.event_lib import ev
from scal3.locale_man import getLocaleFirstWeekDay, langSh
from scal3.locale_man import tr as _
from scal3.path import sourceDir, svgDir
from scal3.ui import conf
from scal3.ui_gtk import Dialog, Menu, gdk, gtk, pack, pixcache
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.log_pref import LogLevelOptionUI
from scal3.ui_gtk.menuitems import ImageMenuItem
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
	OptionUI,
	WidthHeightOptionUI,
)
from scal3.ui_gtk.option_ui_extra import (
	ActiveInactiveCalsOptionUI,
	CheckStartupOptionUI,
	LangOptionUI,
	WeekDayCheckListOptionUI,
)
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.toolbox import ToolBoxItem, VerticalStaticToolBox
from scal3.ui_gtk.utils import (
	confirm,
	dialog_add_button,
	imageFromFile,
	labelImageButton,
	newAlignLabel,
	newHSep,
	openWindow,
	showError,
)

if typing.TYPE_CHECKING:
	from scal3.pytypes import PluginType
	from scal3.ui_gtk.pytypes import StackPageType

__all__ = ["PreferencesWindow"]


class PreferencesPluginsToolbar(VerticalStaticToolBox):
	def __init__(self, parent: PreferencesWindow) -> None:
		VerticalStaticToolBox.__init__(
			self,
			parent,
			# buttonBorder=0,
			# buttonPadding=0,
		)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		self.extend(
			[
				ToolBoxItem(
					name="goto-top",
					imageName="go-top.svg",
					onClick=parent.plugTreeviewTop,
					desc=_("Move to top"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick=parent.plugTreeviewUp,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick=parent.plugTreeviewDown,
					desc=_("Move down"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="goto-bottom",
					imageName="go-bottom.svg",
					onClick=parent.plugTreeviewBottom,
					desc=_("Move to bottom"),
					continuousClick=False,
				),
			],
		)
		self.buttonAdd = self.append(
			ToolBoxItem(
				name="add",
				imageName="list-add.svg",
				onClick=parent.onPlugAddClick,
				desc=_("Add"),
				continuousClick=False,
			),
		)
		self.buttonAdd.w.set_sensitive(False)
		self.append(
			ToolBoxItem(
				name="delete",
				imageName="edit-delete.svg",
				onClick=parent.onPlugDeleteClick,
				desc=_("Delete"),
				continuousClick=False,
			),
		)

	def setCanAdd(self, canAdd: bool) -> None:
		self.buttonAdd.w.set_sensitive(canAdd)


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
		self.defaultWidget = button
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
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=self.spacing)
		vbox.set_border_width(int(self.spacing / 2))
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "lang_calTypes"
		page.pageTitle = _("Language and Calendar Types")
		page.pageLabel = _("_Language and Calendar Types")
		page.pageIcon = "preferences-desktop-locale.png"
		self.prefPages.append(page)
		# --------------------------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		pack(hbox, gtk.Label(label=_("Language")))
		itemLang = LangOptionUI()
		self.localeOptionUIs.append(itemLang)
		# ---
		pack(hbox, itemLang.getWidget())
		if langSh != "en":
			pack(hbox, gtk.Label(label="Language"))
		pack(vbox, hbox)
		# --------------------------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		frame = gtk.Frame()
		frame.set_label(_("Calendar Types"))
		itemCals = ActiveInactiveCalsOptionUI()
		self.coreOptionUIs.append(itemCals)
		itemCalsWidget = itemCals.getWidget()
		assert isinstance(itemCalsWidget, gtk.Container), f"{itemCalsWidget=}"
		itemCalsWidget.set_border_width(10)
		frame.add(itemCalsWidget)
		pack(hbox, frame, 1, 1)
		hbox.set_border_width(5)
		frame.set_border_width(0)
		pack(vbox, hbox, 1, 1)

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
			optionUI: typing.Any
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
		vbox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL, spacing=int(self.spacing / 2)
		)
		page = StackPage()
		vbox.set_border_width(int(self.spacing / 2))
		page.pageWidget = vbox
		page.pageName = "plugins"
		page.pageTitle = _("Plugins")
		page.pageLabel = _("_Plugins")
		page.pageIcon = "preferences-plugin.svg"
		self.prefPages.append(page)
		# -----
		treev = gtk.TreeView()
		treev.set_headers_clickable(True)
		listStore = self.plugListStore = gtk.ListStore(
			int,  # index
			bool,  # enable
			bool,  # show_date
			str,  # title
		)
		treev.set_model(listStore)
		treev.enable_model_drag_source(
			gdk.ModifierType.BUTTON1_MASK,
			[
				gtk.TargetEntry.new("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.enable_model_drag_dest(
			[
				gtk.TargetEntry.new("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.connect("drag_data_received", self.plugTreevDragReceived)
		treev.get_selection().connect("changed", self.plugTreevCursorChanged)
		treev.connect("row-activated", self.plugTreevRActivate)
		treev.connect("button-press-event", self.plugTreevButtonPress)
		# ---
		# treev.drag_source_add_text_targets()
		# treev.drag_source_add_uri_targets()
		# treev.drag_source_unset()
		# ---
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(
			gtk.PolicyType.AUTOMATIC,
			gtk.PolicyType.AUTOMATIC,
		)
		# ------
		# each named font size if 1.2 times larger than last
		# size='medium' is the same as not having this tag (equal to widget's font)
		# so size='large' is 1.2 times larger and size='small' is 1.2 times
		# smaller than default
		# font='12.5' is equal to size='12800' because 12.5*1024 = 12800
		# named sizes:
		#   xx-small	= default * 0.5787
		#   x-small		= default * 0.6944
		#   small		= default * 0.8333
		#   medium		= default * 1.0
		#   large		= default * 1.2
		#   x-large		= default * 1.44
		#   xx-large	= default * 1.7279
		# ------
		size = ui.getFont().size
		cell: gtk.CellRenderer
		# ------
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.plugTreeviewCellToggled)
		titleLabel = gtk.Label(
			label=f"<span font='{size * 0.7}'>" + _("Enable") + "</span>",
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
		# ------
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.plugTreeviewCellToggled2)
		titleLabel = gtk.Label(
			label=f"<span font='{size * 0.5}'>" + _("Show\nDate") + "</span>",
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
		# ------
		# cell = gtk.CellRendererText()
		# col = gtk.TreeViewColumn(title=_("File Name"), cell_renderer=cell, text=2)
		# col.set_resizable(True)
		# treev.append_column(col)
		# treev.set_search_column(1)
		# ------
		cell = gtk.CellRendererText()
		# cell.set_property("wrap-mode", gtk.WrapMode.WORD)
		# cell.set_property("editable", True)
		# cell.set_property("wrap-width", 200)
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=3)
		# treev.connect("draw", self.plugTreevExpose)
		# self.plugTitleCell = cell
		# self.plugTitleCol = col
		# col.set_resizable(True)-- No need!
		col.set_property("expand", True)
		treev.append_column(col)
		# ------
		# for i in xrange(len(core.plugIndex.v)):
		# 	x = core.plugIndex.v[i]
		# 	treeModel.append([x[0], x[1], x[2], .v[x[0]].title])
		# ------
		self.plugTreeview = treev
		# -----------------------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		vboxPlug = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(vboxPlug, swin, 1, 1)
		pack(hbox, vboxPlug, 1, 1)
		# ---
		aboutHbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# ---
		button = labelImageButton(
			label=_("_About Plugin"),
			imageName="dialog-information.svg",
		)
		button.set_sensitive(False)
		button.connect("clicked", self.onPlugAboutClick)
		self.plugButtonAbout = button
		pack(aboutHbox, button)
		pack(aboutHbox, gtk.Label(), 1, 1)
		# ---
		button = labelImageButton(
			label=_("C_onfigure Plugin"),
			imageName="preferences-system.svg",
		)
		button.set_sensitive(False)
		button.connect("clicked", self.onPlugConfClick)
		self.plugButtonConf = button
		pack(aboutHbox, button)
		pack(aboutHbox, gtk.Label(), 1, 1)
		# ---
		pack(vboxPlug, aboutHbox)
		# ---
		toolbar = PreferencesPluginsToolbar(self)
		pack(hbox, toolbar.w)
		self.pluginsToolbar = toolbar
		# -----
		"""
		vpan = gtk.VPaned()
		vpan.add1(hbox)
		vbox2 gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(vbox2, gtk.Label(label="Test Label"))
		vpan.add2(vbox2)
		vpan.set_position(100)
		pack(vbox, vpan)
		"""
		pack(vbox, hbox, 1, 1)
		# --------------------------
		d = Dialog(transient_for=self)
		d.set_transient_for(self)
		# dialog.set_transient_for(parent) makes the window on top of parent
		# and at the center point of parent
		# but if you call dialog.show() or dialog.present(), the parent is
		# still active(clickabel widgets) before closing child "dialog"
		# you may call dialog.run() to realy make it transient for parent
		# d.set_has_separator(False)
		d.connect("delete-event", self.plugAddDialogDeleteEvent)
		d.set_title(_("Add Plugin"))
		# ---
		dialog_add_button(
			d,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			onClick=self.plugAddDialogClose,
		)
		dialog_add_button(
			d,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Choose"),
			onClick=self.plugAddDialogOK,
		)
		# ---
		treev = gtk.TreeView()
		listStore = gtk.ListStore(str)
		treev.set_model(listStore)
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
		# ----
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=0)
		# col.set_resizable(True)# no need when have only one column!
		treev.append_column(col)
		# ----
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(d.vbox, swin, 1, 1)
		d.vbox.show_all()
		self.plugAddDialog = d
		self.plugAddTreeview = treev
		self.plugAddTreeModel = listStore
		# -------------
		# treev.set_resize_mode(gtk.RESIZE_IMMEDIATE)
		# self.plugAddItems = []

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
		vbox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL, spacing=int(self.spacing / 2)
		)
		vbox.set_border_width(int(self.spacing / 2))
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "accounts"
		page.pageTitle = _("Accounts")
		page.pageLabel = _("Accounts")
		page.pageIcon = "applications-development-web.png"
		self.prefPages.append(page)
		# -----
		treev = gtk.TreeView()
		treev.set_headers_clickable(True)
		treeModel = gtk.ListStore(int, bool, str)  # id (hidden), enable, title
		treev.set_model(treeModel)
		treev.enable_model_drag_source(
			gdk.ModifierType.BUTTON1_MASK,
			[
				gtk.TargetEntry.new("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.enable_model_drag_dest(
			[
				gtk.TargetEntry.new("row", gtk.TargetFlags.SAME_WIDGET, 0),
			],
			gdk.DragAction.MOVE,
		)
		treev.connect("row-activated", self.accountsTreevRActivate)
		treev.connect("button-press-event", self.accountsTreevButtonPress)
		# ---
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		cell: gtk.CellRenderer
		# ------
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.accountsTreeviewCellToggled)
		col = gtk.TreeViewColumn(title=_("Enable"), cell_renderer=cell)
		col.add_attribute(cell, "active", 1)
		# cell.set_active(False)
		col.set_resizable(True)
		col.set_property("expand", False)
		treev.append_column(col)
		# ------
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=2)
		col.set_property("expand", True)
		treev.append_column(col)
		# ------
		self.accountsTreeview = treev
		self.accountsTreeModel = treeModel
		# -----------------------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		vboxPlug = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(vboxPlug, swin, 1, 1)
		pack(hbox, vboxPlug, 1, 1)
		# -----
		toolbar = VerticalStaticToolBox(self)
		# -----
		toolbar.extend(
			[
				ToolBoxItem(
					name="register",
					imageName="starcal.svg",
					onClick=self.onAccountsRegisterClick,
					desc=_("Register at StarCalendar.net"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="add",
					imageName="list-add.svg",
					onClick=self.onAccountsAddClick,
					desc=_("Add"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="edit",
					imageName="document-edit.svg",
					onClick=self.onAccountsEditClick,
					desc=_("Edit"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="delete",
					imageName="edit-delete.svg",
					onClick=self.onAccountsDeleteClick,
					desc=_("Delete", ctx="button"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="moveUp",
					imageName="go-up.svg",
					onClick=self.onAccountsUpClick,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="moveDown",
					imageName="go-down.svg",
					onClick=self.onAccountsDownClick,
					desc=_("Move down"),
					continuousClick=False,
				),
			],
		)
		# -----------
		pack(hbox, toolbar.w)
		pack(vbox, hbox, 1, 1)

	@staticmethod
	def onMainVBoxRealize(_w: gtk.Widget) -> None:
		ud.windowList.updateCSS()

	@staticmethod
	def onClearImageCacheClick(_b: gtk.Widget) -> None:
		pixcache.clearFiles()
		pixcache.clear()

	def onPageButtonClicked(self, _b: gtk.Widget, page: StackPageType) -> None:
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
		_data: typing.Any = None,
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

	@staticmethod
	def loadPlugin(plug: PluginType, plugI: int) -> PluginType:
		plug2 = plugin_man.loadPlugin(plug.file, enable=True)
		if plug2:
			assert plug2.loaded
		core.allPlugList.v[plugI] = plug2
		return plug

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
		index = []
		for row in self.plugListStore:
			plugI = row[0]
			enable = row[1]
			show_date = row[2]
			index.append(plugI)
			plug = core.allPlugList.v[plugI]
			if plug.loaded:
				try:
					plug.enable = enable
					plug.show_date = show_date
				except NameError:
					core.log.exception("")
					log.info(f"plugIndex = {core.plugIndex.v}")
			elif enable:
				plug = self.loadPlugin(plug, plugI)
		core.plugIndex.v = index
		core.updatePlugins()
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
		self.accountsTreeModel.clear()
		for account in ev.accounts:
			self.accountsTreeModel.append(
				[
					account.id,
					account.enable,
					account.title,
				],
			)

	def updatePrefGui(self) -> None:  # Updating Pref Gui (NOT MAIN GUI)
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
		model = self.plugListStore
		model.clear()
		for p in core.getPluginsTable():
			model.append(
				[
					p.idx,
					p.enable,
					p.show_date,
					p.title,
				],
			)
		self.plugAddItems = []
		self.plugAddTreeModel.clear()
		for i, title in core.getDeletedPluginsTable():
			self.plugAddItems.append(i)
			self.plugAddTreeModel.append([title])
			self.pluginsToolbar.setCanAdd(True)
		# Accounts
		self.refreshAccounts()

	# def plugTreevExpose(self, widget: gtk.Widget, gevent: gdk.Event):
	# 	self.plugTitleCell.set_property(
	# 		"wrap-width",
	# 		self.plugTitleCol.get_width() + 2
	# 	)

	def plugTreevCursorChanged(
		self,
		_selection: gtk.SelectionData | None = None,
	) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		model = self.plugListStore
		j = model[index][0]
		plug = core.allPlugList.v[j]
		self.plugButtonAbout.set_sensitive(bool(plug.about))
		self.plugButtonConf.set_sensitive(plug.hasConfig)

	def onPlugAboutClick(self, _w: gtk.Widget | None = None) -> None:
		from scal3.ui_gtk.about import AboutDialog

		cur: gtk.TreePath = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		model = self.plugListStore
		pIndex = model[index][0]
		plug = core.allPlugList.v[pIndex]
		# open_about returns True only if overriden by external plugin
		if plug.open_about():
			return
		if plug.about is None:
			return
		about = AboutDialog(
			# name="",  # FIXME
			title=_("About Plugin"),  # _("About ") + plug.title
			authors=plug.authors,
			comments=plug.about,
		)
		about.set_transient_for(self)
		about.connect("delete-event", lambda w, _e: w.destroy())
		about.connect("response", lambda w, _e: w.destroy())
		# about.set_resizable(True)
		# about.vbox.show_all()  # OR about.vbox.show_all() ; about.run()
		openWindow(about)  # FIXME

	def onPlugConfClick(self, _w: gtk.Widget | None = None) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		model = self.plugListStore
		pIndex = model[index][0]
		plug = core.allPlugList.v[pIndex]
		if not plug.hasConfig:
			return
		plug.open_configure()

	@staticmethod
	def onPlugExportToIcsClick(_w: gtk.Widget, plug: PluginType) -> None:
		from scal3.ui_gtk.export import ExportToIcsDialog

		ExportToIcsDialog(plug.exportToIcs, plug.title).run()  # type: ignore[no-untyped-call]

	def plugTreevRActivate(
		self,
		_treev: gtk.TreeView,
		_path: gtk.TreePath,
		col: gtk.TreeViewColumn,
	) -> None:
		if col.get_title() == _("Title"):  # FIXME
			self.onPlugAboutClick()

	def plugTreevButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		b = gevent.button
		if b != 3:
			return False
		cur = self.plugTreeview.get_cursor()[0]
		if not cur:
			return True
		index = cur.get_indices()[0]
		pIndex = self.plugListStore[index][0]
		plug = core.allPlugList.v[pIndex]
		menu = Menu()
		# --
		item = ImageMenuItem(
			_("_About"),
			imageName="dialog-information.svg",
			func=self.onPlugAboutClick,
		)
		item.set_sensitive(bool(plug.about))
		menu.add(item)
		# --
		item = ImageMenuItem(
			_("_Configure"),
			imageName="preferences-system.svg",
			func=self.onPlugConfClick,
		)
		item.set_sensitive(plug.hasConfig)
		menu.add(item)

		# --
		def onPlugExportToIcsClick(w: gtk.Widget) -> None:
			self.onPlugExportToIcsClick(w, plug)

		menu.add(
			ImageMenuItem(
				_("Export to {format}").format(format="iCalendar"),
				imageName="text-calendar-ics.png",
				func=onPlugExportToIcsClick,
			),
		)
		# --
		menu.show_all()
		self.tmpMenu = menu
		menu.popup(None, None, None, None, 3, gevent.time)
		return True

	def onPlugAddClick(self, _b: gtk.Widget) -> None:
		# FIXME
		# Reize window to show all texts
		# self.plugAddTreeview.columns_autosize()  # FIXME
		column = self.plugAddTreeview.get_column(0)
		assert column is not None
		_x, _y, w, _h = column.cell_get_size()
		# log.debug(x, y, w, h)
		self.plugAddDialog.resize(
			w + 30,
			75 + 30 * len(self.plugAddTreeModel),
		)
		# ---------------
		self.plugAddDialog.run()
		self.pluginsToolbar.setCanAdd(len(self.plugAddItems) > 0)

	def plugAddDialogDeleteEvent(
		self,
		_widget: gtk.Widget,
		_gevent: gdk.Event,
	) -> bool:
		self.plugAddDialog.hide()
		return True

	def plugAddDialogClose(
		self,
		_widget: gtk.Widget,
	) -> None:
		self.plugAddDialog.hide()

	def plugTreeviewCellToggled(
		self,
		cell: gtk.CellRendererToggle,
		path: str,
	) -> None:
		model = self.plugListStore
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 1, active)
		if active:
			plugI = model[path][0]
			plug = core.allPlugList.v[plugI]
			if not plug.loaded:
				plug = self.loadPlugin(plug, plugI)
			self.plugTreevCursorChanged()

	def plugTreeviewCellToggled2(
		self,
		cell: gtk.CellRendererToggle,
		path: str,
	) -> None:
		model = self.plugListStore
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 2, active)

	def plugSetCursor(self, index: int) -> None:
		self.plugTreeview.set_cursor(gtk.TreePath.new_from_indices([index]))

	def plugTreeviewTop(self, _b: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		if index <= 0 or index >= len(listStore):
			gdk.beep()
			return
		listStore.prepend(list(listStore[index]))  # type: ignore[call-overload]
		listStore.remove(listStore.get_iter(str(index + 1)))
		self.plugSetCursor(0)

	def plugTreeviewBottom(self, _b: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		if index < 0 or index >= len(listStore) - 1:
			gdk.beep()
			return
		listStore.append(list(listStore[index]))  # type: ignore[call-overload]
		listStore.remove(listStore.get_iter(str(index)))
		self.plugSetCursor(len(listStore) - 1)

	def plugTreeviewUp(self, _b: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		if index <= 0 or index >= len(listStore):
			gdk.beep()
			return
		listStore.swap(
			listStore.get_iter(str(index - 1)),
			listStore.get_iter(str(index)),
		)
		self.plugSetCursor(index - 1)

	def plugTreeviewDown(self, _b: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		if index < 0 or index >= len(listStore) - 1:
			gdk.beep()
			return
		listStore.swap(
			listStore.get_iter(str(index)),
			listStore.get_iter(str(index + 1)),
		)
		self.plugSetCursor(index + 1)

	def plugTreevDragReceived(
		self,
		treev: gtk.TreeView,
		_context: gdk.DragContext,
		x: int,
		y: int,
		_selection: gtk.SelectionData,
		_target_id: int,
		_etime: int,
	) -> None:
		t = self.plugListStore
		cur = treev.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		dest = treev.get_dest_row_at_pos(x, y)
		if dest is None:
			t.move_after(
				t.get_iter(str(index)),
				t.get_iter(str(len(t) - 1)),
			)
		elif dest[1] in {
			gtk.TreeViewDropPosition.BEFORE,
			gtk.TreeViewDropPosition.INTO_OR_BEFORE,
		}:
			t.move_before(
				t.get_iter(str(index)),
				t.get_iter(str(dest[0].get_indices()[0])),
			)
		else:
			t.move_after(
				t.get_iter(str(index)),
				t.get_iter(str(dest[0].get_indices()[0])),
			)

	def onPlugDeleteClick(self, _b: gtk.Widget) -> None:
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		listStore = self.plugListStore
		n = len(listStore)
		if index < 0 or index >= n:
			gdk.beep()
			return
		j = listStore[index][0]
		listStore.remove(listStore.get_iter(str(index)))
		# j is index of deleted plugin
		self.plugAddItems.append(j)
		title = core.allPlugList.v[j].title
		self.plugAddTreeModel.append([title])
		log.debug(f"deleting {title}")
		self.pluginsToolbar.setCanAdd(True)
		if n > 1:
			self.plugSetCursor(min(n - 2, index))

	def plugAddDialogOK(self, _w: gtk.Widget | None) -> None:
		cur = self.plugAddTreeview.get_cursor()[0]
		if cur is None:
			gdk.beep()
			return
		index = cur.get_indices()[0]
		j = self.plugAddItems[index]
		cur2 = self.plugTreeview.get_cursor()[0]
		if cur2 is None:
			pos = len(self.plugListStore)
		else:
			pos = cur2.get_indices()[0] + 1
		plug = core.allPlugList.v[j]
		if plug is None:
			log.error("plug is None")
			return
		self.plugListStore.insert(  # type: ignore[no-untyped-call]
			pos,
			[
				j,
				True,
				False,
				plug.title,
			],
		)
		self.plugAddTreeModel.remove(self.plugAddTreeModel.get_iter(str(index)))
		self.plugAddItems.pop(index)
		self.plugAddDialog.hide()
		self.plugSetCursor(pos)  # pos == -1 # FIXME

	def plugAddTreevRActivate(
		self,
		_treev: gtk.TreeView,
		_path: gtk.TreePath,
		_col: gtk.TreeViewColumn,
	) -> None:
		self.plugAddDialogOK(None)  # FIXME

	def editAccount(self, index: int) -> None:
		from scal3.ui_gtk.event.account_op import AccountEditorDialog

		accountId = self.accountsTreeModel[index][0]
		account = ev.accounts[accountId]
		if not account.loaded:
			showError(_("Account must be enabled before editing"), transient_for=self)
			return
		accountNew = AccountEditorDialog(account, transient_for=self).run2()
		if accountNew is None:
			return
		accountNew.save()
		ev.accounts.save()
		self.accountsTreeModel[index][2] = accountNew.title

	def onAccountsEditClick(self, _b: gtk.Widget) -> None:
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		self.editAccount(index)

	def onAccountsRegisterClick(self, _b: gtk.Widget) -> None:
		from scal3.ui_gtk.event.register_starcal import StarCalendarRegisterDialog

		win = StarCalendarRegisterDialog(transient_for=self)
		win.run()  # type: ignore[no-untyped-call]

	def onAccountsAddClick(self, _b: gtk.Widget) -> None:
		from scal3.ui_gtk.event.account_op import AccountEditorDialog

		account = AccountEditorDialog(transient_for=self).run2()
		if account is None:
			return
		account.save()
		ev.accounts.append(account)
		ev.accounts.save()
		self.accountsTreeModel.append(
			[
				account.id,
				account.enable,
				account.title,
			],
		)
		# ---
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		try:
			account.fetchGroups()
		except Exception as e:
			log.error(f"error in fetchGroups: {e}")
			return
		account.save()

	def onAccountsDeleteClick(self, _b: gtk.Widget) -> None:
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		accountId = self.accountsTreeModel[index][0]
		account = ev.accounts[accountId]
		if not confirm(
			_('Do you want to delete account "{accountTitle}"').format(
				accountTitle=account.title,
			),
			transient_for=self,
		):
			return
		ev.accounts.delete(account)
		ev.accounts.save()
		del self.accountsTreeModel[index]

	def accountSetCursor(self, index: int) -> None:
		self.accountsTreeview.set_cursor(gtk.TreePath.new_from_indices([index]))

	def onAccountsUpClick(self, _b: gtk.Widget) -> None:
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		t = self.accountsTreeModel
		if index <= 0 or index >= len(t):
			gdk.beep()
			return
		ev.accounts.moveUp(index)
		ev.accounts.save()
		t.swap(
			t.get_iter(str(index - 1)),
			t.get_iter(str(index)),
		)
		self.accountSetCursor(index - 1)

	def onAccountsDownClick(self, _b: gtk.Widget) -> None:
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur.get_indices()[0]
		t = self.accountsTreeModel
		if index < 0 or index >= len(t) - 1:
			gdk.beep()
			return
		ev.accounts.moveDown(index)
		ev.accounts.save()
		t.swap(t.get_iter(str(index)), t.get_iter(str(index + 1)))
		self.accountSetCursor(index + 1)

	def accountsTreevRActivate(
		self,
		_treev: gtk.TreeView,
		path: gtk.TreePath,
		_col: gtk.TreeViewColumn,
	) -> None:
		index = path.get_indices()[0]
		self.editAccount(index)

	@staticmethod
	def accountsTreevButtonPress(_widget: gtk.Widget, gevent: gdk.EventButton) -> bool:
		b = gevent.button
		if b == 3:  # noqa: SIM103
			# FIXME
			# cur = self.accountsTreeview.get_cursor()[0]
			# if cur:
			# 	index = cur[0]
			# 	accountId = self.accountsTreeModel[index][0]
			# 	account = ev.accounts[accountId]
			# 	menu = Menu()
			# 	#
			# 	menu.show_all()
			# 	self.tmpMenu = menu
			# 	menu.popup(None, None, None, None, 3, gevent.time)
			return True
		return False

	def accountsTreeviewCellToggled(
		self,
		cell: gtk.CellRendererToggle,
		path: gtk.TreePath,
	) -> None:
		index = path.get_indices()[0]
		active = not cell.get_active()
		# ---
		accountId = self.accountsTreeModel[index][0]
		account = ev.accounts[accountId]
		# not account.loaded -> it's a dummy account
		if active and not account.loaded:
			account = ev.accounts.replaceDummyObj(account)
			if account is None:
				return
		account.enable = active
		account.save()
		# ---
		self.accountsTreeModel[index][1] = active


if __name__ == "__main__":
	dialog = PreferencesWindow()
	dialog.updatePrefGui()
	dialog.present()
