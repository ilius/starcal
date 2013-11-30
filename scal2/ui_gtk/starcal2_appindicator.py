#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal2.path import *
from scal2 import locale_man
from scal2.locale_man import tr as _

import gtk
import appindicator

from scal2.ui_gtk.utils import CopyLabelMenuItem

class IndicatorStatusIconWrapper(appindicator.Indicator):
    imPath = join(tmpDir, 'starcal2-indicator-%s.png'%os.getuid())## FIXME
    def __init__(self, mainWin):
        self.mainWin = mainWin
        appindicator.Indicator.__init__(
            self,
            'starcal2',## app id
            'starcal2',## icon
            appindicator.CATEGORY_APPLICATION_STATUS,
        )
        self.set_status(appindicator.STATUS_ACTIVE)
        #self.set_attention_icon("new-messages-red")
        ######
        self.create_menu()
    '''
    def create_menu_simple(self):
        menu = gtk.Menu()
        ###
        for item in [self.mainWin.getMainWinMenuItem()] + self.mainWin.getTrayPopupItems():
            item.show()
            menu.add(item)
        ###
        #if locale_man.rtl:
            #menu.set_direction(gtk.TEXT_DIR_RTL)
        self.set_menu(menu)
    '''
    def create_menu(self):
        menu = gtk.Menu()
        ####
        for line in self.mainWin.getTrayTooltip().split('\n'):
            item = CopyLabelMenuItem(line)
            item.show()
            menu.append(item)
        ####
        item = self.mainWin.getMainWinMenuItem()
        item.show()
        menu.append(item)
        ####
        submenu = gtk.Menu()
        for item in self.mainWin.getTrayPopupItems():
            item.show()
            submenu.add(item)
        sitem = gtk.MenuItem(label=_('More'))
        sitem.set_submenu(submenu)
        sitem.show()
        menu.append(sitem)
        self.set_menu(menu)
    def set_from_pixbuf(self, pbuf):
        pbuf.save(self.imPath, 'png')
        self.set_icon('')
        self.set_icon(self.imPath)
        self.create_menu()
    #def __del__(self):
    #    os.remove(self.imPath)
    is_embedded = lambda self: True ## FIXME
    def set_visible(self, visible):## FIXME
        pass
    def set_tooltip_text(self, text):
        #self.set_label_guide(text)
        pass
        


