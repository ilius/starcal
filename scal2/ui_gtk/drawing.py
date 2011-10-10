# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License,    or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal2 import ui
from scal2.ui_gtk.font_utils import *
from scal2.ui_gtk.color_utils import *


import gobject, pango, cairo
import gtk
from gtk import gdk

if not ui.fontCustom:
    ui.fontCustom = ui.fontDefault

def setColor(cr, color):
    ## arguments to set_source_rgb and set_source_rgba must be between 0 and 1
    if len(color)==3:
        cr.set_source_rgb(color[0] / 255.0,
                          color[1] / 255.0,
                          color[2] / 255.0)
    elif len(color)==4:
        cr.set_source_rgba(color[0] / 255.0,
                           color[1] / 255.0,
                           color[2] / 255.0,
                           color[3] / 255.0)
    else:
        raise ValueError('bad color %s'%color)


def fillColor(cr, color):
    setColor(cr, color)
    cr.fill()


def newTextLayout(widget, text='', font=None):
    lay = widget.create_pango_layout(text) ## a pango.Layout object
    if not font:
        font = ui.fontDefault if ui.fontUseDefault else ui.fontCustom
    lay.set_font_description(pfontEncode(font))
    return lay

