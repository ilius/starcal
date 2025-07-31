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


from scal3.locale_man import langSh
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui_extra import (
	ActiveInactiveCalsOptionUI,
	LangOptionUI,
)
from scal3.ui_gtk.stack import StackPage

__all__ = ["PreferencesLanguageCalTypes"]



class PreferencesLanguageCalTypes:
	def __init__(self, window: gtk.Window, spacing: int) -> None:
		self.win = window
		self.spacing = spacing
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=self.spacing)
		vbox.set_border_width(int(self.spacing / 2))
		page = StackPage()
		self.page = page
		page.pageWidget = vbox
		page.pageName = "lang_calTypes"
		page.pageTitle = _("Language and Calendar Types")
		page.pageLabel = _("_Language and Calendar Types")
		page.pageIcon = "preferences-desktop-locale.png"
		# --------------------------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL, spacing=int(self.spacing / 2)
		)
		pack(hbox, gtk.Label(label=_("Language")))
		langOption = LangOptionUI()
		self.langOption = langOption
		# ---
		pack(hbox, langOption.getWidget())
		if langSh != "en":
			pack(hbox, gtk.Label(label="Language"))
		pack(vbox, hbox)
		# --------------------------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		frame = gtk.Frame()
		frame.set_label(_("Calendar Types"))
		calsOption = ActiveInactiveCalsOptionUI()
		self.calsOption = calsOption
		itemCalsWidget = calsOption.getWidget()
		assert isinstance(itemCalsWidget, gtk.Container), f"{itemCalsWidget=}"
		itemCalsWidget.set_border_width(10)
		frame.add(itemCalsWidget)
		pack(hbox, frame, 1, 1)
		hbox.set_border_width(5)
		frame.set_border_width(0)
		pack(vbox, hbox, 1, 1)

