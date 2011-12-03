#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal2.time_utils import hmEncode, hmDecode
from scal2.locale_man import tr as _
from scal2.locale_man import localeNumDecode

from scal2 import core

from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton
from scal2.ui_gtk.event import common
from scal2.ui_gtk.event.groups.group import GroupWidget as BaseGroupWidget

from scal2.ui_gtk.utils import toolButtonFromStock, set_tooltip

import gtk



class CourseListEditor(gtk.HBox):
    def __init__(self, term, defaultCourseName=_('New Course'), defaultCourseUnits=3):
        self.term = term ## UniversityTerm obj
        self.defaultCourseName = defaultCourseName
        self.defaultCourseUnits = defaultCourseUnits
        #####
        gtk.HBox.__init__(self)
        self.treev = gtk.TreeView()
        self.treev.set_headers_visible(True)
        self.trees = gtk.ListStore(int, str, int)
        self.treev.set_model(self.trees)
        ##########
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.courseNameEdited)
        col = gtk.TreeViewColumn(_('Course Name'), cell, text=1)
        self.treev.append_column(col)
        ###
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.courseUnitsEdited)
        col = gtk.TreeViewColumn(_('Units'), cell, text=2)
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
        tb = toolButtonFromStock(gtk.STOCK_DELETE, size)
        set_tooltip(tb, _('Delete'))
        tb.connect('clicked', self.deleteClicked)
        toolbar.insert(tb, -1)
        #self.buttonDel = tb
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
    def getSelectedIndex(self):
        cur = self.treev.get_cursor()
        try:
            (path, col) = cur
            index = path[0]
            return index
        except:
            return None
    def addClicked(self, button):
        index = self.getSelectedIndex()
        row = [self.term.getNewCourseID(), self.defaultCourseName, self.defaultCourseUnits]
        if index is None:
            newIter = self.trees.append(row)
        else:
            newIter = self.trees.insert(index+1, row)
        self.treev.set_cursor(self.trees.get_path(newIter))
        #col = self.treev.get_column(0)
        #cell = col.get_cell_renderers()[0]
        #cell.start_editing(...) ## FIXME
    def deleteClicked(self, button):
        index = self.getSelectedIndex()
        if index is None:
            return
        del self.trees[index]
    def moveUpClicked(self, button):
        index = self.getSelectedIndex()
        if index is None:
            return
        t = self.trees
        if index<=0 or index>=len(t):
            gdk.beep()
            return
        t.swap(t.get_iter(index-1), t.get_iter(index))
        self.treev.set_cursor(index-1)
    def moveDownClicked(self, button):
        index = self.getSelectedIndex()
        if index is None:
            return
        t = self.trees
        if index<0 or index>=len(t)-1:
            gdk.beep()
            return
        t.swap(t.get_iter(index), t.get_iter(index+1))
        self.treev.set_cursor(index+1)
    def courseNameEdited(self, cell, path, newText):
        index = int(path)
        self.trees[index][1] = newText
    def courseUnitsEdited(self, cell, path, newText):
        index = int(path)
        units = localeNumDecode(newText)
        self.trees[index][2] = units
    def setData(self, rows):
        self.trees.clear()
        for row in rows:
            self.trees.append(row)
    def getData(self):
        return [tuple(row) for row in self.trees]


class ClassTimeBoundsEditor(gtk.HBox):
    def __init__(self, term):
        self.term = term
        #####
        gtk.HBox.__init__(self)
        self.treev = gtk.TreeView()
        self.treev.set_headers_visible(False)
        self.trees = gtk.ListStore(str)
        self.treev.set_model(self.trees)
        ##########
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.timeEdited)
        col = gtk.TreeViewColumn(_('Time'), cell, text=0)
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
        tb = toolButtonFromStock(gtk.STOCK_DELETE, size)
        set_tooltip(tb, _('Delete'))
        tb.connect('clicked', self.deleteClicked)
        toolbar.insert(tb, -1)
        #self.buttonDel = tb
        #######
        self.pack_start(toolbar, 0, 0)
    def getSelectedIndex(self):
        cur = self.treev.get_cursor()
        try:
            (path, col) = cur
            index = path[0]
            return index
        except:
            return None
    def addClicked(self, button):
        index = self.getSelectedIndex()
        row = ['00:00']
        if index is None:
            newIter = self.trees.append(row)
        else:
            newIter = self.trees.insert(index+1, row)
        self.treev.set_cursor(self.trees.get_path(newIter))
    def deleteClicked(self, button):
        index = self.getSelectedIndex()
        if index is None:
            return
        del self.trees[index]
    def moveUpClicked(self, button):
        index = self.getSelectedIndex()
        if index is None:
            return
        t = self.trees
        if index<=0 or index>=len(t):
            gdk.beep()
            return
        t.swap(t.get_iter(index-1), t.get_iter(index))
        self.treev.set_cursor(index-1)
    def moveDownClicked(self, button):
        index = self.getSelectedIndex()
        if index is None:
            return
        t = self.trees
        if index<0 or index>=len(t)-1:
            gdk.beep()
            return
        t.swap(t.get_iter(index), t.get_iter(index+1))
        self.treev.set_cursor(index+1)
    def timeEdited(self, cell, path, newText):
        index = int(path)
        parts = newText.split(':')
        h = localeNumDecode(parts[0])
        m = localeNumDecode(parts[1])
        hm = hmEncode((h, m))
        self.trees[index][0] = hm
        #self.trees.sort()## FIXME
    def setData(self, hmList):
        self.trees.clear()
        for hm in hmList:
            self.trees.append([hmEncode(hm)])
    def getData(self):
        return sorted([hmDecode(row[0]) for row in self.trees])

class GroupWidget(BaseGroupWidget):
    def __init__(self, group):
        BaseGroupWidget.__init__(self, group)
        #####
        totalFrame = gtk.Frame(group.desc)
        totalVbox = gtk.VBox()
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('Start'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.startDateInput = DateButton(lang=core.langSh)
        hbox.pack_start(self.startDateInput, 0, 0)
        totalVbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('End'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.endDateInput = DateButton(lang=core.langSh)
        hbox.pack_start(self.endDateInput, 0, 0)
        totalVbox.pack_start(hbox, 0, 0)
        ###
        expandHbox = gtk.HBox()## for courseList and classTimeBounds
        ##
        frame = gtk.Frame(_('Course List'))
        self.courseListEditor = CourseListEditor(self.group)
        self.courseListEditor.set_size_request(100, 150)
        frame.add(self.courseListEditor)
        expandHbox.pack_start(frame, 1, 1)
        ##
        frame = gtk.Frame(_('Class Time Bounds'))## FIXME
        self.classTimeBoundsEditor = ClassTimeBoundsEditor(self.group)
        self.classTimeBoundsEditor.set_size_request(50, 150)
        frame.add(self.classTimeBoundsEditor)
        expandHbox.pack_start(frame, 1, 1)
        ##
        totalVbox.pack_start(expandHbox, 1, 1)
        #####
        totalFrame.add(totalVbox)
        self.pack_start(totalFrame, 1, 1)## expand? FIXME
    def updateWidget(self):## FIXME
        BaseGroupWidget.updateWidget(self)
        self.startDateInput.set_date(self.group['start'].date)
        self.endDateInput.set_date(self.group['end'].date)
        self.courseListEditor.setData(self.group.courses)
        self.classTimeBoundsEditor.setData(self.group.classTimeBounds)
    def updateVars(self):
        BaseGroupWidget.updateVars(self)
        ##
        startRule = self.group['start']
        startRule.date = self.startDateInput.get_date()
        startRule.time = (0, 0, 0)
        ##
        endRule = self.group['end']
        endRule.date = self.endDateInput.get_date()
        endRule.time = (24, 0, 0) ## FIXME
        ##
        self.group.courses = self.courseListEditor.getData()
        self.group.classTimeBounds = self.classTimeBoundsEditor.getData()



