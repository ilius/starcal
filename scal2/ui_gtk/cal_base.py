# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2013 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from time import time

from scal2 import ui

import gtk
from gtk import gdk

from scal2.ui_gtk.drawing import newTextLayout
from scal2.ui_gtk.color_utils import rgbToGdkColor
from scal2.ui_gtk.utils import processDroppedDate


class CalBase:
    def changeDate(self, year, month, day, mode=None):
        ui.changeDate(year, month, day, mode)
        self.onDateChange()
    def defineDragAndDrop(self):
        self.drag_source_set(
            gdk.MODIFIER_MASK,
            (
                ('', 0, 0),
            ),
            gdk.ACTION_MOVE,## FIXME
        )
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
            gdk.ACTION_COPY,## FIXME
        )
        self.drag_dest_add_text_targets()
        self.drag_dest_add_uri_targets()
        ## ACTION_MOVE ?????????????????????
        ## if source ACTION was ACTION_COPY, calendar recieves its own dragged day
        ## just like gnome-calendar-applet (but it seems not a logical behaviar)
        '''
        #self.drag_source_add_uri_targets()#???????
        ##self.connect('drag-end', self.dragCalEnd)
        ##self.connect('drag-drop', self.dragCalDrop)
        ##self.connect('drag-failed', self.dragCalFailed)
        #self.connect('drag-leave', self.dragLeave)
        '''
    def dragDataGet(self, obj, context, selection, target_id, etime):
        selection.set_text('%.2d/%.2d/%.2d'%ui.cell.dates[ui.dragGetMode])
        return True
    def dragLeave(self, obj, context, etime):
        context.drop_reply(False, etime)
        return True
    def dragDataRec(self, obj, context, x, y, selection, target_id, etime):
        try:
            dtype = selection.get_data_type()
        except AttributeError:## Old PyGTK
            dtype = selection.type
        text = selection.get_text()
        dateM = processDroppedDate(text, dtype)
        if dateM:
            self.changeDate(*dateM)
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
        else:
            print 'Unknown dropped data type "%s", text="%s", data="%s"'%(dtype, text, selection.data)
            return True
        return False
    def dragBegin(self, obj, context):
        ui.focusTime = time()
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
        ##pmap.set_direction(gtk.DIR_LTR)## FIXME
        pmap.draw_layout(
            gc,
            0,
            0,
            textLay,
            rgbToGdkColor(*ui.textColor),
            rgbToGdkColor(*ui.bgColor),
        )
        #c = ui.textColor
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
        context.set_icon_pixbuf(pbuf, w/2-10, -20) ## x offset FIXME
        return True

