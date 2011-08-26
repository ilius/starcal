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

from scal2.locale_man import tr as _
from scal2.locale_man import rtl

from scal2.core import myRaise, getCurrentTimeZone
                       
from scal2 import ui
from scal2.timeline import *

from scal2.ui_gtk.drawing import setColor, fillColor, newLimitedWidthTextLayout, Button
#from scal2.ui_gtk import preferences
import scal2.ui_gtk.events_gtk

import gobject
from gobject import timeout_add

import gtk
from gtk import gdk

def show_event(widget, event):
    print type(widget), event.type.value_name, event.get_time()#, event.send_event

rootWindow = gdk.get_default_root_window() ## Good Place?????

getCurrentTime = lambda: time.time() + getCurrentTimeZone()

class TimeLine(gtk.Widget):
    def centerToNow(self):
        self.stopMovingAnim()
        self.timeStart = getCurrentTime() - self.timeWidth/2.0
    def centerToNowClicked(self, arg=None):
        self.centerToNow()
        self.queue_draw()
    def __init__(self, closeFunc):
        gtk.Widget.__init__(self)
        self.connect('expose-event', self.onExposeEvent)
        self.connect('scroll-event', self.onScroll)
        self.connect('button-press-event', self.buttonPress)
        self.connect('key-press-event', self.keyPress)
        #self.connect('event', show_event)
        self.currentTime = getCurrentTime()
        self.timeWidth = 24*3600
        self.timeStart = self.currentTime - self.timeWidth/2.0
        self.buttons = [
            Button('week-home.png', self.centerToNowClicked, 1, -1, False),
            Button('week-small.png', self.startResize, -1, -1, False),
            Button('week-exit.png', closeFunc, 35, -1, False)
        ]
        ## zoom in and zoom out buttons FIXME
        ########
        self.movingLastPress = 0
        self.movingV = 0
        self.movingF = 0
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
        self.currentTimeUpdate()
    def currentTimeUpdate(self):
        tm = getCurrentTime()
        timeout_add(int(1000*(1.01-tm%1)), self.currentTimeUpdate)
        self.currentTime = int(tm)
        if self.timeStart <= tm <= self.timeStart + self.timeWidth + 1:
            self.queue_draw()
    def onExposeEvent(self, widget=None, event=None):
        width = self.allocation.width
        height = self.allocation.height
        pixelPerSec = float(self.allocation.width)/self.timeWidth ## pixel/second
        dayPixel = 24*3600*pixelPerSec ## pixel
        maxTickHeight = maxTickHeightRatio*height
        #####
        cr = self.window.cairo_create()
        cr.rectangle(0, 0, width, height)
        fillColor(cr, bgColor)
        data = calcTimeLineData(self.timeStart, self.timeWidth, width)
        #####
        setColor(cr, holidayBgBolor)
        for x in data['holidays']:
            cr.rectangle(x, 0, dayPixel, height)
            cr.fill()
        #####
        for tick in data['ticks']:
            tickH = tick.height
            tickW = tick.width
            tickH = min(tickH, maxTickHeight)
            ###
            tickX = tick.pos-tickW/2.0
            tickY = 1
            cr.rectangle(tickX, tickY, tickW, tickH)
            try:
                fillColor(cr, tick.color)
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
                    cr.show_layout(layout)## with the same tick.color
        ######
        baforBoxH = maxTickHeight ## FIXME
        maxBoxH = height - baforBoxH
        d = boxLineWidth
        for box in data['boxes']:
            x = (box.t0-self.timeStart)*pixelPerSec
            w = (box.t1 - box.t0)*pixelPerSec
            y = baforBoxH + maxBoxH * box.y0
            h = maxBoxH * (box.y1 - box.y0)
            ###
            cr.rectangle(x, y, w, h)
            fillColor(cr, (
                box.color[0],
                box.color[1],
                box.color[2],
                int(box.color[3]*boxInnerAlpha),
            ))
            ###
            cr.move_to(x, y)
            cr.line_to(x+w, y)
            cr.line_to(x+w, y+h)
            cr.line_to(x, y+h)
            cr.line_to(x, y)
            cr.line_to(x+d, y)
            cr.line_to(x+d, y+h-d)
            cr.line_to(x+w-d, y+h-d)
            cr.line_to(x+w-d, y+d)
            cr.line_to(x+d, y+d)
            cr.close_path()
            fillColor(cr, box.color)
        ######
        if self.timeStart <= self.currentTime <= self.timeStart + self.timeWidth:
            setColor(cr, currenTimeMarkerColor)
            cr.rectangle(
                (self.currentTime-self.timeStart)*pixelPerSec - currentTimeMarkerWidth/2.0,
                0,
                currentTimeMarkerWidth,
                currentTimeMarkerHeightRatio * self.allocation.height
            )
            cr.fill()
        ######
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
            self.movingUserEvent(-1 if isUp else 1)## FIXME
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
    def keyPress(self, arg, event):
        k = gdk.keyval_name(event.keyval).lower()
        #print '%.3f'%time.time()
        if k in ('space', 'home'):
            self.centerToNow()
        elif k=='right':
            self.movingUserEvent(1)
        elif k=='left':
            self.movingUserEvent(-1)
        elif k=='down':
            self.stopMovingAnim()
        elif k=='q':
            gtk.main_quit()## FIXME
        #elif k=='end':
        #    pass
        #elif k=='page_up':
        #    pass
        #elif k=='page_down':
        #    pass
        #elif k=='menu':# Simulate right click (key beside Right-Ctrl)
        #    #self.emit('popup-menu-cell', event.time, *self.getCellPos())
        #elif k in ('f10','m'):	# F10 or m or M
        #    if event.state & gdk.SHIFT_MASK:
        #        # Simulate right click (key beside Right-Ctrl)
        #        self.emit('popup-menu-cell', event.time, *self.getCellPos())
        #    else:
        #        self.emit('popup-menu-main', event.time, *self.getMainMenuPos())
        else:
            return False
        self.queue_draw()
        return True
    def movingUserEvent(self, force=1):
        if enableAnimation:
            tm = time.time()
            #dtEvent = tm - self.movingLastPress
            self.movingLastPress = tm
            '''
                We should call a new updateMovingAnim if:
                    last key press has bin timeout, OR
                    force direction has been change, OR
                    its currently still (no speed and no force)
            '''
            if self.movingF*force < 0 or self.movingF*self.movingV==0:## or dtEvent > movingKeyTimeout
                self.movingF = force * movingHandForce
                self.movingV += movingV0*force
                self.updateMovingAnim(self.movingF, tm, tm, self.movingV, self.movingF)
        else:
            self.timeStart += force * staticMoveStep * self.timeWidth/float(self.allocation.width)
    def updateMovingAnim(self, f1, t0, t1, v0, a1):
        t2 = time.time()
        f = self.movingF
        if f!=f1:
            return
        v1 = self.movingV
        if f==0 and v1==0:
            return
        timeout = movingKeyTimeoutFirst if t2-t0<movingKeyTimeoutFirst else movingKeyTimeout
        if f!=0 and t2 - self.movingLastPress >= timeout:## Stopping
            f = self.movingF = 0
        if v1 > 0:
            a2 = f - movingSurfaceForce
        elif v1 < 0:
            a2 = f + movingSurfaceForce
        else:
            a2 = f
        if a2 != a1:
            return self.updateMovingAnim(f, t2, t2, v1, a2)
        v2 = v0 + a2*(t2-t0)
        if v2 > movingMaxSpeed:
            v2 = movingMaxSpeed
        elif v2 < -movingMaxSpeed:
            v2 = -movingMaxSpeed
        if f==0 and v1*v2 <= 0:
            self.movingV = 0
            return
        timeout_add(movingUpdateTime, self.updateMovingAnim, f, t0, t2, v0, a2)
        self.movingV = v2
        self.timeStart += v2 * (t2-t1) * self.timeWidth/float(self.allocation.width)
        self.queue_draw()
    def stopMovingAnim(self):## stop moving immudiatly
        self.movingF = 0
        self.movingV = 0


class TimeLineWindow(gtk.Window):
    def __init__(self, mainWin=None):
        gtk.Window.__init__(self)
        self.set_title(_('Time Line'))
        self.set_decorated(False)
        self.connect('delete-event', self.closeClicked)
        self.connect('button-press-event', self.buttonPress)
        self.tline = TimeLine(self.closeClicked)
        self.connect('key-press-event', self.tline.keyPress)
        self.add(self.tline)
        self.tline.show()
    def closeClicked(self, arg=None, event=None):
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
setRandomColorsToEvents()

if __name__=='__main__':
    gtk.window_set_default_icon_from_file(ui.logo)
    if rtl:
        gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)
    win = TimeLineWindow()
    win.resize(rootWindow.get_geometry()[2], 150)
    win.move(0, 0)
    win.show()
    gtk.main()




