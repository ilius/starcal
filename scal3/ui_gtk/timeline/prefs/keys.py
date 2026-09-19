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

from scal3.locale_man import tr as _
from scal3.timeline import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.option_ui_extra import KeyBindingOptionUI
from scal3.ui_gtk.stack import StackPage

__all__ = ["buildKeysPages"]


def buildKeysPages() -> list[StackPage]:
	pages: list[StackPage] = []
	vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
	vbox.set_border_width(5)
	page = StackPage()
	page.pageWidget = vbox
	page.pageName = "keys"
	page.pageTitle = _("Keys")
	page.pageLabel = _("Keys")
	page.pageIcon = "configure-shortcuts.png"
	pages.append(page)
	# -----
	option = KeyBindingOptionUI(
		option=conf.keys,
		actions=sorted(conf.keys.v.values()),
	)
	option.updateWidget()
	pack(vbox, option.getWidget(), 1, 1)
	return pages
