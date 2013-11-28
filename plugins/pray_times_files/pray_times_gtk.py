# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com>
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

import os
from os.path import dirname

from scal2 import locale_man
from scal2.locale_man import tr as _
from pray_times_backend import timeNames, methodsList

import gtk

from scal2.ui_gtk.app_info import popenFile

buffer_get_text = lambda b: b.get_text(b.get_start_iter(), b.get_end_iter())
buffer_select_all = lambda b: b.select_range(b.get_start_iter(), b.get_end_iter())


dataDir = dirname(__file__)
earthR = 6370

class AboutDialog(gtk.AboutDialog):## I had to duplicate!!
    def __init__(self, name='', version='', title='', authors=[], comments='', license='', website=''):
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
            self.set_website(website) ## A palin label (not link)
        #if ui.autoLocale:
        buttonbox = self.vbox.get_children()[1]
        buttons = buttonbox.get_children()## List of buttons of about dialogs
        buttons[1].set_label(_('C_redits'))
        buttons[2].set_label(_('_Close'))
        buttons[2].set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE,gtk.ICON_SIZE_BUTTON))
        buttons[0].set_label(_('_License'))

class LocationDialog(gtk.Dialog):
    EXIT_OK     = 0
    EXIT_CANCEL = 1
    def __init__(self, maxResults=200):
        gtk.Dialog.__init__(self)
        self.set_title(_('Location'))
        self.maxResults = maxResults
        ###############
        cancelB = self.add_button(gtk.STOCK_CANCEL, self.EXIT_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, self.EXIT_OK)
        #if autoLocale:
        cancelB.set_label(_('_Cancel'))
        cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON))
        okB.set_label(_('_OK'))
        okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON))
        self.okB = okB
        ###############
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Search Cities:')), 0, 0)
        entry = gtk.Entry()
        hbox.pack_start(entry, 1, 1)
        entry.connect('changed', self.entry_changed)
        self.vbox.pack_start(hbox, 0, 0)
        ######################
        treev = gtk.TreeView()
        treev.set_headers_clickable(False)
        treev.set_headers_visible(False)
        trees = gtk.ListStore(int, str)
        treev.set_model(trees)
        swin = gtk.ScrolledWindow()
        swin.add(treev)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(swin, 1, 1)
        self.treev = treev
        self.trees = trees
        treev.connect('cursor-changed', self.treev_cursor_changed)
        #########
        #cell = gtk.CellRendererText()
        #col = gtk.TreeViewColumn('Index', cell, text=0)
        #col.set_resizable(True)## No need!
        #treev.append_column(col)
        ########
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn('City', cell, text=1)
        #col.set_resizable(True)## No need!
        treev.append_column(col)
        #########
        treev.set_search_column(1)
        ###########
        frame = gtk.Frame()
        checkb = gtk.CheckButton(_('Edit Manually'))
        checkb.connect('clicked', self.edit_checkb_clicked)
        frame.set_label_widget(checkb)
        self.checkbEdit = checkb
        vbox = gtk.VBox()
        group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Name:'))
        hbox.pack_start(label, 0, 0)
        group.add_widget(label)
        label.set_alignment(0, 0.5)
        entry = gtk.Entry()
        hbox.pack_start(entry, 1, 1)
        vbox.pack_start(hbox, 0, 0)
        self.entry_edit_name = entry
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Latitude:'))
        hbox.pack_start(label, 0, 0)
        group.add_widget(label)
        label.set_alignment(0, 0.5)
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(-180, 180)
        spin.set_digits(3)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        hbox.pack_start(spin, 0, 0)
        vbox.pack_start(hbox, 0, 0)
        self.spin_lat = spin
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Longitude:'))
        hbox.pack_start(label, 0, 0)
        group.add_widget(label)
        label.set_alignment(0, 0.5)
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(-180, 180)
        spin.set_digits(3)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        hbox.pack_start(spin, 0, 0)
        vbox.pack_start(hbox, 0, 0)
        self.spin_lng = spin
        ####
        hbox = gtk.HBox()
        self.lowerLabel = gtk.Label('')
        hbox.pack_start(self.lowerLabel, 1, 1)
        self.lowerLabel.set_alignment(0, 0.5)
        button = gtk.Button(_('Calculate Nearest City'))
        button.connect('clicked', self.calc_clicked)
        hbox.pack_start(button, 0, 0)
        vbox.pack_start(hbox, 0, 0)
        ####
        vbox.set_sensitive(False)
        frame.add(vbox)
        self.vbox_edit = vbox
        self.vbox.pack_start(frame, 0, 0)
        ###
        self.vbox.show_all()
        #########
        lines = file(dataDir+'/locations.txt').read().split('\n')
        cityData = []
        country = ''
        for l in lines:
            p = l.split('\t')
            if len(p)<2:
                #print p
                continue
            if p[0]=='':
                if p[1]=='':
                    city, lat, lng = p[2:5]
                    #if country=='Iran':
                    #    print city
                    if len(p)>4:
                        cityData.append((
                            country + '/' + city,
                            _(country) + '/' + _(city),
                            float(lat),
                            float(lng)
                        ))
                    else:
                        print country, p
                else:
                    country = p[1]

        self.cityData = cityData
        self.update_list()
    def calc_clicked(self, button):
        lat = self.spin_lat.get_value()
        lng = self.spin_lng.get_value()
        md = earthR*2*pi
        city = ''
        for (name, lname, lat2, lng2) in self.cityData:
            d = earthDistance(lat, lng, lat2, lng2)
            assert d>=0
            if d<md:
                md = d
                city = lname
        self.lowerLabel.set_label(_('%s kilometers from %s')%(md, city))
    def treev_cursor_changed(self, treev):
        c = treev.get_cursor()[0]
        if c!=None:
            i = c[0]
            j, s = self.trees[i]
            self.entry_edit_name.set_text(s)
            self.spin_lat.set_value(self.cityData[j][2])
            self.spin_lng.set_value(self.cityData[j][3])
            self.lowerLabel.set_label(_('%s kilometers from %s')%(0.0, s))
        self.okB.set_sensitive(True)
    def edit_checkb_clicked(self, checkb):
        active = checkb.get_active()
        self.vbox_edit.set_sensitive(active)
        if not active:
            cur = self.treev.get_cursor()[0]
            if cur==None:
                lname = ''
                lat = 0
                lng = 0
            else:
                i = cur[0]
                j = self.trees[i][0]
                name, lname, lat, lng = self.cityData[j]
            self.entry_edit_name.set_text(lname)
            self.spin_lat.set_value(lat)
            self.spin_lng.set_value(lng)
        self.updateOkButton()
    updateOkButton = lambda self: self.okB.set_sensitive(
        bool(self.treev.get_cursor()[0] or self.checkbEdit.get_active())
    )
    def update_list(self, s=''):
        s = s.lower()
        t = self.trees
        t.clear()
        d = self.cityData
        n = len(d)
        if s=='':
            for i in range(n):
                t.append((i, d[i][0]))
        else:## here check also translations
            mr = self.maxResults
            r = 0
            for i in range(n):
                if s in (d[i][0]+'\n'+d[i][1]).lower():
                    t.append((i, d[i][1]))
                    r += 1
                    if r>=mr:
                        break
        self.okB.set_sensitive(self.checkbEdit.get_active())
    entry_changed = lambda self, entry: self.update_list(entry.get_text())
    def run(self):
        ex = gtk.Dialog.run(self)
        self.hide()
        if ex==self.EXIT_OK:
            if self.checkbEdit.get_active() or self.treev.get_cursor()[0]!=None:#?????????????????
                return (self.entry_edit_name.get_text(), self.spin_lat.get_value(), self.spin_lng.get_value())
        return None


class LocationButton(gtk.Button):
    def __init__(self, locName, lat, lng):
        gtk.Button.__init__(self, locName)
        self.setLocation(locName, lat, lng)
        self.dialog = LocationDialog()
        ####
        self.connect('clicked', self.onClicked)
    def setLocation(self, locName, lat, lng):
        self.locName = locName
        self.lat = lat
        self.lng = lng
    def onClicked(self, widget):
        res = self.dialog.run()
        if res:
            self.locName, self.lat, self.lng = res
            self.set_label(self.locName)




class TextPlugUI:
    def makeWidget(self):
        self.confDialog = gtk.Dialog()
        self.confDialog.set_title(_('Pray Times') + ' - ' + _('Configuration'))
        group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('Location'))
        group.add_widget(label)
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.locButton = LocationButton(self.locName, self.ptObj.lat, self.ptObj.lng)
        hbox.pack_start(self.locButton, 0, 0)
        self.confDialog.vbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('Calculation Method'))
        group.add_widget(label)
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.methodCombo = gtk.combo_box_new_text()
        for methodObj in methodsList:
            self.methodCombo.append_text(_(methodObj.desc))
        hbox.pack_start(self.methodCombo, 0, 0)
        self.confDialog.vbox.pack_start(hbox, 0, 0)
        #######
        treev = gtk.TreeView()
        treev.set_headers_clickable(False)
        treev.set_headers_visible(False)
        trees = gtk.ListStore(bool, str, str)## enable, desc, name
        treev.set_model(trees)
        ###
        cell = gtk.CellRendererToggle()
        #cell.set_property('activatable', True)
        cell.connect('toggled', self.shownTreeviewCellToggled)
        col = gtk.TreeViewColumn(_('Enable'), cell)
        col.add_attribute(cell, 'active', 0)
        #cell.set_active(False)
        col.set_resizable(True)
        treev.append_column(col)
        ###
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Name'), cell, text=1)## desc, not name
        treev.append_column(col)
        ###
        self.shownTimesTreestore = trees
        for name in timeNames:
            trees.append([True, _(name.capitalize()), name])
        frame = gtk.Frame(_('Shown Times'))
        frame.add(treev)
        self.confDialog.vbox.pack_start(frame, 0, 0)
        ######
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Imsak')), 0, 0)
        spin = gtk.SpinButton()
        spin.set_increments(1, 5)
        spin.set_range(0, 99)
        spin.set_digits(0)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        self.imsakSpin = spin
        hbox.pack_start(spin, 0, 0)
        hbox.pack_start(gtk.Label(' '+_('minutes before fajr')), 0, 0)
        self.confDialog.vbox.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Seperator')), 0, 0)
        textview = gtk.TextView()
        textview.set_wrap_mode(gtk.WRAP_CHAR)
        if locale_man.rtl:
            textview.set_direction(gtk.TEXT_DIR_RTL)
        self.sepView = textview
        self.sepBuff = textview.get_buffer()
        frame = gtk.Frame()
        frame.set_border_width(4)
        frame.add(textview)
        hbox.pack_start(frame, 1, 1)
        self.confDialog.vbox.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        frame = gtk.Frame()
        #frame.set_border_width(5)
        frame.set_label(_('Azan'))
        hbox.set_border_width(5)
        vboxFrame = gtk.VBox()
        vboxFrame.set_border_width(10)
        #####
        sgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        #sgroupFcb = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ####
        hbox1 = gtk.HBox()
        self.preAzanEnableCheck = gtk.CheckButton(_('Play Pre-Azan Sound'))
        sgroup.add_widget(self.preAzanEnableCheck)
        hbox2 = gtk.HBox()
        self.preAzanEnableCheck.box = hbox2
        self.preAzanEnableCheck.connect('clicked', lambda w: w.box.set_sensitive(w.get_active()))
        hbox1.pack_start(self.preAzanEnableCheck, 0, 0)
        hbox2.pack_start(gtk.Label('  '), 0, 0)
        self.preAzanFileButton = gtk.FileChooserButton(_('Pre-Azan Sound'))
        #sgroupFcb.add_widget(self.preAzanFileButton)
        hbox2.pack_start(self.preAzanFileButton, 1, 1)
        hbox2.pack_start(gtk.Label('  '), 0, 0)
        ##
        spin = gtk.SpinButton()
        spin.set_increments(1, 5)
        spin.set_range(0, 60)
        spin.set_digits(2)
        spin.set_direction(gtk.TEXT_DIR_LTR)
        self.preAzanMinutesSpin = spin
        hbox2.pack_start(spin, 0, 0)
        ##
        hbox2.pack_start(gtk.Label('  '), 0, 0)
        hbox2.pack_start(gtk.Label(_('minutes before azan')), 0, 0)
        hbox1.pack_start(hbox2, 1, 1)
        vboxFrame.pack_start(hbox1, 0, 0)
        #####
        hbox1 = gtk.HBox()
        self.azanEnableCheck = gtk.CheckButton(_('Play Azan Sound'))
        sgroup.add_widget(self.azanEnableCheck)
        hbox2 = gtk.HBox()
        self.azanEnableCheck.box = hbox2
        self.azanEnableCheck.connect('clicked', lambda w: w.box.set_sensitive(w.get_active()))
        hbox1.pack_start(self.azanEnableCheck, 0, 0)
        hbox2.pack_start(gtk.Label('  '), 0, 0)
        self.azanFileButton = gtk.FileChooserButton(_('Azan Sound'))
        #sgroupFcb.add_widget(self.azanFileButton)
        hbox2.pack_start(self.azanFileButton, 1, 1)
        #hbox2.pack_start(gtk.Label(''), 1, 1)
        ##
        hbox1.pack_start(hbox2, 1, 1)
        vboxFrame.pack_start(hbox1, 0, 0)
        #####
        frame.add(vboxFrame)
        hbox.pack_start(frame, 1, 1)
        self.confDialog.vbox.pack_start(hbox, 0, 0)
        ######
        self.updateConfWidget()
        ###
        cancelB = self.confDialog.add_button(gtk.STOCK_CANCEL, 1)
        okB = self.confDialog.add_button(gtk.STOCK_OK, 3)
        #if autoLocale:
        cancelB.set_label(_('_Cancel'))
        cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON))
        okB.set_label(_('_OK'))
        okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON))
        cancelB.connect('clicked', self.confDialogCancel)
        okB.connect('clicked', self.confDialogOk)
        ###
        self.confDialog.vbox.show_all()
        ##############
        '''
        submenu = gtk.Menu()
        submenu.add(gtk.MenuItem('Item 1'))
        submenu.add(gtk.MenuItem('Item 2'))
        #self.submenu = submenu
        self.menuitem = gtk.MenuItem('Owghat')
        self.menuitem.set_submenu(submenu)
        self.menuitem.show_all()
        '''
        self.dialog = None
    def updateConfWidget(self):
        self.locButton.setLocation(self.locName, self.ptObj.lat, self.ptObj.lng)
        self.methodCombo.set_active(methodsList.index(self.ptObj.method))
        ###
        for row in self.shownTimesTreestore:
            row[0] = (row[2] in self.shownTimeNames)
        ###
        self.imsakSpin.set_value(self.imsak)
        self.sepBuff.set_text(self.sep)
        buffer_select_all(self.sepBuff)
        ###
        self.preAzanEnableCheck.set_active(self.preAzanEnable)
        self.preAzanEnableCheck.box.set_sensitive(self.preAzanEnable)
        if self.preAzanFile:
            self.preAzanFileButton.set_filename(self.preAzanFile)
        self.preAzanMinutesSpin.set_value(self.preAzanMinutes)
        ##
        self.azanEnableCheck.set_active(self.azanEnable)
        self.azanEnableCheck.box.set_sensitive(self.azanEnable)
        if self.azanFile:
            self.azanFileButton.set_filename(self.azanFile)
    def updateConfVars(self):
        self.locName = self.locButton.locName
        self.ptObj.lat = self.locButton.lat
        self.ptObj.lng = self.locButton.lng
        self.ptObj.method = methodsList[self.methodCombo.get_active()]
        self.shownTimeNames = [row[2] for row in self.shownTimesTreestore if row[0]]
        self.imsak = int(self.imsakSpin.get_value())
        self.sep = buffer_get_text(self.sepBuff)
        self.ptObj.imsak = '%d min'%self.imsak
        ###
        self.preAzanEnable = self.preAzanEnableCheck.get_active()
        self.preAzanFile = self.preAzanFileButton.get_filename()
        self.preAzanMinutes = self.preAzanMinutesSpin.get_value()
        ##
        self.azanEnable = self.azanEnableCheck.get_active()
        self.azanFile = self.azanFileButton.get_filename()
    def confDialogCancel(self, widget):
        self.confDialog.hide()
        self.updateConfWidget()
    def confDialogOk(self, widget):
        self.confDialog.hide()
        self.updateConfVars()
        self.saveConfig()
    def shownTreeviewCellToggled(self, cell, path):
        i = int(path)
        active = not cell.get_active()
        self.shownTimesTreestore[i][0] = active
        cell.set_active(active)
    def set_dialog(self, dialog):
        self.dialog = dialog
    def open_configure(self):
        self.confDialog.run()
    def open_about(self):
        about = AboutDialog(
            name=self.name,
            title=_('About')+' '+self.name,
            authors=[
                _('Hamid Zarrabi-Zadeh <zarrabi@scs.carleton.ca>'),
                _('Saeed Rasooli <saeed.gnu@gmail.com>')
            ],
        )
        about.connect('delete-event', lambda w, e: about.destroy())
        #about.connect('response', lambda w: about.hide())
        #about.set_skip_taskbar_hint(True)
        about.run()
        about.destroy()









