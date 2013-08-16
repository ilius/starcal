# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

import sys, os
from math import pi

from scal2.utils import escape
from scal2 import core

from scal2.locale_man import tr as _
from scal2.locale_man import rtl, rtlSgn
from scal2.time_utils import getEpochFromJd
from scal2.cal_types import calTypes
from scal2.core import myRaise, getMonthName, getMonthLen, pixDir

from scal2 import ui
from scal2.weekcal import getCurrentWeekStatus

import gtk
from gtk import gdk


from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.drawing import *
from scal2.ui_gtk.utils import pixbufFromFile, DirectionComboBox
from scal2.ui_gtk.color_utils import colorize
from scal2.ui_gtk.mywidgets import MyFontButton
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton, FloatSpinButton
from scal2.ui_gtk.mywidgets.font_family_combo import FontFamilyCombo
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.pref_utils import CheckPrefItem, ColorPrefItem
from scal2.ui_gtk.cal_base import CalBase
from scal2.ui_gtk.customize import CustomizableCalObj, CustomizableCalBox
from scal2.ui_gtk.toolbar import ToolbarItem, CustomizableToolbar

from scal2.ui_gtk import timeline_box as tbox


def show_event(widget, event):
    print type(widget), event.type.value_name#, event.get_value()#, event.send_event


class ColumnBase(CustomizableCalObj):
    customizeWidth = False
    customizeFont = False
    autoButtonPressHandler = True
    ##
    getWidthAttr = lambda self: 'wcal_%s_width'%self._name
    getWidthValue = lambda self: getattr(ui, self.getWidthAttr(), None)
    setWidthValue = lambda self, value: setattr(ui, self.getWidthAttr(), value)
    setWidthWidget = lambda self, value: self.set_property('width-request', value)
    ##
    getFontAttr = lambda self: 'wcalFont_%s'%self._name
    getFontValue = lambda self: getattr(ui, self.getFontAttr(), None)
    def widthSpinChanged(self, spin):
        if self._name:
            value = spin.get_value()
            self.setWidthValue(value)
            self.setWidthWidget(value)
    def fontFamilyComboChanged(self, combo):
        if self._name:
            setattr(ui, self.getFontAttr(), combo.get_value())
            self.onDateChange()
    def confStr(self):
        text = CustomizableCalObj.confStr(self)
        if self.customizeWidth:
            text += 'ui.%s = %r\n'%(
                self.getWidthAttr(),
                self.getWidthValue(),
            )
        if self.customizeFont:
            text += 'ui.%s = %r\n'%(
                self.getFontAttr(),
                self.getFontValue(),
            )
        return text
    def initVars(self, *a, **ka):
        CustomizableCalObj.initVars(self, *a, **ka)
        if not self.optionsWidget:
            self.optionsWidget = gtk.VBox()
        ####
        if self.customizeWidth:
            value = self.getWidthValue()
            self.setWidthWidget(value)
            ###
            hbox = gtk.HBox()
            hbox.pack_start(gtk.Label(_('Width')), 0, 0)
            spin = IntSpinButton(0, 999)
            hbox.pack_start(spin, 0, 0)
            spin.set_value(value)
            spin.connect('changed', self.widthSpinChanged)
            self.optionsWidget.pack_start(hbox, 0, 0)
        ####
        if self.customizeFont:
            hbox = gtk.HBox()
            hbox.pack_start(gtk.Label(_('Font Family')), 0, 0)
            combo = FontFamilyCombo(hasAuto=True)
            combo.set_value(self.getFontValue())
            hbox.pack_start(combo, 0, 0)
            combo.connect('changed', self.fontFamilyComboChanged)
            self.optionsWidget.pack_start(hbox, 0, 0)
        ####
        self.optionsWidget.show_all()


@registerSignals
class Column(gtk.Widget, ColumnBase):
    colorizeHolidayText = False
    showCursor = False
    truncateText = False
    def __init__(self, wcal):
        gtk.Widget.__init__(self)
        self.initVars()
        #self.connect('button-press-event', self.buttonPress)
        #self.connect('event', show_event)
        self.wcal = wcal
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(),
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gdk.WINDOW_CHILD,
            wclass=gdk.INPUT_OUTPUT,
            event_mask=self.get_events() \
                | gdk.EXPOSURE_MASK | gdk.BUTTON1_MOTION_MASK
                | gdk.BUTTON_PRESS_MASK | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK,
        )
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
    def drawBg(self, cr):
        w = self.allocation.width
        h = self.allocation.height
        cr.rectangle(0, 0, w, h)
        fillColor(cr, ui.bgColor)
        rowH = h/7.0
        for i in range(7):
            c = self.wcal.status[i]
            y0 = i*rowH
            if c.jd == ui.todayCell.jd:
                cr.rectangle(0, i*rowH, w, rowH)
                fillColor(cr, ui.todayCellColor)
            if self.showCursor and c.jd == ui.cell.jd:
                drawCursorBg(cr, 0, y0, w, rowH)
                fillColor(cr, ui.cursorBgColor)
        if ui.wcalGrid:
            w = self.allocation.width
            h = self.allocation.height
            setColor(cr, ui.wcalGridColor)
            ###
            cr.rectangle(w-1, 0, 1, h)
            cr.fill()
            ###
            for i in range(1, 7):
                cr.rectangle(0, i*rowH, w, 1)
                cr.fill()
    def drawCursorFg(self, cr):
        w = self.allocation.width
        h = self.allocation.height
        rowH = h/7.0
        for i in range(7):
            c = self.wcal.status[i]
            y0 = i*rowH
            if self.showCursor and c.jd == ui.cell.jd:
                drawCursorOutline(cr, 0, y0, w, rowH)
                fillColor(cr, ui.cursorOutColor)
    def drawTextList(self, cr, textData, font=None):
        w = self.allocation.width
        h = self.allocation.height
        ###
        rowH = h/7.0
        itemW = w - ui.wcalPadding
        if font is None:
            fontName = self.getFontValue()
            fontSize = ui.getFont()[-1] ## FIXME
            font = [fontName, False, False, fontSize] if fontName else None
        for i in range(7):
            data = textData[i]
            if data:
                linesN = len(data)
                lineH = rowH/linesN
                lineI = 0
                if len(data[0]) < 2:
                    print self._name
                for line, color in data:
                    layout = newTextLayout(
                        self,
                        text=line,
                        font=font,
                        maxSize=(itemW, lineH),
                        maximizeScale=ui.wcalTextSizeScale,
                        truncate=self.truncateText,
                    )
                    if not layout:
                        continue
                    layoutW, layoutH = layout.get_pixel_size()
                    layoutX = (w-layoutW)/2.0
                    layoutY = i*rowH + (lineI+0.5)*lineH - layoutH/2.0 
                    cr.move_to(layoutX, layoutY)
                    if self.colorizeHolidayText and self.wcal.status[i].holiday:
                        color = ui.holidayColor                
                    if not color:
                        color = ui.textColor
                    setColor(cr, color)
                    cr.show_layout(layout)
                    lineI += 1
    def buttonPress(self, widget, event):
        return False
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        self.queue_draw()



class WeekNumToolbarItem(ToolbarItem):
    def __init__(self):
        ToolbarItem.__init__(self, 'weekNum', None, '', tooltip=_('Week Number'), text='')
        self.label = gtk.Label()
        self.set_property('label-widget', self.label)
    def onDateChange(self, *a, **ka):
        ToolbarItem.onDateChange(self, *a, **ka)
        self.label.set_label(_(ui.cell.weekNum))


@registerSignals
class ToolbarColumn(CustomizableToolbar, ColumnBase):
    autoButtonPressHandler = False
    defaultItems = [
        WeekNumToolbarItem(),
        ToolbarItem('backward4', 'goto_top', 'goBackward4', 'Backward 4 Weeks'),
        ToolbarItem('backward', 'go_up', 'goBackward', 'Previous Week'),
        ToolbarItem('today', 'home', 'goToday', 'Today'),
        ToolbarItem('forward', 'go_down', 'goForward', 'Next Week'),
        ToolbarItem('forward4', 'goto_bottom', 'goForward4', 'Forward 4 Weeks'),
    ]
    defaultItemsDict = dict([(item._name, item) for item in defaultItems])
    params = (
        'ud.wcalToolbarData',
    )
    def __init__(self, wcal):
        CustomizableToolbar.__init__(self, wcal, True, True)
        if not ud.wcalToolbarData['items']:
            ud.wcalToolbarData['items'] = [(item._name, True) for item in self.defaultItems]
        self.setData(ud.wcalToolbarData)
    def updateVars(self):
        CustomizableToolbar.updateVars(self)
        ud.wcalToolbarData = self.getData()



class WeekDaysColumn(Column):
    _name = 'weekDays'
    desc = _('Week Days')
    colorizeHolidayText = True
    showCursor = True
    customizeWidth = True
    customizeFont = True
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.connect('expose-event', self.onExposeEvent)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        self.drawTextList(
            cr,
            [
                [
                    (core.getWeekDayN(i), ''),
                ]
                for i in range(7)
            ],
        )
        self.drawCursorFg(cr)
        
        
class PluginsTextColumn(Column):
    _name = 'pluginsText'
    desc = _('Plugins Text')
    expand = True
    customizeFont = True
    truncateText = True
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.connect('expose-event', self.onExposeEvent)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        self.drawTextList(
            cr,
            [
                [
                    (self.wcal.status[i].pluginsText, ''),
                ]
                for i in range(7)
            ]
        )


class EventsIconColumn(Column):
    _name = 'eventsIcon'
    desc = _('Events Icon')
    maxPixH = 26.0
    maxPixW = 26.0
    customizeWidth = True
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.connect('expose-event', self.onExposeEvent)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        ###
        w = self.allocation.width
        h = self.allocation.height
        ###
        rowH = h/7.0
        itemW = w - ui.wcalPadding
        for i in range(7):
            c = self.wcal.status[i]
            iconList = c.getWeekEventIcons()
            if not iconList:
                continue
            n = len(iconList)
            scaleFact = min(
                1.0,
                h / self.maxPixH,
                w / (n * self.maxPixW),
            )
            x0 = (w/scaleFact - (n-1)*self.maxPixW) / 2.0
            y0 = (2*i + 1) * h / (14.0*scaleFact)
            if rtl:
                iconList.reverse()## FIXME
            for iconIndex, icon in enumerate(iconList):
                try:
                    pix = gdk.pixbuf_new_from_file(icon)
                except:
                    myRaise(__file__)
                    continue
                pix_w = pix.get_width()
                pix_h = pix.get_height()
                x1 = x0 + iconIndex*self.maxPixW - pix_w/2.0
                y1 = y0 - pix_h/2.0
                cr.scale(scaleFact, scaleFact)
                cr.set_source_pixbuf(pix, x1, y1)
                cr.rectangle(x1, y1, pix_w, pix_h)
                cr.fill()
                cr.scale(1.0/scaleFact, 1.0/scaleFact)


class EventsCountColumn(Column):
    _name = 'eventsCount'
    desc = _('Events Count')
    customizeWidth = True
    params = (
        'ui.wcal_eventsCount_expand',
    )
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.expand = ui.wcal_eventsCount_expand
        ##
        hbox = gtk.HBox()
        check = gtk.CheckButton(_('Expand'))
        check.set_active(ui.wcal_eventsCount_expand)
        check.connect('clicked', self.expandCheckClicked)
        hbox.pack_start(check, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.optionsWidget.pack_start(hbox, 0, 0)
        self.optionsWidget.show_all()
        ##
        self.connect('expose-event', self.onExposeEvent)
    def expandCheckClicked(self, check):
        active = check.get_active()
        self.expand = ui.wcal_eventsCount_expand = active
        self.wcal.set_child_packing(self, active, active, 0, gtk.PACK_START)
        self.queue_draw()
    def getDayTextData(self, i):
        n = len(self.wcal.status[i].eventsData)
        ## item['show'][1] FIXME
        if n > 0:
            line = _('%s events')%_(n)
        else:
            line = ''
        return [
            (line, None),
        ]
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        ###
        w = self.allocation.width
        h = self.allocation.height
        ###
        self.drawTextList(
            cr,
            [
                self.getDayTextData(i)
                for i in range(7)
            ],
        )

class EventsTextColumn(Column):
    _name = 'eventsText'
    desc = _('Events Text')
    expand = True
    customizeFont = True
    params = (
        'ui.wcal_eventsText_showDesc',
        'ui.wcal_eventsText_colorize',
    )
    truncateText = True
    def __init__(self, wcal):
        Column.__init__(self, wcal)
        self.connect('expose-event', self.onExposeEvent)
        #####
        hbox = gtk.HBox()
        check = gtk.CheckButton(_('Show Description'))
        check.set_active(ui.wcal_eventsText_showDesc)
        hbox.pack_start(check, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        check.connect('clicked', self.descCheckClicked)
        self.optionsWidget.pack_start(hbox, 0, 0)
        ##
        hbox = gtk.HBox()
        check = gtk.CheckButton(_('Colorize'))
        check.set_active(ui.wcal_eventsText_colorize)
        hbox.pack_start(check, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        check.connect('clicked', self.colorizeCheckClicked)
        self.optionsWidget.pack_start(hbox, 0, 0)
        ##
        self.optionsWidget.show_all()
    def descCheckClicked(self, check):
        ui.wcal_eventsText_showDesc = check.get_active()
        self.queue_draw()
    def colorizeCheckClicked(self, check):
        ui.wcal_eventsText_colorize = check.get_active()
        self.queue_draw()
    def getDayTextData(self, i):
        data = []
        for item in self.wcal.status[i].eventsData:
            if not item['show'][1]:
                continue
            line = ''.join(item['text']) if ui.wcal_eventsText_showDesc else item['text'][0]
            line = escape(line)
            if item['time']:
                line = item['time'] + ' ' + line
            color = item['color'] if ui.wcal_eventsText_colorize else ''
            data.append((line, color))
        return data
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        self.drawTextList(
            cr,
            [
                self.getDayTextData(i)
                for i in range(7)
            ],
        )


class EventsBoxColumn(Column):
    _name = 'eventsBox'
    desc = _('Events Box')
    expand = True ## FIXME
    customizeFont = True
    #params = (
    #)
    def __init__(self, wcal):
        self.boxes = None
        self.padding = 2
        self.timeWidth = 7*24*3600
        self.boxEditing = None
        #####
        Column.__init__(self, wcal)
        #####
        self.connect('realize', lambda w: self.updateData())
        self.connect('expose-event', self.onExposeEvent)
    def updateData(self):
        self.timeStart = getEpochFromJd(self.wcal.status[0].jd)
        self.pixelPerSec = float(self.allocation.height) / self.timeWidth ## pixel/second
        self.borderTm = 0 ## tbox.boxMoveBorder / self.pixelPerSec ## second
        self.boxes = tbox.calcEventBoxes(
            self.timeStart,
            self.timeStart + self.timeWidth,
            self.pixelPerSec,
            self.borderTm,
        )
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        self.updateData()
        self.queue_draw()
    def onConfigChange(self, *a, **kw):
        CustomizableCalObj.onConfigChange(self, *a, **kw)
        self.updateData()
        self.queue_draw()
    def drawBox(self, cr, box):
        x = box.y
        y = box.x
        w = box.h
        h = box.w
        ###
        tbox.drawBoxBG(cr, box, x, y, w, h)
        tbox.drawBoxText(cr, box, x, y, w, h, self)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        if not self.boxes:
            return
        ###
        w = self.allocation.width
        h = self.allocation.height
        ###
        for box in self.boxes:
            box.setPixelValues(
                self.timeStart,
                self.pixelPerSec,
                self.padding,
                w - 2*self.padding,
            )
            self.drawBox(cr, box)


class WcalTypeParamBox(gtk.HBox):
    def __init__(self, wcal, index, mode, params, sgroupLabel, sgroupFont):
        gtk.HBox.__init__(self)
        self.wcal = wcal
        self.index = index
        self.mode = mode
        ######
        label = gtk.Label(_(calTypes[mode].desc)+'  ')
        label.set_alignment(0, 0.5)
        self.pack_start(label, 0, 0)
        sgroupLabel.add_widget(label)
        ###
        self.fontCheck = gtk.CheckButton(_('Font'))
        self.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(self.fontCheck, 0, 0)
        ###
        self.fontb = MyFontButton(wcal)
        self.pack_start(self.fontb, 0, 0)
        sgroupFont.add_widget(self.fontb)
        ####
        self.set(params)
        ####
        self.fontCheck.connect('clicked', self.onChange)
        self.fontb.connect('font-set', self.onChange)
    def get(self):
        return {
            'font': self.fontb.get_font_name() if self.fontCheck.get_active() else None,
        }
    def set(self, data):
        font = data['font']
        self.fontCheck.set_active(bool(font))
        if not font:
            font = ui.getFont()
        self.fontb.set_font_name(font)
    def onChange(self, obj=None, event=None):
        ui.wcalTypeParams[self.index] = self.get()
        self.wcal.queue_draw()

class DaysOfMonthColumn(Column):
    colorizeHolidayText = True
    showCursor = True
    def __init__(self, wcal, cgroup, mode, index):
        Column.__init__(self, wcal)
        self.cgroup = cgroup
        self.mode = mode
        self.index = index
        ###
        self.connect('expose-event', self.onExposeEvent)
    def onExposeEvent(self, widget=None, event=None):
        cr = self.window.cairo_create()
        self.drawBg(cr)
        try:
            font = ui.wcalTypeParams[self.index]['font']
        except:
            font = None
        self.drawTextList(
            cr,
            [
                [
                    (
                        _(self.wcal.status[i].dates[self.mode][2], self.mode),
                        '',
                    )
                ]
                for i in range(7)
            ],
            font=font,
        )
        self.drawCursorFg(cr)

@registerSignals
class DaysOfMonthColumnGroup(gtk.HBox, CustomizableCalBox, ColumnBase):
    _name = 'daysOfMonth'
    desc = _('Days of Month')
    customizeWidth = True
    params = (
        'ui.wcal_daysOfMonth_dir',
    )
    updateDir = lambda self: self.set_direction(ud.textDirDict[ui.wcal_daysOfMonth_dir])
    def __init__(self, wcal):
        gtk.HBox.__init__(self)
        self.initVars()
        self.wcal = wcal
        self.updateCols()
        self.updateDir()
        self.show()
        #####
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Direction')), 0, 0)
        combo = DirectionComboBox()
        hbox.pack_start(combo, 0, 0)
        combo.setValue(ui.wcal_daysOfMonth_dir)
        combo.connect('changed', self.dirComboChanged)
        self.optionsWidget.pack_start(hbox, 0, 0)
        ####
        frame = gtk.Frame(_('Calendars'))
        self.typeParamsVbox = gtk.VBox()
        frame.add(self.typeParamsVbox)
        frame.show_all()
        self.optionsWidget.pack_start(frame, 0, 0)
        self.updateTypeParamsWidget()## FIXME
        ####
        self.optionsWidget.show_all()
    def setWidthWidget(self, value):## overwrites method from ColumnBase
        for child in self.get_children():
            child.set_property('width-request', value)
    def dirComboChanged(self, combo):
        ui.wcal_daysOfMonth_dir = combo.getValue()
        self.updateDir()
    def updateCols(self):
        #self.foreach(gtk.Widget.destroy)## Couses crash tray icon in gnome3
        #self.foreach(lambda child: self.remove(child))## Couses crash tray icon in gnome3
        ########
        columns = self.get_children()
        n = len(columns)
        n2 = len(calTypes.active)
        width = self.getWidthValue()
        if n > n2:
            for i in range(n2, n):
                columns[i].destroy()
        elif n < n2:
            for i in range(n, n2):
                col = DaysOfMonthColumn(self.wcal, self, 0, i)
                self.pack_start(col, 0, 0)
                columns.append(col)
        for i, mode in enumerate(calTypes.active):
            col = columns[i]
            col.mode = mode
            col.show()
            col.set_property('width-request', width)
    def confStr(self):
        text = ColumnBase.confStr(self)
        text += 'ui.wcalTypeParams=%r\n'%ui.wcalTypeParams
        return text
    def updateTypeParamsWidget(self):
        vbox = self.typeParamsVbox
        for child in vbox.get_children():
            child.destroy()
        ###
        n = len(calTypes.active)
        while len(ui.wcalTypeParams) < n:
            ui.wcalTypeParams.append({
                'font': None,
            })
        sgroupLabel = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        sgroupFont = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        for i, mode in enumerate(calTypes.active):
            #try:
            params = ui.wcalTypeParams[i]
            #except IndexError:
            ##
            hbox = WcalTypeParamBox(self.wcal, i, mode, params, sgroupLabel, sgroupFont)
            vbox.pack_start(hbox, 0, 0)
        ###
        vbox.show_all()
    def onConfigChange(self, *a, **ka):
        CustomizableCalBox.onConfigChange(self, *a, **ka)
        self.updateCols()
        self.updateTypeParamsWidget()




@registerSignals
class WeekCal(gtk.HBox, CustomizableCalBox, ColumnBase, CalBase):
    _name = 'weekCal'
    desc = _('Week Calendar')
    params = (
        'ui.wcalHeight',
        'ui.wcalTextSizeScale',
        'ui.wcalItems',
        'ui.wcalGrid',
        'ui.wcalGridColor',
    )
    myKeys = CalBase.myKeys + (
        'up', 'down',
        'page_up',
        'k', 'p',
        'page_down',
        'j', 'n',
        'end',
        #'f10', 'm',
    )
    def __init__(self):
        gtk.HBox.__init__(self)
        CalBase.__init__(self)
        self.set_property('height-request', ui.wcalHeight)
        ######################
        self.connect('scroll-event', self.scroll)
        ###
        self.connect('button-press-event', self.buttonPress)
        #####
        defaultItems = [
            ToolbarColumn(self),
            WeekDaysColumn(self),
            PluginsTextColumn(self),
            EventsIconColumn(self),
            EventsCountColumn(self),
            EventsTextColumn(self),
            EventsBoxColumn(self),
            DaysOfMonthColumnGroup(self),
        ]
        defaultItemsDict = dict([(item._name, item) for item in defaultItems])
        itemNames = defaultItemsDict.keys()
        for name, enable in ui.wcalItems:
            try:
                item = defaultItemsDict[name]
            except KeyError:
                print 'weekCal item %s does not exist'%name
            else:
                item.enable = enable
                self.appendItem(item)
                itemNames.remove(name)
        for name in itemNames:
            item = defaultItemsDict[name]
            item.enable = False
            self.appendItem(item)
        #####
        hbox = gtk.HBox()
        spin = IntSpinButton(1, 9999)
        spin.set_value(ui.wcalHeight)
        spin.connect('changed', self.heightSpinChanged)
        hbox.pack_start(gtk.Label(_('Height')), 0, 0)
        hbox.pack_start(spin, 0, 0)
        self.optionsWidget.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        spin = FloatSpinButton(0.01, 1, 2)
        spin.set_value(ui.wcalTextSizeScale)
        spin.connect('changed', self.textSizeScaleSpinChanged)
        hbox.pack_start(gtk.Label(_('Text Size Scale')), 0, 0)
        hbox.pack_start(spin, 0, 0)
        self.optionsWidget.pack_start(hbox, 0, 0)
        ########
        hbox = gtk.HBox(spacing=3)
        ####
        item = CheckPrefItem(ui, 'wcalGrid', _('Grid'))
        item.updateWidget()
        gridCheck = item.widget
        hbox.pack_start(gridCheck, 0, 0)
        gridCheck.item = item
        ####
        colorItem = ColorPrefItem(ui, 'wcalGridColor', True)
        colorItem.updateWidget()
        hbox.pack_start(colorItem.widget, 0, 0)
        gridCheck.colorb = colorItem.widget
        gridCheck.connect('clicked', self.gridCheckClicked)
        colorItem.widget.item = colorItem
        colorItem.widget.connect('color-set', self.gridColorChanged)
        colorItem.widget.set_sensitive(ui.wcalGrid)
        ####
        self.optionsWidget.pack_start(hbox, 0, 0)
        ###
        self.optionsWidget.show_all()
    def heightSpinChanged(self, spin):
        v = spin.get_value()
        self.set_property('height-request', v)
        ui.wcalHeight = v
    def textSizeScaleSpinChanged(self, spin):
        ui.wcalTextSizeScale = spin.get_value()
        self.queue_draw()
    def updateVars(self):
        CustomizableCalBox.updateVars(self)
        ui.wcalItems = self.getItemsData()
    def updateStatus(self):
        self.status = getCurrentWeekStatus()
    def onConfigChange(self, *a, **kw):
        self.updateStatus()
        CustomizableCalBox.onConfigChange(self, *a, **kw)        
        self.queue_draw()
    def onDateChange(self, *a, **kw):
        self.updateStatus()
        CustomizableCalBox.onDateChange(self, *a, **kw)        
        self.queue_draw()
        #for item in self.items:
        #    item.queue_draw()
    def goBackward4(self, obj=None):
        self.jdPlus(-28)
    def goBackward(self, obj=None):
        self.jdPlus(-7)
    def goForward(self, obj=None):
        self.jdPlus(7)
    def goForward4(self, obj=None):
        self.jdPlus(28)
    def buttonPress(self, widget, event):
        col = event.window.get_user_data()
        while not isinstance(col, ColumnBase):
            col = col.get_parent()
            if col is None:
                break
        else:
            if not col.autoButtonPressHandler:
                return False
        ###
        b = event.button
        #x, y, mask = event.window.get_pointer()
        x, y = self.get_pointer()
        #y += 10
        ###
        i = int(event.y * 7.0 / self.allocation.height)
        cell = self.status[i]
        self.gotoJd(cell.jd)
        if event.type==gdk._2BUTTON_PRESS:
            self.emit('2button-press')
        if b == 3:
            self.emit('popup-menu-cell', event.time, x, y)
        return True
    def keyPress(self, arg, event):
        if CalBase.keyPress(self, arg, event):
            return True
        kname = gdk.keyval_name(event.keyval).lower()
        if kname=='up':
            self.jdPlus(-1)
        elif kname=='down':
            self.jdPlus(1)
        elif kname=='end':
            self.gotoJd(self.status[-1].jd)
        elif kname in ('page_up', 'k', 'p'):
            self.jdPlus(-7)
        elif kname in ('page_down', 'j', 'n'):
            self.jdPlus(7)
        #elif kname in ('f10', 'm'):
        #    if event.state & gdk.SHIFT_MASK:
        #        # Simulate right click (key beside Right-Ctrl)
        #        self.emit('popup-menu-cell', event.time, *self.getCellPos())
        #    else:
        #        self.emit('popup-menu-main', event.time, *self.getMainMenuPos())
        else:
            return False
        return True
    def scroll(self, widget, event):
        d = event.direction.value_nick
        if d=='up':
            self.jdPlus(-1)
        elif d=='down':
            self.jdPlus(1)
        else:
            return False
    getCellPos = lambda self: (
        int(self.allocation.width / 2.0),
        (ui.cell.weekDayIndex+1) * self.allocation.height / 7.0,
    )


    






if __name__=='__main__':
    win = gtk.Dialog()
    cal = WeekCal()
    win.add_events(
        gdk.POINTER_MOTION_MASK | gdk.FOCUS_CHANGE_MASK | gdk.BUTTON_MOTION_MASK |
        gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK | gdk.SCROLL_MASK |
        gdk.KEY_PRESS_MASK | gdk.VISIBILITY_NOTIFY_MASK | gdk.EXPOSURE_MASK
    )
    win.vbox.pack_start(cal, 1, 1)
    win.vbox.show()
    win.resize(600, 400)
    win.run()











