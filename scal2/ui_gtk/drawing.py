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
from os.path import join

from scal2.paths import *

from scal2.locale_man import cutText, rtl
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
        raise ValueError('bad color %s'%str(color))


def fillColor(cr, color):
    setColor(cr, color)
    cr.fill()


def newTextLayout(widget, text='', font=None):
    layout = widget.create_pango_layout(text) ## a pango.Layout object
    if not font:
        font = ui.getFont()
    layout.set_font_description(pfontEncode(font))
    return layout

def newLimitedWidthTextLayout(widget, text, width, font=None, truncate=True):
    if not font:
        font = ui.getFont()
    layout = widget.create_pango_layout(text)
    layout.set_font_description(pfontEncode(font))
    if not layout:
        return None
    layoutW, layoutH = layout.get_pixel_size()
    if layoutW > width:
        if truncate:
            char_w = layoutW/len(text)
            char_num = int(width//char_w)
            while layoutW > width:
                text = cutText(text, char_num)
                layout = widget.create_pango_layout(text)
                layout.set_font_description(pfontEncode(font))
                layoutW, layoutH = layout.get_pixel_size()
                char_num -= max(int((layoutW-width)//char_w), 1)
                if char_num<0:
                    layout = None
                    break
        else:## use smaller font
            font2 = list(font)
            while layoutW > width:
                font2[3] = 0.9*font2[3]*width/layoutW
                layout.set_font_description(pfontEncode(font2))
                layoutW, layoutH = layout.get_pixel_size()
                #print layoutW, width
            #print
    return layout

class Button:
    def __init__(self, imageName, func, x, y, autoDir=True):
        self.imageName = imageName
        if imageName.startswith('gtk-'):
            self.pixbuf = gdk.pixbuf_new_from_stock(imageName)
        else:
            self.pixbuf = gdk.pixbuf_new_from_file(join(pixDir, imageName))
        self.func = func
        self.width = self.pixbuf.get_width()
        self.height = self.pixbuf.get_height()
        self.x = x
        self.y = y
        self.autoDir = autoDir
    __repr__ = lambda self: 'Button(%r, %r, %r, %r, %r)'%(self.imageName, self.func.__name__, self.x, self.y, self.autoDir)
    def getAbsPos(self, w, h):
        x = self.x
        y = self.y
        if self.autoDir and rtl:
            x = -x
        if x<0:
            x = w - self.width + x
        if y<0:
            y = h - self.height + y
        return (x, y)
    def draw(self, cr, w, h):
        (x, y) = self.getAbsPos(w, h)
        cr.set_source_pixbuf(self.pixbuf, x, y)
        cr.rectangle(x, y, self.width, self.height)
        cr.fill()
    def contains(self, px, py, w, h):
        (x, y) = self.getAbsPos(w, h)
        return (x <= px < x+self.width and y <= py < y+self.height)

