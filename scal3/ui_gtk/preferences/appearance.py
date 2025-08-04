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

from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui.base import OptionUI
from scal3.ui_gtk.option_ui.check import CheckOptionUI
from scal3.ui_gtk.option_ui.color import ColorOptionUI
from scal3.ui_gtk.option_ui.font import FontOptionUI
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.utils import newAlignLabel, newHSep

if typing.TYPE_CHECKING:
	from scal3.ui_gtk.option_ui.base import OptionUI

__all__ = ["PreferencesAppearance"]


class PreferencesAppearance:
	def __init__(self, window: gtk.Window, spacing: int) -> None:
		self.optionUIs: list[OptionUI] = []
		self.win = window
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=spacing)
		self.vbox = vbox
		vbox.set_border_width(spacing)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "appearance"
		page.pageTitle = _("Appearance")
		# A is for Apply, P is for Plugins, R is for Regional,
		# C is for Cancel, only "n" is left!
		page.pageLabel = _("Appeara_nce")
		page.pageIcon = "preferences-desktop-theme.png"
		self.prefPages = [page]
		# --------
		padding = int(spacing / 2)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=int(spacing / 2))
		# ---
		customCheckItem = CheckOptionUI(
			option=conf.fontCustomEnable,
			label=_("Application Font"),
		)
		self.optionUIs.append(customCheckItem)
		pack(hbox, customCheckItem.getWidget())
		# ---
		customItem = FontOptionUI(option=conf.fontCustom)
		self.optionUIs.append(customItem)
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
		self.optionUIs.append(item)
		pack(vbox, item.getWidget())
		# ---------------------------
		item = CheckOptionUI(
			option=conf.useSystemIcons,
			label=_("Use System Icons"),
		)
		self.optionUIs.append(item)
		pack(vbox, item.getWidget())
		# ---------------------------
		item = CheckOptionUI(
			option=conf.oldStyleProgressBar,
			label=_("Old-style Progress Bar"),
		)
		self.optionUIs.append(item)
		pack(vbox, item.getWidget())
		# ------------------------- Colors ---------------------
		pageHBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pageHBox.set_border_width(spacing)
		spacing = int(spacing / 3)
		# ---
		pageVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Background")))
		item = ColorOptionUI(option=conf.bgColor, useAlpha=True)
		self.optionUIs.append(item)
		self.colorbBg = item.getWidget()  # FIXME
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Border")))
		item = ColorOptionUI(option=conf.borderColor, useAlpha=True)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Cursor")))
		item = ColorOptionUI(option=conf.cursorOutColor, useAlpha=False)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Cursor BG")))
		item = ColorOptionUI(option=conf.cursorBgColor, useAlpha=True)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Today")))
		item = ColorOptionUI(option=conf.todayCellColor, useAlpha=True)
		self.optionUIs.append(item)
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
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Holidays Font")))
		item = ColorOptionUI(option=conf.holidayColor, useAlpha=False)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Inactive Day Font")))
		item = ColorOptionUI(option=conf.inactiveColor, useAlpha=True)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
		pack(hbox, newAlignLabel(sgroup=sgroup, label=_("Border Font")))
		item = ColorOptionUI(option=conf.borderTextColor, useAlpha=False)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		pack(pageHBox, pageVBox, 1, 1, padding=int(spacing / 2))
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
		self.subPages = appearanceSubPages
