#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, os, time
from os.path import join, isfile, dirname
from math import pi, floor, ceil, sqrt, sin, cos, tan, asin, acos, atan, atan2

_mypath = __file__
if _mypath.endswith('.pyc'):
    _mypath = _mypath[:-1]
dataDir = os.path.dirname(_mypath) + '/pray_times_files/'
rootDir = '/usr/share/starcal2'

sys.path.insert(0, dataDir) ## FIXME
sys.path.insert(0, rootDir) ## FIXME


from scal2.paths import *
from prayTimesBackend import PrayTimes, timeNames, methodsList

## DO NOT IMPORT core IN PLUGINS
from scal2.locale import tr as _
from scal2.plugin_man import BasePlugin


import gettext
import gtk


confPath = join(plugConfDir, 'pray_times')
earthR = 6370

####################################################




####################### Methods and Classes ##################
sind = lambda x: sin(pi/180.0*x)
cosd = lambda x: cos(pi/180.0*x)
#tand = lambda x: tan(pi/180.0*x)
#asind = lambda x: asin(x)*180.0/pi
#acosd = lambda x: acos(x)*180.0/pi
#atand = lambda x: atan(x)*180.0/pi
#loc2hor = lambda z, delta, lat: acosd((cosd(z)-sind(delta)*sind(lat))/cosd(delta)/cosd(lat))/15.0

def earthDistance(lat1, lng1, lat2, lng2):
    #if lat1==lat2 and lng1==lng2:
    #    return 0
    dx = lng2 - lng1
    if dx<0:
        dx += 360
    if dx>180:
        dx = 360-dx
    ####
    dy = lat2 - lat1
    if dy<0:
        dy += 360
    if dy>180:
        dy = 360-dy
    ####
    deg = acos(cosd(dx)*cosd(dy))
    if deg>pi:
        deg = 2*pi-deg
    return deg*earthR
    #return ang*180/pi
    
def hms(x):
    (days, s) = divmod(int(x), 24*3600)
    (m, s) = divmod(s, 60)
    (h, m) = divmod(m, 60)
    return '%d:%.2d:%.2d'%(h, m, s)

def hm(x):
    (days, m) = divmod(int(x/60), 24*60)
    (h, m) = divmod(m, 60)
    return '%d:%.2d'%(m, s)




class LocationDialog(gtk.Dialog):
    EXIT_OK     = 0
    EXIT_CANCEL = 1
    def __init__(self, maxResults=200):
        gtk.Dialog.__init__(self)
        self.maxResults = maxResults
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
                    (city, lat, lng) = p[2:5]
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
        cancelB = self.add_button(gtk.STOCK_CANCEL, self.EXIT_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, self.EXIT_OK)
        #if autoLocale:
        cancelB.set_label(_('_Cancel'))
        cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON))
        okB.set_label(_('_OK'))
        okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON))
        self.vbox.show_all()
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
            (j, s) = self.trees[i]
            self.entry_edit_name.set_text(s)
            self.spin_lat.set_value(self.cityData[j][2])
            self.spin_lng.set_value(self.cityData[j][3])
            self.lowerLabel.set_label(_('%s kilometers from %s')%(0.0, s))
    def edit_checkb_clicked(self, checkb):
        active = checkb.get_active()
        self.vbox_edit.set_sensitive(active)
        if not active:
            cur = self.treev.get_cursor()[0]
            if cur==None:
                name = ''
                lat = 0
                lng = 0
            else:
                i = cur[0]
                j = self.trees[i][0]
                (name, lname, lat, lng) = self.cityData[j]
            self.entry_edit_name.set_text(lname)
            self.spin_lat.set_value(lat)
            self.spin_lng.set_value(lng)
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
    entry_changed = lambda self, entry: self.update_list(entry.get_text())
    def run(self):
        ex = gtk.Dialog.run(self)
        self.hide()
        if ex==self.EXIT_OK:
            if not self.checkbEdit.get_active() and self.treev.get_cursor()[0]==None:#?????????????????
                return None
            else:
                return (self.entry_edit_name.get_text(), self.spin_lat.get_value(), self.spin_lng.get_value())
        else:
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
            (self.locName, self.lat, self.lng) = res
            self.set_label(self.locName)



class TextPlug(BasePlugin):
    ## all options (except "enable" and "show_date") will be saved in file confPath
    def __init__(self, enable=True, show_date=False):
        BasePlugin.__init__(self, path=_mypath, mode='gregorian', desc=_('Islamic Pray Times'),
                            enable=enable, show_date=show_date, last_day_merge=False)
        self.external = True
        self.name = _('Islamic Pray Times')
        self.about = _('Islamic Pray Times') ## FIXME
        self.has_config = True
        ##############
        ## here load config ## FIXME
        locName = 'Tehran'
        lat = 35.705
        lng = 51.4216
        method = 'Tehran'
        imsak = 10 ## minutes before Fajr (Morning Azan)
        #asrMode=ASR_STANDARD
        #highLats='NightMiddle'
        #timeFormat='24h'
        shownTimeNames = ('fajr', 'sunrise', 'dhuhr', 'maghrib', 'midnight')
        ####
        if isfile(confPath):
            exec(open(confPath).read())
        #######
        self.locName = locName
        self.imsak = imsak
        self.ptObj = PrayTimes(lat, lng, methodName=method, imsak='%d min'%imsak)
        self.shownTimeNames = shownTimeNames
        #######
        self.confDialog = gtk.Dialog()
        self.confDialog.set_title(_('Pray Times') + ' - ' + _('Configuration'))
        group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ###
        hbox = gtk.HBox()
        label = gtk.Label(_('Location'))
        group.add_widget(label)
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.locButton = LocationButton(locName, lat, lng)
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
    def updateConfVars(self):
        self.locName = self.locButton.locName
        self.ptObj.lat = self.locButton.lat
        self.ptObj.lng = self.locButton.lng
        self.ptObj.method = methodsList[self.methodCombo.get_active()]
        self.shownTimeNames = [row[2] for row in self.shownTimesTreestore if row[0]]
        self.imsak = int(self.imsakSpin.get_value())
        self.ptObj.imsak = '%d min'%self.imsak
    def saveConfig(self):
        text = 'locName=%r\n'%self.locName
        text += 'lat=%r\n'%self.ptObj.lat
        text += 'lng=%r\n'%self.ptObj.lng
        text += 'method=%r\n'%self.ptObj.method.name
        text += 'shownTimeNames=%r\n'%self.shownTimeNames
        text += 'imsak=%r\n'%self.imsak
        open(confPath, 'w').write(text)
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
    #def date_change_after(self, widget, year, month, day):
    #    self.dialog.menuCell.add(self.menuitem)
    #    self.menu_unmap_id = self.dialog.menuCell.connect('unmap', self.menu_unmap)
    #def menu_unmap(self, menu):
    #    menu.remove(self.menuitem)
    #    menu.disconnect(self.menu_unmap_id)
    def get_text(self, year, month, day):
        times = self.ptObj.getTimes(year, month, day)
        return '\t'.join(['%s: %s'%(_(name.capitalize()), times[name]) for name in self.shownTimeNames])
    def open_configure(self):
        self.confDialog.run()
    def open_about(self):
        about = gtk.AboutDialog()
        about.set_name(self.name) ## or set_program_name
        #about.set_version(VERSION)
        about.set_title(_('About')+' '+self.name) ## must call after set_name and set_version !
        about.set_authors([
            _('Hamid Zarrabi-Zadeh <zarrabi@scs.carleton.ca>'),
            _('Saeed Rasooli <saeed.gnu@gmail.com>')
        ])
        #about.set_comments(_(''))
        about.connect('delete-event', lambda w, e: about.destroy())
        #about.connect('response', lambda w: about.hide())
        #about.set_skip_taskbar_hint(True)
        #buttonbox = about.vbox.get_children()[1]
        ##buttonbox.set_homogeneous(False)
        ##buttonbox.set_layout(gtk.BUTTONBOX_SPREAD)
        #buttons = buttonbox.get_children()## List of buttons of about dialogs
        #buttons[1].set_label(_('C_redits'))
        #buttons[2].set_label(_('_Close'))
        #buttons[2].set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE,gtk.ICON_SIZE_BUTTON))
        about.run()
        about.destroy()




if __name__=='__main__':
    #sys.path.insert(0, '/usr/share')
    #from scal2 import core
    #from scal2.locale import rtl
    #if rtl:
    #    gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)
    dialog = LocationDialog()
    dialog.connect('delete-event', gtk.main_quit)
    #dialog.connect('response', gtk.main_quit)
    dialog.resize(600, 600)
    print dialog.run()
    #gtk.main()
    



