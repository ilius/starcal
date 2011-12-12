import os, shutil
from os.path import join, split

from scal2.utils import toStr
from scal2.time_utils import durationUnitsAbs, durationUnitValues
from scal2 import core
from scal2.locale_man import tr as _
from scal2.locale_man import localeNumDecode

from scal2.core import pixDir, myRaise

from scal2 import event_man
from scal2 import ui

from scal2.ui_gtk.utils import toolButtonFromStock, set_tooltip, buffer_get_text

import gtk
from gtk import gdk

#print 'Testing translator', __file__, _('_About')## OK


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
        if response==gtk.RESPONSE_OK:
            self.set_filename(dialog.get_filename())
        elif response==gtk.RESPONSE_REJECT:
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
        combo = gtk.combo_box_new_text()
        for module in core.modules:
            combo.append_text(_(module.desc))
        combo.set_active(core.primaryMode)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.modeCombo = combo
        ###
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Summary')), 0, 0)
        self.summuryEntry = gtk.Entry()
        hbox.pack_start(self.summuryEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Description')), 0, 0)
        textview = gtk.TextView()
        textview.set_wrap_mode(gtk.WRAP_WORD)
        self.descriptionBuff = textview.get_buffer()
        frame = gtk.Frame()
        frame.set_border_width(4)
        frame.add(textview)
        hbox.pack_start(frame, 1, 1)
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
    def updateWidget(self):
        #print 'updateWidget', self.event.files
        self.modeCombo.set_active(self.event.mode)
        self.summuryEntry.set_text(self.event.summary)
        self.descriptionBuff.set_text(self.event.description)
        self.iconSelect.set_filename(self.event.icon)
        try:
            filesBox = self.filesBox
        except AttributeError:
            pass
        else:
            filesBox.updateWidget()
        self.modeComboChanged(self.modeCombo)
    def updateVars(self):
        self.event.mode = self.modeCombo.get_active()
        self.event.summary = self.summuryEntry.get_text()
        self.event.description = buffer_get_text(self.descriptionBuff)
        self.event.icon = self.iconSelect.get_filename()
    def modeComboChanged(self, combo):## FIXME
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
        if fcd.run()==gtk.RESPONSE_OK:
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
        for cls in event_man.eventNotifiersClassList:
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
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(0, 999)
        spin.set_digits(1)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        #spin.set_width_chars
        self.pack_start(spin, 0, 0)
        self.valueSpin = spin
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




class GroupComboBox(gtk.ComboBox):
    def __init__(self):
        pass


class EventEditorDialog(gtk.Dialog):
    def __init__(self, event, eventTypeChangable=True, title=None, parent=None, useSelectedDate=False):
        gtk.Dialog.__init__(self, parent=parent)
        #self.set_transient_for(parent)
        if title:
            self.set_title(title)
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
        self.event = event
        self._group = event.group
        self.activeEventWidget = None
        #######
        if eventTypeChangable and len(event.group.acceptsEventTypes)>1:## FIXME
            hbox = gtk.HBox()
            combo = gtk.combo_box_new_text()
            for eventType in event.group.acceptsEventTypes:
                combo.append_text(event_man.eventsClassDict[eventType].desc)
            hbox.pack_start(gtk.Label(_('Event Type')), 0, 0)
            hbox.pack_start(combo, 0, 0)
            hbox.pack_start(gtk.Label(''), 1, 1)
            hbox.show_all()
            self.vbox.pack_start(hbox, 0, 0)
            ####
            combo.set_active(event.group.acceptsEventTypes.index(event.name))
            #self.activeEventWidget = event.makeWidget()
            combo.connect('changed', self.eventTypeChanged)
            self.comboEventType = combo
        if useSelectedDate:
            self.event.setJd(ui.cell.jd)
        self.activeEventWidget = event.makeWidget()
        self.vbox.pack_start(self.activeEventWidget, 0, 0)
        self.vbox.show()
    def dateModeChanged(self, combo):
        pass
    def eventTypeChanged(self, combo):
        print '--- eventTypeChanged'
        if self.activeEventWidget:
            self.activeEventWidget.destroy()
        eventType = self._group.acceptsEventTypes[combo.get_active()]
        self.event = self._group.copyEventWithType(self.event, eventType)
        self._group.updateCache(self.event)## needed? FIXME
        self.activeEventWidget = self.event.makeWidget()
        self.vbox.pack_start(self.activeEventWidget, 0, 0)
    def run(self):
        #if not self.activeEventWidget:
        #    return None
        if gtk.Dialog.run(self)!=gtk.RESPONSE_OK:
            try:
                filesBox = self.activeEventWidget.filesBox
            except AttributeError:
                pass
            else:
                filesBox.removeNewFiles()
            return None
        self.activeEventWidget.updateVars()
        self.event.saveConfig()
        self.destroy()
        return self.event

def addNewEvent(group, eventType, title, **kw):
    event = group.createEvent(eventType)
    event = EventEditorDialog(
        event,
        eventTypeChangable=(eventType=='custom'),## or True FIXME
        title=title,
        **kw
    ).run()
    if event is None:
        return
    group.append(event)
    group.saveConfig()
    return event

class GroupEditorDialog(gtk.Dialog):
    def __init__(self, group=None):
        gtk.Dialog.__init__(self)
        self.set_title(_('Edit Group') if group else _('Add New Group'))
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
        self._group = group
        self.activeGroupWidget = None
        #######
        hbox = gtk.HBox()
        combo = gtk.combo_box_new_text()
        for cls in event_man.eventGroupsClassList:
            combo.append_text(cls.desc)
        hbox.pack_start(gtk.Label(_('Group Type')), 0, 0)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        if self._group:
            self.isNewGroup = False
            combo.set_active(event_man.eventGroupsClassNameList.index(self._group.name))
        else:
            self.isNewGroup = True
            combo.set_active(event_man.defaultGroupTypeIndex)
            self._group = event_man.eventGroupsClassList[event_man.defaultGroupTypeIndex]()
        self.activeGroupWidget = None
        combo.connect('changed', self.groupTypeChanged)
        self.comboGroupType = combo
        self.vbox.show_all()
        self.groupTypeChanged()
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
    def groupTypeChanged(self, combo=None):
        if self.activeGroupWidget:
            self.activeGroupWidget.updateVars()
            self.activeGroupWidget.destroy()
        cls = event_man.eventGroupsClassList[self.comboGroupType.get_active()]
        group = cls()
        if self._group:
            if self.isNewGroup:
                if group.icon:
                    self._group.icon = group.icon
            group.copyFrom(self._group)
            group.setId(self._group.gid)
            del self._group
        if self.isNewGroup:
            group.title = self.getNewGroupTitle(cls.desc)
        self._group = group
        self.activeGroupWidget = group.makeWidget()
        self.vbox.pack_start(self.activeGroupWidget, 0, 0)
    def run(self):
        if self.activeGroupWidget is None or self._group is None:
            return None
        if gtk.Dialog.run(self)!=gtk.RESPONSE_OK:
            return None
        self.activeGroupWidget.updateVars()
        self._group.saveConfig()
        ui.eventGroups[self._group.gid] = self._group
        self.destroy()
        return self._group

if __name__ == '__main__':
    from pprint import pformat
    if core.rtl:
        gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)
    dialog = gtk.Window()
    dialog.vbox = gtk.VBox()
    dialog.add(dialog.vbox)
    #widget = ViewEditTagsHbox()
    widget = EventTagsAndIconSelect()
    #widget = TagsListBox('task')
    dialog.vbox.pack_start(widget, 1, 1)
    #dialog.vbox.show_all()
    #dialog.resize(300, 500)
    #dialog.run()
    dialog.show_all()
    gtk.main()
    print pformat(widget.getData())



