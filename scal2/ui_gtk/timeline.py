#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Saeed Rasooli <saeed.gnu@gmail.com>
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
from time import time as now

import math
from math import pi


from scal2 import core

from scal2.locale_man import tr as _
from scal2.locale_man import rtl

from scal2.utils import toUnicode
from scal2.core import myRaise

from scal2 import ui
from scal2.timeline import *

from scal2.ui_gtk.font_utils import pfontEncode
from scal2.ui_gtk.utils import labelStockMenuItem, labelImageMenuItem
from scal2.ui_gtk.drawing import setColor, fillColor, newTextLayout, Button
from scal2.ui_gtk import gtk_ud as ud
#from scal2.ui_gtk import preferences
import scal2.ui_gtk.event.main
from scal2.ui_gtk.event.common import EventEditorDialog, GroupEditorDialog, confirmEventTrash

import gobject
from gobject import timeout_add

import cairo
import gtk
from gtk import gdk

from scal2.ui_gtk.decorators import *
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.timeline_box import *

def show_event(widget, event):
    print type(widget), event.type.value_name, event.get_value()#, event.send_event


@registerSignals
class TimeLine(gtk.Widget, ud.IntegratedCalObj):
    _name = 'timeLine'
    desc = _('Time Line')
    def centerToNow(self):
        self.stopMovingAnim()
        self.timeStart = now() - self.timeWidth/2.0
    def centerToNowClicked(self, arg=None):
        self.centerToNow()
        self.queue_draw()
    def __init__(self, closeFunc):
        gtk.Widget.__init__(self)
        self.initVars()
        ###
        self.closeFunc = closeFunc
        self.connect('expose-event', self.onExposeEvent)
        self.connect('scroll-event', self.onScroll)
        self.connect('button-press-event', self.buttonPress)
        self.connect('motion-notify-event', self.motionNotify)
        self.connect('button-release-event', self.buttonRelease)
        self.connect('key-press-event', self.keyPress)
        #self.connect('event', show_event)
        self.currentTime = now()
        self.timeWidth = dayLen
        self.timeStart = self.currentTime - self.timeWidth/2.0
        self.buttons = [
            Button('home.png', self.centerToNowClicked, 1, -1, False),
            Button('resize-small.png', self.startResize, -1, -1, False),
            Button('exit.png', closeFunc, 35, -1, False)
        ]
        ## zoom in and zoom out buttons FIXME
        self.data = None
        ########
        self.movingLastPress = 0
        self.movingV = 0
        self.movingF = 0
        #######
        self.boxEditing = None
        ## or (editType, box, x0, t0)
        ## editType=0   moving
        ## editType=-1  resizing to left
        ## editType=+1  resizing to right
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(),
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gdk.WINDOW_CHILD,
            wclass=gdk.INPUT_OUTPUT,
            event_mask=self.get_events() | gdk.EXPOSURE_MASK
            | gdk.BUTTON1_MOTION_MASK | gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK
            | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK)
            #colormap=self.get_screen().get_rgba_colormap())
        #self.window.set_composited(True)
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
        self.currentTimeUpdate()
    def currentTimeUpdate(self):
        tm = now()
        timeout_add(int(1000*(1.01-tm%1)), self.currentTimeUpdate)
        self.currentTime = int(tm)
        if self.parent:
            if self.parent.get_visible() and \
            self.timeStart <= tm <= self.timeStart + self.timeWidth + 1:
                self.queue_draw()
    def updateData(self):
        width = self.allocation.width
        self.pixelPerSec = float(width) / self.timeWidth ## pixel/second
        self.borderTm = boxMoveBorder / self.pixelPerSec ## second
        self.data = calcTimeLineData(
            self.timeStart,
            self.timeWidth,
            self.pixelPerSec,
            self.borderTm,
        )
    def drawTick(self, cr, tick, maxTickHeight):
        tickH = tick.height
        tickW = tick.width
        tickH = min(tickH, maxTickHeight)
        ###
        tickX = tick.pos - tickW/2.0
        tickY = 1
        cr.rectangle(tickX, tickY, tickW, tickH)
        try:
            fillColor(cr, tick.color)
        except:
            print 'error in fill, x=%.2f, y=%.2f, w=%.2f, h=%.2f'%(tickX, tickY, tickW, tickH)
        ###
        font = [
            fontFamily,
            False,
            False,
            tick.fontSize,
        ]
        #layout = newLimitedWidthTextLayout(
        #    self,
        #    tick.label,
        #    tick.maxLabelWidth,
        #    font=font,
        #    truncate=truncateTickLabel,
        #)## FIXME
        layout = newTextLayout(
            self,
            text=tick.label,
            font=font,
            maxSize=(tick.maxLabelWidth, 0),
            maximizeScale=1.0,
            truncate=truncateTickLabel,
        )## FIXME
        if layout:
            #layout.set_auto_dir(0)## FIXME
            #print 'layout.get_auto_dir() = %s'%layout.get_auto_dir()
            layoutW, layoutH = layout.get_pixel_size()
            layoutX = tick.pos - layoutW/2.0
            layoutY = tickH*labelYRatio
            try:
                cr.move_to(layoutX, layoutY)
            except:
                print 'error in move_to, x=%.2f, y=%.2f'%(layoutX, layoutY)
            else:
                cr.show_layout(layout)## with the same tick.color
    def drawBox(self, cr, box):
        d = box.lineW
        x = box.x
        w = box.w
        y = box.y
        h = box.h
        ###
        drawBoxBG(cr, box, x, y, w, h)
        drawBoxBorder(cr, box, x, y, w, h)
        drawBoxText(cr, box, x, y, w, h, self)
    def drawBoxEditingHelperLines(self, cr):
        if not self.boxEditing:
            return
        editType, event, box, x0, t0 = self.boxEditing
        setColor(cr, fgColor)
        d = editingBoxHelperLineWidth
        cr.rectangle(
            box.x,
            0,
            d,
            box.y,
        )
        cr.fill()
        cr.rectangle(
            box.x + box.w - d,
            0,
            d,
            box.y,
        )
        cr.fill()
    def drawAll(self, cr):
        width = self.allocation.width
        height = self.allocation.height
        pixelPerSec = self.pixelPerSec
        dayPixel = dayLen * pixelPerSec ## pixel
        maxTickHeight = maxTickHeightRatio * height
        #####
        cr.rectangle(0, 0, width, height)
        fillColor(cr, bgColor)
        #####
        setColor(cr, holidayBgBolor)
        for x in self.data['holidays']:
            cr.rectangle(x, 0, dayPixel, height)
            cr.fill()
        #####
        for tick in self.data['ticks']:
            self.drawTick(cr, tick, maxTickHeight)
        ######
        beforeBoxH = maxTickHeight ## FIXME
        maxBoxH = height - beforeBoxH
        for box in self.data['boxes']:
            box.setPixelValues(self.timeStart, pixelPerSec, beforeBoxH, maxBoxH)
            self.drawBox(cr, box)
        self.drawBoxEditingHelperLines(cr)
        ###### Draw Current Time Marker
        dt = self.currentTime - self.timeStart
        if 0 <= dt <= self.timeWidth:
            setColor(cr, currentTimeMarkerColor)
            cr.rectangle(
                dt*pixelPerSec - currentTimeMarkerWidth/2.0,
                0,
                currentTimeMarkerWidth,
                currentTimeMarkerHeightRatio * self.allocation.height
            )
            cr.fill()
        ######
        for button in self.buttons:
            button.draw(cr, width, height)
    def onExposeEvent(self, widget=None, event=None):
        #t0 = now()
        if not self.boxEditing:
            self.updateData()
        #t1 = now()
        self.drawAll(self.window.cairo_create())
        #t2 = now()
        #print 'drawing time / data calc time: %.2f'%((t2-t1)/(t1-t0))
    def onScroll(self, widget, event):
        isUp = event.direction.value_nick=='up'
        if event.state & gdk.CONTROL_MASK:
            self.zoom(
                isUp,
                scrollZoomStep, 
                float(event.x) / self.allocation.width,
            )
        else:
            self.movingUserEvent(
                direction=(-1 if isUp else 1),
            )## FIXME
        self.queue_draw()
        return True
    def buttonPress(self, obj, gevent):
        x = gevent.x
        y = gevent.y
        w = self.allocation.width
        h = self.allocation.height
        if gevent.button==1:
            for button in self.buttons:
                if button.contains(x, y, w, h):
                    button.func(gevent)
                    return True
            ####
            for box in self.data['boxes']:
                if not box.hasBorder:
                    continue
                if not box.ids:
                    continue
                if not box.contains(x, y):
                    continue
                gid, eid = box.ids
                group = ui.eventGroups[gid]
                event = group[eid]
                ####
                top = y - box.y
                left = x - box.x
                right = box.x + box.w - x
                minA = min(boxMoveBorder, top, left, right)
                editType = None
                if top == minA:
                    editType = 0
                    t0 = event.getStartEpoch()
                    self.window.set_cursor(gdk.Cursor(gdk.FLEUR))
                elif right == minA:
                    editType = 1
                    t0 = event.getEndEpoch()
                    self.window.set_cursor(gdk.Cursor(gdk.RIGHT_SIDE))
                elif left == minA:
                    editType = -1
                    t0 = event.getStartEpoch()
                    self.window.set_cursor(gdk.Cursor(gdk.LEFT_SIDE))
                if editType is not None:
                    self.boxEditing = (editType, event, box, x, t0)
                    return True
        elif gevent.button==3:
            for box in self.data['boxes']:
                if not box.ids:
                    continue
                if not box.contains(x, y):
                    continue
                gid, eid = box.ids
                group = ui.eventGroups[gid]
                event = group[eid]
                ####
                menu = gtk.Menu()
                ##
                if not event.readOnly:
                    winTitle = _('Edit') + ' ' + event.desc
                    menu.add(labelStockMenuItem(
                        winTitle,
                        gtk.STOCK_EDIT,
                        self.editEventClicked,
                        winTitle,
                        event,
                        gid,
                    ))
                ##
                winTitle = _('Edit') + ' ' + group.desc
                menu.add(labelStockMenuItem(
                    winTitle,
                    gtk.STOCK_EDIT,
                    self.editGroupClicked,
                    winTitle,
                    group,
                ))
                ##
                menu.add(gtk.SeparatorMenuItem())
                ##
                menu.add(labelImageMenuItem(
                    _('Move to %s')%ui.eventTrash.title,
                    ui.eventTrash.icon,
                    self.moveEventToTrash,
                    group,
                    event,
                ))
                ##
                menu.show_all()
                menu.popup(None, None, None, 3, 0)
        return False
    def motionNotify(self, obj, gevent):
        if self.boxEditing:
            editType, event, box, x0, t0 = self.boxEditing
            t1 = t0 + (gevent.x - x0)/self.pixelPerSec
            if editType==0:
                event.modifyPos(t1)
            elif editType==1:
                if t1-box.t0 > 2*boxMoveBorder/self.pixelPerSec:
                    event.modifyEnd(t1)
            elif editType==-1:
                if box.t1-t1 > 2*boxMoveBorder/self.pixelPerSec:
                    event.modifyStart(t1)
            box.t0 = max(
                event.getStartEpoch(),
                self.timeStart - self.borderTm,
            )
            box.t1 = min(
                event.getEndEpoch(),
                self.timeStart + self.timeWidth + self.borderTm,
            )
            self.queue_draw()
    def buttonRelease(self, obj, gevent):
        if self.boxEditing:
            editType, event, box, x0, t0 = self.boxEditing
            event.afterModify()
            event.save()
            self.boxEditing = None
        self.window.set_cursor(gdk.Cursor(gdk.LEFT_PTR))
        self.queue_draw()
    def onConfigChange(self, *a, **kw):
        ud.IntegratedCalObj.onConfigChange(self, *a, **kw)
        self.queue_draw()
    def editEventClicked(self, menu, winTitle, event, gid):
        event = EventEditorDialog(
            event,
            title=winTitle,
            #parent=self,## FIXME
        ).run()
        if event is None:
            return
        ui.reloadGroups.append(gid)
        self.onConfigChange()
    def editGroupClicked(self, menu, winTitle, group):
        group = GroupEditorDialog(group).run()
        if group is not None:
            group.afterModify()
            group.save()## FIXME
            ui.changedGroups.append(group.id)
            ud.windowList.onConfigChange()
            self.queue_draw()
    def moveEventToTrash(self, menu, group, event):
        if not confirmEventTrash(event):
            return
        eventIndex = group.index(event.id)
        ui.moveEventToTrashFromOutside(group, event)
        self.onConfigChange()
    def startResize(self, event):
        self.parent.begin_resize_drag(
            gdk.WINDOW_EDGE_SOUTH_EAST,
            event.button,
            int(event.x_root),
            int(event.y_root),
            event.time,
        )
    def zoom(self, zoomIn, stepFact, posFact):
        zoomValue = 1.0/stepFact if zoomIn else stepFact
        self.timeStart += self.timeWidth * (1-zoomValue) * posFact
        self.timeWidth *= zoomValue
    keyboardZoom = lambda self, zoomIn: self.zoom(zoomIn, keyboardZoomStep, 0.5)
    def keyPress(self, arg, event):
        k = gdk.keyval_name(event.keyval).lower()
        #print '%.3f'%now()
        if k in ('space', 'home'):
            self.centerToNow()
        elif k=='right':
            self.movingUserEvent(
                direction=1,
                smallForce=(event.state & gdk.SHIFT_MASK),
            )
        elif k=='left':
            self.movingUserEvent(
                direction=-1,
                smallForce=(event.state & gdk.SHIFT_MASK),
            )
        elif k=='down':
            self.stopMovingAnim()
        elif k in ('q', 'escape'):
            self.closeFunc()
        #elif k=='end':
        #    pass
        #elif k=='page_up':
        #    pass
        #elif k=='page_down':
        #    pass
        #elif k=='menu':# Simulate right click (key beside Right-Ctrl)
        #    #self.emit('popup-menu-cell', event.time, *self.getCellPos())
        #elif k in ('f10','m'): # F10 or m or M
        #    if event.state & gdk.SHIFT_MASK:
        #        # Simulate right click (key beside Right-Ctrl)
        #        self.emit('popup-menu-cell', event.time, *self.getCellPos())
        #    else:
        #        self.emit('popup-menu-main', event.time, *self.getMainMenuPos())
        elif k in ('plus', 'equal', 'kp_add'):
            self.keyboardZoom(True)
        elif k in ('minus', 'kp_subtract'):
            self.keyboardZoom(False)
        else:
            #print k
            return False
        self.queue_draw()
        return True
    def movingUserEvent(self, direction=1, smallForce=False):
        if enableAnimation:
            tm = now()
            #dtEvent = tm - self.movingLastPress
            self.movingLastPress = tm
            '''
                We should call a new updateMovingAnim if:
                    last key press has bin timeout, OR
                    force direction has been change, OR
                    its currently still (no speed and no force)
            '''
            if self.movingF*direction < 0 or self.movingF*self.movingV==0:
            ## or dtEvent > movingKeyTimeout
                self.movingF = direction * \
                    (movingHandSmallForce if smallForce else movingHandForce)
                self.movingV += movingV0 * direction
                self.updateMovingAnim(self.movingF, tm, tm, self.movingV, self.movingF)
        else:
            self.timeStart += direction * movingStaticStep * \
                self.timeWidth/float(self.allocation.width)
    def updateMovingAnim(self, f1, t0, t1, v0, a1):
        t2 = now()
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
            a2 = f - movingFrictionForce
        elif v1 < 0:
            a2 = f + movingFrictionForce
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


@registerSignals
class TimeLineWindow(gtk.Window, ud.IntegratedCalObj):
    _name = 'timeLineWin'
    desc = _('Time Line')
    def __init__(self):
        gtk.Window.__init__(self)
        self.initVars()
        ud.windowList.appendItem(self)
        ###
        self.resize(ud.screenW, 150)
        self.move(0, 0)
        self.set_title(_('Time Line'))
        self.set_decorated(False)
        self.connect('delete-event', self.closeClicked)
        self.connect('button-press-event', self.buttonPress)
        ###
        self.tline = TimeLine(self.closeClicked)
        self.connect('key-press-event', self.tline.keyPress)
        self.add(self.tline)
        self.tline.show()
        self.appendItem(self.tline)
    def closeClicked(self, arg=None, event=None):
        if ui.mainWin:
            self.hide()
        else:
            gtk.main_quit()## FIXME
        return True
    def buttonPress(self, obj, event):
        if event.button==1:
            px, py, mask = ud.rootWindow.get_pointer()
            self.begin_move_drag(event.button, px, py, event.time)
            return True
        return False


if __name__=='__main__':
    win = TimeLineWindow()
    #win.tline.timeWidth = 100 * minYearLenSec # 2 * 10**17
    #win.tline.timeStart = now() - win.tline.timeWidth # -10**17
    win.show()
    gtk.main()




