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
from os.path import isfile, join

from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.path import sourceDir, svgDir
from scal3.ui import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui import (
	CheckColorOptionUI,
	CheckOptionUI,
	ColorOptionUI,
	FontFamilyOptionUI,
	ImageFileChooserOptionUI,
	WidthHeightOptionUI,
)
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.utils import newAlignLabel

if typing.TYPE_CHECKING:
	from scal3.ui_gtk.option_ui import OptionUI

__all__ = ['PreferencesStatusIcon']

class PreferencesStatusIcon:
	def __init__(self, spacing: int) -> None:
		self.optionUIs: list[OptionUI] = []
		pageVBox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=int(spacing * 0.8),
		)
		pageVBox.set_border_width(spacing)
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
		self.optionUIs.append(item)
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
		self.optionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		checkItem = CheckOptionUI(
			option=conf.statusIconFontFamilyEnable,
			label=_("Change font family to"),
			# tooltip=_("In SVG files"),
		)
		self.optionUIs.append(checkItem)
		# sgroup.add_widget(checkItem.getWidget())
		pack(hbox, checkItem.getWidget())
		item = FontFamilyOptionUI(
			option=conf.statusIconFontFamily,
		)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		item = CheckOptionUI(
			option=conf.statusIconLocalizeNumber,
			label=_("Localize the number"),
		)
		self.optionUIs.append(item)
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
		self.optionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(pageVBox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=1)
		checkItem = CheckOptionUI(
			option=conf.statusIconFixedSizeEnable,
			label=_("Fixed Size"),
			# tooltip=_(""),
		)
		self.optionUIs.append(checkItem)
		# sgroup.add_widget(checkItem.getWidget())
		pack(hbox, checkItem.getWidget())
		pack(hbox, gtk.Label(label=" "))
		item = WidthHeightOptionUI(
			option=conf.statusIconFixedSizeWH,
			maxim=999,
		)
		self.optionUIs.append(item)
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
		self.optionUIs.append(item)
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
		self.prefPages = [page]
