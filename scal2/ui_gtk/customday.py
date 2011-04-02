# -*- coding: utf-8 -*-
#    
#    Copyright (C) 2007  Mola Pahnadayan
#    Copyright (C) 2009-2010  Saeed Rasooli <saeed.gnu@gmail.com> (ilius) 
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
#    Or on Debian systems, from /usr/share/common-licenses/GPL

import time
#print time.time(), __file__

import os, sys

from scal2.locale import langSh
from scal2.locale import tr as _

from scal2 import core
from scal2.core import pixDir, convert, numLocale

from scal2 import ui
from scal2.ui import getElementText

from scal2.ui_gtk.mywidgets.multi_spin_box import DateBox, TimeBox
from scal2.ui_gtk import player

from xml.dom.minidom import getDOMImplementation, parse
from xml.parsers.expat import ExpatError

import gtk
from gtk import gdk




class CustomDayDialog(gtk.Window):
  def __init__(self, main, month=None, day=None):
    self.main = main
    gtk.Window.__init__(self)
    self.set_title(_('Add Custom Day'))
    self.connect('delete-event', lambda wid, ev: self.hide())
    winVbox = gtk.VBox()
    self.add(winVbox)
    ##############################################
    """
    hbox = gtk.HBox(spacing=3)
    hbox.pack_start(gtk.Label(_('Day Type')), 0, 0)
    combo1 = gtk.combo_box_new_text()
    for item in ui.customdayModes:
      combo1.append_text(item[0])
    combo1.set_active(3)
    combo1.connect('changed', lambda wid: self.cbTime.set_active(wid.get_active()>3))
    hbox.pack_start(combo1, 0, 0)
    ##
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(gtk.Label(_('Date Mode')), 0, 0)
    combo2 = gtk.combo_box_new_text()
    for item in datesModeDesc:
      combo2.append_text(item)
    #combo2.set_active(core.primaryMode)
    combo2.set_active(ui.shownCals[0]['mode'])
    combo2.set_sensitive(False)### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    combo2.connect('changed', self.dateModeChanged)
    hbox.pack_start(combo2, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    winVbox.pack_start(hbox, 0, 0)
    self.comboDayType = combo1
    self.comboDateMode = combo2
    #self.hbox1 = hbox"""
    hbox = gtk.HBox(spacing=3)
    hbox.pack_start(gtk.Label(_('Day Type')), 0, 0)
    ##combo1 = gtk.combo_box_new_text()
    ls = gtk.ListStore(gdk.Pixbuf, str)
    combo1 = gtk.ComboBox(ls)
    ###
    cell = gtk.CellRendererPixbuf()
    combo1.pack_start(cell, False)
    combo1.add_attribute(cell, 'pixbuf', 0)  
    ###
    cell = gtk.CellRendererText()
    combo1.pack_start(cell, True)
    combo1.add_attribute(cell, 'text', 1)  
    ###
    for item in ui.customdayModes:
      ##combo1.append_text(item[0])
      if item[1]==None:
        pix = item[1]
      else:
        pix = gdk.pixbuf_new_from_file('%s%s%s'%(pixDir,os.sep,item[1]))
      ls.append([pix, item[0]])
    ###
    combo1.set_active(3)
    combo1.connect('changed', lambda wid: self.cbTime.set_active(wid.get_active()>3))
    hbox.pack_start(combo1, 0, 0)
    ##
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(gtk.Label(_('Date Mode')), 0, 0)
    combo2 = gtk.combo_box_new_text()
    for m in core.modules:
      combo2.append_text(_(m.desc))
    #combo2.set_active(core.primaryMode)
    combo2.set_active(ui.shownCals[0]['mode'])
    combo2.set_sensitive(False)### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    combo2.connect('changed', self.dateModeChanged)
    hbox.pack_start(combo2, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    winVbox.pack_start(hbox, 0, 0)
    self.comboDayType = combo1
    self.comboDateMode = combo2
    #self.hbox1 = hbox
    ############################################
    hbox = gtk.HBox(spacing=4)
    hbox.pack_start(gtk.Label(_('Comment')), 0, 0)
    self.entryComment = gtk.Entry()
    hbox.pack_start(self.entryComment, 1, 1)
    winVbox.pack_start(hbox, 0, 0)
    #################################
    hbox = gtk.HBox(spacing=3)
    cbY = gtk.CheckButton()
    cbY.set_active(False)
    #hbox.pack_start(cbY, 0, 0) ### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #hbox.pack_start(gtk.Label(_('Year')), 0, 0) ### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    spinY=gtk.SpinButton()
    spinY.set_increments(1, 10)
    spinY.set_range(0, 10000)
    spinY.set_direction(gtk.TEXT_DIR_LTR)
    spinY.set_width_chars(4)
    self.spinY = spinY
    cbY.connect('clicked', lambda wid: self.spinY.set_sensitive(wid.get_active()))
    #hbox.pack_start(spinY, 0, 0)### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #hbox.pack_start(gtk.Label(''), 1, 1)### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    hbox.pack_start(gtk.Label(_('Month')), 0, 0)
    combo3 = gtk.combo_box_new_text()
    module = core.modules[core.primaryMode] ## mode ????????
    for m in range(module.getMonthsInYear(None)):
      combo3.append_text(_(module.getMonthName(m+1, None)))
    combo3.set_active(0)
    hbox.pack_start(combo3, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(gtk.Label(_('Day')), 0, 0)
    spinD=gtk.SpinButton()
    spinD.set_increments(1, 5)
    spinD.set_range(1, 31)
    spinD.set_direction(gtk.TEXT_DIR_LTR)
    spinD.set_width_chars(2)
    hbox.pack_start(spinD, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    winVbox.pack_start(hbox, 0, 0)
    self.comboMonth = combo3
    self.spinDay = spinD
    self.hbox2 = hbox
    ##################################################3
    exp = gtk.Expander(label='<b>%s</b>'%_('Advanced'))
    exp.set_use_markup(True)
    vbox = gtk.VBox()
    ############
    hbox = gtk.HBox(spacing=3)
    hbox.pack_start(gtk.Label(_('Duration As')), 0, 0)
    combo = gtk.combo_box_new_text()
    combo.append_text(_('Year, Month and Day'))
    combo.append_text(_('WeekDay'))
    combo.append_text(_('Specific Length'))
    hbox.pack_start(combo, 0, 0)
    item0 = gtk.combo_box_entry_new_text()
    item1 = gtk.combo_box_new_text()
    for i in range(7):
      item1.append_text(core.weekDayName[i])
    item1.set_active(0)
    item2 = gtk.HBox(spacing=3)
    self.spinDLen = gtk.SpinButton()
    self.spinDLen.set_increments(1, 10)
    self.spinDLen.set_range(0, 10000)
    item2.pack_start(self.spinDLen, 0, 0)
    item2.pack_start(gtk.Label('%s %s'%(_('Day'),_('and'))), 0, 0)
    self.tboxDLen = TimeBox(hms=time.localtime()[3:6], lang=langSh)
    item2.pack_start(self.tboxDLen, 0, 0)
    hbox.pack_start(item0, 0, 0)
    hbox.pack_start(item1, 0, 0)
    hbox.pack_start(item2, 0, 0)
    self.durItems = (item0, item1, item2)
    combo.connect('changed', self.comboDurChanged)
    self.comboDur = combo
    vbox.pack_start(hbox)
    ###########
    hbox = gtk.HBox(spacing=3)
    label = gtk.Label(_('Start Date'))
    label.set_property('width-request', 90)
    label.set_justify(gtk.JUSTIFY_LEFT)
    hbox.pack_start(label, 0, 0)
    self.dboxStart = DateBox(lang=langSh)
    hbox.pack_start(self.dboxStart, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(gtk.Label(_('Time')), 0, 0)
    self.tboxStart = TimeBox(hms=time.localtime()[3:6], lang=langSh)
    hbox.pack_start(self.tboxStart, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    vbox.pack_start(hbox, 0, 0)
    ###########
    hbox = gtk.HBox(spacing=3)
    self.cbDurEnd = gtk.CheckButton(_('End Date'))
    self.cbDurEnd.set_property('width-request', 90)
    hbox.pack_start(self.cbDurEnd, 0, 0)
    self.dboxEnd = DateBox(lang=langSh)
    hbox.pack_start(self.dboxEnd, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(gtk.Label(_('Time')), 0, 0)
    self.tboxEnd = TimeBox(hms=time.localtime()[3:6], lang=langSh)
    hbox.pack_start(self.tboxEnd, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    vbox.pack_start(hbox, 0, 0)
    ###########
    exp.add(vbox)
    exp.connect('notify::expanded', lambda wid, event: self.hbox2.set_sensitive(not wid.get_expanded()))
    #winVbox.pack_start(exp, 0, 0)  ### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #self.exp = exp
    ################################
    hbox = gtk.HBox(spacing=3)
    hboxi = gtk.HBox(spacing=3)
    self.cbTime = gtk.CheckButton(_('Time'))
    self.cbTime.connect('clicked', lambda widget: hboxi.set_sensitive(widget.get_active()))
    hbox.pack_start(self.cbTime, 0, 0)
    self.tbox = TimeBox(hms=time.localtime()[3:6], lang=langSh)
    hboxi.pack_start(self.tbox, 0, 0)
    hboxi.pack_start(gtk.Label(''), 1, 1)
    self.cbNotify = gtk.CheckButton(_('Remind Window'))
    hboxi.pack_start(self.cbNotify, 0, 0)
    hboxi.pack_start(gtk.Label(''), 1, 1)
    self.cbAlarm = gtk.CheckButton(_('Alarm'))
    hboxi.pack_start(self.cbAlarm, 0, 0)
    self.fcbAlarm = gtk.FileChooserButton(_('Select Alarm Sound'))
    hboxi.pack_start(self.fcbAlarm, 0, 0)
    hboxi.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(hboxi, 1, 1)
    hboxi.set_sensitive(False)
    #self.cbTime.set_active(False)
    #self.comboDayType.set_active(0)
    #winVbox.pack_start(hbox, 0, 0)  ### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #self.hbox3 = hbox
    ################################
    butBox = gtk.HButtonBox()
    butBox.set_layout(gtk.BUTTONBOX_END)
    self.but_add = gtk.Button(stock=gtk.STOCK_ADD)
    self.but_edit = gtk.Button(stock=gtk.STOCK_EDIT)
    self.but_del = gtk.Button(stock=gtk.STOCK_DELETE)
    self.but_ok = gtk.Button(stock=gtk.STOCK_OK)
    if ui.autoLocale:
      self.but_add.set_label(_('_Add'))
      self.but_add.set_use_underline(True)
      self.but_add.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD,
                             gtk.ICON_SIZE_BUTTON))
      ##########
      self.but_edit.set_label(_('_Edit'))
      self.but_edit.set_use_underline(True)
      self.but_edit.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
                              gtk.ICON_SIZE_BUTTON))
      ##########
      self.but_del.set_label(_('_Delete'))
      self.but_del.set_use_underline(True)
      self.but_del.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE,
                             gtk.ICON_SIZE_BUTTON))
      #########
      self.but_ok.set_label(_('_OK'))
      self.but_ok.set_use_underline(True)
      self.but_ok.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,
                            gtk.ICON_SIZE_BUTTON))
    butBox.add(self.but_add)
    butBox.add(self.but_edit)
    butBox.add(self.but_del)
    winVbox.pack_start(butBox, 0, 0)
    #############################################
    #obox = OptionsBox(self)######## FOR TESTING
    #winVbox.pack_start(obox, 0, 0)
    #########################################
    self.treeview = gtk.TreeView()
    swin = gtk.ScrolledWindow()
    swin.add(self.treeview)
    swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    winVbox.pack_start(swin, 1, 1)
    ################################
    hbox = gtk.HBox(spacing=0)
    hbox.set_direction(gtk.TEXT_DIR_LTR)
    vbox=gtk.VBox()
    vbox.pack_start(self.but_ok, 0, 0, 8)
    self.but_ok.set_property('width-request', 80)
    self.but_ok.set_property('height-request', 30)
    hbox.pack_start(vbox, 1, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    sbar = gtk.Statusbar()
    sbar.set_direction(gtk.TEXT_DIR_LTR)
    sbar.set_property('width-request', 20)
    hbox.pack_start(sbar, 0, 0)
    winVbox.pack_start(hbox, 0, 0)
    ##################################
    self.treestore = gtk.ListStore(gdk.Pixbuf,str,str,int,int)
    self.treeview.set_model(self.treestore)
    ################        
    cell0 = gtk.CellRendererPixbuf()
    col = gtk.TreeViewColumn('', cell0, pixbuf = 0)
    col.set_resizable(True)
    self.treeview.append_column(col)
    ###############
    cell1 = gtk.CellRendererText()
    col = gtk.TreeViewColumn(_('Date'), cell1, text=1)
    col.set_resizable(True)
    self.treeview.append_column(col)
    self.treeview.set_search_column(1)
    ##############
    cell3 = gtk.CellRendererText()
    col = gtk.TreeViewColumn(_('Comment'), cell3, text=2)
    self.treeview.append_column(col)
    ##############
    self.db=None
    self.fxml = None
    self.getFile()
    self.loadList()
    self.selected_cursor = None
    if month==None:
      self.comboMonth.set_active(0)
    else:
      self.comboMonth.set_active(month-1)
    if day!=None:
      self.spinDay.set_value(day)
    self.comboDayType.set_active(3)
    #########################################
    self.but_add.connect('clicked', self.add_clicked)
    self.but_del.connect('clicked', self.element_delete)
    self.but_edit.connect('clicked', self.element_edit)
    self.treeview.connect('cursor-changed', self.element_change)
    self.but_ok.connect('clicked', self.main.hideCustomDay)
    self.connect('delete_event', self.main.hideCustomDay)
    ########################################
    winVbox.show_all()
    self.comboDur.set_active(0)
  def dateModeChanged(self, widget):
    combo = self.comboMonth
    for i in range(len(combo.get_model())):
      combo.remove_text(0)
    module = core.modules[core.primaryMode] ## mode ????????
    for m in range(module.getMonthsInYear(None)):
      combo.append_text(_(module.getMonthName(m+1, None)))
    combo.set_active(0)
  def comboDurChanged(self, wid):
    #print 'comboDurChanged'
    i = wid.get_active()
    for j in range(3):
      if i==j:
        self.durItems[j].show()
      else:
        self.durItems[j].hide()
  def set_month_day(self, month, day):
    self.comboMonth.set_active(month-1)
    self.spinDay.set_value(day)
  def getFile(self):
    if not(os.path.isfile(ui.customFile)):
      self.db=None
      return
    self.fxml = parse(ui.customFile)
    self.db=self.fxml.getElementsByTagName('day')
  def loadList(self):
    if not(os.path.isfile(ui.customFile)):
      self.db=None
      return
    self.fxml = parse(ui.customFile)
    self.db=self.fxml.getElementsByTagName('day')
    if (self.db==None):
      return None
    element_code=1
    pix = gtk.Image()
    for record in self.db:
      lst = []
      for element in record.childNodes:
        if element.nodeType != element.TEXT_NODE:
          if element.nodeType != element.TEXT_NODE:
             name, data = getElementText(element)
             if (name=='num'):
               sp=data.split('/')
               lst.append(sp[0])
               lst.append(sp[1])
             if (name=='kind'):
               lst.append(data)
             if (name=='desc'):
               lst.append(data)
      try:
        pix.set_from_file(pixDir+os.sep+customdayModes[int(lst[2])][1])
        p=pix.get_pixbuf()
      except:
        p=None
      try:
        self.treestore.append([p, lst[0]+'/'+lst[1], lst[3],
                               element_code, int(lst[2])])
      except IndexError:
        print lst
      element_code+=1
    if element_code==1:
        self.but_edit.set_property('sensitive', False)

  def clear_new(self):
    #cur = self.treeview.get_cursor()
    #print cur, type(cur)
    #self.treeview.set_cursor((0, None))
    self.entryComment.set_text('')

  def add_clicked(self,obj,data=None):
    if not os.path.isfile(ui.customFile):
      self.create_homefile()
    self.add_item()
    self.treestore.clear()
    self.getFile()
    self.loadList()
        
  def element_delete(self,obj,data=None):
    self.delete()
    self.treestore.clear()
    self.getFile()
    self.loadList()

  def element_delete_date(self, m, d):
    find = False
    db2=self.fxml.getElementsByTagName('customday')[0]
    for record in db2.getElementsByTagName('day'):
      for element in record.childNodes:
        if element.nodeType != element.TEXT_NODE:
          if element.nodeType != element.TEXT_NODE:
             name, data = getElementText(element)
             if name=='num':
               sp=data.split('/')
               #if len(sp)<2:
               #  continue
               if str(d)==sp[-1] and str(m)==sp[-2]:
                 removeday = db2.removeChild(record)
                 removeday.unlink()
                 find = True
                 break
      if find:
        break
    for i in range(len(self.treestore)):
      try:
        sp2 = self.treestore[i][1].split('/')
      except:
        myRaise(__file__)
        continue
      if sp==sp2:
        del self.treestore[i]
    libxml = open(ui.customFile, 'w')
    libxml.write(self.fxml.toprettyxml(''))
    libxml.close()

  def element_search_select(self, m, d):
    for i in range(len(self.treestore)):
      sp = self.treestore[i][1].split('/')
      #if len(sp)<2:
      #  continue
      if str(d)==sp[-1] and str(m)==sp[-2]:
        self.treeview.set_cursor(i)


  def element_edit(self,obj,data=None):
    self.delete()
    self.add_item()
    self.treestore.clear()
    self.getFile()
    self.loadList()
    self.entryComment.set_text('')
        
  def add_item(self):
    if self.fxml==None:
      return
    newday = self.fxml.createElement('day')
    field_day = self.fxml.createElement('num')
    mon = str(self.comboMonth.get_active()+1)
    day = str(int(self.spinDay.get_value()))
    field_day_text = self.fxml.createTextNode(mon+'/'+day)
        
    field_kind = self.fxml.createElement('kind')
    kind = str(self.comboDayType.get_active())
    field_kind_text = self.fxml.createTextNode(kind)

    field_desc = self.fxml.createElement('desc')
    text = self.entryComment.get_text()
    field_desc_text = self.fxml.createTextNode(text)

    field_day.appendChild(field_day_text)
    field_kind.appendChild(field_kind_text)
    field_desc.appendChild(field_desc_text)
        
    newday.appendChild(field_day)
    newday.appendChild(field_kind)
    newday.appendChild(field_desc)
        
    db2=self.fxml.getElementsByTagName('customday')[0]
    db2.appendChild(newday)
        
    #self.main.cal.customDB.append([mon,day,kind,text])
    #self.main.cal.updateWindow()
        
    libxml = open(ui.customFile,'w')
    libxml.write(self.fxml.toprettyxml(''))
    libxml.close()
        
    self.entryComment.set_text('')

  def element_change(self, obj, data=None, event=None):
    selection=obj.get_selection()
    (mode, tIter)=selection.get_selected()
    #print mode, tIter
    if tIter==None:## not a gtk.TreeIter
      return
    self.selected_cursor=mode.get(tIter, 3)[0]
    sp= mode.get(tIter, 1)[0].split('/')
    self.comboMonth.set_active(int(sp[0])-1)
    self.spinDay.set_value(int(sp[1]))
    self.comboDayType.set_active(int(mode.get(tIter, 4)[0]))
    self.entryComment.set_text(mode.get(tIter, 2)[0])
    self.but_edit.set_property('sensitive', True)
     
  def delete(self):
    if (self.db==None):
      return None
    el_code=1
    find =False

    db2=self.fxml.getElementsByTagName('customday')[0]
    for record in db2.getElementsByTagName('day'):
      for element in record.childNodes:
        if (el_code==self.selected_cursor):
          removeday = db2.removeChild(record)
          removeday.unlink()
          find = True
          break
      if find:
        break
      el_code+=1

    libxml = open(ui.customFile, 'w')
    libxml.write(self.fxml.toprettyxml(''))
    libxml.close()
        
  def create_homefile(self):
    xml = open(ui.customFile,'w')
    xml.write("<?xml version='1.0' ?>")
    xml.write('<customday>')
    xml.write('</customday>')
    xml.close()
    self.fxml = parse(ui.customFile)

  def bquit(self,obg,data=None):
    self.destroy()

