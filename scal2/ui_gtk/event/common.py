# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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


import os, shutil
from os.path import join, split

from scal2.utils import toStr
from scal2.time_utils import durationUnitsAbs, durationUnitValues
from scal2 import core
from scal2.locale_man import tr as _

from scal2.core import pixDir, myRaise

from scal2 import event_lib
from scal2 import ui

from scal2.ui_gtk.utils import toolButtonFromStock, set_tooltip, labelStockMenuItem
from scal2.ui_gtk.utils import dialog_add_button, DateTypeCombo

from scal2.ui_gtk.color_utils import gdkColorToRgb
from scal2.ui_gtk.drawing import newOutlineSquarePixbuf

import gtk
from gtk import gdk

from scal2.ui_gtk.mywidgets import TextFrame
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton, FloatSpinButton

#print 'Testing translator', __file__, _('_About')## OK


getGroupRow = lambda group, rowBgColor: (
    group.id,
    newOutlineSquarePixbuf(
        group.color,
        20,
        0 if group.enable else 15,
        rowBgColor,
    ),
    group.title
)

class IconSelectButton(gtk.Button):
    def __init__(self, filename=''):
        gtk.Button.__init__(self)
        self.image = gtk.Image()
        self.add(self.image)
        self.dialog = gtk.FileChooserDialog(
            title=_('Select Icon File'),
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
        )
        okB = self.dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        cancelB = self.dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        clearB = self.dialog.add_button(gtk.STOCK_CLEAR, gtk.RESPONSE_REJECT)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
            clearB.set_label(_('Clear'))
            clearB.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR,gtk.ICON_SIZE_BUTTON))
        ###
        menu = gtk.Menu()
        self.menu = menu
        menu.add(labelStockMenuItem(_('None'), None, self.menuItemActivate, ''))
        for item in ui.eventTags:
            icon = item.icon
            if icon:
                menuItem = gtk.ImageMenuItem(item.desc)
                menuItem.set_image(gtk.image_new_from_file(icon))
                menuItem.connect('activate', self.menuItemActivate, icon)
                menu.add(menuItem)
        menu.show_all()
        ###
        self.dialog.connect('file-activated', self.fileActivated)
        self.dialog.connect('response', self.dialogResponse)
        #self.connect('clicked', lambda button: button.dialog.run())
        self.connect('button-press-event', self.buttonPressEvent)
        ###
        self.set_filename(filename)
    def buttonPressEvent(self, widget, event):
        b = event.button
        if b==1:
            self.dialog.run()
        elif b==3:
            self.menu.popup(None, None, None, b, event.time)
    menuItemActivate = lambda self, widget, icon: self.set_filename(icon)
    def dialogResponse(self, dialog, response=0):
        if response == gtk.RESPONSE_OK:
            self.set_filename(dialog.get_filename())
        elif response == gtk.RESPONSE_REJECT:
            self.set_filename('')
        dialog.hide()
    def fileActivated(self, dialog):
        self.filename = dialog.get_filename()
        self.image.set_from_file(self.filename)
        self.dialog.hide()
    get_filename = lambda self: self.filename
    def set_filename(self, filename):
        self.dialog.set_filename(filename)
        self.filename = filename
        if not filename:
            self.image.set_from_file(join(pixDir, 'empty.png'))
        else:
            self.image.set_from_file(filename)

class EventWidget(gtk.VBox):
    def __init__(self, event):
        gtk.VBox.__init__(self)
        self.event = event
        ###########
        hbox = gtk.HBox()
        ###
        hbox.pack_start(gtk.Label(_('Calendar Type')+':'), 0, 0)
        combo = DateTypeCombo()
        combo.set_active(core.primaryMode)## overwritten in updateWidget()
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.modeCombo = combo
        ###
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Summary')), 0, 0)
        self.summaryEntry = gtk.Entry()
        hbox.pack_start(self.summaryEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Description')), 0, 0)
        self.descriptionInput = TextFrame()
        hbox.pack_start(self.descriptionInput, 1, 1)
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Icon')+':'), 0, 0)
        self.iconSelect = IconSelectButton()
        #print join(pixDir, self.icon)
        hbox.pack_start(self.iconSelect, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.pack_start(hbox, 0, 0)
        ##########
        self.modeCombo.connect('changed', self.modeComboChanged)## right place? before updateWidget? FIXME
    def focusSummary(self):
        self.summaryEntry.select_region(0, -1)
        self.summaryEntry.grab_focus()
    def updateWidget(self):
        #print 'updateWidget', self.event.files
        self.modeCombo.set_active(self.event.mode)
        self.summaryEntry.set_text(self.event.summary)
        self.descriptionInput.set_text(self.event.description)
        self.iconSelect.set_filename(self.event.icon)
        #####
        for attr in ('notificationBox', 'filesBox'):
            try:
                getattr(self, attr).updateWidget()
            except AttributeError:
                pass
        #####
        self.modeComboChanged()
    def updateVars(self):
        self.event.mode = self.modeCombo.get_active()
        self.event.summary = self.summaryEntry.get_text()
        self.event.description = self.descriptionInput.get_text()
        self.event.icon = self.iconSelect.get_filename()
        #####
        for attr in ('notificationBox', 'filesBox'):
            try:
                getattr(self, attr).updateVars()
            except AttributeError:
                pass
        #####
    def modeComboChanged(self, obj=None):## FIXME
        pass


class FilesBox(gtk.VBox):
    def __init__(self, event):
        gtk.VBox.__init__(self)
        self.event = event
        self.vbox = gtk.VBox()
        self.pack_start(self.vbox, 0, 0)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(''), 1, 1)
        addButton = gtk.Button()
        addButton.set_label(_('_Add File'))
        addButton.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        addButton.connect('clicked', self.addClicked)
        hbox.pack_start(addButton, 0, 0)
        self.pack_start(hbox, 0, 0)
        self.show_all()
        self.newFiles = []
    def showFile(self, fname):
        hbox = gtk.HBox()
        hbox.pack_start(gtk.LinkButton(
            self.event.getUrlForFile(fname),
            _('File') + ': ' + fname,
        ), 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        delButton = gtk.Button()
        delButton.set_label(_('_Delete'))
        delButton.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_BUTTON))
        delButton.fname = fname
        delButton.hbox = hbox
        delButton.connect('clicked', self.delClicked)
        hbox.pack_start(delButton, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        hbox.show_all()
    def addClicked(self, button):
        fcd = gtk.FileChooserDialog(
            buttons=(
                toStr(_('_OK')), gtk.RESPONSE_OK,
                toStr(_('_Cancel')), gtk.RESPONSE_CANCEL,
            ),
            title=_('Add File'),
        )
        fcd.connect('response', lambda w, e: fcd.hide())
        if fcd.run() == gtk.RESPONSE_OK:
            fpath = fcd.get_filename()
            fname = split(fpath)[-1]
            dstDir = self.event.filesDir
            ## os.makedirs(dstDir, exist_ok=True)## only on new pythons FIXME
            try:
                os.makedirs(dstDir)
            except:
                myRaise()
            shutil.copy(fpath, join(dstDir, fname))
            self.event.files.append(fname)
            self.newFiles.append(fname)
            self.showFile(fname)
    def delClicked(self, button):
        os.remove(join(self.event.filesDir, button.fname))
        try:
            self.event.files.remove(button.fname)
        except:
            pass
        button.hbox.destroy()
    def removeNewFiles(self):
        for fname in self.newFiles:
            os.remove(join(self.event.filesDir, fname))
        self.newFiles = []
    def updateWidget(self):
        for hbox in self.vbox.get_children():
            hbox.destroy()
        for fname in self.event.files:
            self.showFile(fname)
    def updateVars(self):## FIXME
        pass


class NotificationBox(gtk.Expander):## or NotificationBox FIXME
    def __init__(self, event):
        gtk.Expander.__init__(self, _('Notification'))
        self.event = event
        self.hboxDict = {}
        totalVbox = gtk.VBox()
        ###
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Notify Before')), 0, 0)## or at the end?
        self.notifyBeforeInput = DurationInputBox()
        hbox.pack_start(self.notifyBeforeInput, 1, 1)
        totalVbox.pack_start(hbox, 0, 0)
        ###
        for cls in event_lib.classes.notifier:
            notifier = cls(self.event)
            inputWidget = notifier.makeWidget()
            hbox = gtk.HBox()
            cb = gtk.CheckButton(notifier.desc)
            cb.inputWidget = inputWidget
            cb.connect('clicked', lambda check: check.inputWidget.set_sensitive(check.get_active()))
            cb.set_active(False)
            hbox.pack_start(cb, 0, 0)
            hbox.cb = cb
            #hbox.pack_start(gtk.Label(''), 1, 1)
            hbox.pack_start(inputWidget, 1, 1)
            hbox.inputWidget = inputWidget
            self.hboxDict[notifier.name] = hbox
            totalVbox.pack_start(hbox, 0, 0)
        self.add(totalVbox)
    def updateWidget(self):
        self.notifyBeforeInput.setDuration(*self.event.notifyBefore)
        for hbox in self.hboxDict.values():
            hbox.cb.set_active(False)
            hbox.inputWidget.set_sensitive(False)
        for notifier in self.event.notifiers:
            hbox = self.hboxDict[notifier.name]
            hbox.cb.set_active(True)
            hbox.inputWidget.set_sensitive(True)
            hbox.inputWidget.notifier = notifier
            hbox.inputWidget.updateWidget()
        self.set_expanded(bool(self.event.notifiers))
    def updateVars(self):
        self.event.notifyBefore = self.notifyBeforeInput.getDuration()
        ###
        notifiers = []
        for hbox in self.hboxDict.values():
            if hbox.cb.get_active():
                hbox.inputWidget.updateVars()
                notifiers.append(hbox.inputWidget.notifier)
        self.event.notifiers = notifiers


class DurationInputBox(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        ##
        self.valueSpin = FloatSpinButton(0, 999, 1)
        self.pack_start(self.valueSpin, 0, 0)
        ##
        combo = gtk.combo_box_new_text()
        for unitValue, unitName in durationUnitsAbs:
            combo.append_text(_(' '+unitName.capitalize()+'s'))
        combo.set_active(2) ## hour FIXME
        self.pack_start(combo, 0, 0)
        self.unitCombo = combo
    def getDuration(self):
        return self.valueSpin.get_value(), durationUnitValues[self.unitCombo.get_active()]
    def setDuration(self, value, unit):
        self.valueSpin.set_value(value)
        self.unitCombo.set_active(durationUnitValues.index(unit))


class StrListEditor(gtk.HBox):
    def __init__(self, defaultValue=''):
        self.defaultValue = defaultValue
        #####
        gtk.HBox.__init__(self)
        self.treev = gtk.TreeView()
        self.treev.set_headers_visible(False)
        self.trees = gtk.ListStore(str)
        self.treev.set_model(self.trees)
        ##########
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        col = gtk.TreeViewColumn('', cell, text=0)
        self.treev.append_column(col)
        ####
        self.pack_start(self.treev, 1, 1)
        ##########
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        #try:## DeprecationWarning #?????????????
            #toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
            ### no different (argument to set_icon_size does not affect) ?????????
        #except:
        #    pass
        size = gtk.ICON_SIZE_SMALL_TOOLBAR
        ##no different(argument2 to image_new_from_stock does not affect) ?????????
        #### gtk.ICON_SIZE_SMALL_TOOLBAR or gtk.ICON_SIZE_MENU
        tb = toolButtonFromStock(gtk.STOCK_ADD, size)
        set_tooltip(tb, _('Add'))
        tb.connect('clicked', self.addClicked)
        toolbar.insert(tb, -1)
        #self.buttonAdd = tb
        ####
        tb = toolButtonFromStock(gtk.STOCK_GO_UP, size)
        set_tooltip(tb, _('Move up'))
        tb.connect('clicked', self.moveUpClicked)
        toolbar.insert(tb, -1)
        ####
        tb = toolButtonFromStock(gtk.STOCK_GO_DOWN, size)
        set_tooltip(tb, _('Move down'))
        tb.connect('clicked', self.moveDownClicked)
        toolbar.insert(tb, -1)
        #######
        self.pack_start(toolbar, 0, 0)
    def addClicked(self, button):
        cur = self.treev.get_cursor()
        if cur:
            self.trees.insert(cur[0], [self.defaultValue])
        else:
            self.trees.append([self.defaultValue])
    def moveUpClicked(self, button):
        cur = self.treev.get_cursor()
        if not cur:
            return
        i = cur[0]
        t = self.trees
        if i<=0 or i>=len(t):
            gdk.beep()
            return
        t.swap(t.get_iter(i-1), t.get_iter(i))
        self.treev.set_cursor(i-1)
    def moveDownClicked(self, button):
        cur = self.treev.get_cursor()
        if not cur:
            return
        i = cur[0]
        t = self.trees
        if i<0 or i>=len(t)-1:
            gdk.beep()
            return
        t.swap(t.get_iter(i), t.get_iter(i+1))
        self.treev.set_cursor(i+1)
    def setData(self, strList):
        self.trees.clear()
        for st in strList:
            self.trees.append([st])
    def getData(self):
        return [row[0] for row in self.trees]


class Scale10PowerComboBox(gtk.ComboBox):
    def __init__(self):
        self.ls = gtk.ListStore(int, str)
        gtk.ComboBox.__init__(self, self.ls)
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 1)
        ###
        self.ls.append((1, _('Years')))
        self.ls.append((100, _('Centuries')))
        self.ls.append((1000, _('Thousand Years')))
        self.ls.append((1000**2, _('Million Years')))
        self.ls.append((1000**3, _('Billion (10^9) Years')))
        ###
        self.set_active(0)
    get_value = lambda self: self.ls[self.get_active()][0]
    def set_value(self, value):
        for i, row in enumerate(self.ls):
            if row[0] == value:
                self.set_active(i)
                return
        self.ls.append((value, _('%s Years')%_(value)))
        self.set_active(len(self.ls)-1)


class EventEditorDialog(gtk.Dialog):
    def __init__(self, event, typeChangable=True, title=None, isNew=False, parent=None, useSelectedDate=False):
        gtk.Dialog.__init__(self, parent=parent)
        #self.set_transient_for(None)
        #self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
        if title:
            self.set_title(title)
        self.isNew = isNew
        #self.connect('delete-event', lambda obj, e: self.destroy())
        #self.resize(800, 600)
        ###
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        ###
        self.connect('response', lambda w, e: self.hide())
        #######
        self.event = event
        self._group = event.parent
        self.activeWidget = None
        #######
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Event Type')), 0, 0)
        if typeChangable and len(self._group.acceptsEventTypes)>1:## FIXME
            combo = gtk.combo_box_new_text()
            for eventType in self._group.acceptsEventTypes:
                combo.append_text(event_lib.classes.event.byName[eventType].desc)
            hbox.pack_start(combo, 0, 0)
            ####
            combo.set_active(self._group.acceptsEventTypes.index(event.name))
            #self.activeWidget = event.makeWidget()
            combo.connect('changed', self.typeChanged)
            self.comboEventType = combo
        else:
            hbox.pack_start(gtk.Label(':  '+event.desc), 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.show_all()
        self.vbox.pack_start(hbox, 0, 0)
        #####
        if useSelectedDate:
            self.event.setJd(ui.cell.jd)
        self.activeWidget = event.makeWidget()
        if self.isNew:
            self.activeWidget.focusSummary()
        self.vbox.pack_start(self.activeWidget, 0, 0)
        self.vbox.show()
    def typeChanged(self, combo):
        if self.activeWidget:
            self.activeWidget.updateVars()
            self.activeWidget.destroy()
        eventType = self._group.acceptsEventTypes[combo.get_active()]
        if self.isNew:
            self.event = self._group.createEvent(eventType)
        else:
            self.event = self._group.copyEventWithType(self.event, eventType)
        self._group.updateCache(self.event)## needed? FIXME
        self.activeWidget = self.event.makeWidget()
        if self.isNew:
            self.activeWidget.focusSummary()
        self.vbox.pack_start(self.activeWidget, 0, 0)
        #self.activeWidget.modeComboChanged()## apearantly not needed
    def run(self):
        #if not self.activeWidget:
        #    return None
        if gtk.Dialog.run(self) != gtk.RESPONSE_OK:
            try:
                filesBox = self.activeWidget.filesBox
            except AttributeError:
                pass
            else:
                filesBox.removeNewFiles()
            return None
        self.activeWidget.updateVars()
        self.event.afterModify()
        self.event.save()
        event_lib.saveLastIds()
        self.destroy()
        return self.event

def addNewEvent(group, eventType, title, typeChangable=False, **kw):
    event = group.createEvent(eventType)
    if eventType=='custom':## FIXME
        typeChangable = True
    event = EventEditorDialog(
        event,
        typeChangable=typeChangable,
        title=title,
        isNew=True,
        **kw
    ).run()
    if event is None:
        return
    group.append(event)
    group.save()
    return event

class GroupEditorDialog(gtk.Dialog):
    def __init__(self, group=None):
        gtk.Dialog.__init__(self)
        self.isNew = (group is None)
        self.set_title(_('Add New Group') if self.isNew else _('Edit Group'))
        #self.connect('delete-event', lambda obj, e: self.destroy())
        #self.resize(800, 600)
        ###
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        self.connect('response', lambda w, e: self.hide())
        #######
        self.activeWidget = None
        #######
        hbox = gtk.HBox()
        combo = gtk.combo_box_new_text()
        for cls in event_lib.classes.group:
            combo.append_text(cls.desc)
        hbox.pack_start(gtk.Label(_('Group Type')), 0, 0)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        if self.isNew:
            self._group = event_lib.classes.group[event_lib.defaultGroupTypeIndex]()
            combo.set_active(event_lib.defaultGroupTypeIndex)
        else:
            self._group = group
            combo.set_active(event_lib.classes.group.names.index(group.name))
        self.activeWidget = None
        combo.connect('changed', self.typeChanged)
        self.comboType = combo
        self.vbox.show_all()
        self.typeChanged()
    def dateModeChanged(self, combo):
        pass
    def getNewGroupTitle(self, baseTitle):
        usedTitles = [group.title for group in ui.eventGroups]
        if not baseTitle in usedTitles:
            return baseTitle
        i = 1
        while True:
            newTitle = baseTitle + ' ' + _(i)
            if newTitle in usedTitles:
                i += 1
            else:
                return newTitle
    def typeChanged(self, combo=None):
        if self.activeWidget:
            self.activeWidget.updateVars()
            self.activeWidget.destroy()
        cls = event_lib.classes.group[self.comboType.get_active()]
        group = cls()
        if self.isNew:
            if group.icon:
                self._group.icon = group.icon
        if not self.isNew:
            group.copyFrom(self._group)
        group.setId(self._group.id)
        if self.isNew:
            group.title = self.getNewGroupTitle(cls.desc)
        self._group = group
        self.activeWidget = group.makeWidget()
        self.vbox.pack_start(self.activeWidget, 0, 0)
    def run(self):
        if self.activeWidget is None:
            return None
        if gtk.Dialog.run(self) != gtk.RESPONSE_OK:
            return None
        self.activeWidget.updateVars()
        self._group.save()
        if self.isNew:
            event_lib.saveLastIds()
        else:
            ui.eventGroups[self._group.id] = self._group ## FIXME
        self.destroy()
        return self._group


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




class SingleGroupComboBox(gtk.ComboBox):
    def __init__(self):
        ls = gtk.ListStore(int, gdk.Pixbuf, str)
        gtk.ComboBox.__init__(self, ls)
        #####
        cell = gtk.CellRendererPixbuf()
        self.pack_start(cell, 0)
        self.add_attribute(cell, 'pixbuf', 1)
        ###
        cell = gtk.CellRendererText()
        self.pack_start(cell, 1)
        self.add_attribute(cell, 'text', 2)
        #####
        self.updateItems()
    def updateItems(self):
        ls = self.get_model()
        activeGid = self.get_active()
        ls.clear()
        ###
        rowBgColor = gdkColorToRgb(self.style.base[gtk.STATE_NORMAL])## bg color of non-selected rows FIXME
        for group in ui.eventGroups:
            if not group.enable:## FIXME
                continue
            ls.append(getGroupRow(group, rowBgColor))
        ###
        #try:
        gtk.ComboBox.set_active(self, 0)
        #except:
        #    pass
        if activeGid not in (None, -1):
            try:
                self.set_active(activeGid)
            except ValueError:
                pass
    def get_active(self):
        index = gtk.ComboBox.get_active(self)
        if index in (None, -1):
            return
        gid = self.get_model()[index][0]
        return gid
    def set_active(self, gid):
        ls = self.get_model()
        for i, row in enumerate(ls):
            if row[0] == gid:
                gtk.ComboBox.set_active(self, i)
                break
        else:
            raise ValueError('SingleGroupComboBox.set_active: Group ID %s is not in items'%gid)

if __name__ == '__main__':
    from pprint import pformat
    dialog = gtk.Window()
    dialog.vbox = gtk.VBox()
    dialog.add(dialog.vbox)
    #widget = ViewEditTagsHbox()
    #widget = EventTagsAndIconSelect()
    #widget = TagsListBox('task')
    widget = SingleGroupComboBox()
    dialog.vbox.pack_start(widget, 1, 1)
    #dialog.vbox.show_all()
    #dialog.resize(300, 500)
    #dialog.run()
    dialog.show_all()
    gtk.main()
    print pformat(widget.getData())



