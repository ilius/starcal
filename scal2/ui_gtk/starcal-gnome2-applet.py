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

import sys
from os.path import dirname
sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal2 import core
from scal2.locale_man import tr as _

from scal2.ui_gtk.starcal2 import *

import gtk
from gtk import gdk

import gnomeapplet
## import gnomeapplet module AFTRE scal2.* modules, to prevent crash on first run (after boot up)


#class MyApplet(gnomeapplet.Applet):
#    def __init__(self, applet):
#        applet.__init__(self)


def getattribute(obj, atrib):
    if atrib not in ('lastGDate', '__class__'):
        print('getattribute', obj.__class__.__name__, atrib)
    return object.__getattribute__(obj, atrib)

#@registerType
class StarCalApplet(MainWin):
    #__getattribute__ = getattribute
    def __init__(self, applet, iid):
        self.applet = applet
        #self.applet.__getattribute__ = getattribute
        #self.applet = MyApplet(applet)
        #self.applet.get_property('popup')
        applet.connect('change_background', self.onChangeBg)
        MainWin.__init__(self, trayMode=1)
        timeout_add_seconds(self.timeout, self.trayUpdate)
        ##self.menu = self.menu_get_for_attach_widget()##????????
        self.connect('unmap', lambda w: self.sicon.set_active(False))##???????
        #self.__getattribute__ = getattribute
    def dialogClose(self, *args):
        self.sicon.set_active(False)
        self.hide()
        return True
    def dialogEsc(self):
        self.sicon.set_active(False)
        self.hide()
        return True
    def trayInit(self):
        self.image = gtk.Image()
        self.tooltips = gtk.Tooltips()
        ## self.sicon = gtk.EventBox()
        self.sicon = gtk.ToggleButton()
        #self.sicon.__getattribute__ = getattribute
        self.sicon.set_from_pixbuf = self.image.set_from_pixbuf
        self.sicon.set_relief(gtk.RELIEF_NONE)
        self.sicon.connect('toggled', self.trayClicked)
        self.sicon.connect('button_press_event', self.appletButtonPress)
        menuData = (
            ('copyTime', _('Copy _Time'), 'copy'),
            ('copyDateToday', _('Copy _Date'), 'copy'),
            ('adjustTime', _('Ad_just System Time'), 'preferences'),
            #('addEvent', _('Add Event'), 'add'),
            ('prefShow', _('_Preferences'), 'preferences'),
            ('exportClickedTray', _('_Export to %s')%'HTML', 'convert'),
            ('aboutShow', _('_About'), 'about'),
        )
        xml = '<popup name="button3">'
        funcList = []
        for funcName, label, icon in menuData:
            xml += '<menuitem name="%s" verb="%s" label="%s" pixtype="stock" pixname="gtk-%s"/>'%(
                funcName,
                funcName,
                label,
                icon,
            )
            funcList.append((funcName, getattr(self, funcName)))
        self.applet.setup_menu(xml, funcList, None)
        ###################################
        #popup = self.applet.get_popup_component()
        #print(type(popup))
        ###################################
        hbox = gtk.HBox()
        hbox.set_direction(gtk.TEXT_DIR_LTR)
        hbox.pack_start(self.image, 0, 0)
        if ui.showDigClockTr:
            #if self.is_composited
            self.clockTr = FClockLabel(preferences.clockFormat)##?????????????
            hbox.pack_start(self.clockTr, 0, 0)
        self.sicon.add(hbox)
        self.applet.add(self.sicon)
        self.trayHbox = hbox
        #######
        self.applet.show_all()
        #self.applet.set_background_widget(self.applet)#????????
        self.trayPix = gdk.Pixbuf(gdk.COLORSPACE_RGB, True, 8, ui.traySize, ui.traySize)
    def trayClicked(self, toggle):
        ##print(tuple(self.menu.allocation))
        if toggle.get_active():
            if (ui.winX, ui.winY) == (-1, -1):
                try:
                    x0, y0 = self.applet.get_window().get_origin()
                    ui.winX = x0 + (self.applet.allocation.width-ui.winWidth)/2
                    ui.winY = y0 + self.applet.allocation.height - 3
                except:
                    core.myRaise(__file__)
            self.move(ui.winX, ui.winY)
            ## every calling of .hide() and .present(), makes dialog not on top (forgets being on top)
            act = self.checkAbove.get_active()
            self.set_keep_above(act)
            if self.checkSticky.get_active():
                self.stick()
            self.deiconify()
            self.present()
        else:
            ui.winX, ui.winY = self.get_position()
            self.hide()
    def appletButtonPress(self, widget, event):
        if event.button != 1:
            widget.stop_emission('button_press_event')
        return False
    def updateTrayClock(self):
        MainWin.updateTrayClock(self, False)
    def trayUpdate(self, gdate=None):
        return MainWin.trayUpdate(self, gdate=gdate, checkTrayMode=False)
    def onChangeBg(self, applet, typ, color, pixmap):
        applet.set_style(None)
        rc_style = gtk.RcStyle()
        applet.modify_style(rc_style)
        if (typ == gnomeapplet.COLOR_BACKGROUND):
            applet.modify_bg(gtk.STATE_NORMAL, color)
        elif (typ == gnomeapplet.PIXMAP_BACKGROUND):
            style = applet.style
            style.bg_pixmap[gtk.STATE_NORMAL] = pixmap
            applet.set_style(style)
    def quit(self, widget=None, event=None):
        ui.saveLiveConf()
        sys.exit(0)
    ## FIXME
    #def restart(self):
    #    self.quit()

def starcalAppletFactory(applet, iid):
    scal = StarCalApplet(applet, iid)
    return True


if len(sys.argv)>1 and sys.argv[1] in ('-w', '--window'):
    main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    main_window.set_title(core.APP_DESC+' Gnome Applet')
    main_window.connect('destroy', gtk.main_quit)
    app = gnomeapplet.Applet()
    starcalAppletFactory(app, None)
    app.reparent(main_window)
    main_window.show_all()
    sys.exit(gtk.main())

if __name__ == '__main__':
    gnomeapplet.bonobo_factory(
        'OAFIID:GNOME_Starcal2Applet_Factory',
         gnomeapplet.Applet.__gtype__,
         core.APP_DESC,
         '0',
         starcalAppletFactory,
     )


