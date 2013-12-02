# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux
import time
from time import localtime, strftime
from time import time as now

from gobject import timeout_add
import gtk
from gtk import gdk

from scal2.ui_gtk.font_utils import *

time_rem = lambda: int(1000*(1.01-now()%1))

class ClockLabel(gtk.Label):
    #from gtk import Label
    def __init__(self, bold=False, seconds=True, selectable=False):
        gtk.Label.__init__(self)
        self.set_use_markup(True)
        self.set_selectable(selectable)
        self.bold = bold
        self.seconds = seconds
        self.running = False
        #self.connect('button-press-event', self.button_press)
        self.start()#???
    def start(self):
        self.running = True
        self.update()
    def update(self):
        if self.running:
            timeout_add(time_rem(), self.update)
            if self.seconds:
                l = '%.2d:%.2d:%.2d'%tuple(localtime()[3:6])
            else:
                l = '%.2d:%.2d'%tuple(localtime()[3:5])
            if self.bold:
                l = '<b>%s</b>'%l
            self.set_label(l)
    def stop(self):
        self.running = False
    #def button_press(self, obj, event):
    #    if event.buuton == 3:


class FClockLabel(gtk.Label):
    #from gtk import Label
    def __init__(self, format='%T', local=True, selectable=False):
        '''format is a string that used in strftime(), it can contains markup that apears in GtkLabel
        for example format can be "<b>%T</b>"
        local is bool. if True, use Local time. and if False, use GMT time.
        selectable is bool that passes to GtkLabel'''
        gtk.Label.__init__(self)
        self.set_use_markup(True)
        self.set_selectable(selectable)
        self.set_direction(gtk.TEXT_DIR_LTR)
        self.format = format
        self.local = local
        self.running = False
        #self.connect('button-press-event', self.button_press)
        self.start()#???
    def start(self):
        self.running = True
        self.update()
    def update(self):
        if self.running:
            timeout_add(time_rem(), self.update)
            if self.local:
                self.set_label(strftime(self.format))
            else:
                self.set_label(strftime(self.format, time.gmtime()))
    def stop(self):
        self.running = False



class FClockWidget(gtk.DrawingArea): ## Time is in Local
    def __init__(self, format='%T', selectable=False):
        '''format is a string that used in strftime(), it can contains markup that apears in GtkLabel
        for example format can be "<b>%T</b>"
        local is bool. if True, use Local time. and if False, use GMT time.
        selectable is bool that passes to GtkLabel'''
        gtk.DrawingArea.__init__(self)
        self.set_direction(gtk.TEXT_DIR_LTR)
        self.format = format
        self.running = False
        #self.connect('button-press-event', self.button_press)
        self.start()#???
    def start(self):
        self.running = True
        self.update()
    def update(self):
        if self.running:
            timeout_add(time_rem(), self.update)
            self.set_label(strftime(self.format))
    def stop(self):
        self.running = False
    def set_label(self, text):
        if self.get_window()==None:
            return
        self.get_window().clear()
        cr = self.get_window().cairo_create()
        cr.set_source_color(gdk.Color(0,0,0))
        lay = self.create_pango_layout(text)
        cr.show_layout(lay)
        w, h = lay.get_pixel_size()
        cr.clip()
        self.set_size_request(w, h)
        """
        textLay = self.create_pango_layout('') ## markup
        textLay.set_markup(text)
        textLay.set_font_description(pango.FontDescription(ui.getFont()))
        w, h = textLay.get_pixel_size()
        pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, True, 8, w, h)
        pixbuf = pixbuf.add_alpha(True, '0','0','0')
        pmap, mask = pixbuf.render_pixmap_and_mask(alpha_threshold=127) ## pixmap is also a drawable
        pmap.draw_layout(pmap.new_gc(), 0, 0, textLay, trayTextColor)#, trayBgColor)
        self.clear()
        #self.set_from_image(pmap.get_image(0, 0, w, h), mask)
        self.set_from_pixmap(pmap, mask)

    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
                                                         self.get_parent_window(),
                                                         width=self.allocation.width,
                                                         height=self.allocation.height,
                                                         window_type=gdk.WINDOW_CHILD,
                                                         wclass=gdk.INPUT_OUTPUT,
                                                         event_mask=self.get_events() | gdk.EXPOSURE_MASK
                                                         | gdk.BUTTON1_MOTION_MASK | gdk.BUTTON_PRESS_MASK
                                                         | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK)
        self.get_window().set_user_data(self)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.get_window().move_resize(*self.allocation)
        """


