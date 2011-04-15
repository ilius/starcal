# -*- coding: utf-8 -*-
#        
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import os, sys

from scal2.locale_man import tr as _

from scal2 import core
from scal2.core import homeDir, numLocale

from scal2 import ui
from scal2.monthcal import getMonthStatus, getCurrentMonthStatus
from scal2.export import exportToHtml

from scal2.ui_gtk.mywidgets.multi_spin_box import YearMonthBox

import gtk
from gtk import gdk

#gdkColorToHtml = lambda color: '#%.2x%.2x%.2x'%(color.red/256, color.green/256, color.blue/256)



class ExportDialog(gtk.Dialog):
    def __init__(self, mainWin):
        self.mainWin = mainWin
        self.mcal = mainWin.mcal
        gtk.Dialog.__init__(self, title=_('Export to HTML'), parent=None)
        self.set_has_separator(False)
        ########
        hbox = gtk.HBox(spacing=2)
        hbox.pack_start(gtk.Label(_('Month Range')), 0, 0)
        combo = gtk.combo_box_new_text()
        for t in ('Current Month', 'Whole Current Year', 'Custom'):
            combo.append_text(_(t))
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.combo = combo
        ###
        hbox2 = gtk.HBox(spacing=2)
        hbox2.pack_start(gtk.Label(_('from month')), 0, 0)
        self.ymBox0 = YearMonthBox(lang=core.langSh)
        hbox2.pack_start(self.ymBox0, 0, 0)
        hbox2.pack_start(gtk.Label(''), 1, 1)
        hbox2.pack_start(gtk.Label(_('to month')), 0, 0)
        self.ymBox1 = YearMonthBox(lang=core.langSh)
        hbox2.pack_start(self.ymBox1, 0, 0)
        hbox.pack_start(hbox2, 1, 1)
        self.hbox2 = hbox2
        combo.set_active(0)
        self.vbox.pack_start(hbox, 0, 0)
        ########
        self.fcw = gtk.FileChooserWidget(action=gtk.FILE_CHOOSER_ACTION_SAVE)
        self.vbox.pack_start(self.fcw, 1, 1)
        self.vbox.show_all()
        combo.connect('changed', self.comboChanged)
        canB = self.add_button(gtk.STOCK_CANCEL, 1)
        saveB = self.add_button(gtk.STOCK_SAVE, 2)
        if ui.autoLocale:
            canB.set_label(_('_Cancel'))
            canB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            saveB.set_label(_('_Save'))
            saveB.set_image(gtk.image_new_from_stock(gtk.STOCK_SAVE,gtk.ICON_SIZE_BUTTON))
        self.connect('delete-event', self.onDelete)
        canB.connect('clicked', self.onDelete)
        saveB.connect('clicked', self.save)
        try:
            self.fcw.set_current_folder('%s/Desktop'%homeDir)
        except:##?????????????????????
            pass    
    def comboChanged(self, widget=None, ym=None):
        i = self.combo.get_active()
        if ym==None:
            ym = (ui.cell.year, ui.cell.month)
        if i==0:
            self.fcw.set_current_name('calendar-%.4d-%.2d.html'%ym)
            self.hbox2.hide()
        elif i==1:
            self.fcw.set_current_name('calendar-%.4d.html'%ym[0])
            self.hbox2.hide()
        else:#elif i==2
            self.fcw.set_current_name('calendar.html')
            self.hbox2.show()
        ## select_region(0, -4) ## FIXME
    def onDelete(self, widget=None, event=None):## hide(close) File Chooser Dialog
        self.hide()
        return True
    def save(self, widget=None):
        self.window.set_cursor(gdk.Cursor(gdk.WATCH))
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        path = self.fcw.get_filename()
        if path in (None, ''):
            return
        print 'Exporting to html file "%s"'%path
        i = self.combo.get_active()
        months = []
        module = core.modules[core.primaryMode]
        if i==0:
            s = getCurrentMonthStatus()
            months = [s]
            title = '%s %s'%(core.getMonthName(core.primaryMode, s.month, s.year), numLocale(s.year))
        elif i==1:
            for i in xrange(1, 13):
                months.append(getMonthStatus(ui.cell.year, i))
            title = '%s %s'%(_('Calendar'), numLocale(ui.cell.year))
        elif i==2:
            (y0, m0) = self.ymBox0.get_date()
            (y1, m1) = self.ymBox1.get_date()
            for ym in xrange(y0*12+m0-1, y1*12+m1):
                (y, m) = divmod(ym, 12)
                m += 1
                months.append(getMonthStatus(y, m))
            title = _('Calendar')
        exportToHtml(path, months, title)
        self.window.set_cursor(gdk.Cursor(gdk.LEFT_PTR))
        self.hide()
    def showDialog(self, year, month):
        self.comboChanged(ym=(year, month))
        self.ymBox0.set_date((year, month))
        self.ymBox1.set_date((year, month))
        self.resize(1, 1)
        self.present()
    def exportSvg(self, path, monthList):## FIXME
        ## monthList is a list of tuples (year, month)
        import cairo
        hspace = 20
        (x, y, w, h0) = self.mcal.allocation
        n = len(monthList)
        h = n*h0 + (n-1)*hspace
        fo = open(path+'.svg', 'w')
        surface = cairo.SVGSurface(fo, w, h)
        cr0 = cairo.Context(surface)
        cr = gtk.gdk.CairoContext(cr0)
        year = ui.cell.year
        month = ui.cell.month
        day = self.mcal.day
        self.mainWin.show() ## ??????????????
        for i in range(n):
            surface.set_device_offset(0, i*(h0+hspace))
            self.mcal.dateChange((monthList[i][0], monthList[i][1], 1))
            self.mcal.drawAll(cr=cr, cursor=False)
            self.mcal.queue_draw()
        self.mainWin.dateChange((year, month, day))
        surface.finish()



