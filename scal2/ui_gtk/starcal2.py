#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
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

import sys

if sys.version_info[0] != 2:
    print('Run this script with Python 2.x')
    sys.exit(1)

from time import time as now
from time import localtime
import os
from os.path import join, dirname, isfile, isdir, splitext

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal2.path import *
from scal2.utils import myRaise

if not isdir(confDir):
    from scal2.utils import restartLow
    try:
        __import__('scal2.ui_gtk.import_config_1to2')
    except:
        myRaise()
    restartLow()

from scal2.utils import toStr, toUnicode
from scal2.utils import versionLessThan
from scal2.cal_types import calTypes
from scal2 import core

#core.showInfo()

from scal2 import locale_man
from scal2.locale_man import rtl, lang ## import scal2.locale_man after core
#_ = locale_man.loadTranslator(False)## FIXME
from scal2.locale_man import tr as _
from scal2 import event_lib
from scal2 import ui

import gobject

from scal2.ui_gtk import *
from scal2.ui_gtk.decorators import registerSignals
from scal2.ui_gtk.utils import *
#from scal2.ui_gtk.color_utils import rgbToGdkColor
from scal2.ui_gtk.drawing import newOutlineSquarePixbuf
#from ui_gtk.mywidgets2.multi_spin_button import DateButtonOption
from scal2.ui_gtk import listener
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.customize import DummyCalObj, CustomizableCalBox


ui.uiName = 'gtk'


mainWinItemsDesc = {
    'eventDayView': _('Events of Day'),
    'labelBox': _('Year & Month Labels'),
    'monthCal': _('Month Calendar'),
    'pluginsText': _('Plugins Text'),
    'seasonPBar': _('Season Progress Bar'),
    'statusBar': _('Status Bar'),
    'toolbar': _('Toolbar'),
    'weekCal': _('Week Calendar'),
    'winContronller': _('Window Controller'),
}




#def show_event(widget, event):
#    print(type(widget), event.type.value_name, event.get_value())#, event.send_event


def liveConfChanged():
    tm = now()
    if tm-ui.lastLiveConfChangeTime > ui.saveLiveConfDelay:
        gobject.timeout_add(int(ui.saveLiveConfDelay*1000), ui.saveLiveConfLoop)
        ui.lastLiveConfChangeTime = tm


# How to define icon of custom stock????????????
#gtk.stock_add((
#('gtk-evolution', 'E_volution', gdk.BUTTON1_MASK, 0, 'gtk20')








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
    def switchWcalMcal(self):
        wi = None
        mi = None
        for i, item in enumerate(self.items):
            if item._name == 'weekCal':
                wi = i
            elif item._name == 'monthCal':
                mi = i
        wcal, mcal = self.items[wi], self.items[mi]
        wcal.enable, mcal.enable = mcal.enable, wcal.enable
        ## FIXME
        #self.reorder_child(wcal, mi)
        #self.reorder_child(mcal, wi)
        #self.items[wi], self.items[mi] = mcal, wcal
        self.showHide()
        self.onDateChange()


@registerSignals
class MainWin(gtk.Window, ud.BaseCalObj):
    _name = 'mainWin'
    desc = _('Main Window')
    timeout = 1 ## second
    setMinHeight = lambda self: self.resize(ui.winWidth, 2)
    '''
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(),
            width=self.get_allocation().width,
            height=self.get_allocation().height,
            window_type=gdk.WINDOW_TOPLEVEL,
            wclass=gdk.INPUT_OUTPUT,
            event_mask=self.get_events() \
                | gdk.EXPOSURE_MASK | gdk.BUTTON1_MOTION_MASK | gdk.BUTTON_PRESS_MASK
                | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK
        )
        self.get_window().set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.get_window().move_resize(*self.get_allocation())
        self.get_window().set_decorations(gdk.DECORE_CLOSE)
        self.get_window().set_functions(gdk.FUNC_CLOSE)
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
        #ui.eventManDialog = None
        #ui.timeLineWin = None
        ###
        #ui.weekCalWin = WeekCalWindow()
        #ud.windowList.appendItem(ui.weekCalWin)
        ###
        self.dayInfoDialog = None
        #print('windowList.items', [item._name for item in ud.windowList.items])
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
        self.winCon = None
        ############
        self.vbox = MainWinVbox()
        ui.checkMainWinItems()
        itemsPkg = 'scal2.ui_gtk.mainwin_items'
        for (name, enable) in ui.mainWinItems:
            #print(name, enable)
            if enable:
                try:
                    module = __import__(
                        '.'.join([
                            itemsPkg,
                            name,
                        ]),
                        fromlist=['CalObj'],
                    )
                    CalObj = module.CalObj
                except:
                    myRaise()
                    continue
                item = CalObj()
                item.enable = enable
                item.connect('size-request', self.childSizeRequest) ## or item.connect
                #modify_bg_all(item, gtk.STATE_NORMAL, rgbToGdkColor(*ui.bgColor))
            else:
                desc = mainWinItemsDesc[name]
                item = DummyCalObj(name, desc, itemsPkg, True)
                ## what about size-request FIXME
            self.vbox.appendItem(item)
        self.appendItem(self.vbox)
        self.vbox.show()
        self.customizeDialog = None
        #######
        self.add(self.vbox)
        ####################
        self.isMaximized = False
        ####################
        #ui.prefDialog = None
        self.exportDialog = None
        self.selectDateDialog = None
        ############### Building About Dialog
        self.aboutDialog = None
        ###############
        self.menuMain = None
        #####
        check = gtk.CheckMenuItem(label=_('_On Top'))
        check.connect('activate', self.keepAboveClicked)
        check.set_active(ui.winKeepAbove)
        self.set_keep_above(ui.winKeepAbove)
        self.checkAbove = check
        #####
        check = gtk.CheckMenuItem(label=_('_Sticky'))
        check.connect('activate', self.stickyClicked)
        check.set_active(ui.winSticky)
        if ui.winSticky:
            self.stick()
        self.checkSticky = check
        ############################################################
        self.trayInit()
        listener.dateChange.add(self)
        #if self.trayMode!=1:
        #    gobject.timeout_add_seconds(self.timeout, self.trayUpdate)
        #########
        self.connect('delete-event', self.onDeleteEvent)
        #########################################
        for plug in core.allPlugList:
            if plug.external and hasattr(plug, 'set_dialog'):
                plug.set_dialog(self)
        ###########################
        self.onConfigChange()
        #ud.rootWindow.set_cursor(gdk.Cursor(gdk.LEFT_PTR))
    #def mainWinStateEvent(self, obj, event):
        #print(dir(event))
        #print(event.new_window_state)
        #self.event = event
    def childSizeRequest(self, cal, req):
        self.setMinHeight()
    def selectDateResponse(self, widget, y, m, d):
        ui.changeDate(y, m, d)
        self.onDateChange()
    def keyPress(self, arg, event):
        kname = gdk.keyval_name(event.keyval).lower()
        #print(now(), 'MainWin.keyPress', kname)
        if kname=='escape':
            self.onEscape()
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
        if self.winCon and self.winCon.enable:
            self.winCon.windowFocusIn()
    def focusOut(self, widegt, event, data=None):
        ## called 0.0004 sec (max) after focusIn (if switched between two windows)
        dt = now()-ui.focusTime
        #print('focusOut', dt)
        if dt > 0.05: ## FIXME
            self.focus = False
            gobject.timeout_add(2, self.focusOutDo)
    def focusOutDo(self):
        if not self.focus:# and t-self.focusOutTime>0.002:
            ab = self.checkAbove.get_active()
            self.set_keep_above(ab)
            if self.winCon and self.winCon.enable:
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
        wx, wy = self.get_position()
        maxPosDelta = max(abs(ui.winX-wx), abs(ui.winY-wy))
        #print(wx, wy)
        ww, wh = self.get_size()
        #if ui.bgUseDesk and maxPosDelta > 1:## FIXME
        #    self.queue_draw()
        if self.get_property('visible'):
            ui.winX, ui.winY = (wx, wy)
        ui.winWidth = ww
        liveConfChanged()
        return False
    def buttonPress(self, obj, event):
        b = event.button
        #print('buttonPress', b)
        if b==3:
            self.menuMainCreate()
            self.menuMain.popup(None, None, None, 3, event.time)
            ui.updateFocusTime()
        elif b==1:
            x, y, mask = ud.rootWindow.get_pointer()
            self.begin_move_drag(event.button, x, y, event.time)
        return False
    def startResize(self, widget, event):
        if self.menuMain:
            self.menuMain.hide()
        x, y, mask = ud.rootWindow.get_pointer()
        self.begin_resize_drag(gdk.WINDOW_EDGE_SOUTH_EAST, event.button, x, y, event.time)
        return True
    def changeDate(self, year, month, day):
        ui.changeDate(year, month, day)
        self.onDateChange()
    goToday = lambda self, obj=None: self.changeDate(*core.getSysDate(calTypes.primary))
    def onDateChange(self, *a, **kw):
        #print('MainWin.onDateChange')
        ud.BaseCalObj.onDateChange(self, *a, **kw)
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
    def menuCellPopup(self, widget, etime, x, y):
        menu = gtk.Menu()
        ####
        menu.add(labelStockMenuItem('_Copy Date', gtk.STOCK_COPY, self.copyDate))
        menu.add(labelStockMenuItem('Day Info', gtk.STOCK_INFO, self.dayInfoShow))
        menu.add(self.getEventAddToMenuItem())
        menu.add(gtk.SeparatorMenuItem())
        menu.add(labelStockMenuItem('Select _Today', gtk.STOCK_HOME, self.goToday))
        menu.add(labelStockMenuItem('Select _Date...', gtk.STOCK_INDEX, self.selectDateShow))
        if widget._name in ('weekCal', 'monthCal'):
            menu.add(labelStockMenuItem(
                'Switch to ' + ('Month Calendar' if widget._name=='weekCal' else 'Week Calendar'),
                gtk.STOCK_REDO,
                self.switchWcalMcal,
            ))
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
        wx, wy = self.get_window().get_origin()
        x = wx+dx
        y = wy+dy
        if rtl:
            mw = menu.size_request()[0]
            x -= mw
        ####
        menu.popup(None, None, lambda m: (x, y, True), 3, etime)
        ui.updateFocusTime()
    def menuMainCreate(self):
        if self.menuMain:
            return
        menu = gtk.Menu()
        ####
        item = gtk.ImageMenuItem(_('Resize'))
        item.set_image(imageFromFile('resize.png'))
        item.connect('button-press-event', self.startResize)
        menu.add(item)
        #######
        menu.add(self.checkAbove)
        menu.add(self.checkSticky)
        #######
        menu.add(labelStockMenuItem('Select _Today', gtk.STOCK_HOME, self.goToday))
        menu.add(labelStockMenuItem('Select _Date...', gtk.STOCK_INDEX, self.selectDateShow))
        menu.add(labelStockMenuItem('Day Info', gtk.STOCK_INFO, self.dayInfoShow))
        menu.add(labelStockMenuItem('_Customize', gtk.STOCK_EDIT, self.customizeShow))
        menu.add(labelStockMenuItem('_Preferences', gtk.STOCK_PREFERENCES, self.prefShow))
        #menu.add(labelStockMenuItem('_Add Event', gtk.STOCK_ADD, ui.addCustomEvent))
        menu.add(labelStockMenuItem('_Event Manager', gtk.STOCK_ADD, self.eventManShow))
        menu.add(labelImageMenuItem('Time Line', 'timeline-18.png', self.timeLineShow))
        #menu.add(labelImageMenuItem('Week Calendar', 'weekcal-18.png', self.weekCalShow))
        menu.add(labelStockMenuItem(_('Export to %s')%'HTML', gtk.STOCK_CONVERT, self.exportClicked))
        menu.add(labelStockMenuItem('_About', gtk.STOCK_ABOUT, self.aboutShow))
        if self.trayMode!=1:
            menu.add(labelStockMenuItem('_Quit', gtk.STOCK_QUIT, self.quit))
        menu.show_all()
        self.menuMain = menu
    def menuMainPopup(self, widget, etime, x, y):
        self.menuMainCreate()
        if etime == 0:
            etime = gtk.get_current_event_time()
        menu = self.menuMain
        dx, dy = widget.translate_coordinates(self, x, y)
        wx, wy = self.get_window().get_origin()
        x = wx+dx
        y = wy+dy
        if rtl:
            mw = menu.size_request()[0]
            x -= mw
        menu.popup(None, None, lambda m: (x, y, True), 3, etime)
        ui.updateFocusTime()
    def addToGroupFromMenu(self, menu, group, eventType):
        from scal2.ui_gtk.event.common import addNewEvent
        #print('addToGroupFromMenu', group.title, eventType)
        title = _('Add ') + event_lib.classes.event.byName[eventType].desc
        event = addNewEvent(group, eventType, title, parent=self, useSelectedDate=True)
        if event is None:
            return
        ui.reloadGroups.append(group.id)
        self.onConfigChange()
    def prefUpdateBgColor(self, cal):
        if ui.prefDialog:
            ui.prefDialog.colorbBg.set_color(ui.bgColor)
        #else:## FIXME
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
    def copyDate(self, obj=None, event=None):
        setClipboard(ui.cell.format(ud.dateFormatBin))
    def copyDateToday(self, obj=None, event=None):
        setClipboard(ui.todayCell.format(ud.dateFormatBin))
    def copyTime(self, obj=None, event=None):
        setClipboard(ui.todayCell.format(ud.clockFormatBin, tm=localtime()[3:6]))
    """
    def updateToolbarClock(self):
        if ui.showDigClockTb:
            if self.clock==None:
                from scal2.ui_gtk.mywidgets.clock import FClockLabel
                self.clock = FClockLabel(ud.clockFormat)
                pack(self.toolbBox, self.clock)
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
                from scal2.ui_gtk.mywidgets.clock import FClockLabel
                self.clockTr = FClockLabel(ud.clockFormat)
                try:
                    pack(self.trayHbox, self.clockTr)
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
    #weekCalShow = lambda self, obj=None, data=None: openWindow(ui.weekCalWin)
    def trayInit(self):
        if self.trayMode==2:
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
        #labelStockMenuItem('_Add Event', gtk.STOCK_ADD, ui.addCustomEvent),## FIXME
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
            tt += '%s%s %s %s'%(sep, _(d), core.getMonthName(mode, m, y), _(y))
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
    def trayUpdateIcon(self, ddate):## FIXME
        imagePath = ui.trayImageHoli if ui.todayCell.holiday else ui.trayImage
        ext = splitext(imagePath)[1][1:].lower()
        loader = gdk.pixbuf_loader_new_with_mime_type('image/%s'%ext)
        data = open(imagePath).read()
        if ext == 'svg':
            dayNum = _(ddate[2])
            if ui.trayFontFamilyEnable:
                if ui.trayFontFamily:
                    family = ui.trayFontFamily
                else:
                    family = ui.getFont()[0]
                dayNum = '<tspan style="font-family:%s">%s</tspan>'%(family, dayNum)
            data = data.replace(
                'TX',
                dayNum,
            )
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf()
        self.sicon.set_from_pixbuf(pixbuf)
    def trayUpdate(self, gdate=None, checkTrayMode=True):
        if checkTrayMode and self.trayMode < 1:
            return
        if gdate is None:
            gdate = localtime()[:3]
        if calTypes.primary==core.DATE_GREG:
            ddate = gdate
        else:
            ddate = core.convert(gdate[0], gdate[1], gdate[2], core.DATE_GREG, calTypes.primary)
        #######
        self.sicon.set_from_file(join(pixDir, 'starcal2-24.png'))
        self.trayUpdateIcon(ddate)
        #######
        set_tooltip(self.sicon, self.getTrayTooltip())
        return True
    def trayButtonPress(self, obj, gevent):
        if gevent.button == 2:
            ## middle button press
            self.copyDate()
            return True
    def trayClicked(self, obj=None):
        if self.get_property('visible'):
            #ui.winX, ui.winY = self.get_position()## FIXME gives bad position sometimes
            #liveConfChanged()
            #print(ui.winX, ui.winY)
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
    def onDeleteEvent(self, widget=None, event=None):
        #ui.winX, ui.winY = self.get_position()## FIXME gives bad position sometimes
        #liveConfChanged()
        #print(ui.winX, ui.winY)
        if self.trayMode==0 or not self.sicon:
            self.quit()
        elif self.trayMode>1:
            if self.sicon.is_embedded():
                self.hide()
            else:
                self.quit()
        return True
    def onEscape(self):
        #ui.winX, ui.winY = self.get_position()## FIXME gives bad position sometimes
        #liveConfChanged()
        #print(ui.winX, ui.winY)
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
        from subprocess import Popen
        Popen(ud.adjustTimeCmd)
    def aboutShow(self, obj=None, data=None):
        if not self.aboutDialog:
            dialog = AboutDialog(
                name=core.APP_DESC,
                version=core.VERSION,
                title=_('About ')+core.APP_DESC,
                authors=[_(line) for line in open(join(rootDir, 'authors-dialog')).read().splitlines()],
                comments=core.aboutText,
                license=core.licenseText,
                website=core.homePage,
            )
            ## add Donate button ## FIXME
            dialog.connect('delete-event', self.aboutHide)
            dialog.connect('response', self.aboutHide)
            #dialog.set_logo(gdk.pixbuf_new_from_file(ui.logo))
            #dialog.set_skip_taskbar_hint(True)
            self.aboutDialog = dialog
        openWindow(self.aboutDialog)
    def aboutHide(self, widget, arg=None):## arg maybe an event, or response id
        self.aboutDialog.hide()
        return True
    def prefShow(self, obj=None, data=None):
        if not ui.prefDialog:
            from scal2.ui_gtk.preferences import PrefDialog
            ui.prefDialog = PrefDialog(self.trayMode)
            ui.prefDialog.updatePrefGui()
        openWindow(ui.prefDialog)
    def eventManCreate(self):
        if not ui.eventManDialog:
            from scal2.ui_gtk.event.main import EventManagerDialog
            ui.eventManDialog = EventManagerDialog()
    def eventManShow(self, obj=None, data=None):
        self.eventManCreate()
        openWindow(ui.eventManDialog)
    def addCustomEvent(self, obj=None):
        self.eventManCreate()
        ui.eventManDialog.addCustomEvent()
    def timeLineShow(self, obj=None, data=None):
        if not ui.timeLineWin:
            from scal2.ui_gtk.timeline import TimeLineWindow
            ui.timeLineWin = TimeLineWindow()
        openWindow(ui.timeLineWin)
    def selectDateShow(self, widget=None):
        if not self.selectDateDialog:
            from scal2.ui_gtk.selectdate import SelectDateDialog
            self.selectDateDialog = SelectDateDialog()
            self.selectDateDialog.connect('response-date', self.selectDateResponse)
        openWindow(self.selectDateDialog)
    def dayInfoShow(self, widget=None):
        if not self.dayInfoDialog:
            from scal2.ui_gtk.day_info import DayInfoDialog
            self.dayInfoDialog = DayInfoDialog()
            self.dayInfoDialog.onDateChange()
        openWindow(self.dayInfoDialog)
    def customizeDialogCreate(self):
        if not self.customizeDialog:
            from scal2.ui_gtk.customize_dialog import CustomizeDialog
            self.customizeDialog = CustomizeDialog(self.vbox)
    def switchWcalMcal(self, widget=None):
        self.customizeDialogCreate()
        self.vbox.switchWcalMcal()
        self.customizeDialog.updateTreeEnableChecks()
        self.customizeDialog.save()
    def customizeShow(self, obj=None, data=None):
        self.customizeDialogCreate()
        openWindow(self.customizeDialog)
    def exportShow(self, year, month):
        if not self.exportDialog:
            from scal2.ui_gtk.export import ExportDialog
            self.exportDialog = ExportDialog()
        self.exportDialog.showDialog(year, month)
    def exportClicked(self, widget=None):
        self.exportShow(ui.cell.year, ui.cell.month)
    def exportClickedTray(self, widget=None, event=None):
        year, month, day = core.getSysDate(calTypes.primary)
        self.exportShow(year, month)
    def onConfigChange(self, *a, **kw):
        ud.BaseCalObj.onConfigChange(self, *a, **kw)
        #self.set_property('skip-taskbar-hint', not ui.winTaskbar) ## self.set_skip_taskbar_hint ## FIXME
        ## skip-taskbar-hint  need to restart ro be applied
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
    ## right place? FIXME
    if core.BRANCH == 'master' and versionLessThan(event_lib.info.version, '2.3.0'):
        from scal2.ui_gtk.event.bulk_save_timezone import BulkSaveTimeZoneDialog
        BulkSaveTimeZoneDialog().run()
    event_lib.info.updateAndSave()
    ###############################
    mainWin = MainWin(trayMode=trayMode)
    #if action=='html':
    #    mainWin.exportHtml('calendar.html') ## exportHtml(path, months, title)
    #    sys.exit(0)
    #elif action=='svg':
    #    mainWin.export.exportSvg('%s/2010-01.svg'%core.deskDir, [(2010, 1)])
    #    sys.exit(0)
    if action=='show' or not mainWin.sicon:
        mainWin.present()
    ##ud.rootWindow.set_cursor(gdk.Cursor(gdk.LEFT_PTR))#???????????
    return gtk.main()


if __name__ == '__main__':## this file may be called from starcal-gnome2-applet
    sys.exit(main())

