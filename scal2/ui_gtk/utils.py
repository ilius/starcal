# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal2.locale_man import tr as _
from scal2.utils import myRaise
from scal2.json_utils import *
from scal2.path import pixDir, rootDir

from scal2.cal_types import calTypes
from scal2 import core
from scal2 import ui

import os
from os.path import join, isabs
from subprocess import Popen

from time import time as now

from gobject import timeout_add

import gtk
from gtk import gdk


def hideList(widgets):
    for w in widgets:
        w.hide()

def showList(widgets):
    for w in widgets:
        w.show()


def set_tooltip(widget, text):
    try:
        widget.set_tooltip_text(text)## PyGTK 2.12 or above
    except AttributeError:
        try:
            widget.set_tooltip(gtk.Tooltips(), text)
        except:
            myRaise(__file__)

buffer_get_text = lambda b: b.get_text(b.get_start_iter(), b.get_end_iter())

def imageFromFile(path):## the file must exist
    if not isabs(path):
        path = join(pixDir, path)
    im = gtk.Image()
    try:
        im.set_from_file(path)
    except:
        myRaise()
    return im

def pixbufFromFile(path):## the file may not exist
    if not path:
        return None
    if not isabs(path):
        path = join(pixDir, path)
    try:
        return gdk.pixbuf_new_from_file(path)
    except:
        myRaise()
        return None

toolButtonFromStock = lambda stock, size: gtk.ToolButton(gtk.image_new_from_stock(stock, size))

def setupMenuHideOnLeave(menu):
    def menuLeaveNotify(m, e):
        t0 = now()
        if t0-m.lastLeaveNotify < 0.001:
            timeout_add(500, m.hide)
        m.lastLeaveNotify = t0
    menu.lastLeaveNotify = 0
    menu.connect('leave-notify-event', menuLeaveNotify)


def labelStockMenuItem(label, stock=None, func=None, *args):
    item = gtk.ImageMenuItem(_(label))
    if stock:
        item.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU))
    if func:
        item.connect('activate', func, *args)
    return item

def labelImageMenuItem(label, image, func=None, *args):
    item = gtk.ImageMenuItem(_(label))
    item.set_image(imageFromFile(image))
    if func:
        item.connect('activate', func, *args)
    return item

def labelMenuItem(label, func=None, *args):
    item = gtk.MenuItem(_(label))
    if func:
        item.connect('activate', func, *args)
    return item

def modify_bg_all(widget, state, gcolor):
    print(widget.__class__.__name__)
    widget.modify_bg(state, gcolor)
    try:
        children = widget.get_children()
    except AttributeError:
        pass
    else:
        for child in children:
            modify_bg_all(child, state, gcolor)

def combo_model_delete_text(model, path, itr, text_to_del):
    ## Usage: combo.get_model().foreach(combo_model_delete_text, 'The Text')
    if model[path[0]][0]==text_to_del:
        del model[path[0]]
        return

def cellToggled(cell, path=None):
    print('cellToggled', path)
    cell.set_active(not cell.get_active())##????????????????????????
    return True

def comboToggleActivate(combo, *args):
    print(combo.get_property('popup-shown'))
    if not combo.get_property('popup-shown'):
        combo.popup()
        return True
    return False

def getTreeviewPathStr(path):
    if not path:
        return None
    return '/'.join([str(x) for x in path])

rectangleContainsPoint = lambda r, x, y: r.x <= x < r.x + r.width and r.y <= y < r.y + r.height

def dialog_add_button(dialog, stock, label, resId, onClicked=None, tooltip=''):
    b = dialog.add_button(stock, resId)
    if ui.autoLocale:
        if label:
            b.set_label(label)
        b.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_BUTTON))
    if onClicked:
        b.connect('clicked', onClicked)
    if tooltip:
        set_tooltip(b, tooltip)
    return b

def confirm(msg, parent=None):
    win = gtk.MessageDialog(
        parent=parent,
        flags=0,
        type=gtk.MESSAGE_INFO,
        buttons=gtk.BUTTONS_NONE,
        message_format=msg,
    )
    dialog_add_button(win, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
    dialog_add_button(win, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
    ok = win.run() == gtk.RESPONSE_OK
    win.destroy()
    return ok

def showError(msg, parent=None):
    win = gtk.MessageDialog(
        parent=parent,
        flags=0,
        type=gtk.MESSAGE_ERROR,
        buttons=gtk.BUTTONS_NONE,
        message_format=msg,
    )
    dialog_add_button(win, gtk.STOCK_CLOSE, _('_Close'), gtk.RESPONSE_OK)
    win.run()
    win.destroy()


def processDroppedDate(text, dtype):
    ## data_type: "UTF8_STRING", "application/x-color", "text/uri-list",
    if dtype=='UTF8_STRING':
        if text.startswith('file://'):
            path = core.urlToPath(text)
            try:
                t = os.stat(path).st_mtime ## modification time
            except OSError:
                print('Dropped invalid file "%s"'%path)
            else:
                y, m, d = localtime(t)[:3]
                #print 'Dropped file "%s", modification time: %s/%s/%s'%(path, y, m, d)
                return (y, m, d, core.DATE_GREG)
        else:
            date = ui.parseDroppedDate(text)
            if date:
                return date + (ui.dragRecMode,)
            else:
                ## Hot to deny dragged object (to return to it's first location)
                ## FIXME
                print('Dropped unknown text "%s"'%text)
                #print etime
                #context.drag_status(gdk.ACTION_DEFAULT, etime)
                #context.drop_reply(False, etime)
                #context.drag_abort(etime)##Segmentation fault
                #context.drop_finish(False, etime)
                #context.finish(False, True, etime)
                #return True
    elif dtype=='text/uri-list':
        path = core.urlToPath(selection.data)
        try:
            t = os.stat(path).st_mtime ## modification time
        except OSError:
            print('Dropped invalid uri "%s"'%path)
            return True
        else:
            return localtime(t)[:3] + (core.DATE_GREG,)






class AboutDialog(gtk.AboutDialog):
    def __init__(
        self,
        name='',
        version='',
        title='',
        authors=[],
        comments='',
        license='',
        website='',
    ):
        gtk.AboutDialog.__init__(self)
        self.set_name(name)## or set_program_name FIXME
        self.set_version(version)
        self.set_title(title) ## must call after set_name and set_version !
        self.set_authors(authors)
        self.set_comments(comments)
        if license:
            self.set_license(license)
            self.set_wrap_license(True)
        if website:
            self.set_website(website) ## A plain label (not link)
        if ui.autoLocale:
            buttonbox = self.vbox.get_children()[1]
            buttons = buttonbox.get_children()## List of buttons of about dialogs
            buttons[1].set_label(_('C_redits'))
            buttons[2].set_label(_('_Close'))
            buttons[2].set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE,gtk.ICON_SIZE_BUTTON))
            buttons[0].set_label(_('_License'))

class WeekDayComboBox(gtk.ComboBox):
    def __init__(self):
        ls = gtk.ListStore(str)
        gtk.ComboBox.__init__(self, ls)
        self.firstWeekDay = core.firstWeekDay
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        ###
        for i in range(7):
            ls.append([core.weekDayName[(i+self.firstWeekDay)%7]])
        self.set_active(0)
    getValue = lambda self: (self.firstWeekDay + self.get_active()) % 7
    def setValue(self, value):
        self.set_active((value-self.firstWeekDay)%7)


class MonthComboBox(gtk.ComboBox):
    def __init__(self, includeEvery=False):
        self.includeEvery = includeEvery
        ###
        ls = gtk.ListStore(str)
        gtk.ComboBox.__init__(self, ls)
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
    def build(self, mode):
        active = self.get_active()
        ls = self.get_model()
        ls.clear()
        if self.includeEvery:
            ls.append([_('Every Month')])
        for m in range(1, 13):
            ls.append([core.getMonthName(mode, m)])
        if active is not None:
            self.set_active(active)
    def getValue(self):
        a = self.get_active()
        if self.includeEvery:
            return a
        else:
            return a + 1
    def setValue(self, value):
        if self.includeEvery:
            self.set_active(value)
        else:
            self.set_active(value - 1)

class DirectionComboBox(gtk.ComboBox):
    keys = ['ltr', 'rtl', 'auto']
    descs = [
        _('Left to Right'),
        _('Right to Left'),
        _('Auto'),
    ]
    def __init__(self):
        ls = gtk.ListStore(str)
        gtk.ComboBox.__init__(self, ls)
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        ###
        for d in self.descs:
            ls.append([d])
        self.set_active(0)
    getValue = lambda self: self.keys[self.get_active()]
    def setValue(self, value):
        self.set_active(self.keys.index(value))

class DateTypeCombo(gtk.ComboBox):
    def __init__(self):## , showInactive=True FIXME
        ls = gtk.ListStore(int, str)
        gtk.ComboBox.__init__(self, ls)
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)
        ###
        for i, mod in calTypes.iterIndexModule():
            ls.append([i, _(mod.desc)])
    def set_active(self, mode):
        ls = self.get_model()
        for i in range(len(ls)):
            if ls[i][0]==mode:
                gtk.ComboBox.set_active(self, i)
                return
    def get_active(self):
        i = gtk.ComboBox.get_active(self)
        if i is None:
            return
        return self.get_model()[i][0]

class TimeZoneComboBoxEntry(gtk.ComboBoxEntry):
    def __init__(self):
        model = gtk.TreeStore(str, bool)
        gtk.ComboBoxEntry.__init__(self, model, 0)
        self.add_attribute(self.get_cells()[0], 'sensitive', 1)
        self.connect('changed', self.onChanged)
        self.child.set_text(str(core.localTz))
        ###
        self.get_text = self.child.get_text
        self.set_text = self.child.set_text
        #####
        recentIter = model.append(None, [
            _('Recent...'),
            False,
        ])
        for tz_name in ui.localTzHist:
            model.append(recentIter, [tz_name, True])
        ###
        self.appendOrderedDict(
            None,
            jsonToOrderedData(
                open(join(rootDir, 'zoneinfo-tree.json')).read()
            ),
        )
    def appendOrderedDict(self, parentIter, dct):
        model = self.get_model()
        for key, value in dct.items():
            if isinstance(value, dict):
                itr = model.append(parentIter, [key, False])
                self.appendOrderedDict(itr, value)
            else:
                itr = model.append(parentIter, [key, True])
    def onChanged(self, widget):
        model = self.get_model()
        itr = self.get_active_iter()
        if itr is None:
            return
        path = model.get_path(itr)
        parts = []
        if path[0] == 0:
            text = model.get(itr, 0)[0]
        else:
            for i in range(len(path)):
                parts.append(
                    model.get(
                        model.get_iter(path[:i+1]),
                        0,
                    )[0]
                )
            text = '/'.join(parts)
        self.set_text(text)




## Thanks to 'Pier Carteri' <m3tr0@dei.unipd.it> for program Py_Shell.py
class GtkBufferFile:
    ## Implements a file-like object for redirect the stream to the buffer
    def __init__(self, buff, tag):
        self.buffer = buff
        self.tag = tag
    ## Write text into the buffer and apply self.tag
    def write(self, text):
        #text = text.replace('\x00', '')
        self.buffer.insert_with_tags(self.buffer.get_end_iter(), text, self.tag)
    writelines = lambda self, l: list(map(self.write, l))
    flush = lambda self: None
    isatty = lambda self: False


def openWindow(win):
    win.set_keep_above(ui.winKeepAbove)
    win.present()

class CopyLabelMenuItem(gtk.MenuItem):
    def __init__(self, label):
        gtk.MenuItem.__init__(self, label=label, use_underline=False)
        self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        self.connect('activate', self.on_activate)
    def on_activate(self, item):
        self.clipboard.set_text(self.get_property('label'))

class WizardWindow(gtk.Window):
    stepClasses = []
    def __init__(self, title):
        gtk.Window.__init__(self)
        self.set_title(title)
        self.connect('delete-event', lambda obj, e: self.destroy())
        self.connect('key-press-event', self.keyPress)
        self.vbox = gtk.VBox()
        self.add(self.vbox)
        ####
        self.steps = []
        for cls in self.stepClasses:
            step = cls(self)
            self.steps.append(step)
            self.vbox.pack_start(step, 1, 1)
        self.stepIndex = 0
        ####
        self.buttonBox = gtk.HButtonBox()
        self.buttonBox.set_layout(gtk.BUTTONBOX_END)
        self.buttonBox.set_spacing(15)
        self.buttonBox.set_border_width(15)
        self.vbox.pack_start(self.buttonBox, 0, 0)
        ####
        self.showStep(0)
        self.vbox.show()
        #self.vbox.pack_end(
        #print id(self.get_action_area())
    def keyPress(self, arg, event):
        kname = gdk.keyval_name(event.keyval).lower()
        if kname=='escape':
            self.destroy()
        return True
    def showStep(self, stepIndex, *args):
        step = self.steps[stepIndex]
        step.run(*args)
        hideList(self.steps)
        step.show()
        self.stepIndex = stepIndex
        ###
        bbox = self.buttonBox
        for child in bbox.get_children():
            child.destroy()
        for label, func in step.buttons:
            #print label, func
            button = gtk.Button(label)
            button.connect('clicked', func)
            bbox.add(button)
            #bbox.pack_start(button, 0, 0)
        bbox.show_all()

if __name__=='__main__':
    diolog = gtk.Dialog()
    w = TimeZoneComboBoxEntry()
    diolog.vbox.pack_start(w, 0, 0)
    diolog.vbox.show_all()
    diolog.run()



