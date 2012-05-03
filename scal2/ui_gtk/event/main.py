# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License,    or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from time import time
#print time(), __file__ ## FIXME

import os, sys, shlex, thread
from os.path import join, dirname, split, splitext

from scal2.paths import *
from scal2.json_utils import *
from scal2.cal_modules import convert

from scal2 import core
from scal2.core import myRaise, fixStrForFileName

from scal2.locale_man import tr as _
from scal2.locale_man import rtl

from scal2 import event_man
from scal2 import ui

from gobject import timeout_add_seconds
import gtk
from gtk import gdk


from scal2.ui_gtk.utils import imageFromFile, pixbufFromFile, rectangleContainsPoint, showError, \
                               labelStockMenuItem, labelImageMenuItem, confirm, toolButtonFromStock, set_tooltip, \
                               hideList, GtkBufferFile
from scal2.ui_gtk.color_utils import gdkColorToRgb
from scal2.ui_gtk.drawing import newOutlineSquarePixbuf
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton

from scal2.ui_gtk.event.common import IconSelectButton, EventEditorDialog, addNewEvent, GroupEditorDialog



#print 'Testing translator', __file__, _('About')

class SingleGroupExportDialog(gtk.Dialog):
    def __init__(self, group):
        self._group = group
        gtk.Dialog.__init__(self)
        self.set_title(_('Export Group'))
        ####
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        self.connect('response', lambda w, e: self.hide())
        ####
        hbox = gtk.HBox()
        frame = gtk.Frame(_('Format'))
        radioBox = gtk.VBox()
        ##
        self.radioIcs = gtk.RadioButton(label='iCalendar')
        self.radioJsonCompact = gtk.RadioButton(label=_('Compact JSON (StarCalendar)'), group=self.radioIcs)
        self.radioJsonPretty = gtk.RadioButton(label=_('Pretty JSON (StarCalendar)'), group=self.radioIcs)
        ##
        radioBox.pack_start(self.radioJsonCompact, 0, 0)
        radioBox.pack_start(self.radioJsonPretty, 0, 0)
        radioBox.pack_start(self.radioIcs, 0, 0)
        ##
        self.radioJsonCompact.set_active(True)
        self.radioIcs.connect('clicked', self.formatRadioChanged)
        self.radioJsonCompact.connect('clicked', self.formatRadioChanged)
        self.radioJsonPretty.connect('clicked', self.formatRadioChanged)
        ##
        frame.add(radioBox)
        hbox.pack_start(frame, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ########
        self.fcw = gtk.FileChooserWidget(action=gtk.FILE_CHOOSER_ACTION_SAVE)
        try:
            self.fcw.set_current_folder(deskDir)
        except AttributeError:## PyGTK < 2.4
            pass
        self.vbox.pack_start(self.fcw, 1, 1)
        ####
        self.vbox.show_all()
        self.formatRadioChanged()
    def formatRadioChanged(self, widget=None):
        fpath = self.fcw.get_filename()
        if fpath:
            fname_nox, ext = splitext(split(fpath)[1])
        else:
            fname_nox, ext = '', ''
        if not fname_nox:
            fname_nox = fixStrForFileName(self._group.title)
        if self.radioIcs.get_active():
            if ext != '.ics':
                ext = '.ics'
        else:
            if ext != '.json':
                ext = '.json'
        self.fcw.set_current_name(fname_nox + ext)
    def save(self):
        fpath = self.fcw.get_filename()
        if self.radioJsonCompact.get_active():
            text = dataToCompactJson(ui.eventGroups.exportData([self._group.id]))
            open(fpath, 'wb').write(text)
        elif self.radioJsonPretty.get_active():
            text =  dataToPrettyJson(ui.eventGroups.exportData([self._group.id]))
            open(fpath, 'wb').write(text)
        elif self.radioIcs.get_active():
            ui.eventGroups.exportToIcs(fpath, [self._group.id])
    def run(self):
        if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
            self.save()
        self.destroy()


class GroupsTreeCheckList(gtk.TreeView):
    def __init__(self):
        gtk.TreeView.__init__(self)
        self.trees = gtk.ListStore(int, bool, str)## groupId(hidden), enable, summary
        self.set_model(self.trees)
        self.set_headers_visible(False)
        ###
        cell = gtk.CellRendererToggle()
        #cell.set_property('activatable', True)
        cell.connect('toggled', self.enableCellToggled)
        col = gtk.TreeViewColumn(_('Enable'), cell)
        col.add_attribute(cell, 'active', 1)
        #cell.set_active(True)
        col.set_resizable(True)
        self.append_column(col)
        ###
        col = gtk.TreeViewColumn(_('Title'), gtk.CellRendererText(), text=2)
        col.set_resizable(True)
        self.append_column(col)
        ###
        for group in ui.eventGroups:
            self.trees.append([group.id, True, group.title])
    def enableCellToggled(self, cell, path):
        i = int(path)
        active = not cell.get_active()
        self.trees[i][1] = active
        cell.set_active(active)
    def getValue(self):
        return [row[0] for row in self.trees if row[1]]
    def setValue(self, gids):
        for row in self.trees:
            row[1] = (row[0] in gids)


class MultiGroupExportDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self)
        self.set_title(_('Export'))
        self.vbox.set_spacing(10)
        ####
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        self.connect('response', lambda w, e: self.hide())
        ####
        hbox = gtk.HBox()
        frame = gtk.Frame(_('Format'))
        radioBox = gtk.VBox()
        ##
        self.radioIcs = gtk.RadioButton(label='iCalendar')
        self.radioJsonCompact = gtk.RadioButton(label=_('Compact JSON (StarCalendar)'), group=self.radioIcs)
        self.radioJsonPretty = gtk.RadioButton(label=_('Pretty JSON (StarCalendar)'), group=self.radioIcs)
        ##
        radioBox.pack_start(self.radioJsonCompact, 0, 0)
        radioBox.pack_start(self.radioJsonPretty, 0, 0)
        radioBox.pack_start(self.radioIcs, 0, 0)
        ##
        self.radioJsonCompact.set_active(True)
        self.radioIcs.connect('clicked', self.formatRadioChanged)
        self.radioJsonCompact.connect('clicked', self.formatRadioChanged)
        self.radioJsonPretty.connect('clicked', self.formatRadioChanged)
        ##
        frame.add(radioBox)
        hbox.pack_start(frame, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ########
        hbox = gtk.HBox(spacing=2)
        hbox.pack_start(gtk.Label(_('File')+':'), 0, 0)
        self.fpathEntry = gtk.Entry()
        self.fpathEntry.set_text(join(deskDir, 'events-%.4d-%.2d-%.2d'%core.getSysDate()))
        hbox.pack_start(self.fpathEntry, 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        self.groupSelect = GroupsTreeCheckList()
        swin = gtk.ScrolledWindow()
        swin.add(self.groupSelect)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(swin, 1, 1)
        ####
        self.vbox.show_all()
        self.formatRadioChanged()
        self.resize(600, 600)
    def formatRadioChanged(self, widget=None):
        #self.dateRangeBox.set_visible(self.radioIcs.get_active())
        ###
        fpath = self.fpathEntry.get_text()
        if fpath:
            fpath_nox, ext = splitext(fpath)
            if fpath_nox:
                if self.radioIcs.get_active():
                    if ext != '.ics':
                        ext = '.ics'
                else:
                    if ext != '.json':
                        ext = '.json'
                self.fpathEntry.set_text(fpath_nox + ext)
    def save(self):
        fpath = self.fpathEntry.get_text()
        activeGroupIds = self.groupSelect.getValue()
        if self.radioIcs.get_active():
            ui.eventGroups.exportToIcs(fpath, activeGroupIds)
        else:
            data = ui.eventGroups.exportData(activeGroupIds)
            ## what to do with all groupData['info'] s? FIXME
            if self.radioJsonCompact.get_active():
                text = dataToCompactJson(data)
            elif self.radioJsonPretty.get_active():
                text = dataToPrettyJson(data)
            else:
                raise RuntimeError
            open(fpath, 'w').write(text)
    def run(self):
        if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
            self.save()
        self.destroy()


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

class EventsImportWindow(WizardWindow):
    def __init__(self, manager):
        self.manager = manager
        WizardWindow.__init__(self, _('Import Events'))
        self.set_type_hint(gdk.WINDOW_TYPE_HINT_DIALOG)
        #self.set_property('skip-taskbar-hint', True)
        #self.set_modal(True)
        #self.set_transient_for(manager)
        #self.set_destroy_with_parent(True)
        self.resize(400, 200)
    class FirstStep(gtk.VBox):
        def __init__(self, win):
            gtk.VBox.__init__(self, spacing=20)
            self.win = win
            self.buttons = (
                (_('Cancel'), self.cancelClicked),
                (_('Next'), self.nextClicked),
            )
            ####
            hbox = gtk.HBox(spacing=10)
            frame = gtk.Frame(_('Format'))
            #frame.set_border_width(10)
            radioBox = gtk.VBox(spacing=10)
            radioBox.set_border_width(10)
            ##
            self.radioJson = gtk.RadioButton(label=_('JSON (StarCalendar)'))
            #self.radioIcs = gtk.RadioButton(label='iCalendar', group=self.radioJson)
            ##
            radioBox.pack_start(self.radioJson, 0, 0)
            #radioBox.pack_start(self.radioIcs, 0, 0)
            ##
            self.radioJson.set_active(True)
            #self.radioJson.connect('clicked', self.formatRadioChanged)
            ##self.radioIcs.connect('clicked', self.formatRadioChanged)
            ##
            frame.add(radioBox)
            hbox.pack_start(frame, 0, 0, 10)
            hbox.pack_start(gtk.Label(''), 1, 1)
            self.pack_start(hbox, 0, 0)
            ####
            hbox = gtk.HBox()
            hbox.pack_start(gtk.Label(_('File')+':'), 0, 0)
            self.fcb = gtk.FileChooserButton(_('Import: Select File'))
            self.fcb.set_current_folder(deskDir)
            hbox.pack_start(self.fcb, 1, 1)
            self.pack_start(hbox, 0, 0)
            ####
            self.show_all()
        def run(self):
            pass
        def cancelClicked(self, obj):
            self.win.destroy()
        def nextClicked(self, obj):
            fpath = self.fcb.get_filename()
            if not fpath:
                return
            if self.radioJson.get_active():
                format = 'json'
            #elif self.radioIcs.get_active():
            #    format = 'ics'
            else:
                return
            self.win.showStep(1, format, fpath)
    class SecondStep(gtk.VBox):
        def __init__(self, win):
            gtk.VBox.__init__(self, spacing=20)
            self.win = win
            self.buttons = (
                (_('Back'), self.backClicked),
                (_('Close'), self.closeClicked),
            )
            ####
            self.textview = gtk.TextView()
            self.pack_start(self.textview, 1, 1)
            ####
            self.show_all()
        def redirectStdOutErr(self):
            t_table = gtk.TextTagTable()
            tag_out = gtk.TextTag('output')
            t_table.add(tag_out)
            tag_err = gtk.TextTag('error')
            t_table.add(tag_err)
            self.buffer = gtk.TextBuffer(t_table)
            self.textview.set_buffer(self.buffer)
            self.out_fp = GtkBufferFile(self.buffer, tag_out)
            sys.stdout = self.out_fp
            self.err_fp = GtkBufferFile(self.buffer, tag_err)
            sys.stderr = self.err_fp
        def restoreStdOutErr(self):
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        def run(self, format, fpath):
            self.redirectStdOutErr()
            try:
                if format=='json':
                    try:
                        text = open(fpath, 'rb').read()
                    except Exception, e:
                        sys.stderr.write(_('Error in reading file')+'\n%s\n'%e)
                    else:
                        try:
                            data = jsonToData(text)
                        except Exception, e:
                            sys.stderr.write(_('Error in loading JSON data')+'\n%s\n'%e)
                        else:
                            try:
                                newGroups = ui.eventGroups.importData(data)
                            except Exception, e:
                                sys.stderr.write(_('Error in importing events')+'\n%s\n'%e)
                            else:
                                for group in newGroups:
                                    self.win.manager.appendGroupTree(group)
                                print _('%s groups imported successfully')%_(len(newGroups))
                else:
                    raise ValueError('invalid format %r'%format)
            finally:
                self.restoreStdOutErr()
        def backClicked(self, obj):
            self.win.showStep(0)
        def closeClicked(self, obj):
            self.win.destroy()
    stepClasses = [FirstStep, SecondStep]


class GroupSortDialog(gtk.Dialog):
    def __init__(self, group):
        self._group = group
        gtk.Dialog.__init__(self)
        self.set_title(_('Sort Events'))
        ####
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        self.connect('response', lambda w, e: self.hide())
        ####
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Sort events of group "%s"')%group.title), 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Based on')+' '), 0, 0)
        self.sortByNames = []
        self.sortByCombo = gtk.combo_box_new_text()
        for item in group.sortBys:
            self.sortByNames.append(item[0])
            self.sortByCombo.append_text(item[1])
        self.sortByCombo.set_active(self.sortByNames.index(group.sortByDefault))## FIXME
        hbox.pack_start(self.sortByCombo, 0, 0)
        self.reverseCheck = gtk.CheckButton(_('Descending'))
        hbox.pack_start(self.reverseCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        self.vbox.show_all()
    def run(self):
        if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
            self._group.sort(
                self.sortByNames[self.sortByCombo.get_active()],
                self.reverseCheck.get_active(),
            )
            self._group.save()
            return True
        self.destroy()



class GroupConvertModeDialog(gtk.Dialog):
    def __init__(self, group):
        self._group = group
        gtk.Dialog.__init__(self)
        self.set_title(_('Convert Calendar Type'))
        ####
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        self.connect('response', lambda w, e: self.hide())
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('This is going to convert calendar types of all events inside group \"%s\" to a specific type. This operation does not work for Yearly events and also some of Custom events. You have to edit those events manually to change calendar type.')%group.title)
        label.set_line_wrap(True)
        hbox.pack_start(label, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Calendar Type')+':'), 0, 0)
        combo = gtk.combo_box_new_text()
        for module in core.modules:
            combo.append_text(_(module.desc))
        combo.set_active(group.mode)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.modeCombo = combo
        self.vbox.pack_start(hbox, 0, 0)
        ####
        self.vbox.show_all()
    def run(self):
        if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
            mode = self.modeCombo.get_active()
            failedSummaryList = []
            for event in self._group:
                if not event.changeMode(mode):
                    failedSummaryList.append(event.summary)
            if failedSummaryList:## FIXME
                print failedSummaryList
        self.destroy()


class TrashEditorDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self)
        self.set_title(_('Edit Trash'))
        #self.connect('delete-event', lambda obj, e: self.destroy())
        #self.resize(800, 600)
        ###
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        self.connect('response', lambda w, e: self.hide())
        #######
        self.trash = ui.eventTrash
        ##
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        #######
        hbox = gtk.HBox()
        label = gtk.Label(_('Title'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.titleEntry = gtk.Entry()
        hbox.pack_start(self.titleEntry, 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Icon'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.iconSelect = IconSelectButton()
        hbox.pack_start(self.iconSelect, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        self.vbox.show_all()
        self.updateWidget()
    def run(self):
        if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
            self.updateVars()
        self.destroy()
    def updateWidget(self):
        self.titleEntry.set_text(self.trash.title)
        self.iconSelect.set_filename(self.trash.icon)
    def updateVars(self):
        self.trash.title = self.titleEntry.get_text()
        self.trash.icon = self.iconSelect.filename
        self.trash.save()

class AccountEditorDialog(gtk.Dialog):
    def __init__(self, account=None):
        gtk.Dialog.__init__(self)
        self.set_title(_('Edit Account') if account else _('Add New Account'))
        ###
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        self.connect('response', lambda w, e: self.hide())
        #######
        self.account = account
        self.activeWidget = None
        #######
        hbox = gtk.HBox()
        combo = gtk.combo_box_new_text()
        for cls in event_man.classes.account:
            combo.append_text(cls.desc)
        hbox.pack_start(gtk.Label(_('Account Type')), 0, 0)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        if self.account:
            self.isNew = False
            combo.set_active(event_man.classes.account.names.index(self.account.name))
        else:
            self.isNew = True
            defaultAccountTypeIndex = 0
            combo.set_active(defaultAccountTypeIndex)
            self.account = event_man.classes.account[defaultAccountTypeIndex]()
        self.activeWidget = None
        combo.connect('changed', self.typeChanged)
        self.comboType = combo
        self.vbox.show_all()
        self.typeChanged()
    def dateModeChanged(self, combo):
        pass
    def typeChanged(self, combo=None):
        if self.activeWidget:
            self.activeWidget.updateVars()
            self.activeWidget.destroy()
        cls = event_man.classes.account[self.comboType.get_active()]
        account = cls()
        if self.account:
            account.copyFrom(self.account)
            account.setId(self.account.id)
            del self.account
        if self.isNew:
            account.title = cls.desc ## FIXME
        self.account = account
        self.activeWidget = account.makeWidget()
        self.vbox.pack_start(self.activeWidget, 0, 0)
    def run(self):
        if self.activeWidget is None or self.account is None:
            return None
        if gtk.Dialog.run(self) != gtk.RESPONSE_OK:
            return None
        self.activeWidget.updateVars()
        self.account.save()
        if self.isNew:
            event_man.saveLastIds()
        else:
            ui.eventAccounts[self.account.id] = self.account
        self.destroy()
        return self.account


class FetchRemoteGroupsDialog(gtk.Dialog):
    def __init__(self, account):
        gtk.Dialog.__init__(self)
        self.account = account


class EventManagerDialog(gtk.Dialog):## FIXME
    def checkEventToAdd(self, group, event):
        if not group.checkEventToAdd(event):
            showError(_('Group type "%s" can not contain event type "%s"')%(group.desc, event.desc), self)
            raise RuntimeError('Invalid event type for this group')
    def onResponse(self, dialog, response_id):
        self.hide()
        if ui.mainWin:
            ui.mainWin.onConfigChange()
        thread.start_new_thread(event_man.restartDaemon, ())
    def showNewGroup(self, group):
        groupIndex = ui.eventGroups.index(group.id)
        groupIter = self.trees.insert(
            None,
            groupIndex,
            self.getGroupRow(group),
        )
        for event in group:
            self.trees.append(
                groupIter,
                self.getEventRow(event),
            )
    def onConfigChange(self):
        if not self.isLoaded:
            return
        ###
        for gid in ui.newGroups:
            self.showNewGroup(ui.eventGroups[gid])
        ui.newGroups = []
        ###
        for gid in ui.changedGroups:
            groupIndex = ui.eventGroups.index(gid)
            group = ui.eventGroups[gid]
            try:
                groupIter = self.trees.get_iter((groupIndex,))
            except:
                print 'changed group: invalid tree path: (%s,)'%groupIndex
            else:
                for i, value in enumerate(self.getGroupRow(group)):
                    self.trees.set_value(groupIter, i, value)
        ui.changedGroups = []
        ###
        for gid, eid in ui.newEvents:
            groupIndex = ui.eventGroups.index(gid)
            self.trees.append(
                self.trees.get_iter((groupIndex,)),
                self.getEventRow(ui.getEvent(gid, eid)),
            )
        ui.newEvents = []
        ###
        for gid, eid in ui.changedEvents:
            groupIndex = ui.eventGroups.index(gid)
            group = ui.eventGroups[gid]
            eventIndex = group.index(eid)
            try:
                eventIter = self.trees.get_iter((groupIndex, eventIndex))
            except:
                print 'changed event: invalid tree path: (%s, %s)'%(groupIndex, eventIndex)
            else:
                for i, value in enumerate(self.getEventRow(group[eid])):
                    self.trees.set_value(eventIter, i, value)
        ui.changedEvents = []
        ###
        for gid, eid, eventIndex in ui.trashedEvents:
            groupIndex = ui.eventGroups.index(gid)
            try:
                eventIter = self.trees.get_iter((groupIndex, eventIndex))
            except:
                print 'trashed event: invalid tree path: (%s, %s)'%(groupIndex, eventIndex)
            else:
                self.trees.remove(eventIter)
                self.trees.insert(
                    self.trashIter,
                    0,
                    self.getEventRow(ui.eventTrash[eid]),
                )
        ui.trashedEvents = []
        ###
    def onShow(self, widget):
        self.onConfigChange()
    def __init__(self):
        gtk.Dialog.__init__(self)
        self.isLoaded = False
        self.set_title(_('Event Manager'))
        self.resize(600, 300)
        self.connect('delete-event', self.onDeleteEvent)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
        ##
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        #self.connect('response', lambda w, e: self.hide())
        self.connect('response', self.onResponse)
        self.connect('show', self.onShow)
        #######
        menubar = gtk.MenuBar()
        ####
        fileItem = gtk.MenuItem(_('_File'))
        fileMenu = gtk.Menu()
        fileItem.set_submenu(fileMenu)
        menubar.append(fileItem)
        ##
        addGroupItem = gtk.MenuItem(_('Add New Group'))
        addGroupItem.connect('activate', self.addGroupBeforeSelection)## or before selected group? FIXME
        fileMenu.append(addGroupItem)
        ##
        exportItem = gtk.MenuItem(_('_Export'))
        exportItem.connect('activate', self.mbarExportClicked)
        fileMenu.append(exportItem)
        ##
        importItem = gtk.MenuItem(_('_Import'))
        importItem.connect('activate', self.mbarImportClicked)
        fileMenu.append(importItem)
        ##
        orphanItem = gtk.MenuItem(_('Check for Orphan Events'))
        orphanItem.connect('activate', self.mbarOrphanClicked)
        fileMenu.append(orphanItem)
        ####
        editItem = gtk.MenuItem(_('_Edit'))
        editMenu = gtk.Menu()
        editItem.set_submenu(editMenu)
        menubar.append(editItem)
        ##
        editEditItem = gtk.MenuItem(_('Edit'))
        editEditItem.connect('activate', self.mbarEditClicked)
        editMenu.append(editEditItem)
        ##
        editMenu.append(gtk.SeparatorMenuItem())
        ##
        cutItem = gtk.MenuItem(_('Cu_t'))
        cutItem.connect('activate', self.mbarCutClicked)
        editMenu.append(cutItem)
        ##
        copyItem = gtk.MenuItem(_('_Copy'))
        copyItem.connect('activate', self.mbarCopyClicked)
        editMenu.append(copyItem)
        ##
        pasteItem = gtk.MenuItem(_('_Paste'))
        pasteItem.connect('activate', self.mbarPasteClicked)
        editMenu.append(pasteItem)
        self.mbarPasteItem = pasteItem
        ##
        editMenu.append(gtk.SeparatorMenuItem())
        ##
        dupItem = gtk.MenuItem(_('_Duplicate'))
        dupItem.connect('activate', self.duplicateSelectedObj)
        editMenu.append(dupItem)
        ####
        viewItem = gtk.MenuItem(_('_View'))
        viewMenu = gtk.Menu()
        viewItem.set_submenu(viewMenu)
        menubar.append(viewItem)
        ##
        collapseItem = gtk.MenuItem(_('Collapse All'))
        collapseItem.connect('activate', self.collapseAllClicked)
        viewMenu.append(collapseItem)
        ##
        expandItem = gtk.MenuItem(_('Expand All'))
        expandItem.connect('activate', self.expandAllClicked)
        viewMenu.append(expandItem)
        ##
        viewMenu.append(gtk.SeparatorMenuItem())
        ##
        self.showDescItem = gtk.CheckMenuItem(_('Show _Description'))
        self.showDescItem.set_active(ui.eventManShowDescription)
        self.showDescItem.connect('toggled', self.showDescItemToggled)
        viewMenu.append(self.showDescItem)
        ####
        #testItem = gtk.MenuItem(_('Test'))
        #testMenu = gtk.Menu()
        #testItem.set_submenu(testMenu)
        #menubar.append(testItem)
        ###
        #item = gtk.MenuItem('GroupsTreeCheckList')
        #item.connect('activate', testGroupsTreeCheckList)
        #testMenu.append(item)
        ####
        menubar.show_all()
        self.vbox.pack_start(menubar, 0, 0)
        #######
        treeBox = gtk.HBox()
        #####
        self.treev = gtk.TreeView()
        self.treev.set_search_column(2)
        #self.treev.set_headers_visible(False)## FIXME
        #self.treev.get_selection().set_mode(gtk.SELECTION_MULTIPLE)## FIXME
        #self.treev.set_rubber_banding(gtk.SELECTION_MULTIPLE)## FIXME
        self.treev.connect('realize', self.onTreeviewRealize)
        self.treev.connect('cursor-changed', self.treeviewCursorChanged)## FIXME
        self.treev.connect('button-press-event', self.treeviewButtonPress)
        self.treev.connect('row-activated', self.onRowActivated)
        self.treev.connect('key-press-event', self.onKeyPress)
        #####
        swin = gtk.ScrolledWindow()
        swin.add(self.treev)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        treeBox.pack_start(swin, 1, 1)
        ###
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        size = gtk.ICON_SIZE_SMALL_TOOLBAR
        ###
        tb = toolButtonFromStock(gtk.STOCK_GO_UP, size)
        set_tooltip(tb, _('Move up'))
        tb.connect('clicked', self.moveUpByButton)
        toolbar.insert(tb, -1)
        ###
        tb = toolButtonFromStock(gtk.STOCK_GO_DOWN, size)
        set_tooltip(tb, _('Move down'))
        tb.connect('clicked', self.moveDownByButton)
        toolbar.insert(tb, -1)
        ###
        tb = toolButtonFromStock(gtk.STOCK_COPY, size)
        set_tooltip(tb, _('Duplicate'))
        tb.connect('clicked', self.duplicateSelectedObj)
        toolbar.insert(tb, -1)
        ###
        treeBox.pack_start(toolbar, 0, 0)
        #####
        self.vbox.pack_start(treeBox)
        #######
        self.trees = gtk.TreeStore(int, gdk.Pixbuf, str, str)
        ## event: eid,  event_icon,   event_summary, event_description
        ## group: gid,  group_pixbuf, group_title,   ?description
        ## trash: -1,        trash_icon,   _('Trash'),    ''
        self.treev.set_model(self.trees)
        ###
        col = gtk.TreeViewColumn()
        cell = gtk.CellRendererPixbuf()
        col.pack_start(cell)
        col.add_attribute(cell, 'pixbuf', 1)
        self.treev.append_column(col)
        ###
        col = gtk.TreeViewColumn(_('Summary'), gtk.CellRendererText(), text=2)
        col.set_resizable(True)
        self.treev.append_column(col)
        ###
        self.colDesc = gtk.TreeViewColumn(_('Description'), gtk.CellRendererText(), text=3)
        if ui.eventManShowDescription:
            self.treev.append_column(self.colDesc)
        ###
        #self.treev.set_search_column(2)## or 3
        ###
        #self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        #self.clipboard = gtk.clipboard_get()
        self.toPasteEvent = None ## (path, bool move)
        #####
        self.sbar = gtk.Statusbar()
        self.sbar.set_direction(gtk.TEXT_DIR_LTR)
        #self.sbar.set_has_resize_grip(False)
        self.vbox.pack_start(self.sbar, 0, 0)
        #####
        self.syncing = None ## or a tuple of (groupId, statusText)
        #####
        self.vbox.show_all()
        #self.reloadEvents()## FIXME
    def canPasteToGroup(self, group):
        if self.toPasteEvent is None:
            return False
        ## check event type here? FIXME
        return True
    def genRightClickMenu(self, path):
        ## how about multi-selection? FIXME
        ## and Select _All menu item
        obj_list = self.getObjsByPath(path)
        #print len(obj_list)
        menu = gtk.Menu()
        if len(obj_list)==1:
            group = obj_list[0]
            if group.name == 'trash':
                #print 'right click on trash', group.title
                menu.add(labelStockMenuItem('Edit', gtk.STOCK_EDIT, self.editTrash))
                menu.add(labelStockMenuItem('Empty Trash', gtk.STOCK_CLEAR, self.emptyTrash))
                menu.add(gtk.SeparatorMenuItem())
                #menu.add(labelStockMenuItem('Add New Group', gtk.STOCK_NEW, self.addGroupBeforeSelection))## FIXME
            else:
                #print 'right click on group', group.title
                menu.add(labelStockMenuItem('Edit', gtk.STOCK_EDIT, self.editGroupFromMenu, path))
                eventTypes = group.acceptsEventTypes
                if eventTypes is None:
                    eventTypes = event_man.classes.event.names
                for eventType in eventTypes:
                    #if eventType == 'custom':## FIXME
                    #    desc = _('Event')
                    #else:
                    desc = event_man.classes.event.byName[eventType].desc
                    menu.add(labelStockMenuItem(
                        _('Add ') + desc,
                        gtk.STOCK_ADD,
                        self.addEventToGroupFromMenu,
                        path,
                        group,
                        eventType,
                        _('Add') + ' ' + desc,
                    ))
                pasteItem = labelStockMenuItem('Paste Event', gtk.STOCK_PASTE, self.pasteEventFromMenu, path)
                pasteItem.set_sensitive(self.canPasteToGroup(group))
                menu.add(pasteItem)
                ##
                menu.add(gtk.SeparatorMenuItem())
                #menu.add(labelStockMenuItem('Add New Group', gtk.STOCK_NEW, self.addGroupBeforeGroup, path))## FIXME
                menu.add(labelStockMenuItem('Duplicate', gtk.STOCK_COPY, self.duplicateGroupFromMenu, path))
                menu.add(labelStockMenuItem('Duplicate with All Events', gtk.STOCK_COPY, self.duplicateGroupWithEventsFromMenu, path))
                menu.add(gtk.SeparatorMenuItem())
                menu.add(labelStockMenuItem('Delete Group', gtk.STOCK_DELETE, self.deleteGroup, path))
                menu.add(gtk.SeparatorMenuItem())
                ##
                #menu.add(labelStockMenuItem('Move Up', gtk.STOCK_GO_UP, self.moveUpFromMenu, path))
                #menu.add(labelStockMenuItem('Move Down', gtk.STOCK_GO_DOWN, self.moveDownFromMenu, path))
                ##
                menu.add(labelStockMenuItem(_('Export'), gtk.STOCK_CONVERT, self.groupExportFromMenu, group))
                menu.add(labelStockMenuItem(_('Sort Events'), gtk.STOCK_SORT_ASCENDING, self.groupSortFromMenu, path))
                menu.add(labelStockMenuItem(_('Convert Calendar Type'), gtk.STOCK_CONVERT, self.groupConvertModeFromMenu, group))
                #if group.remoteIds:
                #    account = ui.eventAccounts[group.remoteIds[0]]
                #    menu.add(labelImageMenuItem(_('Synchronize with %s')%account.title, gtk.STOCK_REFRESH, self.syncGroup, path))
                ###
                if group.canConvertTo:
                    for newGroupType in group.canConvertTo:
                        menu.add(labelStockMenuItem(
                            _('Convert to %s')%event_man.classes.group.byName[newGroupType].desc,
                            None,
                            self.groupConvertTo,
                            group,
                            newGroupType,
                        ))
                ###
                for (actionName, actionFuncName) in group.actions:
                    menu.add(labelStockMenuItem(_(actionName), None, self.groupActionClicked, group, actionFuncName))
        elif len(obj_list)==2:
            (group, event) = obj_list
            #print 'right click on event', event.summary
            if group.name != 'trash':
                menu.add(labelStockMenuItem('Edit', gtk.STOCK_EDIT, self.editEventFromMenu, path))
                menu.add(gtk.SeparatorMenuItem())
            menu.add(labelStockMenuItem('Cut', gtk.STOCK_CUT, self.cutEvent, path))
            menu.add(labelStockMenuItem('Copy', gtk.STOCK_COPY, self.copyEvent, path))
            ##
            if group.name == 'trash':
                menu.add(gtk.SeparatorMenuItem())
                menu.add(labelStockMenuItem('Delete', gtk.STOCK_DELETE, self.deleteEventFromTrash, path))
            else:
                pasteItem = labelStockMenuItem('Paste', gtk.STOCK_PASTE, self.pasteEventFromMenu, path)
                pasteItem.set_sensitive(self.canPasteToGroup(group))
                menu.add(pasteItem)
                ##
                menu.add(gtk.SeparatorMenuItem())
                #menu.add(labelImageMenuItem(_('Move to Trash'), ui.eventTrash.icon, self.moveEventToTrash, path))
                menu.add(labelImageMenuItem(_('Move to %s')%ui.eventTrash.title, ui.eventTrash.icon, self.moveEventToTrash, path))
        else:
            return
        menu.show_all()
        return menu
    def openRightClickMenu(self, path, etime=None):
        menu = self.genRightClickMenu(path)
        if not menu:
            return
        if etime is None:
            etime = gtk.get_current_event_time()
        menu.popup(None, None, None, 3, etime)
    def onTreeviewRealize(self, event):
        self.reloadEvents()## FIXME
        self.isLoaded = True
    def onRowActivated(self, treev, path, col):
        if len(path)==1:
            if self.treev.row_expanded(path):
                self.treev.collapse_row(path)
            else:
                self.treev.expand_row(path, False)
        elif len(path)==2:
            self.editEventByPath(path)
    def onKeyPress(self, treev, g_event):
        #from scal2.time_utils import getCurrentTime, getGtkTimeFromEpoch
        #print g_event.time-getGtkTimeFromEpoch(time())## FIXME
        #print getCurrentTime()-gdk.CURRENT_TIME/1000.0
        ## gdk.CURRENT_TIME == 0## FIXME
        ## g_event.time == gtk.get_current_event_time() ## OK
        kname = gdk.keyval_name(g_event.keyval).lower()
        if kname=='menu':## Simulate right click (key beside Right-Ctrl)
            path = self.treev.get_cursor()[0]
            if path:
                menu = self.genRightClickMenu(path)
                if not menu:
                    return
                rect = self.treev.get_cell_area(path, self.treev.get_column(1))
                x = rect.x
                if rtl:
                    x -= 100
                else:
                    x += 50
                (dx, dy) = self.treev.translate_coordinates(self, x, rect.y + rect.height)
                (wx, wy) = self.window.get_origin()
                menu.popup(None, None, lambda m: (wx+dx, wy+dy+20, True), 3, g_event.time)
        else:
            return False
        return True
    getRowBgColor = lambda self: gdkColorToRgb(self.treev.style.base[gtk.STATE_NORMAL])## bg color of non-selected rows
    getEventRow = lambda self, event: (
        event.id,
        pixbufFromFile(event.icon),
        event.summary,
        event.getShownDescription(),
    )
    def getGroupRow(self, group, rowBgColor=None):
        if not rowBgColor:
            rowBgColor = self.getRowBgColor()
        return (
            group.id,
            newOutlineSquarePixbuf(
                group.color,
                20,
                0 if group.enable else 15,
                rowBgColor,
            ),
            group.title,
            '',
        )
    def appendGroupTree(self, group):
        groupIter = self.trees.insert_before(None, self.trashIter, self.getGroupRow(group))
        for event in group:
            self.trees.append(groupIter, self.getEventRow(event))
    def reloadEvents(self):
        self.trees.clear()
        self.trashIter = self.trees.append(None, (
            -1,
            pixbufFromFile(ui.eventTrash.icon),
            ui.eventTrash.title,
            '',
        ))
        for group in ui.eventGroups:
            self.appendGroupTree(group)
        for event in ui.eventTrash:
            self.trees.append(self.trashIter, self.getEventRow(event))
        self.treeviewCursorChanged()
    def onDeleteEvent(self, obj, event):
        self.hide()
        return True
    def getObjsByPath(self, path):
        obj_list = []
        for i in range(len(path)):
            it = self.trees.get_iter(path[:i+1])
            obj_id = self.trees.get_value(it, 0)
            if i==0:
                if obj_id==-1:
                    obj_list.append(ui.eventTrash)
                else:
                    obj_list.append(ui.eventGroups[obj_id])
            else:
                obj_list.append(obj_list[i-1][obj_id])
        return obj_list
    def mbarExportClicked(self, obj):
        MultiGroupExportDialog().run()
    def mbarImportClicked(self, obj):
        EventsImportWindow(self).present()
    def mbarOrphanClicked(self, obj):
        self.startWaiting()
        newGroup = ui.eventGroups.checkForOrphans()
        if newGroup is not None:
            self.showNewGroup(newGroup)
        self.endWaiting()
    def mbarEditClicked(self, obj):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        if len(path)==1:
            self.editGroupByPath(path)
        elif len(path)==2:
            self.editEventByPath(path)
    def mbarCutClicked(self, obj):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        if len(path)==2:
            self.toPasteEvent = (path, True)
    def mbarCopyClicked(self, obj):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        if len(path)==2:
            self.toPasteEvent = (path, False)
    def mbarPasteClicked(self, obj):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        self.pasteEventToPath(path)
    collapseAllClicked = lambda self, obj: self.treev.collapse_all()
    expandAllClicked = lambda self, obj: self.treev.expand_all()
    def showDescItemToggled(self, obj):
        active = self.showDescItem.get_active()
        #self.showDescItem.set_active(active)
        ui.eventManShowDescription = active
        ui.saveLiveConf()## FIXME
        if active:
            self.treev.append_column(self.colDesc)
        else:
            self.treev.remove_column(self.colDesc)
    def treeviewCursorChanged(self, treev=None):
        path = self.treev.get_cursor()[0]
        ## update eventInfoBox
        #print 'treeviewCursorChanged', path
        if not self.syncing:
            if path and len(path)==1:
                group = self.getObjsByPath(path)[0]
                message_id = self.sbar.push(0, _('contains %s events and %s occurences')%(
                    _(len(group)),
                    _(group.occurCount),
                ))
            else:
                #self.sbar.remove_all(0)
                message_id = self.sbar.push(0, '')
        return True
    def onGroupModify(self, group):
        self.startWaiting()
        group.afterModify()
        group.save()
        self.endWaiting()
    def treeviewButtonPress(self, treev, g_event):
        pos_t = treev.get_path_at_pos(int(g_event.x), int(g_event.y))
        if not pos_t:
            return
        (path, col, xRel, yRel) = pos_t
        if not path:
            return
        if g_event.button == 3:
            self.openRightClickMenu(path, g_event.time)
        elif g_event.button == 1:
            if not col:
                return
            if not rectangleContainsPoint(treev.get_cell_area(path, col), g_event.x, g_event.y):
                return
            obj_list = self.getObjsByPath(path)
            if len(obj_list) == 1:## group, not event
                group = obj_list[0]
                if group.name != 'trash':
                    cell = col.get_cell_renderers()[0]
                    try:
                        cell.get_property('pixbuf')
                    except:
                        pass
                    else:
                        group.enable = not group.enable
                        self.trees.set_value(
                            self.trees.get_iter(path),
                            1,
                            newOutlineSquarePixbuf(
                                group.color,
                                20,
                                0 if group.enable else 15,
                                self.getRowBgColor(),
                            ),
                        )
                        group.save()
                        self.onGroupModify(group)
                        self.treev.set_cursor(path)
                        return True
    def insertNewGroup(self, groupIndex):
        group = GroupEditorDialog().run()
        if group is None:
            return
        ui.eventGroups.insert(groupIndex, group)
        ui.eventGroups.save()
        beforeGroupIter = self.trees.get_iter((groupIndex,))
        self.trees.insert_before(
            #self.trees.get_iter_root(),## parent
            self.trees.iter_parent(beforeGroupIter),
            beforeGroupIter,## sibling
            self.getGroupRow(group),
        )
        self.onGroupModify(group)
    def addGroupBeforeGroup(self, menu, path):
        self.insertNewGroup(path[0])
    def addGroupBeforeSelection(self, obj=None):
        path = self.treev.get_cursor()[0]
        if path:
            groupIndex = path[0]
        else:
            groupIndex = len(self.trees)-1
        self.insertNewGroup(groupIndex)
    def duplicateGroup(self, path):
        (index,) = path
        (group,) = self.getObjsByPath(path)
        newGroup = group.copy()
        ui.duplicateGroupTitle(newGroup)
        newGroup.save()
        ui.eventGroups.insert(index+1, newGroup)
        ui.eventGroups.save()
        self.trees.insert(
            None,
            index+1,
            self.getGroupRow(newGroup),
        )
    def duplicateGroupWithEvents(self, path):
        (index,) = path
        (group,) = self.getObjsByPath(path)
        newGroup = group.deepCopy()
        ui.duplicateGroupTitle(newGroup)
        newGroup.save()
        ui.eventGroups.insert(index+1, newGroup)
        ui.eventGroups.save()
        newGroupIter = self.trees.insert(
            None,
            index+1,
            self.getGroupRow(newGroup),
        )
        for event in newGroup:
            self.trees.append(newGroupIter, self.getEventRow(event))
    duplicateGroupFromMenu = lambda self, menu, path: self.duplicateGroup(path[0])
    duplicateGroupWithEventsFromMenu = lambda self, menu, path: self.duplicateGroupWithEvents(path)
    def duplicateSelectedObj(self, button=None):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        if len(path)==1:
            self.duplicateGroup(path)
        elif len(path)==2:## FIXME
            self.toPasteEvent = (path, False)
            self.pasteEventToPath(path)
    def editGroupByPath(self, path):
        (group,) = self.getObjsByPath(path)
        group = GroupEditorDialog(group).run()
        if group is None:
            return
        groupIter = self.trees.get_iter(path)
        for i, value in enumerate(self.getGroupRow(group)):
            self.trees.set_value(groupIter, i, value)
        self.onGroupModify(group)
    editGroupFromMenu = lambda self, menu, path: self.editGroupByPath(path)
    def deleteGroup(self, menu, path):
        (index,) = path
        (group,) = self.getObjsByPath(path)
        if not confirm(_('Press OK if you are sure to delete group "%s"')%group.title):
            return
        self.startWaiting()
        trashedIds = group.idList
        if core.eventTrashLastTop:
            for eid in reversed(trashedIds):
                self.trees.insert(
                    self.trashIter,
                    0,
                    self.getEventRow(group[eid]),
                )
        else:
            for eid in trashedIds:
                self.trees.append(
                    self.trashIter,
                    self.getEventRow(group[eid]),
                )
        ui.deleteEventGroup(group)
        self.trees.remove(self.trees.get_iter(path))
        self.endWaiting()
    def addEventToGroupFromMenu(self, menu, path, group, eventType, title):
        event = addNewEvent(group, eventType, title, parent=self)
        if event is None:
            return
        self.trees.append(
            self.trees.get_iter(path),## parent
            self.getEventRow(event), ## row
        )
    def editEventByPath(self, path):
        (group, event) = self.getObjsByPath(path)
        if group.name == 'trash':## FIXME
            return
        event = EventEditorDialog(
            event,
            title=_('Edit ')+event.desc,
            parent=self,
        ).run()
        if event is None:
            return
        eventIter = self.trees.get_iter(path)
        for i, value in enumerate(self.getEventRow(event)):
            self.trees.set_value(eventIter, i, value)
    editEventFromMenu = lambda self, menu, path: self.editEventByPath(path)
    def moveEventToTrash(self, menu, path):
        (group, event) = self.getObjsByPath(path)
        ui.moveEventToTrash(group, event)
        self.trees.remove(self.trees.get_iter(path))
        if core.eventTrashLastTop:
            self.trees.insert(
                self.trashIter,
                0,
                self.getEventRow(event),
            )
        else:
            self.trees.append(
                self.trashIter,
                self.getEventRow(event),
            )
    def deleteEventFromTrash(self, menu, path):
        (trash, event) = self.getObjsByPath(path)
        trash.delete(event.id)## trash == ui.eventTrash
        trash.save()
        self.trees.remove(self.trees.get_iter(path))
    def removeIterChildren(self, _iter):
        while True:
            childIter = self.trees.iter_children(_iter)
            if childIter is None:
                break
            self.trees.remove(childIter)
    def emptyTrash(self, menu):
        ui.eventTrash.empty()
        self.removeIterChildren(self.trashIter)
    def editTrash(self, menu):
        TrashEditorDialog().run()
        self.trees.set_value(
            self.trashIter,
            1,
            pixbufFromFile(ui.eventTrash.icon),
        )
        self.trees.set_value(
            self.trashIter,
            2,
            ui.eventTrash.title,
        )
    def moveUp(self, path):
        srcIter = self.trees.get_iter(path)
        if len(path)==1:
            if path[0]==0:
                return
            if self.trees.get_value(srcIter, 0)==-1:
                return
            tarIter = self.trees.get_iter((path[0]-1))
            self.trees.move_before(srcIter, tarIter)
            ui.eventGroups.moveUp(path[0])
            ui.eventGroups.save()
        elif len(path)==2:
            (parentObj, event) = self.getObjsByPath(path)
            parentLen = len(parentObj)
            (parentIndex, eventIndex) = path
            #print eventIndex, parentLen
            if eventIndex > 0:
                tarIter = self.trees.get_iter((parentIndex, eventIndex-1))
                self.trees.move_before(srcIter, tarIter)## or use self.trees.swap FIXME
                parentObj.moveUp(eventIndex)
                parentObj.save()
            else:
                ## move event to end of previous group
                #if parentObj.name == 'trash':
                #    return
                if parentIndex < 1:
                    return
                newParentIter = self.trees.get_iter((parentIndex - 1))
                newParentId = self.trees.get_value(newParentIter, 0)
                if newParentId==-1:## could not be!
                    return
                newGroup = ui.eventGroups[newParentId]
                self.checkEventToAdd(newGroup, event)
                self.trees.remove(srcIter)
                srcIter = self.trees.append(
                    newParentIter,## parent
                    self.getEventRow(event), ## row
                )
                ###
                parentObj.remove(event)
                parentObj.save()
                newGroup.append(event)
                newGroup.save()
        else:
            raise RuntimeError('invalid tree path %s'%path)
        newPath = self.trees.get_path(srcIter)
        if len(path)==2:
            self.treev.expand_to_path(newPath)
        self.treev.set_cursor(newPath)
        self.treev.scroll_to_cell(newPath)
    def moveDown(self, path):
        srcIter = self.trees.get_iter(path)
        if len(path)==1:
            if self.trees.get_value(srcIter, 0)==-1:
                return
            tarIter = self.trees.get_iter((path[0]+1))
            if self.trees.get_value(tarIter, 0)==-1:
                return
            self.trees.move_after(srcIter, tarIter)## or use self.trees.swap FIXME
            ui.eventGroups.moveDown(path[0])
            ui.eventGroups.save()
        elif len(path)==2:
            (parentObj, event) = self.getObjsByPath(path)
            parentLen = len(parentObj)
            (parentIndex, eventIndex) = path
            #print eventIndex, parentLen
            if eventIndex < parentLen-1:
                tarIter = self.trees.get_iter((parentIndex, eventIndex+1))
                self.trees.move_after(srcIter, tarIter)
                parentObj.moveDown(eventIndex)
                parentObj.save()
            else:
                ## move event to top of next group
                if parentObj.name == 'trash':
                    return
                newParentIter = self.trees.get_iter((parentIndex + 1))
                newParentId = self.trees.get_value(newParentIter, 0)
                if newParentId==-1:
                    return
                newGroup = ui.eventGroups[newParentId]
                self.checkEventToAdd(newGroup, event)
                self.trees.remove(srcIter)
                srcIter = self.trees.insert(
                    newParentIter,## parent
                    0,## position
                    self.getEventRow(event), ## row
                )
                ###
                parentObj.remove(event)
                parentObj.save()
                newGroup.insert(0, event)
                newGroup.save()
        else:
            raise RuntimeError('invalid tree path %s'%path)
        newPath = self.trees.get_path(srcIter)
        if len(path)==2:
            self.treev.expand_to_path(newPath)
        self.treev.set_cursor(newPath)
        self.treev.scroll_to_cell(newPath)
    moveUpFromMenu = lambda self, menu, path: self.moveUp(path)
    moveDownFromMenu = lambda self, menu, path: self.moveDown(path)
    def moveUpByButton(self, button):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        self.moveUp(path)
    def moveDownByButton(self, button):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        self.moveDown(path)
    def groupExportFromMenu(self, menu, group):
        SingleGroupExportDialog(group).run()
    def groupSortFromMenu(self, menu, path):
        (index,) = path
        (group,) = self.getObjsByPath(path)
        if GroupSortDialog(group).run():
            groupIter = self.trees.get_iter(path)
            expanded = self.treev.row_expanded(path)
            self.removeIterChildren(groupIter)
            for event in group:
                self.trees.append(groupIter, self.getEventRow(event))
            if expanded:
                self.treev.expand_row(path, False)
    def groupConvertModeFromMenu(self, menu, group):
        GroupConvertModeDialog(group).run()
    def startWaiting(self):
        self.vbox.set_sensitive(False)
        self.window.set_cursor(gdk.Cursor(gdk.WATCH))
        while gtk.events_pending():
            gtk.main_iteration_do(False)
    def endWaiting(self):
        self.window.set_cursor(gdk.Cursor(gdk.LEFT_PTR))
        self.vbox.set_sensitive(True)
    def groupConvertTo(self, menu, group, newGroupType):
        self.startWaiting()
        newGroup = ui.eventGroups.convertGroupTo(group, newGroupType)
        self.endWaiting()
    def groupActionClicked(self, menu, group, actionFuncName):
        getattr(group, actionFuncName)(parentWin=self)
    def cutEvent(self, menu, path):
        self.toPasteEvent = (path, True)
    def copyEvent(self, menu, path):
        self.toPasteEvent = (path, False)
    pasteEventFromMenu = lambda self, menu, tarPath: self.pasteEventToPath(tarPath)
    def pasteEventToPath(self, tarPath):
        if not self.toPasteEvent:
            return
        (srcPath, move) = self.toPasteEvent
        (srcGroup, srcEvent) = self.getObjsByPath(srcPath)
        tarGroup = self.getObjsByPath(tarPath)[0]
        self.checkEventToAdd(tarGroup, srcEvent)
        if len(tarPath)==1:
            tarGroupIter = self.trees.get_iter(tarPath)
            tarEventIter = None
            tarEventIndex = len(tarGroup)
        elif len(tarPath)==2:
            tarGroupIter = self.trees.get_iter(tarPath[:1])
            tarEventIter = self.trees.get_iter(tarPath)
            tarEventIndex = tarPath[1]
        ####
        if move:
            srcGroup.remove(srcEvent)
            srcGroup.save()
            tarGroup.insert(tarEventIndex, srcEvent)
            tarGroup.save()
            self.trees.remove(self.trees.get_iter(srcPath))
            newEvent = srcEvent
        else:
            newEvent = srcEvent.copy()
            newEvent.save()
            tarGroup.insert(tarEventIndex, newEvent)
            tarGroup.save()
        ####
        if tarEventIter:
            newEventIter = self.trees.insert_after(
                tarGroupIter,## parent
                tarEventIter,## sibling
                self.getEventRow(newEvent), ## row
            )
        else:
            newEventIter = self.trees.append(
                tarGroupIter,## parent
                self.getEventRow(newEvent), ## row
            )
        self.treev.set_cursor(self.trees.get_path(newEventIter))
        self.toPasteEvent = None
    #def selectAllEventInGroup(self, menu):## FIXME
    #    pass
    #def selectAllEventInTrash(self, menu):## FIXME
    #    pass





def makeWidget(obj):## obj is an instance of Event, EventRule, EventNotifier or EventGroup
    if hasattr(obj, 'WidgetClass'):
        widget = obj.WidgetClass(obj)
        try:
            widget.show_all()
        except AttributeError:
            widget.show()
        widget.updateWidget()## FIXME
        return widget
    else:
        return None


##############################################################################

if rtl:
    gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)


modPrefix = 'scal2.ui_gtk.event.'

for cls in event_man.classes.event:
    try:
        module = __import__(modPrefix + cls.name, fromlist=['EventWidget'])
        cls.WidgetClass = module.EventWidget
    except:
        myRaise()

for cls in event_man.classes.rule:
    try:
        module = __import__(modPrefix + 'rules.' + cls.name, fromlist=['RuleWidget'])
    except:
        #if not cls.name.startswith('ex_'):
        myRaise()
        continue
    try:
        cls.WidgetClass = module.RuleWidget
    except AttributeError:
        print 'no class RuleWidget defined in module "%s"'%cls.name

for cls in event_man.classes.notifier:
    try:
        module = __import__(modPrefix + 'notifiers.' + cls.name, fromlist=['NotifierWidget', 'notify'])
        cls.WidgetClass = module.NotifierWidget
        cls.notify = module.notify
    except:
        myRaise()

for cls in event_man.classes.group:
    try:
        module = __import__(modPrefix + 'groups.' + cls.name, fromlist=['GroupWidget'])
    except:
        myRaise()
        continue
    try:
        cls.WidgetClass = module.GroupWidget
    except AttributeError:
        print 'no class GroupWidget defined in module "%s"'%cls.name

    for actionDesc, actionName in cls.actions:
        try:
            func = getattr(module, actionName)
        except AttributeError:
            print 'no function %s defined in module "%s"'%(actionName, cls.name)
        else:
            setattr(cls, actionName, func)


for cls in event_man.classes.account:
    try:
        module = __import__(modPrefix + 'accounts.' + cls.name, fromlist=['AccountWidget'])
    except:
        myRaise()
        continue
    try:
        cls.WidgetClass = module.AccountWidget
    except AttributeError:
        print 'no class AccountWidget defined in module "%s"'%cls.name


event_man.EventRule.makeWidget = makeWidget
event_man.EventNotifier.makeWidget = makeWidget
event_man.Event.makeWidget = makeWidget
event_man.EventGroup.makeWidget = makeWidget
event_man.Account.makeWidget = makeWidget


### Load accounts, groups and trash? FIXME





import scal2.ui_gtk.event.import_customday ## opens a dialog if neccessery


##############################################################################

def testCustomEventEditor():
    from pprint import pprint, pformat
    dialog = gtk.Dialog()
    #dialog.vbox.pack_start(IconSelectButton(ui.logo))
    event = event_man.Event(1)
    event.load()
    widget = event.makeWidget()
    dialog.vbox.pack_start(widget)
    dialog.vbox.show_all()
    dialog.add_button('OK', 0)
    if dialog.run()==0:
        widget.updateVars()
        #widget.event.afterModify()
        widget.event.save()
        pprint(widget.event.getData())


def testGroupsTreeCheckList(obj=None):
    dialog = gtk.Dialog()
    treev = GroupsTreeCheckList()
    swin = gtk.ScrolledWindow()
    swin.add(treev)
    swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    dialog.vbox.pack_start(swin, 1, 1)
    dialog.vbox.show_all()
    dialog.resize(500, 500)
    treev.setValue([8, 7, 1, 3])
    dialog.run()
    print treev.getValue()


if __name__=='__main__':
    #testCustomEventEditor()
    testGroupsTreeCheckList()


