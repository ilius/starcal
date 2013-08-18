#!/usr/bin/env python2
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

from time import time as now
from time import localtime

import sys

if sys.version_info[0] != 2:
    print 'Run this script with Python 2.x'
    sys.exit(1)

import os
from os.path import join, dirname, isfile, isdir
from subprocess import Popen
from pprint import pprint, pformat

sys.path.insert(0, dirname(dirname(dirname(__file__))))
from scal2.path import *
from scal2.utils import myRaise, restartLow

if not isdir(confDir):
    try:
        __import__('scal2.ui_gtk.import_config_1to2')
    except:
        myRaise()
    restartLow()

from scal2.utils import toStr, toUnicode, cmpVersion
from scal2.cal_types import calTypes
from scal2 import core

from scal2 import locale_man
from scal2.locale_man import rtl, lang ## import scal2.locale_man after core
#_ = locale_man.loadTranslator(False)## FIXME
from scal2.locale_man import tr as _
from scal2.season import getSeasonNamePercentFromJd

from scal2.core import rootDir, pixDir, deskDir, myRaise, getMonthName, APP_DESC

#core.showInfo()

from scal2 import event_lib
from scal2 import ui

import gobject ##?????
from gobject import timeout_add, timeout_add_seconds

import gtk
from gtk import gdk

from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.utils import *
from scal2.ui_gtk.color_utils import rgbToGdkColor
from scal2.ui_gtk import listener
import scal2.ui_gtk.export
import scal2.ui_gtk.selectdate

from scal2.ui_gtk.drawing import newTextLayout, newOutlineSquarePixbuf
from scal2.ui_gtk.mywidgets.clock import FClockLabel
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton
#from ui_gtk.mywidgets2.multi_spin_button import DateButtonOption

from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk import preferences
from scal2.ui_gtk.preferences import PrefItem, gdkColorToRgb
from scal2.ui_gtk.customize import CustomizableCalObj, CustomizableCalBox, CustomizeDialog
from scal2.ui_gtk.toolbar import ToolbarItem, CustomizableToolbar
from scal2.ui_gtk.year_month_labels import YearMonthLabelBox
from scal2.ui_gtk.monthcal import MonthCal

from scal2.ui_gtk.event.common import addNewEvent
from scal2.ui_gtk.event.occurrence_view import DayOccurrenceView
from scal2.ui_gtk.event.main import EventManagerDialog

from scal2.ui_gtk.timeline import TimeLineWindow
#from scal2.ui_gtk.weekcal_old import WeekCalWindow
from scal2.ui_gtk.weekcal import WeekCal
from scal2.ui_gtk.day_info import DayInfoDialog



ui.uiName = 'gtk'


def show_event(widget, event):
    print type(widget), event.type.value_name, event.get_value()#, event.send_event


def liveConfChanged():
    tm = now()
    if tm-ui.lastLiveConfChangeTime > ui.saveLiveConfDelay:
        timeout_add(int(ui.saveLiveConfDelay*1000), ui.saveLiveConfLoop)
    ui.lastLiveConfChangeTime = tm


# How to define icon of custom stock????????????
#gtk.stock_add((
#('gtk-evolution', 'E_volution', gdk.BUTTON1_MASK, 0, 'gtk20')



class DateLabel(gtk.Label):
    def __init__(self, text=None):
        gtk.Label.__init__(self, text)
        self.set_selectable(True)
        #self.set_cursor_visible(False)## FIXME
        self.set_can_focus(False)
        self.set_use_markup(True)
        self.connect('populate-popup', self.popupPopulate)
        self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        ####
        self.menu = gtk.Menu()
        ##
        itemCopyAll = gtk.ImageMenuItem(_('Copy _All'))
        itemCopyAll.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        itemCopyAll.connect('activate', self.copyAll)
        self.menu.add(itemCopyAll)
        ##
        itemCopy = gtk.ImageMenuItem(_('_Copy'))
        itemCopy.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        itemCopy.connect('activate', self.copy)
        self.itemCopy = itemCopy
        self.menu.add(itemCopy)
        ##
        self.menu.show_all()
    def popupPopulate(self, label, menu):
        self.itemCopy.set_sensitive(self.get_property('cursor-position') > self.get_property('selection-bound'))## FIXME
        self.menu.popup(None, None, None, 3, 0)
        ui.updateFocusTime()
    def copy(self, item):
        start = self.get_property('selection-bound')
        end = self.get_property('cursor-position')
        self.clipboard.set_text(toStr(toUnicode(self.get_text())[start:end]))
    copyAll = lambda self, label: self.clipboard.set_text(self.get_text())



@registerSignals
class WinConButton(gtk.EventBox, CustomizableCalObj):
    expand = False
    imageName = ''
    imageNameFocus = ''
    imageNameInactive = 'button-inactive.png'
    def __init__(self, controller, size=23):
        gtk.EventBox.__init__(self)
        self.initVars()
        ###
        self.size = size
        self.controller = controller
        CustomizableCalObj.initVars(self)
        self.build()
    def onClicked(self, gWin, event):
        raise NotImplementedError
    setImage = lambda self, imName: self.im.set_from_file('%s/wm/%s'%(pixDir, imName))
    setFocus = lambda self, focus:\
        self.setImage(self.imageNameFocus if focus else self.imageName)
    setInactive = lambda self: self.setImage(self.imageNameInactive)
    def build(self):
        self.im = gtk.Image()
        self.setFocus(False)
        self.im.set_size_request(self.size, self.size)
        self.add(self.im)
        self.connect('enter-notify-event', self.enterNotify)
        self.connect('leave-notify-event', self.leaveNotify)
        self.connect('button-press-event', self.buttonPress)
        self.connect('button-release-event', self.buttonRelease)
        set_tooltip(self, self.desc)## FIXME
    def enterNotify(self, widget, event):
        self.setFocus(True)
    def leaveNotify(self, widget, event):
        if self.controller.winFocused:
            self.setFocus(False)
        else:
            self.setInactive()
        return False
    def buttonPress(self, widget, event):
        self.setFocus(False)
        return True
    def onClicked(self, gWin, event):
        pass
    def buttonRelease(self, button, event):
        if event.button==1:
            self.onClicked(self.controller.gWin, event)
        return False
    show = lambda self: self.show_all()

class WinConButtonMin(WinConButton):
    _name = 'min'
    desc = _('Minimize Window')
    imageName = 'button-min.png'
    imageNameFocus = 'button-min-focus.png'
    def onClicked(self, gWin, event):
        if ui.winTaskbar:
            gWin.iconify()
        else:
            gWin.emit('delete-event', event)

class WinConButtonMax(WinConButton):
    _name = 'max'
    desc = _('Maximize Window')
    imageName = 'button-max.png'
    imageNameFocus = 'button-max-focus.png'
    def onClicked(self, gWin, event):
        if gWin.isMaximized:
            gWin.unmaximize()
            gWin.isMaximized = False
        else:
            gWin.maximize()
            gWin.isMaximized = True

class WinConButtonClose(WinConButton):
    _name = 'close'
    desc = _('Close Window')
    imageName = 'button-close.png'
    imageNameFocus = 'button-close-focus.png'
    def onClicked(self, gWin, event):
        gWin.emit('delete-event', event)

class WinConButtonSep(WinConButton):
    _name = 'sep'
    desc = _('Seperator')
    expand = True
    def build(self):
        pass
    def setFocus(self, focus):
        pass
    def setInactive(self):
        pass

## Stick
## Above
## Below

## What is "GTK Window Decorator" ??????????
@registerSignals
class MainWinController(gtk.HBox, CustomizableCalBox):
    _name = 'winContronller'
    desc = _('Window Controller')
    params = (
        'ui.winControllerButtons',
    )
    buttonClassList = (WinConButtonMin, WinConButtonMax, WinConButtonClose, WinConButtonSep)
    buttonClassDict = dict([(cls._name, cls) for cls in buttonClassList])
    def __init__(self):
        gtk.HBox.__init__(self, spacing=ui.winControllerSpacing)
        self.set_property('height-request', 15)
        self.set_direction(gtk.TEXT_DIR_LTR)## FIXME
        self.initVars()
        ###########
        for bname, enable in ui.winControllerButtons:
            button = self.buttonClassDict[bname](self)
            button.enable = enable
            self.appendItem(button)
        self.set_property('can-focus', True)
        ##################
        self.gWin = ui.mainWin
        ##gWin.connect('focus-in-event', self.windowFocusIn)
        ##gWin.connect('focus-out-event', self.windowFocusOut)
        self.winFocused = True
    def windowFocusIn(self, widget=None, event=None):
        for b in self.items:
            b.setFocus(False)
        self.winFocused = True
        return False
    def windowFocusOut(self, widget=None, event=None):
        for b in self.items:
            b.setInactive()
        self.winFocused = False
        return False



@registerSignals
class MainWinToolbar(CustomizableToolbar):
    params = (
        'ud.mainToolbarData',
    )
    defaultItems = [
        ToolbarItem('today', 'home', 'goToday', 'Select Today'),
        ToolbarItem('date', 'index', 'selectDateShow', 'Select Date...', 'Date...'),
        ToolbarItem('customize', 'edit', 'customizeShow'),
        ToolbarItem('preferences', 'preferences', 'prefShow'),
        ToolbarItem('add', 'add', 'eventManShow', 'Event Manager'),
        ToolbarItem('export', 'convert', 'exportClicked', _('Export to %s')%'HTML'),
        ToolbarItem('about', 'about', 'aboutShow', _('About ')+APP_DESC),
        ToolbarItem('quit', 'quit', 'quit'),
    ]
    defaultItemsDict = dict([(item._name, item) for item in defaultItems])
    def __init__(self):
        CustomizableToolbar.__init__(self, ui.mainWin, vertical=False)
        if not ud.mainToolbarData['items']:
            ud.mainToolbarData['items'] = [(item._name, True) for item in self.defaultItems]
        self.setData(ud.mainToolbarData)
    def updateVars(self):
        CustomizableToolbar.updateVars(self)
        ud.mainToolbarData = self.getData()




@registerSignals
class StatusBox(gtk.HBox, CustomizableCalObj):
    _name = 'statusBar'
    desc = _('Status Bar')
    def __init__(self):
        gtk.HBox.__init__(self)
        self.initVars()
        self.labelBox = gtk.HBox()
        self.pack_start(self.labelBox, 1, 1)
        sbar = gtk.Statusbar()
        if rtl:
            self.set_direction(gtk.TEXT_DIR_LTR)
            sbar.set_direction(gtk.TEXT_DIR_LTR)
            self.labelBox.set_direction(gtk.TEXT_DIR_LTR)
        sbar.set_property('width-request', 18)
        sbar.connect('button-press-event', self.sbarButtonPress)
        sbar.show()
        self.pack_start(sbar, 0, 0)
    sbarButtonPress = lambda self, widget, event: ui.mainWin.startResize(widget, event)
    def onConfigChange(self, *a, **kw):
        CustomizableCalObj.onConfigChange(self, *a, **kw)
        ###
        for label in self.labelBox.get_children():
            label.destroy()
        ###
        for mode in calTypes.active:
            label = DateLabel(None)
            label.mode = mode
            self.labelBox.pack_start(label, 1, 0, 0)
        self.show_all()
        ###
        self.onDateChange()
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        for i, label in enumerate(self.labelBox.get_children()):
            text = ui.cell.format(ud.dateFormatBin, label.mode)
            if i==0:
                text = '<b>%s</b>'%text
            label.set_label(text)

@registerSignals
class SeasonProgressBarMainWinItem(gtk.ProgressBar, CustomizableCalObj):
    _name = 'seasonPBar'
    desc = _('Season Progress Bar')
    def __init__(self):
        gtk.ProgressBar.__init__(self)
        self.initVars()
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        name, frac = getSeasonNamePercentFromJd(ui.cell.jd)
        if rtl:
            percent = '%d%%'%(frac*100)
        else:
            percent = '%%%d'%(frac*100)
        self.set_text(
            _(name) +
            ' - ' +
            locale_man.textNumEncode(
                percent,
                changeDot=True,
            )
        )
        self.set_fraction(frac)
        

@registerSignals
class PluginsTextBox(gtk.VBox, CustomizableCalObj):
    _name = 'pluginsText'
    desc = _('Plugins Text')
    params = (
        'ui.pluginsTextInsideExpander',
    )
    def __init__(self):
        gtk.VBox.__init__(self)
        self.initVars()
        ####
        self.textview = gtk.TextView()
        self.textview.set_wrap_mode(gtk.WRAP_WORD)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_justification(gtk.JUSTIFY_CENTER)
        self.textbuff = self.textview.get_buffer()
        self.textview.connect('populate-popup', ui.updateFocusTime)
        ##
        self.expander = gtk.Expander()
        self.expander.connect('activate', self.expanderExpanded)
        if ui.pluginsTextInsideExpander:
            self.expander.add(self.textview)
            self.pack_start(self.expander, 0, 0)
            self.expander.set_expanded(ui.pluginsTextIsExpanded)
            self.textview.show()
        else:
            self.pack_start(self.textview, 0, 0)
        #####
        optionsWidget = gtk.HBox()
        self.enableExpanderCheckb = gtk.CheckButton(_('Inside Expander'))
        self.enableExpanderCheckb.set_active(ui.pluginsTextInsideExpander)
        self.enableExpanderCheckb.connect('clicked', lambda check: self.setEnableExpander(check.get_active()))
        self.setEnableExpander(ui.pluginsTextInsideExpander)
        optionsWidget.pack_start(self.enableExpanderCheckb, 0, 0)
        ####
        optionsWidget.show_all()
        self.optionsWidget = optionsWidget
    def expanderExpanded(self, exp):
        ui.pluginsTextIsExpanded = not exp.get_expanded()
        ui.saveLiveConf()
    getWidget = lambda self: self.expander if ui.pluginsTextInsideExpander else self.textview
    def setText(self, text):
        if text:
            self.textbuff.set_text(text)
            self.getWidget().show()
        else:## elif self.get_property('visible')
            self.textbuff.set_text('')## forethought
            self.getWidget().hide()
    def setEnableExpander(self, enable):
        #print 'setEnableExpander', enable
        if enable:
            if not ui.pluginsTextInsideExpander:
                self.remove(self.textview)
                self.expander.add(self.textview)
                self.pack_start(self.expander, 0, 0)
                self.expander.show_all()
        else:
            if ui.pluginsTextInsideExpander:
                self.expander.remove(self.textview)
                self.remove(self.expander)
                self.pack_start(self.textview, 0, 0)
                self.textview.show()
        ui.pluginsTextInsideExpander = enable
        self.onDateChange()
    def onDateChange(self, *a, **kw):
        CustomizableCalObj.onDateChange(self, *a, **kw)
        self.setText(ui.cell.pluginsText)


#@registerSignals
class EventViewMainWinItem(DayOccurrenceView, CustomizableCalObj):## FIXME
    def __init__(self):
        DayOccurrenceView.__init__(self)
        self.maxHeight = ui.eventViewMaxHeight
        self.optionsWidget = gtk.HBox()
        ###
        hbox = gtk.HBox()
        spin = IntSpinButton(1, 9999)
        spin.set_value(ui.eventViewMaxHeight)
        spin.connect('changed', self.heightSpinChanged)
        hbox.pack_start(gtk.Label(_('Maximum Height')), 0, 0)
        hbox.pack_start(spin, 0, 0)
        self.optionsWidget.pack_start(hbox, 0, 0)
        ###
        self.optionsWidget.show_all()
    def heightSpinChanged(self, spin):
        v = spin.get_value()
        self.maxHeight = ui.eventViewMaxHeight = v
        self.queue_resize()



@registerSignals
class MainWinVbox(gtk.VBox, CustomizableCalBox):
    _name = 'mainWin'
    desc = _('Main Window')
    params = (
        'ui.mainWinItems',
    )
    def __init__(self):
        gtk.VBox.__init__(self)
        self.initVars()
    def updateVars(self):
        CustomizableCalBox.updateVars(self)
        ui.mainWinItems = self.getItemsData()
    def keyPress(self, arg, event):
        CustomizableCalBox.keyPress(self, arg, event)
        return True ## FIXME


@registerSignals
class MainWin(gtk.Window, ud.IntegratedCalObj):
    _name = 'mainWin'
    desc = _('Main Window')
    timeout = 1 ## second
    setMinHeight = lambda self: self.resize(ui.winWidth, 2)
    '''
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(),
            width=self.allocation.width,
            height=self.allocation.height,
            window_type=gdk.WINDOW_TOPLEVEL,
            wclass=gdk.INPUT_OUTPUT,
            event_mask=self.get_events() \
                | gdk.EXPOSURE_MASK | gdk.BUTTON1_MOTION_MASK | gdk.BUTTON_PRESS_MASK
                | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK
        )
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
        self.window.set_decorations(gdk.DECORE_CLOSE)
        self.window.set_functions(gdk.FUNC_CLOSE)
    '''
    #def maximize(self):
    #    pass
    def __init__(self, trayMode=2):
        gtk.Window.__init__(self)##, gtk.WINDOW_POPUP) ## ????????????
        self.initVars()
        ud.windowList.appendItem(self)
        ui.mainWin = self
        ##################
        ## trayMode:
            ## ('none', 'none')
            ## ('tray', 'normal')
            ## ('applet', 'gnome')
            ## ('applet', 'kde')
            ##
            ## 0: none (simple window)
            ## 1: applet
            ## 2: standard tray icon
        self.trayMode = trayMode
        ###
        ui.eventManDialog = EventManagerDialog()
        ###
        ui.timeLineWin = TimeLineWindow()
        ###
        #ui.weekCalWin = WeekCalWindow()
        #ud.windowList.appendItem(ui.weekCalWin)
        ###
        self.dayInfoDialog = DayInfoDialog()
        #print 'windowList.items', [item._name for item in ud.windowList.items]
        ###########
        ##self.connect('window-state-event', selfStateEvent)
        self.set_title('%s %s'%(core.APP_DESC, core.VERSION))
        #self.connect('main-show', lambda arg: self.present())
        #self.connect('main-hide', lambda arg: self.hide())
        self.set_decorated(False)
        self.set_property('skip-taskbar-hint', not ui.winTaskbar) ## self.set_skip_taskbar_hint  ## FIXME
        self.set_role('starcal2')
        #self.set_focus_on_map(True)#????????
        #self.set_type_hint(gdk.WINDOW_TYPE_HINT_NORMAL)
        #self.connect('realize', self.onRealize)
        self.set_default_size(ui.winWidth, 1)
        try:
            self.move(ui.winX, ui.winY)
        except:
            pass
        #############################################################
        self.connect('focus-in-event', self.focusIn, 'Main')
        self.connect('focus-out-event', self.focusOut, 'Main')
        self.connect('button-press-event', self.buttonPress)
        self.connect('key-press-event', self.keyPress)
        self.connect('configure-event', self.configureEvent)
        self.connect('destroy', self.quit)
        #############################################################
        """
        #self.add_events(gdk.VISIBILITY_NOTIFY_MASK)
        #self.connect('frame-event', show_event)
        ## Compiz does not send configure-event(or any event) when MOVING window(sends in last point,
        ## when moving completed)
        #self.connect('drag-motion', show_event)
        ud.rootWindow.set_events(...
        ud.rootWindow.add_filter(self.onRootWinEvent)
        #self.realize()
        #gdk.flush()
        #self.configureEvent(None, None)
        #self.connect('drag-motion', show_event)
        ######################
        ## ????????????????????????????????????????????????
        ## when button is down(before button-release-event), motion-notify-event does not recived!
        """
        ##################################################################
        self.focus = False
        #self.focusOutTime = 0
        #self.clockTr = None
        ############################################################################
        self.winCon = MainWinController()
        ############
        defaultItems = [
            self.winCon,
            MainWinToolbar(),
            YearMonthLabelBox(),
            MonthCal(),
            WeekCal(),
            StatusBox(),
            SeasonProgressBarMainWinItem(),
            PluginsTextBox(),
            EventViewMainWinItem(),
        ]
        defaultItemsDict = dict([(obj._name, obj) for obj in defaultItems])
        ui.checkMainWinItems()
        self.vbox = MainWinVbox()
        for (name, enable) in ui.mainWinItems:
            #print name, enable
            try:
                item = defaultItemsDict[name]
            except:
                myRaise()
                continue
            item.enable = enable
            item.connect('size-request', self.childSizeRequest) ## or item.connect
            #modify_bg_all(item, gtk.STATE_NORMAL, rgbToGdkColor(*ui.bgColor))
            self.vbox.appendItem(item)
        self.appendItem(self.vbox)
        self.vbox.show()
        self.customizeDialog = CustomizeDialog(self.vbox)
        #######
        self.add(self.vbox)
        ####################
        self.isMaximized = False
        ####################
        ui.prefDialog = preferences.PrefDialog(self.trayMode)
        self.exportDialog = scal2.ui_gtk.export.ExportDialog()
        self.selectDateDialog = scal2.ui_gtk.selectdate.SelectDateDialog()
        self.selectDateDialog.connect('response-date', self.selectDateResponse)
        selectDateShow = self.selectDateShow
        ############### Building About Dialog
        about = AboutDialog(
            name=core.APP_DESC,
            version=core.VERSION,
            title=_('About ')+core.APP_DESC,
            authors=[_(line) for line in open(join(rootDir, 'authors-dialog')).read().splitlines()],
            comments=core.aboutText,
            license=core.licenseText,
            website=core.homePage,
        )
        ## add Donate button ## FIXME
        about.connect('delete-event', self.aboutHide)
        about.connect('response', self.aboutHide)
        #about.set_logo(gdk.pixbuf_new_from_file(ui.logo))
        #about.set_skip_taskbar_hint(True)
        self.about = about
        ########################################### Building main menu
        menu = gtk.Menu()
        ####
        item = gtk.ImageMenuItem(_('Resize'))
        item.set_image(imageFromFile('resize.png'))
        item.connect('button-press-event', self.startResize)
        menu.add(item)
        ####
        check = gtk.CheckMenuItem(label=_('_On Top'))
        check.connect('activate', self.keepAboveClicked)
        menu.add(check)
        check.set_active(ui.winKeepAbove)
        self.set_keep_above(ui.winKeepAbove)
        self.checkAbove = check
        #####
        check = gtk.CheckMenuItem(label=_('_Sticky'))
        check.connect('activate', self.stickyClicked)
        menu.add(check)
        check.set_active(ui.winSticky)
        if ui.winSticky:
            self.stick()
        self.checkSticky = check
        #####
        menu.add(labelStockMenuItem('Select _Today', gtk.STOCK_HOME, self.goToday))
        menu.add(labelStockMenuItem('Select _Date...', gtk.STOCK_INDEX, selectDateShow))
        menu.add(labelStockMenuItem('Day Info', gtk.STOCK_INFO, self.dayInfoShow))
        menu.add(labelStockMenuItem('_Customize', gtk.STOCK_EDIT, self.customizeShow))
        menu.add(labelStockMenuItem('_Preferences', gtk.STOCK_PREFERENCES, self.prefShow))
        #menu.add(labelStockMenuItem('_Add Event', gtk.STOCK_ADD, ui.eventManDialog.addCustomEvent))
        menu.add(labelStockMenuItem('_Event Manager', gtk.STOCK_ADD, self.eventManShow))
        menu.add(labelImageMenuItem('Time Line', 'timeline-18.png', self.timeLineShow))
        #menu.add(labelImageMenuItem('Week Calendar', 'weekcal-18.png', self.weekCalShow))
        menu.add(labelStockMenuItem(_('Export to %s')%'HTML', gtk.STOCK_CONVERT, self.exportClicked))
        menu.add(labelStockMenuItem('_About', gtk.STOCK_ABOUT, self.aboutShow))
        if self.trayMode!=1:
            menu.add(labelStockMenuItem('_Quit', gtk.STOCK_QUIT, self.quit))
        menu.show_all()
        self.menuMain = menu
        ############################################################
        self.trayInit()
        listener.dateChange.add(self)
        #if self.trayMode!=1:
        #    timeout_add_seconds(self.timeout, self.trayUpdate)
        #########
        self.connect('delete-event', self.dialogClose)
        ######################
        self.updateMenuSize()
        ui.prefDialog.updatePrefGui()
        self.clipboard = gtk.clipboard_get(gdk.SELECTION_CLIPBOARD)
        #########################################
        for plug in core.allPlugList:
            if plug.external and hasattr(plug, 'set_dialog'):
                plug.set_dialog(self)
        ###########################
        self.onConfigChange()
        #ud.rootWindow.set_cursor(gdk.Cursor(gdk.LEFT_PTR))
    #def mainWinStateEvent(self, obj, event):
        #print dir(event)
        #print event.new_window_state
        #self.event = event
    def childSizeRequest(self, cal, req):
        self.setMinHeight()
    selectDateShow = lambda self, widget=None: self.selectDateDialog.show()
    dayInfoShow = lambda self, widget=None: self.dayInfoDialog.show()
    def selectDateResponse(self, widget, y, m, d):
        ui.changeDate(y, m, d)
        self.onDateChange()
    def keyPress(self, arg, event):
        kname = gdk.keyval_name(event.keyval).lower()
        #print now(), 'MainWin.keyPress', kname
        if kname=='escape':
            self.dialogEsc()
        elif kname=='f1':
            self.aboutShow()
        elif kname in ('insert', 'plus', 'kp_add'):
            self.eventManShow()
        elif kname in ('q', 'arabic_dad'):## FIXME
            self.quit()
        else:
            self.vbox.keyPress(arg, event)
        return True ## FIXME
    def focusIn(self, widegt, event, data=None):
        self.focus = True
        if self.winCon.enable:
            self.winCon.windowFocusIn()
    def focusOut(self, widegt, event, data=None):
        ## called 0.0004 sec (max) after focusIn (if switched between two windows)
        dt = now()-ui.focusTime
        #print 'focusOut', dt
        if dt > 0.05: ## FIXME
            self.focus = False
            timeout_add(2, self.focusOutDo)
    def focusOutDo(self):
        if not self.focus:# and t-self.focusOutTime>0.002:
            ab = self.checkAbove.get_active()
            self.set_keep_above(ab)
            if self.winCon.enable:
                self.winCon.windowFocusOut()
        return False

    """
    def checkResize(self, widget, req):
        if ui.mcalHeight != req.height:# and ui.winWidth==req.width:
            if req.height==0:
                req.height=1
            ui.mcalHeight = req.height
    """
    def configureEvent(self, widget, event):
        liveConfChanged()
        ###
        wx, wy = self.get_position()
        ww, wh = self.get_size()
        if ui.bgUseDesk and max(abs(ui.winX-wx), abs(ui.winY-wy))>1:## FIXME
            self.queue_draw()
        if self.get_property('visible'):
            ui.winX, ui.winY = (wx, wy)## FIXME
        ui.winWidth = ww
        return False
    def buttonPress(self, obj, event):
        b = event.button
        #print 'buttonPress', b
        if b==3:
            self.menuMain.popup(None, None, None, 3, event.time)
            ui.updateFocusTime()
        elif b==1:
            x, y, mask = ud.rootWindow.get_pointer()
            self.begin_move_drag(event.button, x, y, event.time)
        return False
    def startResize(self, widget, event):
        self.menuMain.hide()
        x, y, mask = ud.rootWindow.get_pointer()
        self.begin_resize_drag(gdk.WINDOW_EDGE_SOUTH_EAST, event.button, x, y, event.time)
        return True
    def changeDate(self, year, month, day):
        ui.changeDate(year, month, day)
        self.onDateChange()
    goToday = lambda self, obj=None: self.changeDate(*core.getSysDate())
    def onDateChange(self, *a, **kw):
        #print 'MainWin.onDateChange'
        ud.IntegratedCalObj.onDateChange(self, *a, **kw)
        #for j in range(len(core.plugIndex)):##????????????????????
        #    try:
        #        core.allPlugList[core.plugIndex[j]].date_change(*date)
        #    except AttributeError:
        #        pass
        self.setMinHeight()
        for j in range(len(core.plugIndex)):
            try:
                core.allPlugList[core.plugIndex[j]].date_change_after(*date)
            except AttributeError:
                pass
    def getEventAddToMenuItem(self):
        addToItem = labelStockMenuItem('_Add to', gtk.STOCK_ADD)
        menu2 = gtk.Menu()
        ##
        for group in ui.eventGroups:
            if not group.enable:
                continue
            if not group.showInCal():## FIXME
                continue
            eventTypes = group.acceptsEventTypes
            if not eventTypes:
                continue
            item2 = gtk.ImageMenuItem()
            item2.set_label(group.title)
            ##
            image = gtk.Image()
            if group.icon:
                image.set_from_file(group.icon)
            else:
                image.set_from_pixbuf(newOutlineSquarePixbuf(group.color, 20))
            item2.set_image(image)
            ##
            if len(eventTypes)==1:
                item2.connect('activate', self.addToGroupFromMenu, group, eventTypes[0])
            else:
                menu3 = gtk.Menu()
                for eventType in eventTypes:
                    eventClass = event_lib.classes.event.byName[eventType]
                    item3 = gtk.ImageMenuItem()
                    item3.set_label(eventClass.desc)
                    icon = eventClass.getDefaultIcon()
                    if icon:
                        item3.set_image(gtk.image_new_from_file(icon))
                    item3.connect('activate', self.addToGroupFromMenu, group, eventType)
                    menu3.add(item3)
                menu3.show_all()
                item2.set_submenu(menu3)
            menu2.add(item2)
        ##
        menu2.show_all()
        addToItem.set_submenu(menu2)
        return addToItem
    def popupMenuCell(self, widget, etime, x, y):
        menu = gtk.Menu()
        ####
        menu.add(labelStockMenuItem('_Copy Date', gtk.STOCK_COPY, self.copyDate))
        menu.add(labelStockMenuItem('Day Info', gtk.STOCK_INFO, self.dayInfoShow))
        menu.add(self.getEventAddToMenuItem())
        menu.add(gtk.SeparatorMenuItem())
        menu.add(labelStockMenuItem('Select _Today', gtk.STOCK_HOME, self.goToday))
        menu.add(labelStockMenuItem('Select _Date...', gtk.STOCK_INDEX, self.selectDateShow))
        if isfile('/usr/bin/evolution'):##??????????????????
            menu.add(labelImageMenuItem('In E_volution', 'evolution-18.png', ui.dayOpenEvolution))
        #if isfile('/usr/bin/sunbird'):##??????????????????
        #    menu.add(labelImageMenuItem('In _Sunbird', 'sunbird-18.png', ui.dayOpenSunbird))
        ####
        moreMenu = gtk.Menu()
        moreMenu.add(labelStockMenuItem('_Customize', gtk.STOCK_EDIT, self.customizeShow))
        moreMenu.add(labelStockMenuItem('_Preferences', gtk.STOCK_PREFERENCES, self.prefShow))
        moreMenu.add(labelStockMenuItem('_Event Manager', gtk.STOCK_ADD, self.eventManShow))
        moreMenu.add(labelImageMenuItem('Time Line', 'timeline-18.png', self.timeLineShow))
        #moreMenu.add(labelImageMenuItem('Week Calendar', 'weekcal-18.png', self.weekCalShow))
        moreMenu.add(labelStockMenuItem(_('Export to %s')%'HTML', gtk.STOCK_CONVERT, self.exportClicked))
        moreMenu.add(labelStockMenuItem('_About', gtk.STOCK_ABOUT, self.aboutShow))
        if self.trayMode!=1:
            moreMenu.add(labelStockMenuItem('_Quit', gtk.STOCK_QUIT, self.quit))
        ##
        moreMenu.show_all()
        moreItem = gtk.MenuItem(_('More'))
        moreItem.set_submenu(moreMenu)
        menu.add(moreItem)
        ####
        menu.show_all()
        dx, dy = widget.translate_coordinates(self, x, y)
        wx, wy = self.window.get_origin()
        x = wx+dx
        y = wy+dy
        if rtl:
            #mw = menu.allocation.width
            #if mw < 2:# menu width
            mw = 145 ## FIXME
            x -= mw
        ####
        menu.popup(None, None, lambda m: (x, y, True), 3, etime)
        ui.updateFocusTime()
    def popupMenuMain(self, widget, etime, x, y):
        menu = self.menuMain
        dx, dy = widget.translate_coordinates(self, x, y)
        wx, wy = self.window.get_origin()
        x = wx+dx
        y = wy+dy
        if rtl:
            mw = menu.allocation.width
            if mw < 2:# menu width
                mw = 145
            x -= mw
        menu.popup(None, None, lambda m: (x, y, True), 3, etime)
        #self.menuMainWidth = menu.allocation.width
        ui.updateFocusTime()
    def addToGroupFromMenu(self, menu, group, eventType):
        #print 'addToGroupFromMenu', group.title, eventType
        title = _('Add ') + event_lib.classes.event.byName[eventType].desc
        event = addNewEvent(group, eventType, title, parent=self, useSelectedDate=True)
        if event is None:
            return
        ui.reloadGroups.append(group.id)
        self.onConfigChange()
    def prefUpdateBgColor(self, cal):
        ui.prefDialog.colorbBg.set_color(ui.bgColor)
        ui.saveLiveConf()
    def keepAboveClicked(self, check):
        act = check.get_active()
        self.set_keep_above(act)
        ui.winKeepAbove = act
        ui.saveLiveConf()
    def stickyClicked(self, check):
        if check.get_active():
            self.stick()
            ui.winSticky = True
        else:
            self.unstick()
            ui.winSticky = False
        ui.saveLiveConf()
    def updateMenuSize(self):## DIRTY FIXME
        ## To calc/update menus size (width is used)
        getMenuPos = lambda widget: (ud.screenW, 0, True)
        self.menuMain.popup(None, None, getMenuPos, 3, 0)
        self.menuMain.hide()
    def copyDate(self, obj=None, event=None):
        self.clipboard.set_text(ui.cell.format(ud.dateFormatBin))
        #self.clipboard.store() ## ?????? No need!
    def copyDateToday(self, obj=None, event=None):
        self.clipboard.set_text(ui.todayCell.format(ud.dateFormatBin))
        #self.clipboard.store() ## ?????? No need!
    def copyTime(self, obj=None, event=None):
        self.clipboard.set_text(ui.todayCell.format(ud.clockFormatBin, tm=localtime()[3:6]))
        #self.clipboard.store() ## ?????? No need!
    """
    def updateToolbarClock(self):
        if ui.showDigClockTb:
            if self.clock==None:
                self.clock = FClockLabel(ud.clockFormat)
                self.toolbBox.pack_start(self.clock, 0, 0)
                self.clock.show()
            else:
                self.clock.format = ud.clockFormat
        else:
            if self.clock!=None:
                self.clock.destroy()
                self.clock = None
    def updateTrayClock(self, checkTrayMode=True):
        if checkTrayMode and self.trayMode!=2:
            return
        if ui.showDigClockTr:
            if self.clockTr==None:
                self.clockTr = FClockLabel(ud.clockFormat)
                try:
                    self.trayHbox.pack_start(self.clockTr, 0, 0)
                except AttributeError:
                    self.clockTr.destroy()
                    self.clockTr = None
                else:
                    self.clockTr.show()
            else:
                self.clockTr.format = ud.clockFormat
        else:
            if self.clockTr!=None:
                self.clockTr.destroy()
                self.clockTr = None
    """
    aboutShow = lambda self, obj=None, data=None: openWindow(self.about)
    def aboutHide(self, widget, arg=None):## arg maybe an event, or response id
        self.about.hide()
        return True
    prefShow = lambda self, obj=None, data=None: openWindow(ui.prefDialog)
    customizeShow = lambda self, obj=None, data=None: openWindow(self.customizeDialog)
    eventManShow = lambda self, obj=None, data=None: openWindow(ui.eventManDialog)
    timeLineShow = lambda self, obj=None, data=None: openWindow(ui.timeLineWin)
    #weekCalShow = lambda self, obj=None, data=None: openWindow(ui.weekCalWin)
    def trayInit(self):
        if self.trayMode==2:
            self.trayPix = gdk.Pixbuf(gdk.COLORSPACE_RGB, True, 8, ui.traySize, ui.traySize)
            ####
            useAppIndicator = ui.useAppIndicator
            if useAppIndicator:
                try:
                    import appindicator
                except ImportError:
                    useAppIndicator = False
            if useAppIndicator:
                from scal2.ui_gtk.starcal2_appindicator import IndicatorStatusIconWrapper
                self.sicon = IndicatorStatusIconWrapper(self)
            else:
                self.sicon = gtk.StatusIcon()
                ##self.sicon.set_blinking(True) ## for Alarms ## some problem with gnome-shell
                #self.sicon.set_name('starcal2')
                ## Warning: g_object_notify: object class `GtkStatusIcon' has no property named `name'
                self.sicon.set_title(core.APP_DESC)
                self.sicon.set_visible(True)## is needed ????????
                self.sicon.connect('button-press-event', self.trayButtonPress)
                self.sicon.connect('activate', self.trayClicked)
                self.sicon.connect('popup-menu', self.trayPopup)
        else:
            self.sicon = None
    getMainWinMenuItem = lambda self: labelMenuItem('Main Window', self.trayClicked)
    getTrayPopupItems = lambda self: [
        labelStockMenuItem('Copy _Time', gtk.STOCK_COPY, self.copyTime),
        labelStockMenuItem('Copy _Date', gtk.STOCK_COPY, self.copyDateToday),
        labelStockMenuItem('Ad_just System Time', gtk.STOCK_PREFERENCES, self.adjustTime),
        #labelStockMenuItem('_Add Event', gtk.STOCK_ADD, ui.eventManDialog.addCustomEvent),## FIXME
        labelStockMenuItem(_('Export to %s')%'HTML', gtk.STOCK_CONVERT, self.exportClickedTray),
        labelStockMenuItem('_Preferences', gtk.STOCK_PREFERENCES, self.prefShow),
        labelStockMenuItem('_Customize', gtk.STOCK_EDIT, self.customizeShow),
        labelStockMenuItem('_Event Manager', gtk.STOCK_ADD, self.eventManShow),
        labelImageMenuItem('Time Line', 'timeline-18.png', self.timeLineShow),
        labelStockMenuItem('_About', gtk.STOCK_ABOUT, self.aboutShow),
        gtk.SeparatorMenuItem(),
        labelStockMenuItem('_Quit', gtk.STOCK_QUIT, self.quit),
    ]
    def trayPopup(self, sicon, button, etime):
        menu = gtk.Menu()
        if os.sep == '\\':
            setupMenuHideOnLeave(menu)
        items = self.getTrayPopupItems()
        # items.insert(0, self.getMainWinMenuItem())## FIXME
        geo = self.sicon.get_geometry() ## Returns None on windows, why???
        if geo is None:## windows, taskbar is on buttom(below)
            items.reverse()
            get_pos_func = None
        else:
            y1 = geo[1][1]
            y = gtk.status_icon_position_menu(menu, self.sicon)[1]
            if y<y1:## taskbar is on bottom
                items.reverse()
            get_pos_func = gtk.status_icon_position_menu
        for item in items:
            menu.add(item)
        menu.show_all()
        menu.popup(None, None, get_pos_func, button, etime, self.sicon)
        ui.updateFocusTime()
    def onCurrentDateChange(self, gdate):
        self.trayUpdate(gdate=gdate)
    def getTrayTooltip(self):
        ##tt = core.weekDayName[core.getWeekDay(*ddate)]
        tt = core.weekDayName[core.jwday(ui.todayCell.jd)]
        #if ui.pluginsTextTray:##?????????
        #    sep = _(',')+' '
        #else:
        sep = '\n'
        for mode in calTypes.active:
            y, m, d = ui.todayCell.dates[mode]
            tt += '%s%s %s %s'%(sep, _(d), getMonthName(mode, m, y), _(y))
        if ui.pluginsTextTray:
            text = ui.todayCell.pluginsText
            if text!='':
                tt += '\n\n%s'%text ## .replace('\t', '\n') ## FIXME
        for item in ui.todayCell.eventsData:
            if not item['showInTray']:
                continue
            itemS = ''
            if item['time']:
                itemS += item['time'] + ' - '
            itemS += item['text'][0]
            tt += '\n\n%s'%itemS
        return tt
    def trayUpdate(self, gdate=None, checkTrayMode=True):
        if checkTrayMode and self.trayMode < 1:
            return
        if gdate is None:
            gdate = localtime()[:3]
        if core.primaryMode==core.DATE_GREG:
            ddate = gdate
        else:
            ddate = core.convert(gdate[0], gdate[1], gdate[2], core.DATE_GREG, core.primaryMode)
        imagePath = ui.trayImageHoli if ui.todayCell.holiday else ui.trayImage
        ######################################
        '''
        import Image, ImageDraw, ImageFont
        im = Image.open(imagePath)
        w, h = im.size
        draw = ImageDraw.Draw(im)
        text = _(ddate[2]).decode('utf8')
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', 15)
        fw, fh = font.getsize(text)
        draw.text(
            ((w-fw)/2, (h-fh)/2),
            text,
            font=font,
            fill=ui.trayTextColor,
        )
        self.sicon.set_from_pixbuf(gdk.pixbuf_new_from_data(im.tostring(), gdk.COLORSPACE_RGB, True, 8, w, h, 4*w))
        '''
        pixbuf = gdk.pixbuf_new_from_file(imagePath)
        ##pixbuf.scale() #????????????
        ###################### PUTTING A TEXT ON A PIXBUF
        pmap = pixbuf.render_pixmap_and_mask(alpha_threshold=127)[0] ## pixmap is also a drawable
        textLay = newTextLayout(self, _(ddate[2]), ui.trayFont)
        w, h = textLay.get_pixel_size()
        s = ui.traySize
        if ui.trayY0 == None:
            y = s/4+int((0.9*s-h)/2)
        else:
            y = ui.trayY0
        pmap.draw_layout(pmap.new_gc(), (s-w)/2, y, textLay, gdk.Color(*ui.trayTextColor))## , foreground, background)
        self.trayPix.get_from_drawable(pmap, self.get_screen().get_system_colormap(), 0, 0, 0, 0, s, s)
        ######################################
        self.sicon.set_from_pixbuf(self.trayPix)
        ######################################
        set_tooltip(self.sicon, self.getTrayTooltip())
        return True
    def trayButtonPress(self, obj, gevent):
        if gevent.button == 2:
            ## middle button press
            self.copyDate()
            return True
    def trayClicked(self, obj=None):
        if self.get_property('visible'):
            ui.winX, ui.winY = self.get_position()
            self.hide()
        else:
            self.move(ui.winX, ui.winY)
            ## every calling of .hide() and .present(), makes dialog not on top
            ## (forgets being on top)
            act = self.checkAbove.get_active()
            self.set_keep_above(act)
            if self.checkSticky.get_active():
                self.stick()
            self.deiconify()
            self.present()
    def dialogClose(self, widget=None, event=None):
        ui.winX, ui.winY = self.get_position()
        if self.trayMode==0 or not self.sicon:
            self.quit()
        elif self.trayMode>1:
            if self.sicon.is_embedded():
                self.hide()
            else:
                self.quit()
        return True
    def dialogEsc(self):
        ui.winX, ui.winY = self.get_position()
        if self.trayMode==0:
            self.quit()
        elif self.trayMode>1:
            if self.sicon.is_embedded():
                self.hide()
    def quit(self, widget=None, event=None):
        try:
            ui.saveLiveConf()
        except:
            myRaise()
        if self.trayMode>1 and self.sicon:
            self.sicon.set_visible(False) ## needed for windows ## before or after main_quit ?
        return gtk.main_quit()
    def adjustTime(self, widget=None, event=None):
        Popen(ud.adjustTimeCmd)
    exportClicked = lambda self, widget=None: self.exportDialog.showDialog(ui.cell.year, ui.cell.month)
    def exportClickedTray(self, widget=None, event=None):
        y, m = core.getSysDate()[:2]
        self.exportDialog.showDialog(y, m)
    def onConfigChange(self, *a, **kw):
        ud.IntegratedCalObj.onConfigChange(self, *a, **kw)
        #self.set_property('skip-taskbar-hint', not ui.winTaskbar) ## self.set_skip_taskbar_hint ## FIXME
        ## skip-taskbar-hint  need to restart ro be applied
        self.updateMenuSize()
        #self.updateToolbarClock()## FIXME
        #self.updateTrayClock()
        self.trayUpdate()


###########################################################################3


#core.COMMAND = sys.argv[0] ## OR __file__ ## ????????


gtk.init_check()

clickWebsite = lambda widget, url: core.openUrl(url)
try:
    gtk.link_button_set_uri_hook(clickWebsite)
except:## old PyGTK (older than 2.10)
    pass

try:
    gtk.about_dialog_set_url_hook(clickWebsite)
except:## old PyGTK (older than 2.10)
    pass

for plug in core.allPlugList:
    if hasattr(plug, 'onCurrentDateChange'):
        listener.dateChange.add(plug)


"""
themeDir = join(rootDir, 'themes')
theme = 'Dark' # 'Default
if theme!=None:
    gtkrc = join(themeDir, theme, 'gtkrc')
    try:
        #gtk.rc_set_default_files([gtkrc])
        gtk.rc_parse(gtkrc)
        #gtk.rc_reparse_all()
        #exec(open(join(themeDir, theme, 'starcalrc')).read())
    except:
        myRaise(__file__)
"""





def main():
    '''
    try:
        import psyco
    except ImportError:
        print('Warning: module "psyco" not found. It could speed up execution.')
        psyco_found=False
    else:
        psyco.full()
        print('Using module "psyco" to speed up execution.')
        psyco_found=True'''
    trayMode = 2
    action = ''
    if ui.showMain:
        action = 'show'
    if len(sys.argv)>1:
        if sys.argv[1]=='--no-tray': ## no tray icon
            trayMode = 0
            action = 'show'
        elif sys.argv[1]=='--hide':
            action = ''
        elif sys.argv[1]=='--show':
            action = 'show'
        #elif sys.argv[1]=='--html':#????????????
        #    action = 'html'
        #elif sys.argv[1]=='--svg':#????????????
        #    action = 'svg'
    ###############################
    ui.init()
    ###############################
    if cmpVersion(event_lib.info.version, '2.2.2') < 0:## right place? FIXME
        from scal2.ui_gtk.event.bulk_save_timezone import BulkSaveTimeZoneDialog
        BulkSaveTimeZoneDialog().run()
    event_lib.info.updateAndSave()
    ###############################
    mainWin = MainWin(trayMode=trayMode)
    #if action=='html':
    #    mainWin.exportHtml('calendar.html') ## exportHtml(path, months, title)
    #    sys.exit(0)
    #elif action=='svg':
    #    mainWin.export.exportSvg('%s/2010-01.svg'%deskDir, [(2010, 1)])
    #    sys.exit(0)
    if action=='show' or not mainWin.sicon:
        mainWin.present()
    ##ud.rootWindow.set_cursor(gdk.Cursor(gdk.LEFT_PTR))#???????????
    return gtk.main()


if __name__ == '__main__':## this file may be called from starcal-gnome2-applet
    sys.exit(main())

