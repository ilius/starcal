#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Saeed Rasooli <saeed.gnu@gmail.com>
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

import os
os.environ['LANG']='en_US.UTF-8' #?????????

from time import localtime
from time import time as now

import sys
from gobject import timeout_add
import gtk


from math import ceil
iceil = lambda f: int(ceil(f))


_ = str ## FIXME

from scal2 import ui
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton, TimeButton


def error_exit(text, parent=None):
    d = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT,\
        gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, text.strip())
    d.set_title('Error')
    d.run()
    sys.exit(1)

class AdjusterDialog(gtk.Dialog):
    xpad = 15
    def __init__(self):
        gtk.Dialog.__init__(self)
        self.set_title(_('Adjust System Date & Time'))##????????
        self.set_icon(self.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_BUTTON))
        #########
        self.buttonCancel = self.add_button(gtk.STOCK_CANCEL, 0)
        #self.buttonCancel.connect('clicked', lambda w: sys.exit(0))
        self.buttonSet = self.add_button(_('Set System Time'), 1)
        #self.buttonSet.connect('clicked', self.setSysTimeClicked)
        #########
        hbox = gtk.HBox()
        self.label_cur = gtk.Label(_('Current:'))
        hbox.pack_start(self.label_cur, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        #########
        hbox = gtk.HBox()
        self.radioMan = gtk.RadioButton(None, _('Set _Manully:'), True)
        self.radioMan.connect('clicked', self.radioManClicked)
        hbox.pack_start(self.radioMan, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        ######
        vb = gtk.VBox()
        sg = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ###
        hbox = gtk.HBox()
        ##
        l = gtk.Label('')
        l.set_property('width-request', self.xpad)
        hbox.pack_start(l, 0, 0)
        ##
        self.ckeckbEditTime = gtk.CheckButton(_('Edit Time'))
        self.editTime = False
        self.ckeckbEditTime.connect('clicked', self.ckeckbEditTimeClicked)
        hbox.pack_start(self.ckeckbEditTime, 0, 0)
        sg.add_widget(self.ckeckbEditTime)
        self.timeInput = TimeButton() ## ??????? options
        hbox.pack_start(self.timeInput, 0, 0)
        vb.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        ##
        l = gtk.Label('')
        l.set_property('width-request', self.xpad)
        hbox.pack_start(l, 0, 0)
        ##
        self.ckeckbEditDate = gtk.CheckButton(_('Edit Date'))
        self.editDate = False
        self.ckeckbEditDate.connect('clicked', self.ckeckbEditDateClicked)
        hbox.pack_start(self.ckeckbEditDate, 0, 0)
        sg.add_widget(self.ckeckbEditDate)
        self.dateInput = DateButton() ## ??????? options
        hbox.pack_start(self.dateInput, 0, 0)
        vb.pack_start(hbox, 0, 0)
        ###
        self.vbox.pack_start(vb, 0, 0, 10)#?????
        self.vboxMan = vb
        ######
        hbox = gtk.HBox()
        self.radioNtp = gtk.RadioButton(self.radioMan, _('Set from _NTP:'), True)
        self.radioNtp.connect('clicked', self.radioNtpClicked)
        hbox.pack_start(self.radioNtp, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        ##
        l = gtk.Label('')
        l.set_property('width-request', self.xpad)
        hbox.pack_start(l, 0, 0)
        ##
        hbox.pack_start(gtk.Label(_('Server:')+' '), 0, 0)
        combo = gtk.combo_box_entry_new_text()
        combo.child.connect('changed', self.updateSetButtonSensitive)
        hbox.pack_start(combo, 1, 1)
        self.ntpServerEntry = combo.child
        for s in ui.ntpServers:
            combo.append_text(s)
        combo.set_active(0)
        self.hboxNtp = hbox
        self.vbox.pack_start(hbox, 0, 0)
        ######
        self.radioManClicked()
        #self.radioNtpClicked()
        self.ckeckbEditTimeClicked()
        self.ckeckbEditDateClicked()
        ######
        self.updateTimes()
        self.vbox.show_all()
    def radioManClicked(self, radio=None):
        if self.radioMan.get_active():
            self.vboxMan.set_sensitive(True)
            self.hboxNtp.set_sensitive(False)
        else:
            self.vboxMan.set_sensitive(False)
            self.hboxNtp.set_sensitive(True)
        self.updateSetButtonSensitive()
    def radioNtpClicked(self, radio=None):
        if self.radioNtp.get_active():
            self.vboxMan.set_sensitive(False)
            self.hboxNtp.set_sensitive(True)
        else:
            self.vboxMan.set_sensitive(True)
            self.hboxNtp.set_sensitive(False)
        self.updateSetButtonSensitive()
    def ckeckbEditTimeClicked(self, checkb=None):
        self.editTime = self.ckeckbEditTime.get_active()
        self.timeInput.set_sensitive(self.editTime)
        self.updateSetButtonSensitive()
    def ckeckbEditDateClicked(self, checkb=None):
        self.editDate = self.ckeckbEditDate.get_active()
        self.dateInput.set_sensitive(self.editDate)
        self.updateSetButtonSensitive()
    """def set_sys_time(self):
        if os.path.isfile('/bin/date'):
            pass##????????
        elif sys.platform == 'win32':
            import win32api
            win32api.SetSystemTime()##????????
        else:
            pass"""
    def updateTimes(self):
        dt = now()%1
        timeout_add(iceil(1000*(1-dt)), self.updateTimes)
        #print('updateTimes', dt)
        lt = localtime()
        self.label_cur.set_label(_('Current:')+' %.4d/%.2d/%.2d - %.2d:%.2d:%.2d'%lt[:6])
        if not self.editTime:
            self.timeInput.set_value(lt[3:6])
        if not self.editDate:
            self.dateInput.set_value(lt[:3])
        return False
    def updateSetButtonSensitive(self, widget=None):
        if self.radioMan.get_active():
            self.buttonSet.set_sensitive(self.editTime or self.editDate)
        elif self.radioNtp.get_active():
            self.buttonSet.set_sensitive(self.ntpServerEntry.get_text()!='')
    def setSysTimeClicked(self, widget=None):
        if self.radioMan.get_active():
            if self.editTime:
                h, m, s = self.timeInput.get_value()
                if self.editDate:
                    Y, M, D = self.dateInput.get_value()
                    cmd = ['/bin/date', '-s', '%.4d/%.2d/%.2d %.2d:%.2d:%.2d'%(Y,M,D,h,m,s)]
                else:
                    cmd = ['/bin/date', '-s', '%.2d:%.2d:%.2d'%(h, m, s)]
            else:
                if self.editDate:
                    Y, M, D = self.dateInput.get_value()
                    ##h, m, s = self.timeInput.get_value()
                    h, m, s = localtime()[3:6]
                    cmd = ['/bin/date', '-s', '%.4d/%.2d/%.2d %.2d:%.2d:%.2d'%(Y,M,D,h,m,s)]
                else:
                    error_exit('No change!', self)#??????????
        elif self.radioNtp.get_active():
            cmd = ['ntpdate', self.ntpServerEntry.get_text()]
            #if os.path.isfile('/usr/sbin/ntpdate'):
            #    cmd = ['/usr/sbin/ntpdate', self.ntpServerEntry.get_text()]
            #else:
            #    error_exit('Could not find command /usr/sbin/ntpdate: no such file!', self)#??????????
        else:
            error_exit('Not valid option!', self)
        inp, out, err = os.popen3(cmd)
        err_text = err.read()
        if err_text=='':
            sys.exit(0)
        else:
            error_exit(err_text, self)#??????????


if __name__=='__main__':
    if os.getuid()!=0:
        error_exit('This program must be run as root')
        #raise OSError('This program must be run as root')
        ###os.setuid(0)#?????????
    d = AdjusterDialog()
    #d.set_keap_above(True)
    if d.run()==1:
        d.setSysTimeClicked()









