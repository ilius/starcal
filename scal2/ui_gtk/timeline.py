#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import time

from scal2 import core

#from scal2.locale_man import tr as _
#from scal2.locale_man import rtl, rtlSgn

from scal2.core import myRaise, getCurrentTimeZone
                       
from scal2 import ui
from scal2.timeline import *

from scal2.ui_gtk.drawing import setColor, fillColor, newLimitedWidthTextLayout, Button
#from scal2.ui_gtk import preferences

import gobject
import gtk
from gtk import gdk

def show_event(widget, event):
    print type(widget), event.type.value_name, event.get_time()#, event.send_event

rootWindow = gdk.get_default_root_window() ## Good Place?????



class TimeLine(gtk.Widget):
    def centerToNow(self):
        self.timeStart = time.time() + getCurrentTimeZone() - self.timeWidth/2.0
    def centerToNowClicked(self, arg=None):
        self.centerToNow()
        self.queue_draw()
    def __init__(self, closeFunc):
        gtk.Widget.__init__(self)
        self.connect('expose-event', self.onExposeEvent)
        self.connect('scroll-event', self.onScroll)
        self.connect('button-press-event', self.buttonPress)
        #self.connect('event', show_event)
        self.timeWidth = 24*3600
        self.centerToNow()
        self.buttons = [
            Button('week-home.png', self.centerToNowClicked, 1, -1, False),
            Button('week-small.png', self.startResize, -1, -1, False),
            Button('week-exit.png', closeFunc, 35, -1, False)
        ]
        ## zoom in and zoom out buttons FIXME
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
            #colormap=self.get_screen().get_rgba_colormap())
        #self.window.set_composited(True)
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
    def onExposeEvent(self, widget=None, event=None):
        width = self.allocation.width
        height = self.allocation.height
        maxTickHeight = maxTickHeightRatio*height
        cr = self.window.cairo_create()
        cr.rectangle(0, 0, width, height)
        fillColor(cr, bgColor)
        setColor(cr, fgColor)
        for tick in splitTime(self.timeStart, self.timeWidth, width):
            tickH = tick.height
            tickW = tick.width
            tickH = min(tickH, maxTickHeight)
            ###
            tickX = tick.pos-tickW/2.0
            tickY = 1
            cr.rectangle(tickX, tickY, tickW, tickH)
            try:
                cr.fill()
            except:
                print 'error in fill, x=%.2f, y=%.2f, w=%.2f, h=%.2f'%(tickX, tickY, tickW, tickH)
            ###
            font = (
                fontFamily,
                False,
                False,
                tick.fontSize,
            )
            layout = newLimitedWidthTextLayout(self, tick.label, tick.maxLabelWidth, font=font, truncate=tick.truncateLabel)## FIXME
            if layout:
                layoutW, layoutH = layout.get_pixel_size()
                layoutX = tick.pos - layoutW/2.0
                layoutY = tickH*labelYRatio
                try:
                    cr.move_to(layoutX, layoutY)
                except:
                    print 'error in move_to, x=%.2f, y=%.2f'%(layoutX, layoutY)
                else:
                    cr.show_layout(layout)
        for button in self.buttons:
            button.draw(cr, width, height)
    def onScroll(self, widget, event):
        isUp = event.direction.value_nick=='up'
        if event.state & gdk.CONTROL_MASK:
            timeLeft = event.x*self.timeWidth/self.allocation.width
            zoomTime = self.timeStart + timeLeft
            zoomValue = 1.0/scrollZoomStep if isUp else scrollZoomStep
            self.timeStart = zoomTime - timeLeft*zoomValue
            self.timeWidth = self.timeWidth*zoomValue
        else:
            self.timeStart += (1 if isUp else -1)*scrollMoveStep*self.timeWidth/float(self.allocation.width)
        self.queue_draw()
        return True            
    def buttonPress(self, obj, event):
        x = event.x
        y = event.y
        w = self.allocation.width
        h = self.allocation.height
        if event.button==1:
            for button in self.buttons:
                if button.contains(x, y, w, h):
                    button.func(event)
                    return True
        return False
    def startResize(self, event):
        self.parent.begin_resize_drag(
            gdk.WINDOW_EDGE_SOUTH_EAST,
            event.button,
            int(event.x_root),
            int(event.y_root), 
            event.time,
        )


class TimeLineWindow(gtk.Window):
    def __init__(self, mainWin=None):
        gtk.Window.__init__(self)
        self.set_decorated(False)
        self.connect('delete-event', self.closeClicked)
        self.connect('button-press-event', self.buttonPress)
        self.tline = TimeLine(self.closeClicked)
        self.add(self.tline)
        self.tline.show()
    def closeClicked(self, arg=None):
        #self.hide()
        gtk.main_quit()## FIXME
        return True
    def buttonPress(self, obj, event):
        if event.button==1:
            (px, py, mask) = rootWindow.get_pointer()
            self.begin_move_drag(event.button, px, py, event.time)
            return True
        return False

gobject.type_register(TimeLine)

if __name__=='__main__':
    win = TimeLineWindow()
    win.resize(rootWindow.get_geometry()[2], 150)
    win.move(0, 0)
    win.show()
    gtk.main()




