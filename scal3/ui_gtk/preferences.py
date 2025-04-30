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

log = logger.get()


import typing
from contextlib import suppress
from os.path import join

from scal3 import core, locale_man, plugin_man, ui
from scal3.cal_types import calTypes
from scal3.locale_man import getLocaleFirstWeekDay, langSh
from scal3.locale_man import tr as _
from scal3.path import (
	sourceDir,
)
from scal3.ui import conf
from scal3.ui_gtk import HBox, Menu, VBox, gdk, gtk, pack, pixcache
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.log_pref import LogLevelPrefItem
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.pref_utils import (
	CheckColorPrefItem,
	CheckPrefItem,
	ColorPrefItem,
	ComboEntryTextPrefItem,
	FontFamilyPrefItem,
	FontPrefItem,
	ImageFileChooserPrefItem,
	ModuleOptionButton,
	ModuleOptionItem,
	SpinPrefItem,
	WidthHeightPrefItem,
)
from scal3.ui_gtk.pref_utils_extra import (
	AICalsPrefItem,
	CheckStartupPrefItem,
	LangPrefItem,
	WeekDayCheckListPrefItem,
)
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.toolbox import (
	StaticToolBox,
	ToolBoxItem,
)
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
	from scal3.plugin_type import PluginType

__all__ = ["PreferencesWindow"]


class PreferencesPluginsToolbar(StaticToolBox):
	def __init__(self, parent):
		StaticToolBox.__init__(
			self,
			parent,
			vertical=True,
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
					onClick="plugTreeviewTop",
					desc=_("Move to top"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick="plugTreeviewUp",
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick="plugTreeviewDown",
					desc=_("Move down"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="goto-bottom",
					imageName="go-bottom.svg",
					onClick="plugTreeviewBottom",
					desc=_("Move to bottom"),
					continuousClick=False,
				),
			],
		)
		self.buttonAdd = self.append(
			ToolBoxItem(
				name="add",
				imageName="list-add.svg",
				onClick="onPlugAddClick",
				desc=_("Add"),
				continuousClick=False,
			),
		)
		self.buttonAdd.set_sensitive(False)
		self.append(
			ToolBoxItem(
				name="delete",
				imageName="edit-delete.svg",
				onClick="onPlugDeleteClick",
				desc=_("Delete"),
				continuousClick=False,
			),
		)

	def setCanAdd(self, canAdd: bool):
		self.buttonAdd.set_sensitive(canAdd)


class PreferencesWindow(gtk.Window):
	mainGridStyleClass = "preferences-main-grid"

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		return ".preferences-main-grid " + cssTextStyle(
			font=ui.getFont(scale=1.5),
		)

	def __init__(self, **kwargs):
		gtk.Window.__init__(self, **kwargs)
		self.set_title(_("Preferences"))
		self.set_position(gtk.WindowPosition.CENTER)
		self.connect("delete-event", self.onDelete)
		self.connect("key-press-event", self.onKeyPress)
		# self.set_has_separator(False)
		# self.set_skip_taskbar_hint(True)
		# ---
		self.spacing = ui.getFont().size
		self.mainGridSpacing = ui.getFont(scale=0.8).size
		# ---
		self.vbox = VBox()
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
		self.loggerPrefItem = None
		self.localePrefItems = []
		self.corePrefItems = []
		self.uiPrefItems = []
		self.gtkPrefItems = []  # FIXME
		# -----
		self.prefPages = []
		# ----------------------------------------------
		stack = MyStack(
			iconSize=conf.stackIconSize,
		)
		stack.setTitleFontSize("large")
		stack.setTitleCentered(True)
		stack.setupWindowTitle(self, _("Preferences"), False)
		self.stack = stack
		# --------------- Page 0 (Language and Calendar Types) ----------------
		vbox = VBox(spacing=self.spacing)
		vbox.set_border_width(self.spacing / 2)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "lang_calTypes"
		page.pageTitle = _("Language and Calendar Types")
		page.pageLabel = _("_Language and Calendar Types")
		page.pageIcon = "preferences-desktop-locale.png"
		self.prefPages.append(page)
		# --------------------------
		hbox = HBox(spacing=self.spacing / 2)
		pack(hbox, gtk.Label(label=_("Language")))
		itemLang = LangPrefItem()
		self.localePrefItems.append(itemLang)
		# ---
		pack(hbox, itemLang.getWidget())
		if langSh != "en":
			pack(hbox, gtk.Label(label="Language"))
		pack(vbox, hbox)
		# --------------------------
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
		# ------------------------------ Page 1 (General) ---------------------
		vbox = VBox(spacing=self.spacing)
		vbox.set_border_width(self.spacing / 2)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "general"
		page.pageTitle = _("General")
		page.pageLabel = _("_General")
		page.pageIcon = "preferences-system.svg"
		self.prefPages.append(page)
		# --------------------------
		hbox = HBox(spacing=self.spacing / 2)
		item = CheckStartupPrefItem()
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------------------------
		item = CheckPrefItem(
			conf,
			"showMain",
			_("Open main window on start"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		# ------------------------
		item = CheckPrefItem(
			conf,
			"showDesktopWidget",
			_("Open desktop widget on start"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		# --------------------------
		item = CheckPrefItem(
			conf,
			"winTaskbar",
			_("Window in Taskbar"),
		)
		self.uiPrefItems.append(item)
		hbox = HBox(spacing=self.spacing / 2)
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
			item = CheckPrefItem(
				conf,
				"useAppIndicator",
				_("Use AppIndicator"),
			)
			self.uiPrefItems.append(item)
			hbox = HBox(spacing=self.spacing / 2)
			pack(hbox, item.getWidget())
			pack(hbox, gtk.Label(), 1, 1)
			pack(vbox, hbox)
		# --------------------------
		# hbox = HBox(spacing=self.spacing/2)
		# pack(hbox, gtk.Label(label=_("Show Digital Clock:")))
		# pack(hbox, gtk.Label(), 1, 1)
		# #item = CheckPrefItem(
		# #	conf,
		# #	"showDigClockTb",
		# #	_("On Toolbar"),
		# #)  # FIXME
		# #self.uiPrefItems.append(item)
		# #pack(hbox, item.getWidget())
		# pack(hbox, gtk.Label(), 1, 1)
		# item = CheckPrefItem(
		# 	conf,
		# 	"showDigClockTr",
		# 	_("On Status Icon"),
		# 	"Notification Area",
		# )
		# self.uiPrefItems.append(item)
		# pack(hbox, item.getWidget())
		# pack(hbox, gtk.Label(), 1, 1)
		# pack(vbox, hbox)
		# ------------------------------ Page 2 (Appearance) ------------------
		vbox = VBox(spacing=self.spacing)
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
		padding = self.spacing / 2
		# ---
		hbox = HBox(spacing=self.spacing / 2)
		# ---
		customCheckItem = CheckPrefItem(
			conf,
			"fontCustomEnable",
			_("Application Font"),
		)
		self.uiPrefItems.append(customCheckItem)
		pack(hbox, customCheckItem.getWidget())
		# ---
		customItem = FontPrefItem(conf, "fontCustom")
		self.uiPrefItems.append(customItem)
		pack(hbox, customItem.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		customCheckItem.syncSensitive(customItem.getWidget())
		pack(vbox, hbox, padding=padding)
		# ---------------------------
		item = CheckPrefItem(
			conf,
			"buttonIconEnable",
			_("Show icons in buttons"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		# ---------------------------
		item = CheckPrefItem(
			conf,
			"useSystemIcons",
			_("Use System Icons"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		# ---------------------------
		item = CheckPrefItem(
			conf,
			"oldStyleProgressBar",
			_("Old-style Progress Bar"),
		)
		self.uiPrefItems.append(item)
		pack(vbox, item.getWidget())
		# ------------------------- Theme ---------------------
		pageHBox = HBox()
		pageHBox.set_border_width(self.spacing)
		spacing = self.spacing / 3
		# ---
		pageVBox = VBox()
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ---
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Background")))
		item = ColorPrefItem(conf, "bgColor", True)
		self.uiPrefItems.append(item)
		self.colorbBg = item.getWidget()  # FIXME
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Border")))
		item = ColorPrefItem(conf, "borderColor", True)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Cursor")))
		item = ColorPrefItem(conf, "cursorOutColor", False)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Cursor BG")))
		item = ColorPrefItem(conf, "cursorBgColor", True)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Today")))
		item = ColorPrefItem(conf, "todayCellColor", True)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ------
		pack(pageHBox, pageVBox, 1, 1)
		pack(pageHBox, newHSep(), 0, 0)
		pageVBox = VBox()
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ------
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Normal Text")))
		item = ColorPrefItem(conf, "textColor", False)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Holidays Font")))
		item = ColorPrefItem(conf, "holidayColor", False)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Inactive Day Font")))
		item = ColorPrefItem(conf, "inactiveColor", True)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = HBox(spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Border Font")))
		item = ColorPrefItem(conf, "borderTextColor", False)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		pack(pageHBox, pageVBox, 1, 1, padding=self.spacing / 2)
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
		# ------------------------------ Page 3 (Regional) -------------------
		vbox = VBox()
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
		# ------
		hbox = HBox(spacing=self.spacing)
		label = gtk.Label(label=_("Date Format"))
		pack(hbox, label)
		sgroup.add_widget(label)
		# pack(hbox, gtk.Label(), 1, 1)
		item = ComboEntryTextPrefItem(
			ud,
			"dateFormat",
			(
				"%Y/%m/%d",
				"%Y-%m-%d",
				"%y/%m/%d",
				"%y-%m-%d",
				"%OY/%Om/%Od",
				"%OY-%Om-%Od",
				"%m/%d",
				"%m/%d/%Y",
			),
		)
		self.gtkPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# --------------------------------
		hbox = HBox(spacing=self.spacing / 3)
		item = CheckPrefItem(
			locale_man,
			"enableNumLocale",
			_("Numbers Localization"),
		)
		self.localePrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(vbox, hbox, padding=self.spacing)
		# --------------------------------
		pageVBox = VBox(spacing=self.spacing / 2)
		# ----
		hbox = HBox(spacing=self.spacing / 3)
		pack(hbox, gtk.Label(label=_("First day of week")))
		# item = ComboTextPrefItem(  # FIXME
		self.comboFirstWD = gtk.ComboBoxText()
		for item in core.weekDayName:
			self.comboFirstWD.append_text(item)
		self.comboFirstWD.append_text(_("Automatic"))
		self.comboFirstWD.connect("changed", self.comboFirstWDChanged)
		pack(hbox, self.comboFirstWD)
		pack(pageVBox, hbox)
		# ---------
		hbox = HBox(spacing=self.spacing / 3)
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
			pageVBox = VBox(spacing=self.spacing)
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
			for opt in mod.options:
				if opt[0] == "button":
					try:
						optl = ModuleOptionButton(opt[1:])
					except Exception:
						log.exception("")
						continue
				else:
					optl = ModuleOptionItem(mod, opt, spacing=self.spacing)
				options.append(optl)
				pack(pageVBox, optl.getWidget())
			# -----
		# -----
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		# grid.set_row_spacing(self.spacing)
		for index, page in enumerate(regionalSubPages):
			button = self.newWideButton(page)
			button.set_border_width(self.spacing * 0.7)
			grid.attach(button, 0, index, 1, 1)
		grid.show_all()
		pack(vbox, grid)
		# ---
		self.moduleOptions = options
		# ------------------------------ Page 4 (Advanced) -------------------
		vbox = VBox(spacing=self.spacing)
		vbox.set_border_width(self.spacing / 2)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "advanced"
		page.pageTitle = _("Advanced")
		page.pageLabel = _("A_dvanced")
		page.pageIcon = "applications-system.svg"
		self.prefPages.append(page)
		# ------
		item = LogLevelPrefItem()
		self.loggerPrefItem = item
		pack(vbox, item.getWidget())
		# ---
		self.initialLogLevel = logger.logLevel
		# ------
		hbox = HBox(spacing=self.spacing / 2)
		# pack(hbox, gtk.Label(), 1, 1)
		label = gtk.Label(label=_("Event Time Format"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = ComboEntryTextPrefItem(
			conf,
			"eventDayViewTimeFormat",
			(
				"HM$",
				"HMS",
				"hMS",
				"hm$",
				"hms",
				"HM",
				"hm",
				"hM",
			),
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
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=self.spacing / 2)
		# pack(hbox, gtk.Label(), 1, 1)
		label = gtk.Label(label=_("Digital Clock Format"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = ComboEntryTextPrefItem(
			ud,
			"clockFormat",
			(
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
			),
		)
		self.gtkPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=self.spacing / 2)
		label = gtk.Label(label=_("Days maximum cache size"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = SpinPrefItem(conf, "maxDayCacheSize", 100, 9999, digits=0, step=10)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=self.spacing / 2)
		label = gtk.Label(label=_("Horizontal offset for day right-click menu"))
		pack(hbox, label)
		item = SpinPrefItem(conf, "cellMenuXOffset", 0, 999, digits=0, step=1)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(vbox, hbox)
		# ------
		hbox = HBox(spacing=self.spacing / 2)
		button = labelImageButton(
			label=_("Clear Image Cache"),
			# TODO: _("Clear Image Cache ({size})").format(size=""),
			imageName="sweep.svg",
		)
		button.connect("clicked", self.onClearImageCacheClick)
		pack(hbox, button)
		pack(vbox, hbox)
		# ------------------------------ Page 5 (Plugins) --------------------
		vbox = VBox(spacing=self.spacing / 2)
		page = StackPage()
		vbox.set_border_width(self.spacing / 2)
		page.pageWidget = vbox
		page.pageName = "plugins"
		page.pageTitle = _("Plugins")
		page.pageLabel = _("_Plugins")
		page.pageIcon = "preferences-plugin.svg"
		self.prefPages.append(page)
		# -----
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
		# for i in xrange(len(core.plugIndex)):
		# 	x = core.plugIndex[i]
		# 	treeModel.append([x[0], x[1], x[2], core.allPlugList[x[0]].title])
		# ------
		self.plugTreeview = treev
		# -----------------------
		hbox = HBox()
		vboxPlug = VBox()
		pack(vboxPlug, swin, 1, 1)
		pack(hbox, vboxPlug, 1, 1)
		# ---
		hboxBut = HBox()
		# ---
		button = labelImageButton(
			label=_("_About Plugin"),
			imageName="dialog-information.svg",
		)
		button.set_sensitive(False)
		button.connect("clicked", self.onPlugAboutClick)
		self.plugButtonAbout = button
		pack(hboxBut, button)
		pack(hboxBut, gtk.Label(), 1, 1)
		# ---
		button = labelImageButton(
			label=_("C_onfigure Plugin"),
			imageName="preferences-system.svg",
		)
		button.set_sensitive(False)
		button.connect("clicked", self.onPlugConfClick)
		self.plugButtonConf = button
		pack(hboxBut, button)
		pack(hboxBut, gtk.Label(), 1, 1)
		# ---
		pack(vboxPlug, hboxBut)
		# ---
		toolbar = PreferencesPluginsToolbar(self)
		pack(hbox, toolbar)
		self.pluginsToolbar = toolbar
		# -----
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
		# --------------------------
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
		# ---
		dialog_add_button(
			d,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
			onClick=self.plugAddDialogClose,
		)
		dialog_add_button(
			d,
			imageName="dialog-ok.svg",
			label=_("_Choose"),
			res=gtk.ResponseType.OK,
			onClick=self.plugAddDialogOK,
		)
		# ---
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
		self.plugAddTreeModel = treeModel
		# -------------
		# treev.set_resize_mode(gtk.RESIZE_IMMEDIATE)
		# self.plugAddItems = []
		# ------------------------------------- Page: Status Icon
		pageVBox = VBox(spacing=self.spacing * 0.8)
		pageVBox.set_border_width(self.spacing)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ----
		hbox = HBox(spacing=1)
		label = newAlignLabel(sgroup=sgroup, label=_("Normal Days"))
		pack(hbox, label)
		item = ImageFileChooserPrefItem(
			conf,
			"statusIconImage",
			title=_("Select Icon"),
			currentFolder=join(sourceDir, "status-icons"),
			defaultVarName="statusIconImageDefault",
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = HBox(spacing=1)
		label = newAlignLabel(sgroup=sgroup, label=_("Holidays"))
		pack(hbox, label)
		item = ImageFileChooserPrefItem(
			conf,
			"statusIconImageHoli",
			title=_("Select Icon"),
			currentFolder=join(sourceDir, "status-icons"),
			defaultVarName="statusIconImageHoliDefault",
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = HBox(spacing=1)
		checkItem = CheckPrefItem(
			conf,
			"statusIconFontFamilyEnable",
			label=_("Change font family to"),
			# tooltip=_("In SVG files"),
		)
		self.uiPrefItems.append(checkItem)
		# sgroup.add_widget(checkItem.getWidget())
		pack(hbox, checkItem.getWidget())
		item = FontFamilyPrefItem(
			conf,
			"statusIconFontFamily",
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = HBox(spacing=1)
		item = CheckPrefItem(
			conf,
			"statusIconLocalizeNumber",
			label=_("Localize the number"),
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = HBox(spacing=1)
		item = CheckColorPrefItem(
			CheckPrefItem(
				conf,
				"statusIconHolidayFontColorEnable",
				label=_("Holiday font color"),
			),
			ColorPrefItem(
				conf,
				"statusIconHolidayFontColor",
			),
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = HBox(spacing=1)
		checkItem = CheckPrefItem(
			conf,
			"statusIconFixedSizeEnable",
			label=_("Fixed Size"),
			# tooltip=_(""),
		)
		self.uiPrefItems.append(checkItem)
		# sgroup.add_widget(checkItem.getWidget())
		pack(hbox, checkItem.getWidget())
		pack(hbox, gtk.Label(label=" "))
		item = WidthHeightPrefItem(
			conf,
			"statusIconFixedSizeWH",
			999,
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		checkItem.syncSensitive(item.getWidget(), reverse=False)
		# --------
		# pluginsTextStatusIcon:
		hbox = HBox()
		item = CheckPrefItem(
			conf,
			"pluginsTextStatusIcon",
			_("Show Plugins Text in Status Icon (for today)"),
		)
		self.uiPrefItems.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# --------
		page = StackPage()
		page.pageParent = ""
		page.pageWidget = pageVBox
		page.pageName = "statusIcon"
		page.pageTitle = _("Status Icon") + " - " + _("Appearance")
		page.pageLabel = _("Status Icon")
		page.pageIcon = "status-icon-example.svg"
		self.prefPages.append(page)
		# ------------------------------------- Page: Accounts
		vbox = VBox(spacing=self.spacing / 2)
		vbox.set_border_width(self.spacing / 2)
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
		# ---
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
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
		hbox = HBox()
		vboxPlug = VBox()
		pack(vboxPlug, swin, 1, 1)
		pack(hbox, vboxPlug, 1, 1)
		# -----
		toolbar = StaticToolBox(self, vertical=True)
		# -----
		toolbar.extend(
			[
				ToolBoxItem(
					name="register",
					imageName="starcal.svg",
					onClick="onAccountsRegisterClick",
					desc=_("Register at StarCalendar.net"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="add",
					imageName="list-add.svg",
					onClick="onAccountsAddClick",
					desc=_("Add"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="edit",
					imageName="document-edit.svg",
					onClick="onAccountsEditClick",
					desc=_("Edit"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="delete",
					imageName="edit-delete.svg",
					onClick="onAccountsDeleteClick",
					desc=_("Delete", ctx="button"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="moveUp",
					imageName="go-up.svg",
					onClick="onAccountsUpClick",
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="moveDown",
					imageName="go-down.svg",
					onClick="onAccountsDownClick",
					desc=_("Move down"),
					continuousClick=False,
				),
			],
		)
		# -----------
		pack(hbox, toolbar)
		pack(vbox, hbox, 1, 1)
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
		page = StackPage()
		page.pagePath = page.pageName = rootPageName
		page.pageWidget = grid
		page.pageExpand = True
		page.pageExpand = True
		stack.addPage(page)
		for page in self.prefPages:
			page.pagePath = page.pageName
			stack.addPage(page)
		# if conf.preferencesPagePath:
		# 	self.stack.gotoPage(conf.preferencesPagePath)
		# -----------------------
		pack(self.vbox, stack, 1, 1)
		pack(self.vbox, self.buttonbox)
		# ----
		self.vbox.show_all()
		self.vbox.connect("realize", self.onMainVBoxRealize)

	@staticmethod
	def onMainVBoxRealize(*_args):
		ud.windowList.updateCSS()

	@staticmethod
	def onClearImageCacheClick(_button):
		pixcache.clearFiles()
		pixcache.clear()

	def onPageButtonClicked(self, _button, page):
		self.stack.gotoPage(page.pagePath)

	def newWideButton(self, page: StackPage):
		hbox = HBox(spacing=self.spacing)
		hbox.set_border_width(self.spacing)
		label = gtk.Label(label=page.pageLabel)
		label.set_use_underline(True)
		pack(hbox, gtk.Label(), 1, 1)
		if hasattr(page, "iconSize"):
			iconSize = page.iconSize
		else:
			iconSize = self.stack.iconSize()
		if page.pageIcon and conf.buttonIconEnable:
			pack(hbox, imageFromFile(page.pageIcon, iconSize))
		pack(hbox, label, 0, 0)
		pack(hbox, gtk.Label(), 1, 1)
		button = gtk.Button()
		button.add(hbox)

		button.connect("clicked", self.onPageButtonClicked, page)
		return button

	def comboFirstWDChanged(self, _combo):
		f = self.comboFirstWD.get_active()  # 0 means Sunday
		if f == 7:  # auto
			with suppress(Exception):
				f = getLocaleFirstWeekDay()
		# core.firstWeekDay will be later = f
		self.holiWDItem.setStart(f)

	def onDelete(self, _obj=None, _data=None):
		self.hide()
		return True

	def onKeyPress(self, _arg: gtk.Widget, gevent: gdk.EventKey):
		if gdk.keyval_name(gevent.keyval) == "Escape":
			self.hide()
			return True
		return False

	def ok(self, _widget):
		self.hide()

		self.apply()

	def cancel(self, _widget=None):
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

	@staticmethod
	def loadPlugin(plug: PluginType, plugI: int) -> PluginType:
		plug = plugin_man.loadPlugin(plug.file, enable=True)
		if plug:
			assert plug.loaded
		core.allPlugList[plugI] = plug
		return plug

	def apply(self, _widget=None):
		from scal3.ui_gtk.font_utils import gfontDecode

		# log.debug(f"{ui.fontDefault=}")
		ui.fontDefault = gfontDecode(
			ud.settings.get_property("gtk-font-name"),
		)
		# log.debug(f"{ui.fontDefault=}")
		# -----
		conf.preferencesPagePath = self.stack.currentPagePath()
		# -----
		# -------------------- Updating pref variables ---------------------
		for prefItem in self.iterAllPrefItems():
			prefItem.updateVar()
		# Plugin Manager
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
					log.info(f"plugIndex = {core.plugIndex}")
			elif enable:
				plug = self.loadPlugin(plug, plugI)
		core.plugIndex = index
		core.updatePlugins()
		# ------
		first = self.comboFirstWD.get_active()
		if first == 7:
			core.firstWeekDayAuto = True
			with suppress(Exception):
				core.firstWeekDay = getLocaleFirstWeekDay()
		else:
			core.firstWeekDayAuto = False
			core.firstWeekDay = first
		# ------
		weekNumberMode = self.comboWeekYear.get_active()
		# if weekNumberMode == 7:
		# core.weekNumberModeAuto = True
		# core.weekNumberMode = getLocaleWeekNumberMode()
		# else:
		core.weekNumberModeAuto = False
		core.weekNumberMode = weekNumberMode
		# ------
		ui.cells.clear()  # Very important
		# ^ specially when calTypes.primary will be changed
		# ------
		ud.updateFormatsBin()
		# ---------------------- Saving Preferences -----------------------
		# ------------------- Saving logger config
		self.loggerPrefItem.save()
		# ------------------- Saving calendar types config
		for mod in calTypes:
			mod.save()
		# ------------------- Saving locale config
		locale_man.saveConf()
		# ------------------- Saving core config
		core.version = core.VERSION
		core.saveConf()
		del core.version
		# ------------------- Saving ui config
		ui.saveConf()
		# ------------------- Saving gtk_ud config
		ud.saveConf()
		# ----------------------- Updating GUI ---------------------------
		ud.windowList.onConfigChange()
		if self.checkNeedRestart():
			d = gtk.Dialog(
				title=_("Restart " + core.APP_DESC),
				transient_for=self,
				modal=True,
				destroy_with_parent=True,
			)
			dialog_add_button(
				d,
				imageName="dialog-cancel.svg",
				label=_("_No"),
				res=gtk.ResponseType.CANCEL,
			)
			d.set_keep_above(True)
			label = gtk.Label(
				label=(
					_(f"Some preferences need restarting {core.APP_DESC} to apply.")  # noqa: INT001
					+ " "
					+ _("Restart Now?")
				),
			)
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

	def checkNeedRestart(self):
		if ui.mainWin is None:
			return False
		if ui.checkNeedRestart():
			return True
		return logger.logLevel != self.initialLogLevel

	def refreshAccounts(self):
		self.accountsTreeModel.clear()
		for account in ui.eventAccounts:
			self.accountsTreeModel.append(
				[
					account.id,
					account.enable,
					account.title,
				],
			)

	def updatePrefGui(self):  # Updating Pref Gui (NOT MAIN GUI)
		for opt in self.iterAllPrefItems():
			opt.updateWidget()
		# -------------------------------
		if core.firstWeekDayAuto:
			self.comboFirstWD.set_active(7)
		else:
			self.comboFirstWD.set_active(core.firstWeekDay)
		if core.weekNumberModeAuto:
			self.comboWeekYear.set_active(8)
		else:
			self.comboWeekYear.set_active(core.weekNumberMode)
		# Plugin Manager
		model = self.plugTreeview.get_model()
		model.clear()
		for p in core.getPluginsTable():
			model.append(
				[
					p.index,
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

	# def plugTreevExpose(self, widget, gevent):
	# 	self.plugTitleCell.set_property(
	# 		"wrap-width",
	# 		self.plugTitleCol.get_width() + 2
	# 	)

	def plugTreevCursorChanged(self, _selection=None):
		cur = self.plugTreeview.get_cursor()[0]
		if cur is None:
			return
		i = cur[0]
		model = self.plugTreeview.get_model()
		j = model[i][0]
		plug = core.allPlugList[j]
		self.plugButtonAbout.set_sensitive(bool(plug.about))
		self.plugButtonConf.set_sensitive(plug.hasConfig)

	def onPlugAboutClick(self, _obj=None):
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
		return None

	def onPlugConfClick(self, _obj=None):
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

	@staticmethod
	def onPlugExportToIcsClick(_menu, plug):
		from scal3.ui_gtk.export import ExportToIcsDialog

		ExportToIcsDialog(plug.exportToIcs, plug.title).run()

	def plugTreevRActivate(self, _treev, _path, col):
		if col.get_title() == _("Title"):  # FIXME
			self.onPlugAboutClick()

	def plugTreevButtonPress(self, _widget, gevent):
		b = gevent.button
		if b == 3:
			cur = self.plugTreeview.get_cursor()[0]
			if cur:
				i = cur[0]
				j = self.plugTreeview.get_model()[i][0]
				plug = core.allPlugList[j]
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
				menu.add(
					ImageMenuItem(
						_("Export to {format}").format(format="iCalendar"),
						imageName="text-calendar-ics.png",
						func=self.onPlugExportToIcsClick,
						args=(plug,),
					),
				)
				# --
				menu.show_all()
				self.tmpMenu = menu
				menu.popup(None, None, None, None, 3, gevent.time)
			return True
		return False

	def onPlugAddClick(self, _button):
		# FIXME
		# Reize window to show all texts
		# self.plugAddTreeview.columns_autosize()  # FIXME
		_x, _y, w, _h = self.plugAddTreeview.get_column(0).cell_get_size()
		# log.debug(x, y, w, h)
		self.plugAddDialog.resize(
			w + 30,
			75 + 30 * len(self.plugAddTreeModel),
		)
		# ---------------
		self.plugAddDialog.run()
		self.pluginsToolbar.setCanAdd(len(self.plugAddItems) > 0)

	def plugAddDialogClose(self, _obj, _gevent=None):
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

	def plugTreeviewTop(self, _button):
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

	def plugTreeviewBottom(self, _button):
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

	def plugTreeviewUp(self, _button):
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

	def plugTreeviewDown(self, _button):
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

	@staticmethod
	def plugTreevDragReceived(
		treev,
		_context,
		x,
		y,
		_selec,
		_info,
		_etime,
	):
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
		elif dest[1] in {
			gtk.TreeViewDropPosition.BEFORE,
			gtk.TreeViewDropPosition.INTO_OR_BEFORE,
		}:
			t.move_before(
				t.get_iter(i),
				t.get_iter(dest[0][0]),
			)
		else:
			t.move_after(
				t.get_iter(i),
				t.get_iter(dest[0][0]),
			)

	def onPlugDeleteClick(self, _button):
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

	def plugAddDialogOK(self, _obj):
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
		self.plugTreeview.get_model().insert(
			pos,
			[
				j,
				True,
				False,
				core.allPlugList[j].title,
			],
		)
		self.plugAddTreeModel.remove(self.plugAddTreeModel.get_iter(i))
		self.plugAddItems.pop(i)
		self.plugAddDialog.hide()
		self.plugTreeview.set_cursor(pos)  # pos == -1 # FIXME

	def plugAddTreevRActivate(self, _treev, _path, _col):
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

	def onAccountsEditClick(self, _button):
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur[0]
		self.editAccount(index)

	def onAccountsRegisterClick(self, _button):
		from scal3.ui_gtk.event.register_starcal import StarCalendarRegisterDialog

		win = StarCalendarRegisterDialog(transient_for=self)
		win.run()

	def onAccountsAddClick(self, _button):
		from scal3.ui_gtk.event.account_op import AccountEditorDialog

		account = AccountEditorDialog(transient_for=self).run()
		if account is None:
			return
		account.save()
		ui.eventAccounts.append(account)
		ui.eventAccounts.save()
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
		error = account.fetchGroups()
		if error:
			log.error(error)
			return
		account.save()

	def onAccountsDeleteClick(self, _button):
		cur = self.accountsTreeview.get_cursor()[0]
		if cur is None:
			return
		index = cur[0]
		accountId = self.accountsTreeModel[index][0]
		account = ui.eventAccounts[accountId]
		if not confirm(
			_('Do you want to delete account "{accountTitle}"').format(
				accountTitle=account.title,
			),
			transient_for=self,
		):
			return
		ui.eventAccounts.delete(account)
		ui.eventAccounts.save()
		del self.accountsTreeModel[index]

	def onAccountsUpClick(self, _button):
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

	def onAccountsDownClick(self, _button):
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

	def accountsTreevRActivate(self, _treev, path, _col):
		index = path[0]
		self.editAccount(index)

	@staticmethod
	def accountsTreevButtonPress(_widget, gevent):
		b = gevent.button
		if b == 3:  # noqa: SIM103
			# FIXME
			# cur = self.accountsTreeview.get_cursor()[0]
			# if cur:
			# 	index = cur[0]
			# 	accountId = self.accountsTreeModel[index][0]
			# 	account = ui.eventAccounts[accountId]
			# 	menu = Menu()
			# 	#
			# 	menu.show_all()
			# 	self.tmpMenu = menu
			# 	menu.popup(None, None, None, None, 3, gevent.time)
			return True
		return False

	def accountsTreeviewCellToggled(self, cell, path):
		index = int(path)
		active = not cell.get_active()
		# ---
		accountId = self.accountsTreeModel[index][0]
		account = ui.eventAccounts[accountId]
		# not account.loaded -> it's a dummy account
		if active and not account.loaded:
			account = ui.eventAccounts.replaceDummyObj(account)
			if account is None:
				return
		account.enable = active
		account.save()
		# ---
		self.accountsTreeModel[index][1] = active


if __name__ == "__main__":
	dialog = PreferencesWindow(0)
	dialog.updatePrefGui()
	dialog.run()
