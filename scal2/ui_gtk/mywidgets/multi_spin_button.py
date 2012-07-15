# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

import sys, os
from time import time, localtime

from scal2.utils import toUnicode, toStr, strFindNth, iceil, ifloor

from scal2 import locale_man
from scal2.locale_man import tr as _

from scal2.cal_modules import to_jd, jd_to, convert

from scal2.mywidgets.multi_spin import *

from gobject import timeout_add, type_register, signal_new, SIGNAL_RUN_LAST, TYPE_NONE
import gtk
from gtk import gdk


class MultiSpinButton(gtk.SpinButton):
    def __init__(self, sep, fields, arrow_select=True, page_step=10):
        gtk.SpinButton.__init__(self)
        ####
        self.field = ContainerField(sep, *fields)
        self.arrow_select = arrow_select
        self.page_step = page_step
        self.editable = True
        ###
        self.digs = locale_man.getDigits()
        ###
        ####
        self.set_direction(gtk.TEXT_DIR_LTR) ## self is a gtk.Entry
        self.set_width_chars(self.field.getMaxWidth())
        self.set_value(0)
        self.set_digits(0)
        self.set_range(-2, 2)
        self.set_increments(1, page_step)
        #self.connect('activate', lambda obj: self.entry_validate())
        self.connect('activate', self._entry_activate)
        self.connect('key-press-event', self._key_press)
        self.connect('scroll-event', self._scroll)
        self.connect('button-press-event', self._button_press)
        self.connect('button-release-event', self._button_release)
        self.connect('output', lambda obj: True)##Disable auto-numeric-validating(the entry text is not a numebr)
        ####
        #self.select_region(0, 0)
    def _entry_activate(self, widget):
        #print '_entry_activate', self.get_text()
        self.entry_validate()
        #print self.get_text()
        return True
    def get_value(self):
        self.field.setText(self.get_text())
        return self.field.getValue()
    def set_value(self, value):
        pos = self.get_position()
        self.field.setValue(value)
        self.set_text(self.field.getText())
        self.set_position(pos)
    def entry_validate(self):
        pos = self.get_position()
        self.field.setText(toUnicode(self.get_text()))
        self.set_text(self.field.getText())
        self.set_position(pos)
    def set_editable(self, editable):
        gtk.SpinButton.set_editable(self, editable)
        self.editable = editable
    def insertText(self, s, clearSeceltion=True):
        selection = self.get_selection_bounds()
        if selection and clearSeceltion:
            (start, end) = selection
            text = toUnicode(self.get_text())
            text = text[:start] + s + text[end:]
            self.set_text(text)
            self.set_position(start+len(s))
        else:
            pos = self.get_position()
            self.insert_text(s, pos)
            self.set_position(pos + len(s))
    def entry_plus(self, p):
        self.entry_validate()
        pos = self.get_position()
        self.field.getFieldAt(toUnicode(self.get_text()), self.get_position()).plus(p)
        self.set_text(self.field.getText())
        self.set_position(pos)
    def _key_press(self, widget, gevent):
        kval = gevent.keyval
        kname = gdk.keyval_name(kval).lower()
        size = len(self.field)
        sep = self.field.sep
        if kname in ('up', 'down', 'page_up', 'page_down', 'left', 'right'):
            if not self.editable:
                return True
            if kname in ('left', 'right'):
                return False
                #if not self.arrow_select:
                #    return False
                #shift = {
                #    'left': -1,
                #    'right': 1
                #}[kname]
                #FIXME
            else:
                p = {
                    'up': 1,
                    'down': -1,
                    'page_up': self.page_step,
                    'page_down': -self.page_step,
                }[kname]
                self.entry_plus(p)
            #if fieldIndex==0:
            #    i1 = 0
            #else:
            #    i1 = strFindNth(text, sep, fieldIndex) + len(sep)
            #i2 = strFindNth(text, sep, fieldIndex+1)
            ##self.grab_focus()
            #self.select_region(i1, i2)
            return True
        #elif kname=='return':## Enter
        #    self.entry_validate()
        #    ##self.emit('activate')
        #    return True
        elif ord('0') <= kval <= ord('9'):
            self.insertText(self.digs[kval-ord('0')])
            return True
        elif 'kp_0' <= kname <= 'kp_9':
            self.insertText(self.digs[int(kname[-1])])
            return True
        elif kname in ('period', 'kp_decimal', 'slash', 'kp_divide'):
            self.insertText(_('.'))
            return True
        else:
            print kname, kval
            return False
    def _button_press(self, widget, gevent):
        gwin = gevent.window
        #print gwin.get_data('name')
        #r = self.allocation ; print 'allocation', r[0], r[2]
        if gevent.type==gdk._2BUTTON_PRESS or gevent.type==gdk._3BUTTON_PRESS:
            return True
        if gevent.button==1:
            #print 'event window position:', gwin.get_position()
            ## gwin.get_pointer()[0] == gevent.x
            if gwin.get_position()[0] < 5:## 2 or 3 (depending to theme)
                return False
            else:
                if self.editable:
                    if gevent.y*2 < self.allocation[3]:
                        self._arrow_press(1)
                        #self.window_up = gwin #??????????
                    else:
                        self._arrow_press(-1)
                        #self.window_down = gwin #?????????
                    #gwin.focus(gevent.time)#???????????
                    #gwin.clear()
                return True
        else:
            if gwin.get_position()[0] < 5:## 2 or 3 (depending to theme)
                return False
            else:
                return True
    def _scroll(self, widget, event):
        if not self.editable:
            return True
        d = event.direction.value_nick
        if d=='up':
            self.entry_plus(1)
            return True
        elif d=='down':
            self.entry_plus(-1)
            return True
        else:
            return False
    #def _move_cursor(self, obj, step, count, extend_selection):
        ## force_select
        #print'_entry_move_cursor', count, extend_selection
    def _arrow_press(self, plus):
        self._remain = True
        timeout_add(150, self._arrow_remain, plus)
        self.entry_plus(plus)
    def _arrow_remain(self, plus):
        if self.editable and self._remain:
            self.entry_plus(plus)
            timeout_add(50, self._arrow_remain, plus)
    def _button_release(self, widget, event):
        self._remain = False
    """## ????????????????????????????????
    def _arrow_enter_notify(self, gtkWin):
        if gtkWin!=None:
            print '_arrow_enter_notify'
            gtkWin.set_background(gdk.Color(-1, 0, 0))
            gtkWin.show()
    def _arrow_leave_notify(self, gtkWin):
        if gtkWin!=None:
            print '_arrow_leave_notify'
            gtkWin.set_background(gdk.Color(-1, -1, -1))
    #"""

class SingleSpinButton(MultiSpinButton):
    def __init__(self, field, **kwargs):
        MultiSpinButton.__init__(
            self,
            ' ',
            (field,),
            **kwargs
        )
    get_value = lambda self: MultiSpinButton.get_value(self)[0]


class IntSpinButton(SingleSpinButton):
    def __init__(self, _min, _max, **kwargs):
        SingleSpinButton.__init__(
            self,
            IntField(_min, _max),
            **kwargs
        )


class YearSpinButton(SingleSpinButton):
    def __init__(self, **kwargs):
        SingleSpinButton.__init__(
            self,
            YearField(),
            **kwargs
        )

class DaySpinButton(SingleSpinButton):
    def __init__(self, **kwargs):
        SingleSpinButton.__init__(
            self,
            DayField(pad=0),
            **kwargs
        )

class FloatSpinButton(MultiSpinButton):
    def __init__(self, _min, _max, digNum, **kwargs):
        if digNum < 1:
            raise ValueError('FloatSpinButton: invalid digNum=%r'%digNum)
        self.digNum = digNum
        self.digDec = 10**digNum
        self._min = _min
        self._max = _max
        MultiSpinButton.__init__(
            self,
            locale_man.getNumSep(),
            (
                IntField(int(_min), int(_max)),
                IntField(0, self.digDec-1, digNum),
            ),
            **kwargs
        )
    def get_value(self):
        return float(locale_man.textNumDecode(self.get_text()))
    def set_value(self, value):
        if value < self._min:
            value = self._min
        elif value > self._max:
            value = self._max
        s1, s2 = ('%.*f'%(self.digNum, value)).split('.')
        v1 = int(s1)
        v2 = int(s2[:self.digNum])
        #print value, v1, v2
        MultiSpinButton.set_value(self, (v1, v2))
    def entry_plus(self, p):
        MultiSpinButton.entry_plus(self, p)
        self.set_value(self.get_value())

class DateButton(MultiSpinButton):
    def __init__(self, date=None, **kwargs):
        MultiSpinButton.__init__(
            self,
            u'/',
            (
                YearField(),
                MonthField(),
                DayField(),
            ),
            **kwargs
        )
        if date==None:
            date = localtime()[:3]
        self.set_value(date)
    def get_jd(self, mode):
        y, m, d = self.get_value()
        return to_jd(y, m, d, mode)
    changeMode = lambda self, fromMode, toMode: self.set_value(jd_to(self.get_jd(fromMode), toMode))
    def setMaxDay(self, _max):
        self.field.children[2].setMax(_max)
        self.entry_validate()

class YearMonthButton(MultiSpinButton):
    def __init__(self, date=None, **kwargs):
        MultiSpinButton.__init__(
            self,
            u'/',
            (
                YearField(),
                MonthField(),
            ),
            **kwargs
        )
        if date==None:
            date = localtime()[:2]
        self.set_value(date)

class TimeButton(MultiSpinButton):
    def __init__(self, hms=None, **kwargs):
        MultiSpinButton.__init__(
            self,
            u':',
            (
                HourField(),
                Z60Field(),
                Z60Field(),
            ),
            **kwargs
        )
        if hms==None:
            hms = localtime()[3:6]
        self.set_value(hms)
    def get_seconds(self):
        (h, m, s) = self.get_value()
        return h*3600 + m*60 + s
    def set_seconds(self, seconds):
        (day, s) = divmod(seconds, 86400) ## do what with "day" ?????
        (h, s) = divmod(s, 3600)
        (m, s) = divmod(s, 60)
        self.set_value((h, m, s))
        ##return day

class HourMinuteButton(MultiSpinButton):
    def __init__(self, hm=None, **kwargs):
        MultiSpinButton.__init__(
            self,
            u':',
            (
                HourField(),
                Z60Field(),
            ),
            **kwargs
        )
        if hm==None:
            hm = localtime()[3:5]
        self.set_value(hm)
    get_value = lambda self: MultiSpinButton.get_value(self) + [0]
    def set_value(self, value):
        if isinstance(value, int):
            value = [value, 0]
        else:
            value = value[:2]
        MultiSpinButton.set_value(self, value)

class DateTimeButton(MultiSpinButton):
    def __init__(self, date_time=None, **kwargs):
        MultiSpinButton.__init__(
            self,
            u' ',
            (
                ContainerField(
                    u'/',
                    YearField(),
                    MonthField(),
                    DayField(),
                ),
                ContainerField(
                    u':',
                    HourField(),
                    Z60Field(),
                    Z60Field(),
                ),
            ),
            #StrConField('seconds'),
            **kwargs
        )
        if date_time==None:
            date_time = localtime()[:6]
        self.set_value(date_time)



class TimerButton(TimeButton):
    def __init__(self, **kwargs):
        TimeButton.__init__(self, **kwargs)
        #self.timer = False
        #self.clock = False
        self.delay = 1.0 # timer delay
        self.tPlus = -1 # timer plus (step)
        self.elapse = 0
    def timer_start(self):
        self.clock = False
        self.timer = True
        #self.delay = 1.0 # timer delay
        #self.tPlus = -1 # timer plus (step)
        #self.elapse = 0
        #########
        self.tOff = time()*self.tPlus - self.get_seconds()
        self.set_editable(False)
        self.timer_update()
    def timer_stop(self):
        self.timer = False
        self.set_editable(True)
    def timer_update(self):
        if not self.timer:
            return
        sec = int(time()*self.tPlus - self.tOff)
        self.set_seconds(sec)
        if self.tPlus*(sec-self.elapse) >= 0:
            self.emit('time-elapse')
            self.timer_stop()
        else:
            timeout_add(int(self.delay*1000), self.timer_update)
    def clock_start(self):
        self.timer = False
        self.clock = True
        self.set_editable(False)
        self.clock_update()
    def clock_stop(self):
        self.clock = False
        self.set_editable(True)
    def clock_update(self):
        if self.clock:
            timeout_add(time_rem(), self.clock_update)
            self.set_value(localtime()[3:6])



##########################################################################
##########################################################################
class MultiSpinOptionBox(gtk.HBox):
    def _entry_activate(self, widget):
        #self.spin.entry_validate() #?????
        #self.add_history()
        self.emit('activate')
        return False
    def __init__(self, sep, fields, spacing=0, is_hbox=False, hist_size=10, **kwargs):
        if not is_hbox:
            gtk.HBox.__init__(self, spacing=spacing)
        self.spin = MultiSpinButton(sep, fields, **kwargs)
        self.pack_start(self.spin, 1, 1)
        self.hist_size = hist_size
        self.option = gtk.Button()
        self.option.add(gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_IN))
        self.pack_start(self.option, 1, 1)
        self.menu = gtk.Menu()
        #self.menu.show()
        self.option.connect('button-press-event', self.option_pressed)
        self.menuItems = []
        #self.option.set_sensitive(False) #???????
        #self.spin._entry_activate = self._entry_activate
        self.spin.connect('activate', self._entry_activate)
        self.get_value = self.spin.get_value
        self.set_value = self.spin.set_value
    def option_pressed(self, widget, event):
        #(x, y, w, h) = self.option.
        self.menu.popup(None, None, None, event.button, event.time)
    def add_history(self):
        self.spin.entry_validate()
        text = self.spin.get_text()
        found = -1
        n = len(self.menuItems)
        for i in range(n):
            if self.menuItems[i].text==text:
                found = i
                break
        if found>-1:
            self.menu.remove(self.menuItems.pop(found))
        else:
            n += 1
        #m.prepend([text])#self.combo.prepend_text(text)
        item = gtk.MenuItem(text)
        item.connect('activate', lambda obj: self.spin.set_text(text))
        item.text = text
        self.menu.add(item)
        self.menu.reorder_child(item, 0)
        if n > self.hist_size:
            self.menu.remove(self.menuItems.pop(n-1))
        self.menu.show_all()
        #self.option.set_sensitive(True) #???????
    def clear_history(self):
        for item in self.menu.get_children():
            self.menu.remove(item)

class DateButtonOption(MultiSpinOptionBox):
    def __init__(self, date=None, **kwargs):
        MultiSpinOptionBox.__init__(
            self,
            u'/',
            (
                YearField(),
                MonthField(),
                DayField(),
            ),
            **kwargs
        )
        if date==None:
            date = localtime()[:3]
        self.set_value(date)
    def setMaxDay(self, _max):
        self.spin.field.children[2].setMax(_max)
        self.spin.entry_validate()


class HourMinuteButtonOption(MultiSpinOptionBox):
    def __init__(self, hm=None, **kwargs):
        MultiSpinOptionBox.__init__(
            self,
            u':',
            (
                HourField(),
                Z60Field(),
            ),
            **kwargs
        )
        if hm==None:
            hm = localtime()[3:5]
        self.set_value(hm)
    get_value = lambda self: MultiSpinOptionBox.get_value(self) + [0]
    def set_value(self, value):
        if isinstance(value, int):
            value = [value, 0]
        else:
            value = value[:2]
        MultiSpinOptionBox.set_value(self, value)


#####################################################################################
#####################################################################################

type_register(MultiSpinButton)
#type_register(DateButton)
#type_register(YearMonthButton)
type_register(TimeButton)
type_register(TimerButton)
type_register(MultiSpinOptionBox)
###############
signal_new('first-max', MultiSpinButton, SIGNAL_RUN_LAST, TYPE_NONE, [])
signal_new('first-min', MultiSpinButton, SIGNAL_RUN_LAST, TYPE_NONE, [])
signal_new('time-elapse', TimerButton, SIGNAL_RUN_LAST, TYPE_NONE, [])
signal_new('activate', MultiSpinOptionBox, SIGNAL_RUN_LAST, TYPE_NONE, [])

def getDateTimeWidget():
    btn = DateTimeButton()
    btn.set_value((2011, 1, 1))
    return btn

def getIntWidget():
    btn = IntSpinButton(0, 99)
    btn.set_value(12)
    return btn

def getFloatWidget():
    btn = FloatSpinButton(-3.3, 5.5, 1)
    btn.set_value(3.67)
    return btn

def getFloatBuiltinWidget():
    btn = gtk.SpinButton()
    btn.set_range(0, 90)
    btn.set_digits(2)
    btn.set_increments(0.01, 1)
    return btn


if __name__=='__main__':
    d = gtk.Dialog()
    btn = getFloatWidget()
    d.vbox.pack_start(btn, 1, 1)
    d.vbox.show_all()
    d.run()
    print btn.get_value()

