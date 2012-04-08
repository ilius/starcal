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

import sys, os, time
from gobject import timeout_add, type_register, signal_new, SIGNAL_RUN_LAST, TYPE_NONE
import gtk
from gtk import gdk

from scal2.locale_man import numEncode, numDecode

def myRaise():
    i = sys.exc_info()
    try:
        print('line %s: %s: %s'%(i[2].tb_lineno, i[0].__name__, i[1]))
    except:
        print i

def show_event(widget, event):
    print type(widget), event.type.value_name#, event.send_event

time_rem = lambda: int(1000*(1.01-time.time()%1))

class MultiSpinBox(gtk.HBox):
    #from gtk import HBox, EventBox, Arrow, gdk.Color, combo_box_entry_new_text, TEXT_DIR_LTR, ARROW_UP, ARROW_DOWN, SHADOW_IN
    def __init__(self, mins, maxs, fields, sep, is_hbox=False, arrow=True, nums=None, spacing=0,\
        hist_size=10, arrow_select=True):##force_select=False
        if not is_hbox:
            gtk.HBox.__init__(self, False, spacing)
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
        self.hist_size = hist_size
        self.arrow_select = arrow_select
        #self.force_select = force_select
        self.arrowNotifyColor = gdk.Color(-1, -1, -1)## bad for a dark theme#??????????????????
        #self.style.base[gtk.STATE_SELECTED]
        #self.style.bg[gtk.STATE_SELECTED]
        '''
        colors = []
        names = []
        for atr in dir(self.style):
            for s in ('NORMAL', 'ACTIVE', 'PRELIGHT', 'SELECTED', 'INSENSITIVE'):
                try:
                    name = 'self.style.%s[gtk.STATE_%s]'%(atr, s)
                    c = eval(name)
                except:
                    pass
                else:
                    if type(c)==gdk.Color:
                        colors.append(c)
                        names.append(name)
        print 'len(colors)=',len(colors)
        self.colors = colors
        self.colorNames = names
        self.colorI = 0
        '''
        self.editable = True
        self.combo = gtk.combo_box_entry_new_text()
        self.entry = self.combo.child
        if nums!=None:
            text = self._ints2str(nums)
            self.combo.append_text(text)
            self.entry.set_text(text)
        self.entry.set_direction(gtk.TEXT_DIR_LTR) ## self.entry is a gtk.Entry
        #self.combo.set_direction(gtk.TEXT_DIR_LTR)
        #############################
        self.sep_index = []
        pos = 0
        for i in range(self.size):
            pos += fields[i]
            self.sep_index.append(pos)
            pos += len(sep[i])
        self.entry.set_width_chars(pos)
        self.char_width = pos
        ############################
        #self.entry.connect('activate', lambda wid: self.add_history())
        self.entry.connect('activate', self._entry_activate)
        self.entry.connect('key-press-event', self._entry_key_press)
        self.entry.connect('scroll-event', self._entry_scroll)
        #if force_select:#??????????
        #    self.entry.connect('move-cursor', self._entry_move_cursor)
        #self.entry.connect('event', show_event)
        #############
        self.combo.connect('notify::popup-shown', self._popup_shown)
        if arrow:
            self.arrowBox = gtk.VBox(spacing=0)
            #h = self.entry.allocation[3]
            #print h
            #####
            self.eventU=gtk.EventBox()
            #self.eventU.set_property('ypad', 1)
            arrow = gtk.Arrow(gtk.ARROW_UP, gtk.SHADOW_IN)
            arrow.set_size_request(12, 12)
            arrow.set_alignment(0.5, 0.8)
            self.eventU.add(arrow)
            self.arrowBox.pack_start(gtk.HBox(), 1, 1)
            self.arrowBox.pack_start(self.eventU, 0, 0)
            #####
            self.eventD=gtk.EventBox()
            #self.eventD.set_property('ypad', 0)
            arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_IN)
            arrow.set_size_request(12, 12)
            arrow.set_alignment(0.5, 0.3)
            self.eventD.add(arrow)
            self.arrowBox.pack_start(self.eventD, 0, 0)
            self.arrowBox.pack_start(gtk.HBox(), 1, 1)
            #####
            self._remain = False ## mouse remains down
            self.eventU.connect('button-press-event', self._arrow_press, 1)
            self.eventD.connect('button-press-event', self._arrow_press, -1)
            self.eventU.connect('button-release-event', self._arrow_release)
            self.eventD.connect('button-release-event', self._arrow_release)
            self.eventU.connect('enter-notify-event', self._arrow_enter_notify)
            self.eventD.connect('enter-notify-event', self._arrow_enter_notify)
            self.eventU.connect('leave-notify-event', self._arrow_leave_notify)
            self.eventD.connect('leave-notify-event', self._arrow_leave_notify)
            #####
            self.pack_start(self.arrowBox, 0, 0)
        self.pack_start(self.combo, 1, 1)
    def entry_plus(self, plus=1, part=None):
        self.entry_validate()
        pos = self.entry.get_position()
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
        self.entry.set_text(self._ints2str(self.nums))
        self.entry.grab_focus()
        if self.arrow_select:
                if part==0:
                    self.entry.select_region(0, self.sep_index[0])
                else:
                    self.entry.select_region(self.sep_index[part-1]+len(self.sep[part-1]), self.sep_index[part])
        else:
            self.entry.set_position(pos)
        return True
    def entry_validate(self):
        n = self.size
        pos = self.entry.get_position()
        text = self.entry.get_text().decode('utf-8')
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
                    num = numDecode(nums[i])
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
            self.entry.set_text(ntext)
            self.entry.set_position(pos)
        self.nums = nums
        return ntext
    def get_nums(self):
        self.entry_validate()
        return self.nums
    def set_nums(self, nums=(0,0,0)):
        if len(nums)!=self.size:
            raise ValueError('argument nums has length %s instaed of %s'%(len(nums), self.size))
        pos = self.entry.get_position()
        self.nums = list(nums)
        self.entry.set_text(self._ints2str(nums))
        self.entry.set_position(pos)
    def set_editable(self, editable):
        self.entry.set_editable(editable)
        self.editable = editable
    def _ints2str(self, ints):
        text = u''
        for i in range(self.size):
            try:
                n = int(ints[i])
            except:
                n = self.mins[i]
            text += numEncode(n, fillZero=self.fields[i]) + self.sep[i]
        return text
    def _entry_activate(self, widget):
        self.add_history()
        self.emit('activate')
    clear_history = lambda self: self.combo.get_model().clear()
    def add_history(self, nums=None):
        if nums==None:
            text = self.entry_validate()
        else:
            text = self._ints2str(nums)
        m = self.combo.get_model()
        n = len(m)
        found = -1
        for i in range(n):
            if m[i][0]==text:
                found = i
                break
        if found>-1:
            m.remove(m.get_iter(found))
        else:
            n += 1
        m.prepend([text])#self.combo.prepend_text(text)
        if    n > self.hist_size:
            m.remove(m.get_iter(n-1))
    def _entry_key_press(self, widget, event):
        kname = gdk.keyval_name(event.keyval).lower()
        if kname=='up':
            if self.editable:
                self._arrow_enter_notify(self.eventU)
                timeout_add(30, self._arrow_leave_notify, self.eventU)
                self.entry_plus(1)
            return True
        elif kname=='down':
            if self.editable:
                self._arrow_enter_notify(self.eventD)
                timeout_add(30, self._arrow_leave_notify, self.eventD)
                self.entry_plus(-1)
            return True
        elif kname=='left':
            if not self.editable or not self.arrow_select:
                return False
            self.entry_validate()
            pos = self.entry.get_position()
            part = self.size-1
            for i in range(self.size):
                if pos <= self.sep_index[i]:
                    part = i
                    break
            if part>0:
                part -=1
            #self.entry.grab_focus()
            if part==0:
                self.entry.select_region(0, self.sep_index[0])
            else:
                self.entry.select_region(self.sep_index[part-1]+len(self.sep[part-1]), self.sep_index[part])
            return True
        elif kname=='right':
            if not self.editable or not self.arrow_select:
                return False
            self.entry_validate()
            pos = self.entry.get_position()
            part = self.size-1
            for i in range(self.size):
                if pos <= self.sep_index[i]:
                    part = i
                    break
            if part < self.size-1:
                part += 1
            #self.entry.grab_focus()
            self.entry.select_region(self.sep_index[part-1]+len(self.sep[part-1]), self.sep_index[part])
            return True
        else:
            return False
    def _entry_scroll(self, widget, event):
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
    #def _entry_move_cursor(self, obj, step, count, extend_selection):
        ## force_select
        #print'_entry_move_cursor', count, extend_selection
    def _popup_shown(self, widget, event=None):
        self.entry_validate()
    def _arrow_press(self, widget, event, plus):
        if not self.editable:
            return False
        self._remain = True
        timeout_add(150, self._arrow_remain, plus)
        self.entry_plus(plus)
    def _arrow_remain(self, plus):
        if self.editable and self._remain:
            self.entry_plus(plus)
            timeout_add(50, self._arrow_remain, plus)
    def _arrow_release(self, widget, event):
        self._remain = False
    def _arrow_enter_notify(self, evbox, event=None):
        #evbox.grab_focus()
        #evbox.set_focus_chain((evbox,))
        evbox.modify_bg(0, self.arrowNotifyColor)
        #evbox.drag_highlight()
        #evbox.modify_bg(0, self.colors[self.colorI])
        #print self.colorNames[self.colorI]
        #self.colorI += 1
    def _arrow_leave_notify(self, evbox, event=None):
        evbox.modify_bg(0, None)
        #evbox.drag_unhighlight()


class DateBox(MultiSpinBox):
    def __init__(self, date=None, **kwargs):
        if date==None:
            date = time.localtime()[:3]
        MultiSpinBox.__init__(self, mins=(0,1,1), maxs=(9999,12,31), fields=(4,2,2), sep=(u'/', u'/'), nums=date, **kwargs)
        self.get_date = self.get_nums
        self.set_date = self.set_nums

class YearMonthBox(MultiSpinBox):
    def __init__(self, date=None, **kwargs):
        if date==None:
            date = time.localtime()[:2]
        MultiSpinBox.__init__(self, mins=(0,1), maxs=(9999,12), fields=(4,2), sep=(u'/',), nums=date, **kwargs)
        self.get_date = self.get_nums
        self.set_date = self.set_nums

class TimeBox(MultiSpinBox):
    def __init__(self, hms=None, **kwargs):
        if hms==None:
            hms = time.localtime()[3:6]
        MultiSpinBox.__init__(self, mins=(0,0,0), maxs=(23,59,59), fields=(2,2,2), sep=(u':', u':'), nums=hms, **kwargs)
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

class HourMinuteBox(MultiSpinBox):
    def __init__(self, hms=None, **kwargs):
        if hms==None:
            hms = time.localtime()[3:5]
        MultiSpinBox.__init__(self, mins=(0,0), maxs=(23,59), fields=(2,2), sep=(u':',), nums=hms, **kwargs)
        self.get_hm = self.get_nums
        self.set_hm = self.set_nums
    get_time = lambda self: self.get_hm() + [0]
    set_time = lambda self, tm: self.set_hm(tm[:2])

class DateTimeBox(MultiSpinBox):
    def __init__(self, date_time=None, **kwargs):
        if date_time==None:
            date_time = time.localtime()[:6]
        MultiSpinBox.__init__(self, mins=(0,1,1,0,0,0), maxs=(9999,12,31,23,59,59),\
            fields=(4,2,2,2,2,2), sep=(u'/', u'/',u'     ',u':',u':',' seconds'), nums=date_time, **kwargs)
        self.get_date_time = self.get_nums
        self.set_date_time = self.set_nums

class TimerBox(TimeBox):
    def __init__(self, **kwargs):
        TimeBox.__init__(self, **kwargs)
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
        self.tOff = time.time()*self.tPlus - self.get_seconds()
        self.set_editable(False)
        self.timer_update()
    def timer_stop(self):
        self.timer = False
        self.set_editable(True)
    def timer_update(self):
        if not self.timer:
            return
        sec = int(time.time()*self.tPlus - self.tOff)
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
            self.set_time(time.localtime()[3:6])



class DayTimeBox(MultiSpinBox):
    #from gtk import SpinButton, Label, Button, image_new_from_stock, STOCK_MEDIA_PLAY, STOCK_MEDIA_STOP, ICON_SIZE_BUTTON
    def __init__(self, day=0, hms=(0,0,0), hasTimerButton=True, spacing=3, label='days and', **kwargs):
        gtk.HBox.__init__(self, False, spacing)
        self.spin = gtk.SpinButton()
        self.spin.set_increments(1, 10)
        self.spin.set_range(0, 999)
        self.pack_start(self.spin, 0, 0)
        ######
        self.label = gtk.Label(label)
        self.pack_start(self.label, 0, 0)
        ######
        MultiSpinBox.__init__(self, is_hbox=True, mins=(0,0,0), maxs=(23,59,59), fields=(2,2,2), sep=(u':',u':'), nums=hms, **kwargs)
        ######
        self.get_time = self.get_nums
        self.set_time = self.set_nums
        #self.get_day = self.spin.get_value
        self.get_day = lambda: int(self.spin.get_value())
        self.set_day = self.spin.set_value
        self.timer = False
        self.delay = 1.0 # timer delay
        self.tPlus = -1 # timer plus (step)
        self.elapse = 0
        ######
        self.connect('first-max', self._first_max)
        self.connect('first-min', self._first_min)
        ######
        self.hasTimerButton = hasTimerButton
        if hasTimerButton:
            self.timerBut = gtk.Button()
            self.timerBut.connect('clicked', self._timer_button_clicked)
            self.pack_start(self.timerBut, 0, 0)
            ####
            self.timerBut.set_label('Start')
            self.timerBut.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON))
    def get_seconds(self):
        (h, m, s) = self.get_time()
        #day = self.spin.get_value()
        day = self.get_day()
        return (day*86400 + h*3600 + m*60 + s)
    def set_seconds(self, seconds):
        (day, s) = divmod(seconds, 86400)
        (h, s) = divmod(s, 3600)
        (m, s) = divmod(s, 60)
        self.set_time((h, m, s))
        #self.spin.set_value(day)
        self.set_day(day)
    def get_day_time(self):
        #d = int(self.spin.get_value())
        d = self.get_day()
        (h, m, s) = self.get_time()
        return (d, h, m, s)
    def set_day_time(self, (d, h, m, s)):
        self.set_day(d)
        self.set_time((h, m, s))
    def timer_start(self):
        self.timer = True
        self.tOff = time.time()*self.tPlus - self.get_seconds()
        self.set_editable(False)
        self.timer_update()
        ##############
        self.spin.set_increments(0, 0)
        self.spin.set_editable(False)
        if self.hasTimerButton:
            self.timerBut.set_label('Stop')
            self.timerBut.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_BUTTON))
            self.timerBut.show_all()
    def timer_stop(self):
        self.timer = False
        self.set_editable(True)
        self.spin.set_editable(True)
        self.spin.set_increments(1, 10)
        if self.hasTimerButton:
            self.timerBut.set_label('Start')
            self.timerBut.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY,gtk.ICON_SIZE_BUTTON))
    def timer_update(self):
        if not self.timer:
            return False
        sec = int(time.time()*self.tPlus - self.tOff)
        self.set_seconds(sec)
        if self.tPlus*(sec-self.elapse) >= 0:
            self.emit('time-elapse')
            self.timer_stop()
        else:
            timeout_add(int(self.delay*1000), self.timer_update)
        return False
    def _timer_button_clicked(self, but):
        if self.timer:
            self.timer_stop()
        else:
            self.timer_start()
    def _first_max(self, widget):
        if not self.timer:
            #self.spin.set_value(self.spin.get_value()+1)
            self.set_day(self.get_day()+1)
    def _first_min(self, widget):
        if not self.timer:
            #self.spin.set_value(self.spin.get_value()-1)
            self.set_day(self.get_day()-1)




#####################################################################################
#####################################################################################



type_register(MultiSpinBox)
#type_register(DateBox)
#type_register(YearMonthBox)
type_register(TimeBox)
type_register(TimerBox)
type_register(DayTimeBox)
###############
signal_new('first-max', MultiSpinBox, SIGNAL_RUN_LAST, TYPE_NONE, [])
signal_new('first-min', MultiSpinBox, SIGNAL_RUN_LAST, TYPE_NONE, [])
signal_new('activate', MultiSpinBox, SIGNAL_RUN_LAST, TYPE_NONE, [])
signal_new('time-elapse', TimerBox, SIGNAL_RUN_LAST, TYPE_NONE, [])
signal_new('time-elapse', DayTimeBox, SIGNAL_RUN_LAST, TYPE_NONE, [])

