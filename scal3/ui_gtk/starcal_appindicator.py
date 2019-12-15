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

import sys
import atexit
import os
from os.path import dirname
sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3.path import *
from scal3 import core
from scal3 import locale_man
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	CopyLabelMenuItem,
	get_pixbuf_hash,
)

import gi
gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as appindicator


class IndicatorStatusIconWrapper:
	imNamePrefix = f"{APP_NAME}-indicator-{os.getuid()}-"

	def __init__(self, mainWin):
		self.mainWin = mainWin
		self.c = appindicator.Indicator.new(
			APP_NAME,## app id
			"",## icon
			appindicator.IndicatorCategory.APPLICATION_STATUS,
		)
		self.c.set_status(appindicator.IndicatorStatus.ACTIVE)
		#self.c.set_attention_icon("new-messages-red")
		######
		atexit.register(self.cleanup)
		######
		self.create_menu()
		self.imPath = ""

	"""
	def create_menu_simple(self):
		menu = Menu()
		###
		for item in [
			self.mainWin.getMainWinMenuItem(),
		] + self.mainWin.getStatusIconPopupItems():
			item.show()
			menu.add(item)
		###
		#if locale_man.rtl:
			#menu.set_direction(gtk.TextDirection.RTL)
		self.c.set_menu(menu)
	"""

	def create_menu(self):
		menu = Menu()
		self.menuItems = []
		# ^ just to prevent GC from removing custom objects for items
		####
		for line in self.mainWin.getStatusIconTooltip().split("\n"):
			item = CopyLabelMenuItem(line)
			self.menuItems.append(item)
			item.show()
			menu.append(item)
		####
		item = self.mainWin.getMainWinMenuItem()
		self.menuItems.append(item)
		item.show()
		menu.append(item)
		####
		item = gtk.MenuItem(_("Desktop Widget"))
		item.connect("activate", self.mainWin.dayCalWinShow)
		item.show()
		menu.append(item)
		####
		submenu = Menu()
		for item in self.mainWin.getStatusIconPopupItems():
			self.menuItems.append(item)
			item.show_all()
			submenu.add(item)
		sitem = MenuItem(label=_("More"))
		sitem.set_submenu(submenu)
		sitem.show()
		menu.append(sitem)
		if locale_man.rtl:
			menu.set_direction(gtk.TextDirection.RTL)  # not working
		self.c.set_menu(menu)

	def set_from_file(self, fpath):
		self.c.set_icon("")
		self.c.set_icon(fpath)
		self.create_menu()

	def set_from_pixbuf(self, pbuf):
		# https://bugs.launchpad.net/ubuntu/+source/indicator-application/+bug/533439
		#pbuf.scale_simple(22, 22, GdkPixbuf.InterpType.HYPER)
		fname = self.imNamePrefix + get_pixbuf_hash(pbuf)
		# to make the filename unique, otherwise it won't change in KDE Plasma
		fpath = join(tmpDir, fname + ".png")
		self.imPath = fpath
		pbuf.savev(fpath, "png", [], [])
		self.set_from_file(fpath)

	def cleanup(self):
		for fname in os.listdir(tmpDir):
			if not fname.startswith(self.imNamePrefix):
				continue
			try:
				os.remove(join(tmpDir, fname))
			except Exception:
				log.exception("")

	def is_embedded(self):
		return True  # FIXME

	def set_visible(self, visible):  # FIXME
		pass

	def set_tooltip_text(self, text):
		#self.c.set_label_guide(text)
		pass
