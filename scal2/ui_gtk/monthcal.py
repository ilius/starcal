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

from time import time, localtime

import sys, os
from os.path import join, isfile
from math import pi, sqrt

from scal2.locale_man import rtl, rtlSgn
from scal2.locale_man import tr as _

from scal2 import core
from scal2.core import log, myRaise, getMonthName, getMonthLen, getNextMonth, getPrevMonth, pixDir

from scal2 import ui
from scal2.monthcal import getMonthStatus, getCurrentMonthStatus

from scal2.ui_gtk.drawing import *
from scal2.ui_gtk import listener
from scal2.ui_gtk import gcommon
from scal2.ui_gtk import preferences
from scal2.ui_gtk.customize import CustomizableCalObj

#from scal2.ui_gtk import desktop
#from scal2.ui_gtk import wallpaper

import gobject
import gtk
from gtk import gdk

from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton

class MonthCal(gtk.Widget, CustomizableCalObj):
    cx = [0, 0, 0, 0, 0, 0, 0]
    def heightSpinChanged(self, spin):
        h = spin.get_value()
        self.set_property('height-request', h)
        ui.calHeight = h
    confStr = lambda self: 'ui.calHeight=%r\n'%ui.calHeight
    def __init__(self, shownCals=ui.shownCals):
        gtk.Widget.__init__(self)
        self.set_property('height-request', ui.calHeight)
        ######
        hbox = gtk.HBox()
        spin = IntSpinButton(1, 999)
        spin.set_value(ui.calHeight)
        spin.connect('changed', self.heightSpinChanged)
        hbox.pack_start(gtk.Label(_('Height:')), 0, 0)
        hbox.pack_start(spin, 0, 0)
        self.initVars('monthCal', _('Month Calendar'), optionsWidget=hbox)
        ######
        self.shownCals = shownCals
        ######################
        #self.kTime = 0
        ######################
        self.drag_source_set(gdk.MODIFIER_MASK,(('',0,0),),gdk.ACTION_COPY)
        self.drag_source_add_text_targets()
        self.connect('drag-data-get', self.dragDataGet)
        self.connect('drag-begin', self.dragBegin)
        self.connect('drag-data-received', self.dragDataRec)
        self.drag_dest_set(
            gdk.MODIFIER_MASK,
            (
                ('', 0, 0),
                ('application/x-color', 0, 0),
            ),
            gdk.ACTION_COPY,
        )
        self.drag_dest_add_text_targets()
        self.drag_dest_add_uri_targets()
        """
        ## ACTION_MOVE ?????????????????????
        ## if source ACTION was ACTION_COPY, calendar recieves its own dragged day
        ## just like gnome-calendar-applet (but it seems not a logical behaviar)
        #self.drag_source_add_uri_targets()#???????
        ##self.connect('drag-end', self.dragCalEnd)
        ##self.connect('drag-drop', self.dragCalDrop)
        ##self.connect('drag-failed', self.dragCalFailed)
        #self.connect('drag-leave', self.dragLeave)
        """
        ######################
        self.connect('expose-event', self.drawAll)
        self.connect('button-press-event', self.buttonPress)
        #self.connect('screen-changed', self.screenChanged)
        self.myKeys = (
            'up', 'down', 'right', 'left', 'page_up', 'page_down',
            'space', 'home', 'end', 'menu', 'f10', 'm',
        )
        self.connect('key-press-event', self.keyPress)
        self.connect('scroll-event', self.scroll)
        ######################
        self.updateTextWidth()
        ######################
        listener.dateChange.add(self)
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(),
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gdk.WINDOW_CHILD,
            wclass=gdk.INPUT_OUTPUT,
            event_mask=self.get_events() \
                | gdk.EXPOSURE_MASK | gdk.BUTTON1_MOTION_MASK | gdk.BUTTON_PRESS_MASK
                | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK
        )
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
    def drawAll(self, widget=None, event=None, cr=None, cursor=True):
        #?????? Must enhance (only draw few cells, not all cells)
        #print time(), 'drawAll'#, tuple(event.area), tuple(self.allocation)
        if event:
            (xu, yu, wu, hu) = tuple(event.area)
            #print 'expose-event area:', xu, yu, wu, hu
        self.calcCoord()
        x, y, w, h = self.allocation
        if not cr:
            cr = self.window.cairo_create()
            #cr.set_line_width(0)#??????????????
            #cr.scale(0.5, 0.5)
        """
        wx = ui.winX
        wy = ui.winY
        if ui.bgUseDesk:## FIXME
            ### ????????????????? Need for mainWin !!!!!
            coord = self.translate_coordinates(self, wx, wy)
            if len(coord)==2:
                (x0, y0) = coord
                try:
                    bg = desktop.get_wallpaper(x0, y0, w, h)
                except:
                    print 'Could not get wallpaper!'
                    myRaise(__file__)
                    os.popen('gnome-settings-daemon')
                    ui.bgUseDesk = False ##??????????????????
                    #self.prefDialog.checkDeskBg.set_active(False)##??????????????????
                else:
                    cr.set_source_pixbuf(bg, 0, 0)
                    cr.paint()
            else:
                print coord
        """
        cr.rectangle(0, 0, w, h)
        fillColor(cr, ui.bgColor)
        status = getCurrentMonthStatus()
        #################################### Drawing Border
        if ui.mcalTopMargin>0:
            ##### Drawing border top background
            ##menuBgColor == borderColor ##???????????????
            cr.rectangle(0, 0, w, ui.mcalTopMargin)
            fillColor(cr, ui.borderColor)
            ######## Drawing weekDays names
            setColor(cr, ui.borderTextColor)
            dx = 0
            wdayAb = (self.wdaysWidth > w)
            for i in xrange(7):
                wday = newTextLayout(self, core.getWeekDayAuto(i, wdayAb))
                try:
                    (fontw, fonth) = wday.get_pixel_size()
                except:
                    myRaise(__file__)
                    (fontw, fonth) = wday.get_pixel_size()
                cr.move_to(
                    self.cx[i]-fontw/2.0,
                    (ui.mcalTopMargin-fonth)/2.0-1,
                )
                cr.show_layout(wday)
            ######## Drawing "Menu" label
            setColor(cr, ui.menuTextColor)
            text = newTextLayout(self, _('Menu'))
            (fontw, fonth) = text.get_pixel_size()
            if rtl:
                cr.move_to(
                    w-(ui.mcalLeftMargin+fontw)/2.0 - 3,
                    (ui.mcalTopMargin-fonth)/2.0 - 1,
                )
            else:
                cr.move_to(
                    (ui.mcalLeftMargin-fontw)/2.0,
                    (ui.mcalTopMargin-fonth)/2.0 - 1,
                )
            cr.show_layout(text)
        if ui.mcalLeftMargin>0:
            ##### Drawing border left background
            if rtl:
                cr.rectangle(w-ui.mcalLeftMargin, ui.mcalTopMargin, ui.mcalLeftMargin, h-ui.mcalTopMargin)
            else:
                cr.rectangle(0, ui.mcalTopMargin, ui.mcalLeftMargin, h-ui.mcalTopMargin)
            fillColor(cr, ui.borderColor)
            ##### Drawing week numbers
            setColor(cr, ui.borderTextColor)
            for i in xrange(6):
                lay = newTextLayout(self, _(status.weekNum[i]))
                fontw, fonth = lay.get_pixel_size()
                if rtl:
                    cr.move_to(
                        w-(ui.mcalLeftMargin+fontw)/2.0,
                        self.cy[i]-fonth/2.0+2,
                    )
                else:
                    cr.move_to(
                        (ui.mcalLeftMargin-fontw)/2.0,
                        self.cy[i]-fonth/2.0+2,
                    )
                cr.show_layout(lay)
        selectedCellPos = ui.cell.monthPos
        shown = self.shownCals
        if ui.todayCell.inSameMonth(ui.cell):
            (tx, ty) = ui.todayCell.monthPos ## today x and y
            x0 = self.cx[tx] - self.dx/2.0
            y0 = self.cy[ty] - self.dy/2.0
            cr.rectangle(x0, y0, self.dx, self.dy)
            fillColor(cr, ui.todayCellColor)
        for yPos in xrange(6):
            for xPos in xrange(7):
                c = status[yPos][xPos]
                x0 = self.cx[xPos]
                y0 = self.cy[yPos]
                cellInactive = (c.month != ui.cell.month)
                cellHasCursor = (cursor and (xPos, yPos) == selectedCellPos)
                if cellHasCursor:
                    ##### Drawing Cursor
                    d = ui.cursorD
                    if ui.cursorFixed:
                        cx0 = x0-ui.cursorW/2.0 - d
                        cy0 = y0-ui.cursorH/2.0 - d
                        cw = ui.cursorW + 2*d
                        ch = ui.cursorH + 2*d
                    else:
                        cx0 = x0-self.dx/2.0+1
                        cy0 = y0-self.dy/2.0+1
                        cw = self.dx-1
                        ch = self.dy-1
                    if ui.cursorR==0:
                        cr.rectangle(cx0, cy0, cw, ch)
                        fillColor(cr, ui.cursorBgColor)
                    else:
                        if ui.cursorCornerOval:
                            ## Oval Rounded
                            yscale = float(ch/cw)
                            cr.scale(1, yscale)
                            cy0 /= yscale
                            ch = cw
                        ######### Circular Rounded
                        ro = min(ui.cursorR, cw/2, ch/2)
                        #a = min(cw, ch); ri = ro*(a-2*d)/a
                        ri = max(ro-d, 0)
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
                        ####
                        cr.close_path()
                        fillColor(cr, ui.cursorBgColor)
                        if ui.cursorCornerOval:
                            cr.scale(1, 1.0/yscale)
                ######## end of Drawing Cursor
                if not cellInactive:
                    iconList = []
                    for item in c.eventsData:
                        icon = item['icon']
                        if icon and not icon in iconList:
                            iconList.append(icon)
                    if iconList:
                        iconsN = len(iconList)
                        scaleFact = 1.0 / sqrt(iconsN)
                        fromRight = 0
                        for index, icon in enumerate(iconList):
                            ## if len(iconList) > 1 ## FIXME
                            try:
                                pix = gdk.pixbuf_new_from_file(icon)
                            except:
                                myRaise(__file__)
                                continue
                            pix_w = pix.get_width()
                            pix_h = pix.get_height()
                            ## right buttom corner ?????????????????????
                            x1 = (self.cx[xPos] + self.dx/2.0)/scaleFact - fromRight - pix_w # right side
                            y1 = (self.cy[yPos] + self.dy/2.0)/scaleFact - pix_h # buttom side
                            cr.scale(scaleFact, scaleFact)
                            cr.set_source_pixbuf(pix, x1, y1)
                            cr.rectangle(x1, y1, pix_w, pix_h)
                            cr.fill()
                            cr.scale(1.0/scaleFact, 1.0/scaleFact)
                            fromRight += pix_w
                #### Drawing numbers inside every cell
                #cr.rectangle(
                #    x0-self.dx/2.0+1,
                #    y0-self.dy/2.0+1,
                #    self.dx-1,
                #    self.dy-1,
                #)
                if shown[0]['enable']:
                    mode = shown[0]['mode']
                    daynum = newTextLayout(self, _(c.dates[mode][2], mode), shown[0]['font'])
                    (fontw, fonth) = daynum.get_pixel_size()
                    if cellInactive:
                        setColor(cr, ui.inactiveColor)
                    elif c.holiday:
                        setColor(cr, ui.holidayColor)
                    else:
                        setColor(cr, shown[0]['color'])
                    cr.move_to(
                        x0 - fontw/2.0 + shown[0]['x'],
                        y0 - fonth/2.0 + shown[0]['y'],
                    )
                    cr.show_layout(daynum)
                if not cellInactive:
                    for item in shown[1:]:
                        if item['enable']:
                            mode = item['mode']
                            daynum = newTextLayout(self, _(c.dates[mode][2], mode), item['font'])
                            (fontw, fonth) = daynum.get_pixel_size()
                            setColor(cr, item['color'])
                            cr.move_to(
                                x0 - fontw/2.0 + item['x'],
                                y0 - fonth/2.0 + item['y'],
                            )
                            cr.show_layout(daynum)
                    if cellHasCursor:
                        ##### Drawing Cursor Outline
                        d = ui.cursorD
                        if ui.cursorFixed:
                            cx0 = x0 - ui.cursorW/2.0 - d
                            cy0 = y0 - ui.cursorH/2.0 - d
                            cw = ui.cursorW + 2*d
                            ch = ui.cursorH + 2* d
                        else:
                            cx0 = x0-self.dx/2.0+1
                            cy0 = y0-self.dy/2.0+1
                            cw = self.dx-1
                            ch = self.dy-1
                        setColor(cr, ui.cursorOutColor)
                        if ui.cursorR==0:
                            cr.rectangle(cx0, cy0, cw, d)
                            cr.fill()
                            cr.rectangle(cx0, cy0+ch-d, cw, d)
                            cr.fill()
                            cr.rectangle(cx0, cy0, d, ch)
                            cr.fill()
                            cr.rectangle(cx0+cw-d, cy0, d, ch)
                            cr.fill()
                        else:
                            if ui.cursorCornerOval:
                                ## Oval Rounded
                                yscale = float(ch/cw)
                                cr.scale(1, yscale)
                                cy0 /= yscale
                                ch = cw
                            ######### Circular Rounded
                            ro = min(ui.cursorR, cw/2, ch/2)
                            #a = min(cw, ch); ri = ro*(a-2*d)/a
                            ri = max(ro-d, 0)
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
                            cr.move_to(cx0+ro, cy0+d) ## or line to?
                            cr.arc_negative(cx0+ro, cy0+ro, ri, 3*pi/2, pi) ## up left corner
                            cr.line_to(cx0+d, cy0+ch-ro)
                            cr.arc_negative(cx0+ro, cy0+ch-ro, ri, pi, pi/2) ## down left
                            cr.line_to(cx0+cw-ro, cy0+ch-d)
                            cr.arc_negative(cx0+cw-ro, cy0+ch-ro, ri, pi/2, 0) ## down right
                            cr.line_to(cx0+cw-d, cy0+ro)
                            cr.arc_negative(cx0+cw-ro, cy0+ro, ri, 2*pi, 3*pi/2) ## up right
                            cr.line_to(cx0+ro, cy0+d)
                            ####
                            cr.close_path()
                            cr.fill()
                            if ui.cursorCornerOval:
                                cr.scale(1, 1.0/yscale)
                        ##### end of Drawing Cursor Outline
        ################ end of drawing cells
        ##### drawGrid
        if ui.calGrid:
            setColor(cr, ui.gridColor)
            for i in xrange(7):
                cr.rectangle(self.cx[i]+rtlSgn()*self.dx/2.0, 0, 1, h)
                cr.fill()
            for i in xrange(6):
                cr.rectangle(0, self.cy[i]-self.dy/2.0, w, 1)
                cr.fill()
        return False
    def dragDataGet(self, obj, context, selection, target_id, etime):
        text = '%.2d/%.2d/%.2d'%ui.cell.dates[ui.dragGetMode]
        #selection.set(selection.target, 8, text)
        selection.set_text(text)
        return True
    def dragLeave(self, obj, context, etime):
        #print 'dragLeave'
        #context.drag_status(gdk.ACTION_ASK, etime)
        #context.finish(False, True, etime)
        context.drop_reply(False, etime)
        #context.drop_finish(False, etime)
        #context.drag_abort(etime)##Segmentation fault
        return True
    def dragDataRec(self, obj, context, x, y, selection, target_id, etime):
        try:
            dtype = selection.get_data_type()
        except AttributeError:## Old PyGTK
            dtype = selection.type
        text = selection.get_text()
        ## data_type: "UTF8_STRING", "application/x-color", "text/uri-list",
        if dtype=='UTF8_STRING':
            #text = selection.get_text()
            #print 'Dropped text "%s"'%text
            if text.startswith('file://'):
                path = core.urlToPath(text)
                try:
                    t = os.stat(path).st_mtime ## modification time
                except OSError:
                    print 'Dropped invalid file "%s"'%path
                else:
                    (y, m, d) = localtime(t)[:3]
                    #print 'Dropped file "%s", modification time: %s/%s/%s'%(path, y, m, d)
                    self.changeDate(y, m, d, core.DATE_GREG)
                """
            elif text.startswith('#') and len(text)>=7:## not occures! disable it????
                ui.bgColor = ui.htmlColorToGdk(text)
                self.emit('pref-update-bg-color')
                self.queue_draw()"""
            else:
                date = ui.parseDroppedDate(text)
                if date:
                    (y, m, d) = date
                    self.changeDate(y, m, d, ui.dragRecMode)
                else:
                    ## Hot to deny(throw down) dragged object (to return to it's first location)
                    ##??????????????????????????????????????????????????????
                    print 'Dropped unknown text "%s"'%text
                    #print etime
                    #context.drag_status(gdk.ACTION_DEFAULT, etime)
                    #context.drop_reply(False, etime)
                    #context.drag_abort(etime)##Segmentation fault
                    #context.drop_finish(False, etime)
                    #context.finish(False, True, etime)
                    #return True
        elif dtype=='application/x-color':
            ## selection.get_text() == None
            text = selection.data
            ui.bgColor = (
                ord(text[1]),
                ord(text[3]),
                ord(text[5]),
                ord(text[7]),
            )
            self.emit('pref-update-bg-color')
            self.queue_draw()
        elif dtype=='text/uri-list':
                path = core.urlToPath(selection.data)
                try:
                    t = os.stat(path).st_mtime ## modification time
                except OSError:
                    print 'Dropped invalid uri "%s"'%path
                    return True
                else:
                    (y, m, d) = localtime(t)[:3]
                    self.changeDate(y, m, d, core.DATE_GREG)
        else:
            print 'Unknown dropped data type "%s", text="%s", data="%s"'%(dtype, text, selection.data)
            return True
        return False
    def dragBegin(self, obj, context):
        ui.focusTime = time()
        if ui.dragIconCell:
            (xPos, yPos) = ui.cell.monthPos
            if ui.cursorFixed:
                x = int(self.cx[xPos]-ui.cursorW/2.0-ui.cursorD)
                y = int(self.cy[yPos]-ui.cursorH/2.0-ui.cursorD)
                w = int(ui.cursorW + 2*ui.cursorD)
                h = int(ui.cursorH + 2*ui.cursorD)
            else:
                x = int(self.cx[xPos]-self.dx/2.0+1)
                y = int(self.cy[yPos]-self.dy/2.0+1)
                w = int(self.dx)
                h = int(self.dy)
            (px, py) = self.pointer
            pmap = gdk.Pixmap(self.window, w, h, self.window.get_depth())
            #print self.window.get_visual().depth, self.window.get_depth(), pmap.get_depth(), pmap.get_visual().depth
            pmap.set_colormap(self.window.get_colormap())
            pmap.draw_drawable(pmap.new_gc(), self.window, x, y, 0, 0, w, h)## a black thin outline FIXME
            """cr = pmap.cairo_create()
            cr.set_line_width(0)#??????????????
            cr.rectangle(0, 0, w, h)
            fillColor(cr, ui.cursorOutColor)"""
            pbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, True, 8, w , h)
            #pbuf.get_from_drawable(self.window,
            #    self.get_screen().get_system_colormap() , x, y, 0, 0, w, h)
            pbuf.get_from_drawable(self.window, self.window.get_colormap() , x, y, 0, 0, w, h)
            ########## Making Cursor Mask
            ## if ui.cursorCornerOval ## FIXME
            mask = gdk.Pixmap(None, w, h, 1)
            cr = mask.cairo_create()
            cr.rectangle(0, 0, w, h)
            cr.set_operator(cairo.OPERATOR_CLEAR)
            cr.fill()
            cr.set_operator(cairo.OPERATOR_SOURCE)
            if ui.cursorR==0:
                cr.rectangle(0, 0, w, h)
                cr.fill()
                return mask
            ## Circular Rounded
            ro = min(ui.cursorR, w/2, h/2)
            ## Outline:
            x0 = y0 = 0
            #e = 0.2
            #x0 = y0 = e
            #w -= 2*x0
            #h -= 2*y0
            ####
            cr.move_to(x0+ro, y0)
            cr.line_to(x0+w-ro, y0)
            cr.arc(x0+w-ro, y0+ro, ro, 3*pi/2, 2*pi) ## up right corner
            cr.line_to(x0+w, y0+h-ro)
            cr.arc(x0+w-ro, y0+h-ro, ro, 0, pi/2) ## down right corner
            cr.line_to(x0+ro, y0+h)
            cr.arc(x0+ro, y0+h-ro, ro, pi/2, pi) ## down left corner
            cr.line_to(x0, y0+ro)
            cr.arc(x0+ro, y0+ro, ro, pi, 3*pi/2) ## up left corner
            #####
            cr.close_path()
            cr.fill()
            ############ End of Making Cursor Mask
            #context.set_icon_pixmap(self.get_screen().get_system_colormap(), pmap, mask, px-x, py-y)
            #pbuf.add_alpha(True, '0', '0', '0')
            #context.set_icon_pixbuf(pbuf, px-x, py-y)
            pmap = gdk.Pixmap(None, w, h, 24) ##???????????????????
            pmap.draw_pixbuf(pmap.new_gc(), pbuf, 0, 0, 0, 0)
            ##, width=-1, height=-1, dither=gtk.gdk.RGB_DITHER_NORMAL, x_dither=0, y_dither=0)
            context.set_icon_pixmap(pmap.get_colormap(), pmap, mask, px-x, py-y)
            return True
        #############################################
        text = '%.2d/%.2d/%.2d'%ui.cell.dates[ui.dragGetMode]
        textLay = newTextLayout(self, text)
        (w, h) = textLay.get_pixel_size()
        pmap = gdk.Pixmap(None, w, h, 24)
        pmap.set_colormap(self.get_screen().get_system_colormap())
        gc = pmap.new_gc()
        gc.set_foreground(rgbToGdkColor(*ui.bgColor))
        pmap.draw_rectangle(gc, True, 0, 0, w, h)
        #gc.set_background(ui.bgColor)
        ##pmap.set_direction(gtk.DIR_LTR)#????????
        pmap.draw_layout(
            gc,
            0,
            0,
            textLay,
            rgbToGdkColor(*self.shownCals[0]['color']),
            rgbToGdkColor(*ui.bgColor),
        )
        #c = self.shownCals[0]['color']
        #pmap.draw_layout(gc, 0, 0, textLay, c, ui.gdkColorInvert(c))##??????????
        pbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, True, 8, w , h)
        pbuf.get_from_drawable(
            pmap,
            self.get_screen().get_system_colormap(),
            0,
            0,
            0,
            0,
            -1,
            -1,
        )
        context.set_icon_pixbuf(pbuf, w/2-10, -20) ## x offset ???????????
        return True
    def updateTextWidth(self):
        ### update width of week days names to understand that should be synopsis or no
        lay = newTextLayout(self)
        wm = 0 ## max width
        for i in xrange(7):
            lay.set_text(core.weekDayName[i])
            w = lay.get_pixel_size()[0] ## ????????
            #w = lay.get_pixel_extents()[0] ## ????????
            #print w,
            if w > wm:
                wm = w
        self.wdaysWidth = wm*7 + ui.mcalLeftMargin ## ????????
        #self.wdaysWidth = wm*7*0.7 + ui.mcalLeftMargin ## ????????
        #print 'max =', wm, '     wdaysWidth =', self.wdaysWidth
    def buttonPress(self, obj, event):
        ## self.winActivate() #?????????
        b = event.button
        (x, y, mask) = event.window.get_pointer() # or self.get_pointer()
        self.pointer = (x, y)
        if b==2:
            return False
        xPos = -1
        yPos = -1
        for i in xrange(7):
            if abs(x-self.cx[i]) <= self.dx/2.0:
                xPos = i
                break
        for i in xrange(6):
            if abs(y-self.cy[i]) <= self.dy/2.0:
                yPos = i
                break
        status = getCurrentMonthStatus()
        if yPos==-1 or xPos==-1:
            self.emit('popup-menu-main', event.time, event.x, event.y)
            #self.menuMainWidth = self.menuMain.allocation.width ## menu.allocation[3]
        elif yPos>=0 and xPos>=0:
            cell = status[yPos][xPos]
            self.changeDate(*cell.dates[core.primaryMode])
            if event.type==gdk._2BUTTON_PRESS:
                self.emit('2button-press')
            if b == 3 and cell.month == ui.cell.month:## right click on a normal cell
                #self.emit('popup-menu-cell', event.time, *self.getCellPos())
                self.emit('popup-menu-cell', event.time, event.x, event.y)
        return True
    def calcCoord(self):## calculates coordidates (x and y of cells centers)
        x, y, w, h = self.allocation
        if rtl:
            self.cx = [(w-ui.mcalLeftMargin)*(13.0-2*i)/14.0 for i in xrange(7) ] ## centers x
        else:
            self.cx = [
                ui.mcalLeftMargin + (w-ui.mcalLeftMargin)*(1.0+2*i)/14.0
                for i in xrange(7)
            ] ## centers x
        self.cy = [
            ui.mcalTopMargin + (h-ui.mcalTopMargin)*(1.0+2*i)/12.0
            for i in xrange(6)
        ] ## centers y
        self.dx = (w-ui.mcalLeftMargin)/7.0 ## delta x
        self.dy = (h-ui.mcalTopMargin)/6.0 ## delta y
    def keyPress(self, arg, event):
        t = time()
        #if t-self.kTime < ui.keyDelay:
        #    return True
        kname = gdk.keyval_name(event.keyval).lower()
        #if kname.startswith('alt'):
        #    return True
        ## How to disable Alt+Space of metacity ?????????????????????
        if kname=='up':
            self.jdPlus(-7)
        elif kname=='down':
            self.jdPlus(7)
        elif kname=='right':
            if rtl:
                self.jdPlus(-1)
            else:
                self.jdPlus(1)
        elif kname=='left':
            if rtl:
                self.jdPlus(1)
            else:
                self.jdPlus(-1)
        elif kname in ('space', 'home'):
            self.goToday()
        elif kname=='end':
            self.changeDate(ui.cell.year, ui.cell.month, getMonthLen(ui.cell.year, ui.cell.month, core.primaryMode))
        elif kname=='page_up':
            ui.monthPlus(-1)
            self.onDateChange()
        elif kname=='page_down':
            ui.monthPlus(1)
            self.onDateChange()
        elif kname=='menu':
            self.emit('popup-menu-cell', event.time, *self.getCellPos())
        elif kname in ('f10', 'm'):
            if event.state & gdk.SHIFT_MASK:
                # Simulate right click (key beside Right-Ctrl)
                self.emit('popup-menu-cell', event.time, *self.getCellPos())
            else:
                self.emit('popup-menu-main', event.time, *self.getMainMenuPos())
        else:
            return False
        return True
    def jdPlus(self, plus):
        ui.jdPlus(plus)
        self.onDateChange()
    def scroll(self, widget, event):
        d = event.direction.value_nick
        if d=='up':
            self.jdPlus(-7)
        elif d=='down':
            self.jdPlus(7)
        else:
            return False
    def changeDate(self, year, month, day, mode=None):
        ui.changeDate(year, month, day, mode)
        self.onDateChange()
    goToday = lambda self, widget=None: self.changeDate(*core.getSysDate())
    getCellPos = lambda self: (
        int(self.cx[ui.cell.monthPos[0]]),
        int(self.cy[ui.cell.monthPos[1]] + self.dy/2.0),
    )
    def getMainMenuPos(self):#???????????????????
        if rtl:
            return (
                int(self.allocation.width - ui.mcalLeftMargin/2.0),
                int(ui.mcalTopMargin/2.0),
            )
        else:
            return (
                int(ui.mcalLeftMargin/2.0),
                int(ui.mcalTopMargin/2.0),
            )
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        self.queue_draw()
    def onConfigChange(self, *a, **kw):
        CustomizableCalObj.onConfigChange(self, *a, **kw)
        self.shownCals = ui.shownCals
        self.updateTextWidth()
        #self.onDateChange()
    def onCurrentDateChange(self, gdate):
        self.queue_draw()


cls = MonthCal
gobject.type_register(cls)
cls.registerSignals()
gobject.signal_new('popup-menu-cell', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [int, int, int])
gobject.signal_new('popup-menu-main', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [int, int, int])
gobject.signal_new('2button-press', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
gobject.signal_new('pref-update-bg-color', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])



if __name__=='__main__':
    win = gtk.Dialog()
    cal = MonthCal()
    win.add_events(
        gdk.POINTER_MOTION_MASK | gdk.FOCUS_CHANGE_MASK | gdk.BUTTON_MOTION_MASK |
        gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK | gdk.SCROLL_MASK |
        gdk.KEY_PRESS_MASK | gdk.VISIBILITY_NOTIFY_MASK | gdk.EXPOSURE_MASK
    )
    win.vbox.pack_start(cal, 1, 1)
    win.vbox.show_all()
    win.resize(600, 400)
    win.run()

