#!/usr/bin/env python2
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
from gobject import timeout_add, type_register, signal_new, SIGNAL_RUN_LAST, TYPE_NONE
import gtk
from gtk import gdk




class MultiSpinButton(gtk.SpinButton):
    #from gtk import SpinButton, TEXT_DIR_LTR
    def __init__(self, mins, maxs, fields, sep, nums=None, lang='en', arrow_select=True):##force_select=False
        gtk.SpinButton.__init__(self)
        #self.window_up = None
        #self.window_down = None
        self.set_increments(1, 1)
        self.set_range(-99, 99)
        n = len(mins)
        if len(sep) == n-1:
            sep = sep + ('',)
        elif len(sep)!=n:
            raise ValueError('bad sep list')
        if len(maxs)!=n:
            raise ValueError('bad maxs list')
        if len(fields)!=n:
            raise ValueError('bad fields list')
        self.sep = sep
        self.size = n
        self.mins = mins
        self.maxs = maxs
        self.fields = fields
        self.arrow_select = arrow_select
        #self.force_select = force_select
        self.lang = lang
        self.editable = True
        self.set_direction(gtk.TEXT_DIR_LTR) ## self is a gtk.Entry
        #############################
        self.sep_index = []
        pos = 0
        for i in range(self.size):
            pos += fields[i]
            self.sep_index.append(pos)
            pos += len(sep[i])
        self.set_width_chars(pos)
        self.char_width = pos
        ############################
        #self.connect('activate', lambda obj: self.entry_validate())
        self.connect('activate', self._entry_activate)
        self.connect('key-press-event', self._key_press)
        self.connect('scroll-event', self._scroll)
        self.connect('button-press-event', self._button_press)
        self.connect('button-release-event', self._button_release)
        self.connect('output', lambda obj: True)##Disable auto-numeric-validating(the entry text is not a numebr)
        #if force_select:#??????????
        #    self.connect('move-cursor', self._entry_move_cursor)
        #self.connect('event', show_event)
        #############
    def _entry_activate(self, widget):
        self.entry_validate()
        return True
    def entry_plus(self, plus=1, part=None):
        self.entry_validate()
        pos = self.get_position()
        if part==None:
            part = self.size-1
            for i in range(self.size):
                if pos <= self.sep_index[i]:
                    part = i
                    break
        #print part, self.nums
        new = self.nums[part] + plus
        if new > self.maxs[part]:#or self.maxs[part]==None:
            new = self.mins[part]
            if part==0:
                self.emit('first-max')
            else:
                self.entry_plus(1, part-1)
        elif new < self.mins[part]:
            new = self.maxs[part]
            if part==0:
                self.emit('first-min')
            else:
                self.entry_plus(-1, part-1)
        self.nums[part] = new
        self.set_text(self._ints2str(self.nums))
        self.grab_focus()
        if self.arrow_select:
                if part==0:
                    self.select_region(0, self.sep_index[0])
                else:
                    self.select_region(self.sep_index[part-1]+len(self.sep[part-1]), self.sep_index[part])
        else:
            self.set_position(pos)
        return True
    def entry_validate(self):
        n = self.size
        pos = self.get_position()
        text = self.get_text().decode('utf-8')
        nums = []
        nfound = [] ## not found seperator
        p = 0
        for i in range(n):
            if i==n-1 and self.sep[i]=='':
                if nfound==[]:
                    nums.append(text[p:])
                else:
                    nums.append('')
                break
            p2 = text.find(self.sep[i], p)
            if p2==-1:
                    nums.append('')
                    nfound.append([i, p])
                    continue
            if nfound==[]:
                nums.append(text[p:p2].strip())
            else:
                [j, np] = nfound[0]
                nums[j] = text[p:p2].strip()
                nfound = []    
                nums.append('')
            p = p2 + len(self.sep[i])
        if p2==-1:
            [j, p] = nfound[0]
            nums[j] = text[p:]
        if len(nums)>n:
            nums = nums[:n]
        else:
            while len(nums)<n:
                nums.append('')
        for i in range(n):
            if nums[i]=='':
                num = self.mins[i]
            else:
                try:
                    num = self._str2int(nums[i])
                except ValueError:
                    try:
                        num = int(nums[i])
                    except:
                        num = self.mins[i]
                if num > self.maxs[i]:#or self.maxs[part]==None:
                    num = self.maxs[i]
                #elif num==0:
                #    num = self.mins[i]
            nums[i] = num
        ntext = self._ints2str(nums)
        if ntext!=text:
            self.set_text(ntext)
            self.set_position(pos)
        self.nums = nums
        return ntext
    def get_nums(self):
        self.entry_validate()
        return self.nums
    def set_nums(self, nums=(0,0,0)):
        if len(nums)!=self.size:
            raise ValueError('argument nums has length %s instaed of %s'%(len(nums), self.size))
        pos = self.get_position()
        self.nums = list(nums)
        self.set_text(self._ints2str(nums))
        self.set_position(pos)
    def set_editable(self, editable):
        gtk.SpinButton.set_editable(self, editable)
        self.editable = editable
    def _ints2str(self, ints):
        if self.lang=='fa':
            off = ord(u'۰')
        elif self.lang=='ar':
            off = ord(u'٠')
        else:
            off = ord(u'0')
        text = u''
        for i in range(self.size):
            uni = u''
            try:
                n = ints[i]
            except:
                n = self.mins[i]
            for j in range(self.fields[i]):
                (d, m) = divmod(n, 10)
                uni = unichr(m+off) + uni
                n = d
            text += (uni+self.sep[i])
        return text
    def _str2int(self, st):
        if self.lang=='en':
            return int(st)
        if self.lang=='fa':
                off = ord(u'۰')
        elif self.lang=='ar':
                off = ord(u'٠')
        else:
                raise ValueError('bad lang %s'%self.lang)
        num = 0
        u = st.decode('utf-8')
        for c in u:
                n = ord(c)-off
                if n<0 or n>9:
                    raise ValueError('bad num %s'%st)
                num = num*10 + n
        return num
    def _key_press(self, widget, event):
        key = event.keyval
        if key==65362:    # Up
            if self.editable:
                #self._arrow_enter_notify(self.window_up)
                #timeout_add(30, self._arrow_leave_notify, self.window_up)
                self.entry_plus(1)
            return True
        elif key==65364:    # Down
            if self.editable:
                #self._arrow_enter_notify(self.window_down)
                #timeout_add(30, self._arrow_leave_notify, self.window_down)
                self.entry_plus(-1)
            return True
        elif key==65361:    # Left
            if not self.editable or not self.arrow_select:
                return False
            self.entry_validate()
            pos = self.get_position()
            part = self.size-1
            for i in range(self.size):
                if pos <= self.sep_index[i]:
                    part = i
                    break
            if part>0:
                part -=1
            #self.grab_focus()
            if part==0:
                self.select_region(0, self.sep_index[0])
            else:
                self.select_region(self.sep_index[part-1]+len(self.sep[part-1]), self.sep_index[part])
            return True
        elif key==65363:    #Right
            if not self.editable or not self.arrow_select:
                return False
            self.entry_validate()
            pos = self.get_position()
            part = self.size-1
            for i in range(self.size):
                if pos <= self.sep_index[i]:
                    part = i
                    break
            if part < self.size-1:
                part += 1
            #self.grab_focus()
            self.select_region(self.sep_index[part-1]+len(self.sep[part-1]), self.sep_index[part])
            return True
        #elif key==65293:    #Enter
        #    self.entry_validate()
        #    return True
        #elif key in (65365, 65366): ## PageUp, PageDown
        #    return True
        else:
            #print key
            return False
    def _button_press(self, widget, e):
        #print e.window.get_data('name')
        #r = self.allocation ; print 'allocation', r[0], r[2]
        if e.type==gdk._2BUTTON_PRESS or e.type==gdk._3BUTTON_PRESS:
            return True
        if e.button==1:
            #print 'event window position:', e.window.get_position()
            ## e.window.get_pointer()[0] == e.x
            if e.window.get_position()[0] < 5:## 2 or 3 (depending to theme)
                return False
            else:
                if self.editable:
                    if e.y*2 < self.allocation[3]:
                        self._arrow_press(1)
                        #self.window_up = e.window #??????????
                    else:
                        self._arrow_press(-1)
                        #self.window_down = e.window #?????????
                    #e.window.focus(e.time)#???????????
                    #e.window.clear()
                return True
        else:
            if e.window.get_position()[0] < 5:## 2 or 3 (depending to theme)
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

class DateButton(MultiSpinButton):
    def __init__(self, date=None, **kwargs):
        if date==None:
            date = localtime()[:3]
        MultiSpinButton.__init__(self, mins=(0,1,1), maxs=(9999,12,31), fields=(4,2,2), sep=(u'/', u'/'), nums=date, **kwargs)
        self.get_date = self.get_nums
        self.set_date = self.set_nums

class YearMonthButton(MultiSpinButton):
    def __init__(self, date=None, **kwargs):
        if date==None:
            date = localtime()[:2]
        MultiSpinButton.__init__(self, mins=(0,1), maxs=(9999,12), fields=(4,2), sep=(u'/',), nums=date, **kwargs)
        self.get_date = self.get_nums
        self.set_date = self.set_nums

class TimeButton(MultiSpinButton):
    def __init__(self, hms=None, **kwargs):
        if hms==None:
            hms = localtime()[3:6]
        MultiSpinButton.__init__(self, mins=(0,0,0), maxs=(23,59,59), fields=(2,2,2), sep=(u':', u':'), nums=hms, **kwargs)
        self.get_time = self.get_nums
        self.set_time = self.set_nums
    def get_seconds(self):
        (h, m, s) = self.get_time()
        return h*3600 + m*60 + s
    def set_seconds(self, seconds):
        (day, s) = divmod(seconds, 86400) ## do what with "day" ?????
        (h, s) = divmod(s, 3600)
        (m, s) = divmod(s, 60)
        self.set_time((h, m, s))
        ##return day

class DateTimeButton(MultiSpinButton):
    def __init__(self, date_time=None, **kwargs):
        if date_time==None:
            date_time = localtime()[:6]
        MultiSpinButton.__init__(self, mins=(0,1,1,0,0,0), maxs=(9999,12,31,23,59,59),\
            fields=(4,2,2,2,2,2), sep=(u'/', u'/',u'     ',u':',u':',' seconds'), nums=date_time, **kwargs)
        self.get_date_time = self.get_nums
        self.set_date_time = self.set_nums

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
            self.set_time(localtime()[3:6])



##########################################################################
##########################################################################
class MultiSpinOptionBox(gtk.HBox):
    def _entry_activate(self, widget):
        #self.spin.entry_validate() #?????
        #self.add_history()
        self.emit('activate')
        return False
    def __init__(self, spacing=0, is_hbox=False, hist_size=10, **kwargs):
        if not is_hbox:
            gtk.HBox.__init__(self, spacing=spacing)
        self.spin = MultiSpinButton(**kwargs)
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
        self.get_nums = self.spin.get_nums
        self.set_nums = self.spin.set_nums
    def option_pressed(self, widget, event):
        #(x, y, w, h) = self.option.
        self.menu.popup(None, None, None, event.button, event.time)
    def add_history(self, nums=None):
        if nums==None:
            text = self.spin.entry_validate()
        else:
            self.spin.entry_validate() #??????
            text = self.spin._ints2str(nums)
        n = len(self.menuItems)
        found = -1
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
        item.text = text
        self.menu.add(item)
        self.menu.reorder_child(item, 0)
        if n > self.hist_size:
            self.menu.remove(self.menuItems.pop(n-1))
        self.menu.show_all()
        #self.option.set_sensitive(True) #???????


class DateButtonOption(MultiSpinOptionBox):
    def __init__(self, date=None, **kwargs):
        if date==None:
            date = localtime()[:3]
        MultiSpinOptionBox.__init__(self, mins=(0,1,1), maxs=(9999,12,31), fields=(4,2,2), sep=(u'/', u'/'), nums=date, **kwargs)
        self.get_date = self.get_nums
        self.set_date = self.set_nums
        



class DateHourBox(gtk.HBox):
    def __init__(self):
        def __init__(self):
            gtk.HBox.__init__(self)
            self.dbutton = DateButton()
            ###
            self.hourSpin = gtk.SpinButton()
            self.hourSpin.set_increments(1, 6)
            self.hourSpin.set_range(0, 23)
            self.hourSpin.set_digits(0)
            self.hourSpin.set_direction(gtk.TEXT_DIR_LTR)
            ###
            self.pack_start(self.dbutton, 0, 0)
            self.pack_start(self.hourSpin, 0, 0)
    def set(self, ymdh):
        self.dbutton.set_date(ymdh[:3])
        self.hourSpin.set_value(ymdh[4])
    def get(self):
        (y, m, d) = self.dbutton.get_date()
        h = int(self.hourSpin.get_value())
        return (y, m, d, h)



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



if __name__=='__main__':
    d = gtk.Dialog()
    tbutton = DateButton()
    tbutton.set_date((2011, 1, 1))
    d.vbox.pack_start(tbutton, 1, 1)
    d.connect('delete-event', lambda widget, event: gtk.main_quit())
    d.show_all()
    gtk.main()


