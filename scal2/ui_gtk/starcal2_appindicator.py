#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import sys
import os
from os.path import dirname
sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal2.paths import *
from scal2 import locale_man

import gtk
import appindicator


class IndicatorStatusIconWrapper(appindicator.Indicator):
    def __init__(self, mainWin):
        appindicator.Indicator.__init__(
            self,
            'starcal2',## app id
            'starcal2',## icon
            appindicator.CATEGORY_APPLICATION_STATUS,
        )
        self.set_status(appindicator.STATUS_ACTIVE)
        #self.set_attention_icon("new-messages-red")
        ######
        menu = gtk.Menu()
        ###
        for item in mainWin.getTrayPopupItems(True):
            menu.add(item)
            item.show()
        ###
        #if locale_man.rtl:
            #menu.set_direction(gtk.TEXT_DIR_RTL)
        self.set_menu(menu)
        self.menu = menu
    def set_from_pixbuf(self, pbuf):
        fpath = join(tmpDir, 'starcal2-tray-%s.png'%os.getuid())## FIXME
        pbuf.save(fpath, 'png')
        self.set_icon(fpath)
    def is_embedded(self):## FIXME
        return True
    def set_visible(self, visible):## FIXME
        pass
    def set_tooltip_text(self, text):
        #self.set_label_guide(text)
        pass
        


