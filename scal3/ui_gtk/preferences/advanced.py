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
from scal3.ui_gtk import gtk, pack, pixcache
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.log_pref import LogLevelOptionUI
from scal3.ui_gtk.option_ui.combo import ComboEntryTextOptionUI
from scal3.ui_gtk.option_ui.spin import IntSpinOptionUI
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.utils import (
	labelImageButton,
)

if typing.TYPE_CHECKING:
	from scal3.ui_gtk.option_ui.base import OptionUI

__all__ = ["PreferencesAdvanced"]


class PreferencesAdvanced:
	def __init__(self, spacing: int) -> None:
		self.optionUIs: list[OptionUI] = []
		# --------
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=spacing)
		vbox.set_border_width(int(spacing / 2))
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "advanced"
		page.pageTitle = _("Advanced")
		page.pageLabel = _("A_dvanced")
		page.pageIcon = "applications-system.svg"
		self.prefPages = [page]
		item: OptionUI
		# ------
		item = LogLevelOptionUI()
		self.loggerOptionUI = item
		pack(vbox, item.getWidget())
		# ------
		hbox = gtk.Box(
			orientation=gtk.Orientation.HORIZONTAL,
			spacing=int(spacing / 2),
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
		self.optionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=int(spacing / 2))
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
		self.optionUIs.append(item)
		pack(hbox, item.getWidget(), 1, 1)
		pack(vbox, hbox)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=int(spacing / 2))
		label = gtk.Label(label=_("Days maximum cache size"))
		pack(hbox, label)
		# sgroup.add_widget(label)
		item = IntSpinOptionUI(
			option=conf.maxDayCacheSize,
			bounds=(100, 9999),
			step=10,
		)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(vbox, hbox)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=int(spacing / 2))
		label = gtk.Label(label=_("Horizontal offset for day right-click menu"))
		pack(hbox, label)
		item = IntSpinOptionUI(
			option=conf.cellMenuXOffset,
			bounds=(0, 999),
			step=1,
		)
		self.optionUIs.append(item)
		pack(hbox, item.getWidget())
		pack(vbox, hbox)
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=int(spacing / 2))
		button = labelImageButton(
			label=_("Clear Image Cache"),
			# TODO: _("Clear Image Cache ({size})").format(size=""),
			imageName="sweep.svg",
		)
		button.connect("clicked", self.onClearImageCacheClick)
		pack(hbox, button)
		pack(vbox, hbox)

	@staticmethod
	def onClearImageCacheClick(_w: gtk.Widget) -> None:
		pixcache.clearFiles()
		pixcache.clear()
