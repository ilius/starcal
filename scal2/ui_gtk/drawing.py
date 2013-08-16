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
from os.path import join
from math import pi

from scal2.path import *

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
        cr.set_source_rgb(
            color[0] / 255.0,
            color[1] / 255.0,
            color[2] / 255.0,
        )
    elif len(color)==4:
        cr.set_source_rgba(
            color[0] / 255.0,
            color[1] / 255.0,
            color[2] / 255.0,
            color[3] / 255.0,
        )
    else:
        raise ValueError('bad color %s'%color)


def fillColor(cr, color):
    setColor(cr, color)
    cr.fill()


def newTextLayout(
    widget,
    text='',
    font=None,
    maxSize=None,
    maximizeScale=0.6,
    truncate=False,
):
    '''
        None return value should be expected and handled, only if maxSize is given
    '''
    layout = widget.create_pango_layout('') ## a pango.Layout object
    if not font:
        font = ui.getFont()
    layout.set_font_description(pfontEncode(font))
    if text:
        layout.set_markup(text)
        if maxSize:
            layoutW, layoutH = layout.get_pixel_size()
            ##
            maxW, maxH = maxSize
            maxW = float(maxW)
            maxH = float(maxH)
            if maxW <= 0:
                return
            if maxH <= 0:
                minRat = 1.0
            else:
                minRat = 1.01 * layoutH/maxH ## FIXME
            if truncate:
                if minRat > 1:
                    font[3] = int(font[3]/minRat)
                layout.set_font_description(pfontEncode(font))
                layoutW, layoutH = layout.get_pixel_size()
                if layoutW > 0:
                    char_w = float(layoutW)/len(text)
                    char_num = int(maxW//char_w)
                    while layoutW > maxW:
                        text = cutText(text, char_num)
                        if not text:
                            break
                        layout = widget.create_pango_layout(text)
                        layout.set_font_description(pfontEncode(font))
                        layoutW, layoutH = layout.get_pixel_size()
                        char_num -= max(int((layoutW-maxW)//char_w), 1)
                        if char_num<0:
                            layout = None
                            break
            else:
                if maximizeScale > 0:
                    minRat = minRat/maximizeScale
                if minRat < layoutW/maxW:
                    minRat = layoutW/maxW
                if minRat > 1:
                    font[3] = int(font[3]/minRat)
                layout.set_font_description(pfontEncode(font))
    return layout

'''
def newLimitedWidthTextLayout(widget, text, width, font=None, truncate=True, markup=True):
    if not font:
        font = ui.getFont()
    layout = widget.create_pango_layout('')
    if markup:
        layout.set_markup(text)
    else:
        layout.set_text(text)
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
'''

def newOutlineSquarePixbuf(color, size, innerSize=0, bgColor=None):
    pmap = gdk.Pixmap(None, size, size, depth=24)
    cr = pmap.cairo_create()
    ###
    if bgColor:
        cr.rectangle(0, 0, size, size)
        fillColor(cr, bgColor)
    ###
    cr.move_to(0, 0)
    cr.line_to(size, 0)
    cr.line_to(size, size)
    cr.line_to(0, size)
    cr.line_to(0, 0)
    if innerSize:
        d = (size-innerSize)/2.0
        cr.line_to(d, 0)
        cr.line_to(d, size-d)
        cr.line_to(size-d, size-d)
        cr.line_to(size-d, d)
        cr.line_to(d, d)
    ###
    cr.close_path()
    fillColor(cr, color)
    ####
    pbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, True, 8, size, size)
    colormap = gtk.gdk.colormap_get_system()
    #colormap = self.get_screen().get_system_colormap()
    #colormap = pmap.get_colormap()
    pbuf.get_from_drawable(pmap, colormap, 0, 0, 0, 0, size, size)
    if bgColor:
        pbuf = pbuf.add_alpha(True, *bgColor)
    return pbuf



def newRoundedSquarePixbuf(color, size, roundR=0, bgColor=None):## a rounded square with specified color
    #color = (255, 0, 0) ## FIXME
    #bgColor = (
    #    min(255, color[0]+1),
    #    min(255, color[1]+1),
    #    min(255, color[2]+1),
    #)
    pmap = gdk.Pixmap(None, size, size, depth=24)
    cr = pmap.cairo_create()
    ###
    if bgColor:
        cr.rectangle(0, 0, size, size)
        fillColor(cr, bgColor)
    ###
    cr.move_to(roundR, 0)
    cr.line_to(size-roundR, 0)
    cr.arc(size-roundR, roundR, roundR, 3*pi/2, 2*pi) ## up right corner
    cr.line_to(size, size-roundR)
    cr.arc(size-roundR, size-roundR, roundR, 0, pi/2) ## down right corner
    cr.line_to(roundR, size)
    cr.arc(roundR, size-roundR, roundR, pi/2, pi) ## down left corner
    cr.line_to(0, roundR)
    cr.arc(roundR, roundR, roundR, pi, 3*pi/2) ## up left corner
    ###
    cr.close_path()
    fillColor(cr, color)
    ####
    pbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, True, 8, size, size)
    colormap = gtk.gdk.colormap_get_system()
    #colormap = self.get_screen().get_system_colormap()
    #colormap = pmap.get_colormap()
    pbuf.get_from_drawable(pmap, colormap, 0, 0, 0, 0, size, size)
    if bgColor:
        pbuf = pbuf.add_alpha(True, *bgColor)
    return pbuf


def drawRoundedRect(cr, cx0, cy0, cw, ch, ro):
    ro = min(ro, cw/2.0, ch/2.0)
    cr.move_to(cx0+ro, cy0)
    cr.line_to(cx0+cw-ro, cy0)
    cr.arc(cx0+cw-ro, cy0+ro, ro, 3*pi/2, 2*pi) ## up right corner
    cr.line_to(cx0+cw, cy0+ch-ro)
    cr.arc(cx0+cw-ro, cy0+ch-ro, ro, 0, pi/2) ## down right corner
    cr.line_to(cx0+ro, cy0+ch)
    cr.arc(cx0+ro, cy0+ch-ro, ro, pi/2, pi) ## down left corner
    cr.line_to(cx0, cy0+ro)
    cr.arc(cx0+ro, cy0+ro, ro, pi, 3*pi/2) ## up left corner
    cr.close_path()


def drawCursorBg(cr, cx0, cy0, cw, ch):
    cursorRadius = ui.cursorRoundingFactor * min(cw, ch) * 0.5
    drawRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius)


def drawOutlineRoundedRect(cr, cx0, cy0, cw, ch, ro, d):
    ro = min(ro, cw/2.0, ch/2.0)
    #a = min(cw, ch); ri = ro*(a-2*d)/a
    ri = max(0, ro-d)
    #print ro, ri
    ######### Outline:
    cr.move_to(cx0+ro, cy0)
    cr.line_to(cx0+cw-ro, cy0)
    cr.arc(cx0+cw-ro, cy0+ro, ro, 3*pi/2, 2*pi) ## up right corner
    cr.line_to(cx0+cw, cy0+ch-ro)
    cr.arc(cx0+cw-ro, cy0+ch-ro, ro, 0, pi/2) ## down right corner
    cr.line_to(cx0+ro, cy0+ch)
    cr.arc(cx0+ro, cy0+ch-ro, ro, pi/2, pi) ## down left corner
    cr.line_to(cx0, cy0+ro)
    cr.arc(cx0+ro, cy0+ro, ro, pi, 3*pi/2) ## up left corner
    #### Inline:
    if ri==0:
        cr.move_to(cx0+d, cy0+d)
        cr.line_to(cx0+d, cy0+ch-d)
        cr.line_to(cx0+cw-d, cy0+ch-d)
        cr.line_to(cx0+cw-d, cy0+d)
        cr.line_to(cx0+d, cy0+d)
    else:
        cr.move_to(cx0+ro, cy0+d)## or line_to
        cr.arc_negative(cx0+ro, cy0+ro, ri, 3*pi/2, pi) ## up left corner
        cr.line_to(cx0+d, cy0+ch-ro)
        cr.arc_negative(cx0+ro, cy0+ch-ro, ri, pi, pi/2) ## down left
        cr.line_to(cx0+cw-ro, cy0+ch-d)
        cr.arc_negative(cx0+cw-ro, cy0+ch-ro, ri, pi/2, 0) ## down right
        cr.line_to(cx0+cw-d, cy0+ro)
        cr.arc_negative(cx0+cw-ro, cy0+ro, ri, 2*pi, 3*pi/2) ## up right
        cr.line_to(cx0+ro, cy0+d)
    cr.close_path()

def drawCursorOutline(cr, cx0, cy0, cw, ch):
    cursorRadius = ui.cursorRoundingFactor * min(cw, ch) * 0.5
    cursorDia = ui.cursorDiaFactor * min(cw, ch) * 0.5
    drawOutlineRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius, cursorDia)


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
        x, y = self.getAbsPos(w, h)
        cr.set_source_pixbuf(self.pixbuf, x, y)
        cr.rectangle(x, y, self.width, self.height)
        cr.fill()
    def contains(self, px, py, w, h):
        x, y = self.getAbsPos(w, h)
        return (x <= px < x+self.width and y <= py < y+self.height)

