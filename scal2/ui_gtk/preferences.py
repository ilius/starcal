# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2013 Saeed Rasooli <saeed.gnu@gmail.com>
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

from time import localtime

import sys, os
from os.path import join

from scal2 import locale_man
from scal2.locale_man import langSh
from scal2.locale_man import tr as _
from scal2.path import *

from scal2.cal_types import calTypes
from scal2 import core
from scal2.core import myRaise, convert, APP_DESC

from scal2 import ui

import gtk
from gtk import gdk

from scal2.ui_gtk.font_utils import *
from scal2.ui_gtk.color_utils import *
from scal2.ui_gtk.utils import *

from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.pref_utils import *
from scal2.ui_gtk.export import ExportToIcsDialog
from scal2.ui_gtk.event.account_op import AccountEditorDialog



class PrefDialog(gtk.Dialog):
    def __init__(self, trayMode):
        gtk.Dialog.__init__(self, title=_('Preferences'))
        self.connect('delete-event', self.onDelete)
        self.set_has_separator(False)
        #self.set_skip_taskbar_hint(True)
        ###
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), 1, self.cancel)
        dialog_add_button(self, gtk.STOCK_APPLY, _('_Apply'), 2, self.apply)
        okB = dialog_add_button(self, gtk.STOCK_OK, _('_OK'), 3, self.ok, tooltip=_('Apply and Close'))
        okB.grab_default()## FIXME
        #okB.grab_focus()## FIXME
        ##############################################
        self.localePrefItems = []
        self.corePrefItems = []
        self.uiPrefItems = []
        self.gtkPrefItems = [] ## FIXME
        #####
        self.prefPages = []
        ################################ Tab 1 (General) ############################################
        vbox = gtk.VBox()
        vbox.label = _('_General')
        vbox.icon = 'preferences-other.png'
        self.prefPages.append(vbox)
        hbox = gtk.HBox(spacing=3)
        hbox.pack_start(gtk.Label(_('Language')), 0, 0)
        itemLang = LangPrefItem()
        self.localePrefItems.append(itemLang)
        ###
        hbox.pack_start(itemLang.widget, 0, 0)
        if langSh!='en':
            hbox.pack_start(gtk.Label('Language'), 0, 0)
        vbox.pack_start(hbox, 0, 0)
        ##########################
        hbox = gtk.HBox()
        frame = gtk.Frame(_('Calendar Types'))
        itemCals = AICalsPrefItem()
        self.corePrefItems.append(itemCals)
        frame.add(itemCals.widget)
        hbox.pack_start(frame, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.set_border_width(5)
        #frame.set_border_width(5)
        vbox.pack_start(hbox, 1, 1)
        ##########################
        if trayMode!=1:
            hbox = gtk.HBox(spacing=3)
            item = CheckStartupPrefItem()
            self.uiPrefItems.append(item)
            hbox.pack_start(item.widget, 1, 1)
            vbox.pack_start(hbox, 0, 0)
            ########################
            item = CheckPrefItem(ui, 'showMain', _('Show main window on start'))
            self.uiPrefItems.append(item)
            vbox.pack_start(item.widget, 0, 0)
        ##########################
        item = CheckPrefItem(ui, 'winTaskbar', _('Window in Taskbar'))
        self.uiPrefItems.append(item)
        hbox = gtk.HBox(spacing=3)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###########
        vbox.pack_start(hbox, 0, 0)
        ##########################
        try:
            import appindicator
        except ImportError:
            pass
        else:
            item = CheckPrefItem(ui, 'useAppIndicator', _('Use AppIndicator'))
            self.uiPrefItems.append(item)
            hbox = gtk.HBox(spacing=3)
            hbox.pack_start(item.widget, 0, 0)
            hbox.pack_start(gtk.Label(''), 1, 1)
            vbox.pack_start(hbox, 0, 0)
        ##########################
        hbox = gtk.HBox(spacing=3)
        hbox.pack_start(gtk.Label(_('Show Digital Clock:')), 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        #item = CheckPrefItem(ui, 'showDigClockTb', _('On Toolbar'))## FIXME
        #self.uiPrefItems.append(item)
        #hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        if trayMode==1:
            item = CheckPrefItem(ui, 'showDigClockTr', _('On Applet'), 'Panel Applet')
        else:
            item = CheckPrefItem(ui, 'showDigClockTr', _('On Tray'), 'Notification Area')
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        vbox.pack_start(hbox, 0, 0)
        ################################ Tab 2 (Appearance) ###########################################
        vbox = gtk.VBox()
        vbox.label = _('A_ppearance')
        vbox.icon = 'preferences-desktop-theme.png'
        self.prefPages.append(vbox)
        ########
        hbox = gtk.HBox(spacing=2)
        ###
        customCheckItem = CheckPrefItem(ui, 'fontCustomEnable', _('Application Font'))
        self.uiPrefItems.append(customCheckItem)
        hbox.pack_start(customCheckItem.widget, 0, 0)
        ###
        customItem = FontPrefItem(ui, 'fontCustom', self)
        self.uiPrefItems.append(customItem)
        hbox.pack_start(customItem.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        customItem.widget.set_sensitive(ui.fontCustomEnable)
        #customItem.widget.connect('clicked', self.checkbFontClicked)
        customCheckItem.widget.connect('clicked', lambda w: customItem.widget.set_sensitive(w.get_active()))## FIXME
        vbox.pack_start(hbox, 0, 0)
        ########################### Theme #####################
        hbox = gtk.HBox(spacing=3)
        item = CheckPrefItem(ui, 'bgUseDesk', _('Use Desktop Background'))
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        vbox.pack_start(hbox, 0, 0)
        #####################
        hbox = gtk.HBox(spacing=3)
        lab = gtk.Label('<b>%s:</b> '%_('Colors'))
        lab.set_use_markup(True)
        hbox.pack_start(lab, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox.pack_start(gtk.Label(_('Background')), 0, 0)
        item = ColorPrefItem(ui, 'bgColor', True)
        self.uiPrefItems.append(item)
        self.colorbBg = item.widget ## FIXME
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox.pack_start(gtk.Label(_('Border')), 0, 0)
        item = ColorPrefItem(ui, 'borderColor', True)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox.pack_start(gtk.Label(_('Cursor')), 0, 0)
        item = ColorPrefItem(ui, 'cursorOutColor', False)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox.pack_start(gtk.Label(_('Cursor BG')), 0, 0)
        item = ColorPrefItem(ui, 'cursorBgColor', True)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox.pack_start(gtk.Label(_('Today')), 0, 0)
        item = ColorPrefItem(ui, 'todayCellColor', True)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        vbox.pack_start(hbox, 0, 0)
        ####################
        hbox = gtk.HBox(spacing=3)
        lab = gtk.Label('<b>%s:</b> '%_('Font Colors'))
        lab.set_use_markup(True)
        hbox.pack_start(lab, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ####
        hbox.pack_start(gtk.Label(_('Normal')), 0, 0)
        item = ColorPrefItem(ui, 'textColor', False)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox.pack_start(gtk.Label(_('Holiday')), 0, 0)
        item = ColorPrefItem(ui, 'holidayColor', False)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox.pack_start(gtk.Label(_('Inactive Day')), 0, 0)
        item = ColorPrefItem(ui, 'inactiveColor', True)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ####
        hbox.pack_start(gtk.Label(_('Border')), 0, 0)
        item = ColorPrefItem(ui, 'borderTextColor', False)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ####
        vbox.pack_start(hbox, 0, 0)
        ###################
        hbox = gtk.HBox(spacing=1)
        label = gtk.Label('<b>%s</b>:'%_('Cursor'))
        label.set_use_markup(True)
        hbox.pack_start(label, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(gtk.Label(_('Diameter Factor')), 0, 0)
        item = SpinPrefItem(ui, 'cursorDiaFactor', 0, 1, 2)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        ###
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(gtk.Label(_('Rounding Factor')), 0, 0)
        item = SpinPrefItem(ui, 'cursorRoundingFactor', 0, 1, 2)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        vbox.pack_start(hbox, 0, 0)
        ################################ Tab 3 (Advanced) ###########################################
        vbox = gtk.VBox()
        vbox.label = _('A_dvanced')
        vbox.icon = 'applications-system.png'
        self.prefPages.append(vbox)
        ######
        sgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ######
        hbox = gtk.HBox(spacing=5)
        label = gtk.Label(_('Date Format'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sgroup.add_widget(label)
        #hbox.pack_start(gtk.Label(''), 1, 1)
        item = ComboEntryTextPrefItem(ud, 'dateFormat', (
            '%Y/%m/%d',
            '%Y-%m-%d',
            '%y/%m/%d',
            '%y-%m-%d',
            '%OY/%Om/%Od',
            '%OY-%Om-%Od',
            '%m/%d',
            '%m/%d/%Y',
        ))
        self.gtkPrefItems.append(item)
        hbox.pack_start(item.widget, 1, 1)
        vbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox(spacing=5)
        #hbox.pack_start(gtk.Label(''), 1, 1)
        label = gtk.Label(_('Digital Clock Format'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sgroup.add_widget(label)
        item = ComboEntryTextPrefItem(ud, 'clockFormat', (
            '%T',
            '%X',
            '%Y/%m/%d - %T',
            '%OY/%Om/%Od - %X',
            '<i>%Y/%m/%d</i> - %T',
            '<b>%T</b>',
            '<b>%X</b>',
            '%H:%M',
            '<b>%H:%M</b>',
            '<span size="smaller">%OY/%Om/%Od</span>,%X'
            '%OY/%Om/%Od,<span color="#ff0000">%X</span>',
            '<span font="bold">%X</span>',
            '%OH:%OM',
            '<b>%OH:%OM</b>',
        ))
        self.gtkPrefItems.append(item)
        hbox.pack_start(item.widget, 1, 1)
        vbox.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox(spacing=5)
        label = gtk.Label(_('Days maximum cache size'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        ##sgroup.add_widget(label)
        item = SpinPrefItem(ui, 'maxDayCacheSize', 100, 9999, 0)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        vbox.pack_start(hbox, 0, 0)
        vbox4 = vbox
        ########
        hbox = gtk.HBox(spacing=3)
        hbox.pack_start(gtk.Label(_('First day of week')), 0, 0)
        ##item = ComboTextPrefItem( ##?????????
        self.comboFirstWD = gtk.combo_box_new_text()
        for item in core.weekDayName:
            self.comboFirstWD.append_text(item)
        self.comboFirstWD.append_text(_('Automatic'))
        self.comboFirstWD.connect('changed', self.comboFirstWDChanged)
        hbox.pack_start(self.comboFirstWD, 0, 0)
        vbox.pack_start(hbox, 0, 0)
        #########
        hbox0 = gtk.HBox(spacing=0)
        hbox0.pack_start(gtk.Label(_('Holidays')+'    '), 0, 0)
        item = WeekDayCheckListPrefItem(core, 'holidayWeekDays')
        self.corePrefItems.append(item)
        self.holiWDItem = item ## Holiday Week Days Item
        hbox0.pack_start(item.widget, 1, 1)
        vbox.pack_start(hbox0, 0, 0)
        #########
        hbox = gtk.HBox(spacing=3)
        hbox.pack_start(gtk.Label(_('First week of year containts')), 0, 0)
        combo = gtk.combo_box_new_text()
        texts = [_('First %s of year')%name for name in core.weekDayName]+[_('First day of year')]
        texts[4] += ' (ISO 8601)' ##??????
        for text in texts:
            combo.append_text(text)
        #combo.append_text(_('Automatic'))## (as Locale)#?????????????????
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        vbox.pack_start(hbox, 0, 0)
        self.comboWeekYear = combo
        #########
        hbox = gtk.HBox(spacing=3)
        item = CheckPrefItem(locale_man, 'enableNumLocale', _('Numbers Localization'))
        self.localePrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        vbox.pack_start(hbox, 0, 0)
        ##################################################
        ################################
        options = []
        for mod in calTypes:
            for opt in mod.options:
                if opt[0]=='button':
                    try:
                        optl = ModuleOptionButton(opt[1:])
                    except:
                        myRaise()
                        continue
                else:
                    optl = ModuleOptionItem(mod, opt)
                options.append(optl)
                vbox.pack_start(optl.widget, 0, 0)
        self.moduleOptions = options
        ################################ Tab 4 (Plugins) ############################################
        vbox = gtk.VBox()
        vbox.label = _('_Plugins')
        vbox.icon = 'preferences-plugin.png'
        self.prefPages.append(vbox)
        #####
        ##pluginsTextTray:
        hbox = gtk.HBox()
        if trayMode==1:
            item = CheckPrefItem(ui, 'pluginsTextTray', _('Show in applet (for today)'))
        else:
            item = CheckPrefItem(ui, 'pluginsTextTray', _('Show in tray (for today)'))
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        vbox.pack_start(hbox, 0, 0)
        #####
        treev = gtk.TreeView()
        treev.set_headers_clickable(True)
        trees = gtk.ListStore(int, bool, bool, str)
        treev.set_model(trees)
        treev.enable_model_drag_source(gdk.BUTTON1_MASK, [('row', gtk.TARGET_SAME_WIDGET, 0)], gdk.ACTION_MOVE)
        treev.enable_model_drag_dest([('row', gtk.TARGET_SAME_WIDGET, 0)], gdk.ACTION_MOVE)
        treev.connect('drag_data_received', self.plugTreevDragReceived)
        treev.connect('cursor-changed', self.plugTreevCursorChanged)
        treev.connect('row-activated', self.plugTreevRActivate)
        treev.connect('button-press-event', self.plugTreevButtonPress)
        ###
        #treev.drag_source_set_icon_stock(gtk.STOCK_CLOSE)
        #treev.drag_source_add_text_targets()
        #treev.drag_source_add_uri_targets()
        #treev.drag_source_unset()
        ###
        swin = gtk.ScrolledWindow()
        swin.add(treev)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        ######
        cell = gtk.CellRendererToggle()
        #cell.set_property('activatable', True)
        cell.connect('toggled', self.plugTreeviewCellToggled)
        col = gtk.TreeViewColumn(_('Enable'), cell)
        col.add_attribute(cell, 'active', 1)
        #cell.set_active(False)
        col.set_resizable(True)
        treev.append_column(col)
        ######
        cell = gtk.CellRendererToggle()
        #cell.set_property('activatable', True)
        cell.connect('toggled', self.plugTreeviewCellToggled2)
        col = gtk.TreeViewColumn(_('Show Date'), cell)
        col.add_attribute(cell, 'active', 2)
        #cell.set_active(False)
        col.set_resizable(True)
        treev.append_column(col)
        ######
        #cell = gtk.CellRendererText()
        #col = gtk.TreeViewColumn(_('File Name'), cell, text=2)
        #col.set_resizable(True)
        #treev.append_column(col)
        #treev.set_search_column(1)
        ######
        cell = gtk.CellRendererText()
        #cell.set_property('wrap-mode', gtk.WRAP_WORD)
        #cell.set_property('editable', True)
        #cell.set_property('wrap-width', 200)
        col = gtk.TreeViewColumn(_('Description'), cell, text=3)
        #treev.connect('expose-event', self.plugTreevExpose)
        #self.plugDescCell = cell
        #self.plugDescCol = col
        #col.set_resizable(True)## No need!
        treev.append_column(col)
        ######
        #for i in xrange(len(core.plugIndex)):
        #    x = core.plugIndex[i]
        #    trees.append([x[0], x[1], x[2], core.allPlugList[x[0]].desc])
        ######
        self.plugTreeview = treev
        self.plugTreestore = trees
        #######################
        hbox = gtk.HBox()
        vboxPlug = gtk.VBox()
        vboxPlug.pack_start(swin, 1, 1)
        hbox.pack_start(vboxPlug, 1, 1)
        ###
        hboxBut = gtk.HBox()
        ###
        button = gtk.Button(_('_About Plugin'))
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_ABOUT, gtk.ICON_SIZE_BUTTON))
        button.set_sensitive(False)
        button.connect('clicked', self.plugAboutClicked)
        self.plugButtonAbout = button
        hboxBut.pack_start(button, 0, 0)
        hboxBut.pack_start(gtk.Label(''), 1, 1)
        ###
        button = gtk.Button(_('C_onfigure Plugin'))
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_BUTTON))
        button.set_sensitive(False)
        button.connect('clicked', self.plugConfClicked)
        self.plugButtonConf = button
        hboxBut.pack_start(button, 0, 0)
        hboxBut.pack_start(gtk.Label(''), 1, 1)
        ###
        vboxPlug.pack_start(hboxBut, 0, 0)
        ###
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        #try:## DeprecationWarning #?????????????
            #toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
            ### no different (argument to set_icon_size does not affect) ?????????
        #except:
        #    pass
        size = gtk.ICON_SIZE_SMALL_TOOLBAR
        ##no different(argument2 to image_new_from_stock does not affect) ?????????
        ######## gtk.ICON_SIZE_SMALL_TOOLBAR or gtk.ICON_SIZE_MENU
        tb = toolButtonFromStock(gtk.STOCK_GOTO_TOP, size)
        set_tooltip(tb, _('Move to top'))
        tb.connect('clicked', self.plugTreeviewTop)
        toolbar.insert(tb, -1)
        ########
        tb = toolButtonFromStock(gtk.STOCK_GO_UP, size)
        set_tooltip(tb, _('Move up'))
        tb.connect('clicked', self.plugTreeviewUp)
        toolbar.insert(tb, -1)
        #########
        tb = toolButtonFromStock(gtk.STOCK_GO_DOWN, size)
        set_tooltip(tb, _('Move down'))
        tb.connect('clicked', self.plugTreeviewDown)
        toolbar.insert(tb, -1)
        ########
        tb = toolButtonFromStock(gtk.STOCK_GOTO_BOTTOM, size)
        set_tooltip(tb, _('Move to bottom'))
        tb.connect('clicked', self.plugTreeviewBottom)
        toolbar.insert(tb, -1)
        ##########
        tb = toolButtonFromStock(gtk.STOCK_ADD, size)
        set_tooltip(tb, _('Add'))
        #tb.connect('clicked', lambda obj: self.plugAddDialog.run())
        tb.connect('clicked', self.plugAddClicked)
        #if len(self.plugAddItems)==0:
        #    tb.set_sensitive(False)
        toolbar.insert(tb, -1)
        self.plugButtonAdd = tb
        ###########
        tb = toolButtonFromStock(gtk.STOCK_DELETE, size)
        set_tooltip(tb, _('Delete'))
        tb.connect('clicked', self.plugTreeviewDel)
        toolbar.insert(tb, -1)
        ###########
        hbox.pack_start(toolbar, 0, 0)
        #####
        '''
        vpan = gtk.VPaned()
        vpan.add1(hbox)
        vbox2 = gtk.VBox()
        vbox2.pack_start(gtk.Label('Test Label'))
        vpan.add2(vbox2)
        vpan.set_position(100)
        vbox.pack_start(vpan)
        '''
        vbox.pack_start(hbox, 1, 1)
        ##########################
        d = gtk.Dialog()
        d.set_transient_for(self)
        ## dialog.set_transient_for(parent) makes the window on top of parent and at the center point of parent
        ## but if you call dialog.show() or dialog.present(), the parent is still active(clickabel widgets) before closing child "dialog"
        ## you may call dialog.run() to realy make it transient for parent
        d.set_has_separator(False)
        d.connect('delete-event', self.plugAddDialogClose)
        d.set_title(_('Add Plugin'))
        ###
        dialog_add_button(d, gtk.STOCK_CANCEL, _('_Cancel'), 1, self.plugAddDialogClose)
        dialog_add_button(d, gtk.STOCK_OK, _('_OK'), 2, self.plugAddDialogOK)
        ###
        treev = gtk.TreeView()
        trees = gtk.ListStore(str)
        treev.set_model(trees)
        #treev.enable_model_drag_source(gdk.BUTTON1_MASK, [('', 0, 0)], gdk.ACTION_MOVE)#?????
        #treev.enable_model_drag_dest([('', 0, 0)], gdk.ACTION_MOVE)#?????
        treev.connect('drag_data_received', self.plugTreevDragReceived)
        treev.connect('row-activated', self.plugAddTreevRActivate)
        ####
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Description'), cell, text=0)
        #col.set_resizable(True)# no need when have only one column!
        treev.append_column(col)
        ####
        swin = gtk.ScrolledWindow()
        swin.add(treev)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        d.vbox.pack_start(swin)
        d.vbox.show_all()
        self.plugAddDialog = d
        self.plugAddTreeview = treev
        self.plugAddTreestore = trees
        #############
        ##treev.set_resize_mode(gtk.RESIZE_IMMEDIATE)
        ##self.plugAddItems = []
        ####################################### Tab 5 (Accounts)
        vbox = gtk.VBox()
        vbox.label = _('Accounts')
        vbox.icon = 'web-settings.png'
        self.prefPages.append(vbox)
        #####
        treev = gtk.TreeView()
        treev.set_headers_clickable(True)
        trees = gtk.ListStore(int, bool, str)## id (hidden), enable, title
        treev.set_model(trees)
        treev.enable_model_drag_source(gdk.BUTTON1_MASK, [('row', gtk.TARGET_SAME_WIDGET, 0)], gdk.ACTION_MOVE)
        treev.enable_model_drag_dest([('row', gtk.TARGET_SAME_WIDGET, 0)], gdk.ACTION_MOVE)
        treev.connect('row-activated', self.accountsTreevRActivate)
        treev.connect('button-press-event', self.accountsTreevButtonPress)
        ###
        swin = gtk.ScrolledWindow()
        swin.add(treev)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        ######
        cell = gtk.CellRendererToggle()
        #cell.set_property('activatable', True)
        cell.connect('toggled', self.accountsTreeviewCellToggled)
        col = gtk.TreeViewColumn(_('Enable'), cell)
        col.add_attribute(cell, 'active', 1)
        #cell.set_active(False)
        col.set_resizable(True)
        treev.append_column(col)
        ######
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Title'), cell, text=2)
        #col.set_resizable(True)## No need!
        treev.append_column(col)
        ######
        self.accountsTreeview = treev
        self.accountsTreestore = trees
        #######################
        hbox = gtk.HBox()
        vboxPlug = gtk.VBox()
        vboxPlug.pack_start(swin, 1, 1)
        hbox.pack_start(vboxPlug, 1, 1)
        ###
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        #try:## DeprecationWarning #?????????????
            #toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
            ### no different (argument to set_icon_size does not affect) ?????????
        #except:
        #    pass
        size = gtk.ICON_SIZE_SMALL_TOOLBAR
        ##no different(argument2 to image_new_from_stock does not affect) ?????????
        ######## gtk.ICON_SIZE_SMALL_TOOLBAR or gtk.ICON_SIZE_MENU
        tb = toolButtonFromStock(gtk.STOCK_EDIT, size)
        set_tooltip(tb, _('Edit'))
        tb.connect('clicked', self.accountsEditClicked)
        toolbar.insert(tb, -1)
        ###########
        tb = toolButtonFromStock(gtk.STOCK_ADD, size)
        set_tooltip(tb, _('Add'))
        tb.connect('clicked', self.accountsAddClicked)
        toolbar.insert(tb, -1)
        ###########
        tb = toolButtonFromStock(gtk.STOCK_DELETE, size)
        set_tooltip(tb, _('Delete'))
        tb.connect('clicked', self.accountsDelClicked)
        toolbar.insert(tb, -1)
        ##########
        tb = toolButtonFromStock(gtk.STOCK_GO_UP, size)
        set_tooltip(tb, _('Move up'))
        tb.connect('clicked', self.accountsUpClicked)
        toolbar.insert(tb, -1)
        #########
        tb = toolButtonFromStock(gtk.STOCK_GO_DOWN, size)
        set_tooltip(tb, _('Move down'))
        tb.connect('clicked', self.accountsDownClicked)
        toolbar.insert(tb, -1)
        ###########
        hbox.pack_start(toolbar, 0, 0)
        vbox.pack_start(hbox, 1, 1)
        ###################################################################################################
        notebook = gtk.Notebook()
        self.notebook = notebook
        #####################################
        for vbox in self.prefPages:
            l = gtk.Label(vbox.label)
            l.set_use_underline(True)
            vb = gtk.VBox(spacing=3)
            vb.pack_start(imageFromFile(vbox.icon))
            vb.pack_start(l)
            vb.show_all()
            notebook.append_page(vbox, vb)
            try:
                notebook.set_tab_reorderable(vbox, True)
            except AttributeError:
                pass
        #######################
        notebook.set_property('homogeneous', True)
        notebook.set_property('tab-border', 5)
        notebook.set_property('tab-hborder', 15)
        self.vbox.pack_start(notebook)
        self.vbox.show_all()
        for i in ui.prefPagesOrder:
            try:
                j = ui.prefPagesOrder[i]
            except IndexError:
                continue
            notebook.reorder_child(self.prefPages[i], j)
    def comboFirstWDChanged(self, combo):
        f = self.comboFirstWD.get_active() ## 0 means Sunday
        if f==7: ## auto
            try:
                f = core.getLocaleFirstWeekDay()
            except:
                pass
        ## core.firstWeekDay will be later = f
        self.holiWDItem.setStart(f)
    def onDelete(self, obj=None, data=None):
        self.hide()
        return True
    def ok(self, widget):
        self.hide()
        self.apply()
    def cancel(self, widget=None):
        self.hide()
        self.updatePrefGui()
        return True
    getAllPrefItems = lambda self: self.moduleOptions + self.localePrefItems + self.corePrefItems +\
                                   self.uiPrefItems + self.gtkPrefItems
    def apply(self, widget=None):
        ####### ?????????????????
        #print 'fontDefault =', ui.fontDefault
        ui.fontDefault = gfontDecode(ud.settings.get_property('gtk-font-name'))
        #print 'fontDefault =', ui.fontDefault
        ############################################## Updating pref variables
        for opt in self.getAllPrefItems():
            opt.updateVar()
        ###### DB Manager (Plugin Manager)
        index = []
        for row in self.plugTreestore:
            index.append(row[0])
            plug = core.allPlugList[row[0]]
            try:
                plug.enable = row[1]
                plug.show_date = row[2]
            except:
                core.myRaise(__file__)
                print(i, core.plugIndex)
        core.plugIndex = index
        ######
        first = self.comboFirstWD.get_active()
        if first==7:
            core.firstWeekDayAuto = True
            try:
                core.firstWeekDay = core.getLocaleFirstWeekDay()
            except:
                pass
        else:
            core.firstWeekDayAuto = False
            core.firstWeekDay = first
        ######
        mode = self.comboWeekYear.get_active()
        if mode==8:
            core.weekNumberModeAuto = True
            core.weekNumberMode = core.getLocaleweekNumberMode()
        else:
            core.weekNumberModeAuto = False
            core.weekNumberMode = mode
        ######
        ui.cellCache.clear() ## Very important, specially when core.primaryMode will be changed
        ######
        ud.updateFormatsBin()
        #################################################### Saving Preferences
        for mod in calTypes:
            mod.save()
        ##################### Saving locale config
        text = ''
        for item in self.localePrefItems:
            text += item.confStr()
        open(locale_man.localeConfPath, 'w').write(text)
        ##################### Saving core config
        text = ''
        text += 'version=%r\n\n'%core.VERSION
        text += 'allPlugList=%s\n\n'%core.getAllPlugListRepr()
        text += 'plugIndex=%r\n'%core.plugIndex
        for item in self.corePrefItems:
            text += item.confStr()
        for key in (
            'firstWeekDayAuto',
            'firstWeekDay',
            'weekNumberModeAuto',
            'weekNumberMode',
            'debugMode',
        ):
            value = eval('core.'+key)
            text += '%s=%r\n'%(key, value)
        open(core.confPath, 'w').write(text)
        ##################### Saving ui config
        text = ''
        for item in self.uiPrefItems:
            text += item.confStr()
        for key in (
            #'localTzHist',## FIXME
            'showYmArrows',
        ):
            value = eval('ui.'+key)
            text += '%s=%r\n'%(key, value)
        text += 'prefPagesOrder=%s\n'%repr(
            tuple(
                [self.notebook.page_num(page) for page in self.prefPages]
            )
        )
        open(ui.confPath, 'w').write(text)
        ##################### Saving here config
        text = ''
        for item in self.gtkPrefItems:
            text += item.confStr()
        text += 'adjustTimeCmd=%r\n'%ud.adjustTimeCmd ## FIXME
        open(ud.confPath, 'w').write(text)
        ################################################### Updating GUI
        ud.windowList.onConfigChange()
        if ui.mainWin:
            """
            if ui.bgUseDesk and ui.bgColor[3]==255:
                msg = gtk.MessageDialog(buttons=gtk.BUTTONS_OK_CANCEL, message_format=_(
                'If you want to have a transparent calendar (and see your desktop),'+\
                'change the opacity of calendar background color!'))
                if msg.run()==gtk.RESPONSE_OK:
                    self.colorbBg.emit('clicked')
                msg.destroy()
            """
            if ui.checkNeedRestart():
                d = gtk.Dialog(_('Need Restart '+APP_DESC), self,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
                    (gtk.STOCK_CANCEL, 0))
                d.set_keep_above(True)
                label = gtk.Label(_('Some preferences need for restart %s to apply.'%APP_DESC))
                label.set_line_wrap(True)
                d.vbox.pack_start(label)
                resBut = d.add_button(_('_Restart'), 1)
                resBut.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH,gtk.ICON_SIZE_BUTTON))
                resBut.grab_default()
                d.vbox.show_all()
                if d.run()==1:
                    core.restart()
                else:
                    d.destroy()
    def updatePrefGui(self):############### Updating Pref Gui (NOT MAIN GUI)
        for opt in self.getAllPrefItems():
            opt.updateWidget()
        ###############################
        if core.firstWeekDayAuto:
            self.comboFirstWD.set_active(7)
        else:
            self.comboFirstWD.set_active(core.firstWeekDay)
        if core.weekNumberModeAuto:
            self.comboWeekYear.set_active(8)
        else:
            self.comboWeekYear.set_active(core.weekNumberMode)
        ###### Plugin Manager
        self.plugTreestore.clear()
        for row in core.getPluginsTable():
            self.plugTreestore.append(row)
        self.plugAddItems = []
        self.plugAddTreestore.clear()
        for (i, desc) in core.getDeletedPluginsTable():
            self.plugAddItems.append(i)
            self.plugAddTreestore.append([desc])
            self.plugButtonAdd.set_sensitive(True)
        ###### Accounts
        self.accountsTreestore.clear()
        for account in ui.eventAccounts:
            self.accountsTreestore.append([account.id, account.enable, account.title])
    #def plugTreevExpose(self, widget, event):
        #self.plugDescCell.set_property('wrap-width', self.plugDescCol.get_width()+2)
    def plugTreevCursorChanged(self, treev):
        cur = treev.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        j = self.plugTreestore[i][0]
        plug = core.allPlugList[j]
        self.plugButtonAbout.set_sensitive(plug.about!=None)
        self.plugButtonConf.set_sensitive(plug.has_config)
    def plugAboutClicked(self, obj=None):
        cur = self.plugTreeview.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        j = self.plugTreestore[i][0]
        plug = core.allPlugList[j]
        if hasattr(plug, 'open_about'):
            return plug.open_about()
        if plug.about==None:
            return
        about = AboutDialog(
            name='',## FIXME
            title=_('About Plugin'),## _('About ')+plug.desc
            authors=plug.authors,
            comments=plug.about,
        )
        about.set_transient_for(self)
        about.connect('delete-event', lambda w, e: w.destroy())
        about.connect('response', lambda w, e: w.destroy())
        #about.set_resizable(True)
        #about.vbox.show_all()## OR about.vbox.show_all() ; about.run()
        openWindow(about)## FIXME
    def plugConfClicked(self, obj=None):
        cur = self.plugTreeview.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        j = self.plugTreestore[i][0]
        plug = core.allPlugList[j]
        if not plug.has_config:
            return
        plug.open_configure()
    def plugExportToIcsClicked(self, menu, plug):
        ExportToIcsDialog(plug.exportToIcs, plug.desc).run()
    def plugTreevRActivate(self, treev, path, col):
        if col.get_title()==_('Description'):##??????????
            self.plugAboutClicked(None) #??????
        #print 'row-activate', path
    def plugTreevButtonPress(self, widget, event):
        b = event.button
        #print 'plugTreevButtonPress', b
        if b==3:
            cur = self.plugTreeview.get_cursor()[0]
            if cur:
                i = cur[0]
                j = self.plugTreestore[i][0]
                plug = core.allPlugList[j]
                menu = gtk.Menu()
                ##
                item = labelStockMenuItem('_About', gtk.STOCK_ABOUT, self.plugAboutClicked)
                item.set_sensitive(bool(plug.about))
                menu.add(item)
                ##
                item = labelStockMenuItem('_Configure', gtk.STOCK_PREFERENCES, self.plugConfClicked)
                item.set_sensitive(plug.has_config)
                menu.add(item)
                ##
                menu.add(labelImageMenuItem(_('Export to %s')%'iCalendar', 'ical-32.png', self.plugExportToIcsClicked, plug))
                ##
                menu.show_all()
                menu.popup(None, None, None, 3, event.time)
            return True
        return False
    def plugAddClicked(self, button):
        ## ???????????????????????????
        ## Reize window to show all texts
        #self.plugAddTreeview.columns_autosize()#??????????
        r, x, y, w, h = self.plugAddTreeview.get_column(0).cell_get_size()
        #print r[2], r[3], x, y, w, h
        self.plugAddDialog.resize(w+30, 75 + 30*len(self.plugAddTreestore))
        ###############
        self.plugAddDialog.run()
        #self.plugAddDialog.present()
        #self.plugAddDialog.show()
    def plugAddDialogClose(self, obj, event=None):
        self.plugAddDialog.hide()
        return True
    def plugTreeviewCellToggled(self, cell, path):
        i = int(path)
        #cur = self.plugTreeview.get_cursor()[0]
        #if cur==None or i!=cur[0]:#?????????
        #    return
        active = not cell.get_active()
        self.plugTreestore[i][1] = active
        cell.set_active(active)
    def plugTreeviewCellToggled2(self, cell, path):
        i = int(path)
        #cur = self.plugTreeview.get_cursor()[0]
        #if cur==None or i!=cur[0]:#?????????
        #    return
        active = not cell.get_active()
        self.plugTreestore[i][2] = active
        cell.set_active(active)
    def plugTreeviewTop(self, button):
        cur = self.plugTreeview.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        t = self.plugTreestore
        if i<=0 or i>=len(t):
            gdk.beep()
            return
        t.prepend(t[i])
        t.remove(t.get_iter(i+1))
        self.plugTreeview.set_cursor(0)
    def plugTreeviewBottom(self, button):
        cur = self.plugTreeview.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        t = self.plugTreestore
        if i<0 or i>=len(t)-1:
            gdk.beep()
            return
        t.append(t[i])
        t.remove(t.get_iter(i))
        self.plugTreeview.set_cursor(len(t)-1)
    def plugTreeviewUp(self, button):
        cur = self.plugTreeview.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        t = self.plugTreestore
        if i<=0 or i>=len(t):
            gdk.beep()
            return
        t.swap(t.get_iter(i-1), t.get_iter(i))
        self.plugTreeview.set_cursor(i-1)
    def plugTreeviewDown(self, button):
        cur = self.plugTreeview.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        t = self.plugTreestore
        if i<0 or i>=len(t)-1:
            gdk.beep()
            return
        t.swap(t.get_iter(i), t.get_iter(i+1))
        self.plugTreeview.set_cursor(i+1)
    def plugTreevDragReceived(self, treev, context, x, y, selec, info, etime):
        t = treev.get_model() #self.plugAddTreestore
        cur = treev.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        dest = treev.get_dest_row_at_pos(x, y)
        if dest == None:
            t.move_after(t.get_iter(i), t.get_iter(len(t)-1))
        elif dest[1] in (gtk.TREE_VIEW_DROP_BEFORE, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
            t.move_before(t.get_iter(i), t.get_iter(dest[0][0]))
        else:
            t.move_after(t.get_iter(i), t.get_iter(dest[0][0]))
    def plugTreeviewDel(self, button):
        cur = self.plugTreeview.get_cursor()[0]
        if cur==None:
            return
        i = cur[0]
        t = self.plugTreestore
        n = len(t)
        if i<0 or i>=n:
            gdk.beep()
            return
        j = t[i][0]
        t.remove(t.get_iter(i))
        ### j
        self.plugAddItems.append(j)
        desc = core.allPlugList[j].desc
        self.plugAddTreestore.append([desc])
        print('deleting', desc)
        self.plugButtonAdd.set_sensitive(True)
        if n>1:
            self.plugTreeview.set_cursor(min(n-2, i))
    def plugAddDialogOK(self, obj):
        cur = self.plugAddTreeview.get_cursor()[0]
        if cur==None:
            gdk.beep()
            return
        i = cur[0]
        j = self.plugAddItems[i]
        cur2 = self.plugTreeview.get_cursor()[0]
        if cur2==None:
            pos = len(self.plugTreestore)
        else:
            pos = cur2[0]+1
        self.plugTreestore.insert(pos, [j, True, False, core.allPlugList[j].desc])
        self.plugAddTreestore.remove(self.plugAddTreestore.get_iter(i))
        self.plugAddItems.pop(i)
        self.plugAddDialog.hide()
        self.plugTreeview.set_cursor(pos)### pos==1- #????????
    def plugAddTreevRActivate(self, treev, path, col):
        self.plugAddDialogOK(None)#???????
    def editAccount(self, index):
        accountId = self.accountsTreestore[index][0]
        account = ui.eventAccounts[accountId]
        account = AccountEditorDialog(account).run()
        if account is None:
            return
        account.save()
        ui.eventAccounts.save()
        self.accountsTreestore[index][2] = account.title
    def accountsEditClicked(self, button):
        cur = self.accountsTreeview.get_cursor()[0]
        if cur==None:
            return
        index = cur[0]
        self.editAccount(index)
    def accountsAddClicked(self, button):
        account = AccountEditorDialog().run()
        if account is None:
            return
        account.save()
        ui.eventAccounts.append(account)
        ui.eventAccounts.save()
        self.accountsTreestore.append([account.id, account.enable, account.title])
    def accountsDelClicked(self, button):
        cur = self.accountsTreeview.get_cursor()[0]
        if cur==None:
            return
        index = cur[0]
        accountId = self.accountsTreestore[index][0]
        account = ui.eventAccounts[accountId]
        if not confirm(_('Do you want to delete account "%s"')%account.title):
            return
        ui.eventAccounts.delete(account)
        del self.accountsTreestore[index]
    def accountsUpClicked(self, button):
        cur = self.accountsTreeview.get_cursor()[0]
        if cur==None:
            return
        index = cur[0]
        t = self.accountsTreestore
        if index<=0 or index>=len(t):
            gdk.beep()
            return
        ui.eventAccounts.moveUp(index)
        ui.eventAccounts.save()
        t.swap(t.get_iter(index-1), t.get_iter(index))
        self.accountsTreeview.set_cursor(index-1)
    def accountsDownClicked(self, button):
        cur = self.accountsTreeview.get_cursor()[0]
        if cur==None:
            return
        index = cur[0]
        t = self.accountsTreestore
        if index<0 or index>=len(t)-1:
            gdk.beep()
            return
        ui.eventAccounts.moveDown(index)
        ui.eventAccounts.save()
        t.swap(t.get_iter(index), t.get_iter(index+1))
        self.accountsTreeview.set_cursor(index+1)
    def accountsTreevRActivate(self, treev, path, col):
        index = path[0]
        self.editAccount(index)
    def accountsTreevButtonPress(self, widget, event):
        b = event.button
        if b==3:
            cur = self.accountsTreeview.get_cursor()[0]
            if cur:
                index = cur[0]
                accountId = self.accountsTreestore[index][0]
                account = ui.eventAccounts[accountId]
                menu = gtk.Menu()
                ##
                ## FIXME
                ##
                #menu.show_all()
                #menu.popup(None, None, None, 3, event.time)
            return True
        return False
    def accountsTreeviewCellToggled(self, cell, path):
        index = int(path)
        active = not cell.get_active()
        ###
        accountId = self.accountsTreestore[index][0]
        account = ui.eventAccounts[accountId]
        account.enable = active
        account.save()
        ###
        self.accountsTreestore[index][1] = active
        cell.set_active(active)









