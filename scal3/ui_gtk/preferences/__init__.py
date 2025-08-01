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
from typing import Any

from scal3 import core, locale_man, ui
from scal3.app_info import APP_DESC
from scal3.cal_types import calTypes
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import Dialog, gdk, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.option_ui import CheckOptionUI
from scal3.ui_gtk.option_ui_extra import CheckStartupOptionUI
from scal3.ui_gtk.preferences.accounts import PreferencesAccounts
from scal3.ui_gtk.preferences.advanced import PreferencesAdvanced
from scal3.ui_gtk.preferences.appearance import PreferencesAppearance
from scal3.ui_gtk.preferences.button import newWideButton
from scal3.ui_gtk.preferences.lang_caltype import PreferencesLanguageCalTypes
from scal3.ui_gtk.preferences.plugins import PreferencesPlugins
from scal3.ui_gtk.preferences.regional import PreferencesRegionalTab
from scal3.ui_gtk.preferences.status_icon import PreferencesStatusIcon
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.utils import dialog_add_button

if typing.TYPE_CHECKING:
	from scal3.ui_gtk.log_pref import LogLevelOptionUI
	from scal3.ui_gtk.option_ui import OptionUI
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
		self.optionUIs: list[OptionUI] = []
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
		self.initialLogLevel = logger.logLevel
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
		button = newWideButton(self, page)
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
				button = newWideButton(self, page)
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
		self.optionUIs += [tab.langOption, tab.calsOption]

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
		self.optionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------------------------
		item = CheckOptionUI(
			option=conf.showMain,
			label=_("Open main window on start"),
		)
		self.optionUIs.append(item)
		pack(vbox, item.getWidget())
		# ------------------------
		item = CheckOptionUI(
			option=conf.showDesktopWidget,
			label=_("Open desktop widget on start"),
		)
		self.optionUIs.append(item)
		pack(vbox, item.getWidget())
		# --------------------------
		item = CheckOptionUI(
			option=conf.winTaskbar,
			label=_("Window in Taskbar"),
		)
		self.optionUIs.append(item)
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
			self.optionUIs.append(item)
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
		# #self.optionUIs.append(item)
		# #pack(hbox, item.getWidget())
		# pack(hbox, gtk.Label(), 1, 1)
		# item = CheckOptionUI(
		# 	option=conf.showDigClockTr,
		# 	label=_("On Status Icon"),
		# 	tooltip="Notification Area",
		# )
		# self.optionUIs.append(item)
		# pack(hbox, item.getWidget())
		# pack(hbox, gtk.Label(), 1, 1)
		# pack(vbox, hbox)

	def _initPageAppearance(self) -> None:
		buttonPadding = self.spacing
		padding = int(self.spacing / 2)
		tab = PreferencesAppearance(window=self, spacing=self.spacing)
		self.prefPages += tab.prefPages
		self.optionUIs += tab.optionUIs
		grid = gtk.Grid()
		pack(tab.vbox, grid, padding=padding)
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		grid.set_row_spacing(buttonPadding)
		for index, page in enumerate(tab.subPages):
			grid.attach(newWideButton(self, page), 0, index, 1, 1)
		grid.show_all()

	def _initPageRegional(self) -> None:
		tab = PreferencesRegionalTab(spacing=self.spacing)
		self.regionalTab = tab
		self.prefPages += tab.prefPages
		self.optionUIs += tab.optionUIs
		# -----
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		# grid.set_row_spacing(self.spacing)
		for index, page in enumerate(tab.prefPages):
			button = newWideButton(self, page)
			button.set_border_width(int(self.spacing * 0.7))
			grid.attach(button, 0, index, 1, 1)
		grid.show_all()
		pack(tab.vbox, grid)

	def _initPageAdvanced(self) -> None:
		tab = PreferencesAdvanced(spacing=self.spacing)
		self.prefPages += tab.prefPages
		self.optionUIs += tab.optionUIs
		self.optionUIs.append(tab.loggerOptionUI)
		self.loggerOptionUI = tab.loggerOptionUI

	def _initPagePlugins(self) -> None:
		tab = PreferencesPlugins(spacing=self.spacing, window=self)
		self.pluginsTab = tab
		self.prefPages.append(tab.page)

	def _initPageStatusIcon(self) -> None:
		tab = PreferencesStatusIcon(spacing=self.spacing)
		self.prefPages += tab.prefPages
		self.optionUIs += tab.optionUIs

	def _initPageAccounts(self) -> None:
		tab = PreferencesAccounts(window=self, spacing=self.spacing)
		self.accountsTab = tab
		self.prefPages.append(tab.page)

	@staticmethod
	def onMainVBoxRealize(_w: gtk.Widget) -> None:
		ud.windowList.updateCSS()

	def onPageButtonClicked(self, _w: gtk.Widget, page: StackPageType) -> None:
		self.stack.gotoPage(page.pagePath)

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
		return self.optionUIs

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
		self.regionalTab.apply()
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
		ud.windowList.broadcastConfigChange()
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
		self.regionalTab.updatePrefGui()
		self.pluginsTab.updatePrefGui()
		self.refreshAccounts()


if __name__ == "__main__":
	dialog = PreferencesWindow()
	dialog.updatePrefGui()
	dialog.present()
