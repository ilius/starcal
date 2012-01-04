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

from time import localtime

import sys, os
from os.path import dirname
from os.path import join
from subprocess import Popen

import scal2.locale_man
from scal2.locale_man import langDict, langSh
from scal2.locale_man import tr as _
from scal2.paths import *

from scal2 import core
from scal2.core import myRaise, convert

from scal2.format_time import compileTmFormat

from scal2 import ui
##from scal2.ui_gtk import starcal_gtk

import gtk
from gtk import gdk

from scal2.ui_gtk.mywidgets import MyFontButton, MyColorButton
from scal2.ui_gtk.drawing import newTextLayout
from scal2.ui_gtk.font_utils import *
from scal2.ui_gtk.color_utils import *
from scal2.ui_gtk.utils import *
from scal2.ui_gtk.export import ExportToIcsDialog

############################################################

## stock image of "Next" and "Previous" buttons(year/month)
## STOCK_GO_BACK, STOCK_GO_FORWARD, STOCK_GO_DOWN, STOCK_GO_UP, STOCK_ZOOM_OUT, STOCK_ZOOM_IN
prevStock = gtk.STOCK_GO_BACK
nextStock = gtk.STOCK_GO_FORWARD

##############################

settings = gtk.settings_get_default()

ui.fontDefault = gfontDecode(settings.get_property('gtk-font-name'))
if not ui.fontCustom:
    ui.fontCustom = ui.fontDefault

if ui.shownCals[0]['font']==None:
    ui.shownCals[0]['font'] = ui.fontDefault

(name, bold, underline, size) = ui.fontDefault
for item in ui.shownCals[1:]:
    if item['font']==None:
        item['font'] = (name, bold, underline, int(size*0.6))
del name, bold, underline, size

##############################

#print settings.get_property('gtk-timeout-initial')## 200
#print settings.get_property('gtk-timeout-repeat')## 20
#settings.set_property('gtk-timeout-repeat', 100)##???????????????? Dosn't affect!!


#if not fontUseDefault:##????????????????
#    settings.set_property('gtk-font-name', fontCustom)

dateFormat = '%Y/%m/%d'
clockFormat = '%X' ## '%T', '%X' (local), '<b>%T</b>', '%m:%d'

dateBinFmt = compileTmFormat(dateFormat)
clockFormatBin = compileTmFormat(clockFormat)

adjustTimeCmd = ''

############################################################

class ToolbarItem:
    def __init__(self, name, stockName, method, tooltip='', text=''):
        self.name = name
        self.stock = getattr(gtk, 'STOCK_%s'%(stockName.upper()))
        self.method = method
        if not text:
            text = name.capitalize()
        self.text = _(text)
        if not tooltip:
            tooltip = name.capitalize()
        self.tooltip = _(tooltip)

toolbarItemsData = (
    ToolbarItem('today',       'home',        'goToday',        'Select Today'),
    ToolbarItem('date',        'index',       'selectDateShow', 'Select Date...', 'Date...'),
    ToolbarItem('customize',   'edit',        'customizeShow'),
    ToolbarItem('preferences', 'preferences', 'prefShow',),
    ToolbarItem('add',         'add',         'eventManShow',   'Event Manager',     ),
    ToolbarItem('export',      'convert',     'exportClicked',  'Export to HTML',     ),
    ToolbarItem('about',       'about',       'aboutShow',      'About StarCalendar', ),
    ToolbarItem('quit',        'quit',        'quit',)
)

toolbarItemsDataDict = dict([(item.name, item) for item in toolbarItemsData])

############################################################

sysConfPath = join(sysConfDir, 'ui-gtk.conf')
if os.path.isfile(sysConfPath):
    try:
        exec(open(sysConfPath).read())
    except:
        myRaise(__file__)

confPath = join(confDir, 'ui-gtk.conf')
if os.path.isfile(confPath):
    try:
        exec(open(confPath).read())
    except:
        myRaise(__file__)

customizeConfPath = join(confDir, 'ui-customize.conf')
if os.path.isfile(customizeConfPath):
    try:
        exec(open(customizeConfPath).read())
    except:
        myRaise(__file__)

ui.checkMainWinItems()

#if adjustTimeCmd=='':## FIXME
for cmd in ('gksudo', 'kdesudo', 'gksu', 'gnomesu', 'kdesu'):
    if os.path.isfile('/usr/bin/%s'%cmd):
        adjustTimeCmd = [
            cmd,
            join(rootDir, 'scripts', 'run'),
            'scal2/ui_gtk/adjust_dtime.py'
        ]
        break


## (VAR_NAME, bool,	    CHECKBUTTON_TEXT)					## CheckButton
## (VAR_NAME, list,	    LABEL_TEXT, (ITEM1, ITEM2, ...))	## ComboBox
## (VAR_NAME, int,	    LABEL_TEXT, MIN, MAX)				## SpinButton
## (VAR_NAME, float,    LABEL_TEXT, MIN, MAX, DIGITS)		## SpinButton
class ModuleOptionItem:
    def __init__(self, module, opt):
        t = opt[1]
        self.opt = opt ## needed??
        self.module = module
        self.type = t
        self.var_name = opt[0]
        hbox = gtk.HBox()
        if t==bool:
            w = gtk.CheckButton(_(opt[2]))
            self.get_value = w.get_active
            self.set_value = w.set_active
        elif t==list:
            hbox.pack_start(gtk.Label(_(opt[2])), 0, 0)
            w = gtk.combo_box_new_text() ### or RadioButton
            for s in opt[3]:
                w.append_text(_(s))
            self.get_value = w.get_active
            self.set_value = w.set_active
        elif t==int:
            hbox.pack_start(gtk.Label(_(opt[2])), 0, 0)
            w = gtk.SpinButton()
            w.set_increments(1, 10)
            w.set_range(opt[3], opt[4])
            w.set_digits(0)
            w.set_direction(gtk.TEXT_DIR_LTR)
            self.get_value = w.get_value
            self.set_value = w.set_value
        elif t==float:
            hbox.pack_start(gtk.Label(_(opt[2])), 0, 0)
            w = gtk.SpinButton()
            w.set_increments(0.1, 1)
            w.set_range(opt[3], opt[4])
            w.set_digits(opt[5])
            w.set_direction(gtk.TEXT_DIR_LTR)
            self.get_value = w.get_value
            self.set_value = w.set_value
        else:
            raise RuntimeError('bad option type "%s"'%t)
        hbox.pack_start(w, 0, 0)
        self.widget = hbox
        ####
        self.updateVar = lambda: setattr(self.module, self.var_name, self.get_value())
        self.updateWidget = lambda: self.set_value(getattr(self.module, self.var_name))
        

## ('button', LABEL, CLICKED_MODULE_NAME, CLICKED_FUNCTION_NAME)
class ModuleOptionButton:
    def __init__(self, opt):
        funcName = opt[2]
        clickedFunc = getattr(__import__('scal2.ui_gtk.%s'%opt[1], fromlist=[funcName]), funcName)
        hbox = gtk.HBox()
        button = gtk.Button(_(opt[0]))
        button.connect('clicked', clickedFunc)
        hbox.pack_start(button, 0, 0)
        self.widget = hbox
    def updateVar(self):
        pass
    def updateWidget(self):
        pass
        


class PrefItem():
    ## self.__init__, self.module, self.varName, self.widget
    ## self.varName an string containing the name of variable
    ## set self.module=None if varName is name of a global variable in this module
    def get(self):
        raise NotImplementedError
    def set(self, value):
        raise NotImplementedError
    #updateVar = lambda self: setattr(self.module, self.varName, self.get())
    def updateVar(self):
        if self.module==None:
            if self.varName=='':
                print 'PrefItem.updateVar: this PrefItem instance has no reference variable to write to!'
            else:
                exec('global %s;%s=%r'%(self.varName, self.varName, self.get()))
        else:
            setattr(self.module, self.varName, self.get())
    #updateWidget = lambda self: self.set(getattr(self.module, self.varName))
    def updateWidget(self):
        if self.module==None:
            if self.varName=='':
                print 'PrefItem.updateWidget: this PrefItem instance has no reference variable to read from!'
            else:
                self.set(eval(self.varName))
        else:
            self.set(getattr(self.module, self.varName))
    ## confStr(): gets the value from variable (not from GUI) and returns a string to save to file
    ## the string will has a NEWLINE at the END
    def confStr(self):
        if self.module==None:
            if self.varName=='':
                return ''
            else:
                return '%s=%r\n'%(self.varName, eval(self.varName))
        else:
            return '%s=%r\n'%(self.varName, getattr(self.module, self.varName))


class ComboTextPrefItem(PrefItem):
    def __init__(self, module, varName, items=[]):## items is a list of strings
        self.module = module
        self.varName = varName
        w = gtk.combo_box_new_text()
        self.widget = w
        for s in items:
            w.append_text(s)
        self.get = w.get_active
        self.set = w.set_active
    #def set(self, value):
    #    print 'ComboTextPrefItem.set', value
    #    self.widget.set_active(int(value))

class ComboEntryTextPrefItem(PrefItem):
    def __init__(self, module, varName, items=[]):## items is a list of strings
        self.module = module
        self.varName = varName
        w = gtk.combo_box_entry_new_text()
        self.widget = w
        for s in items:
            w.append_text(s)
        self.get = w.child.get_text
        self.set = w.child.set_text

class ComboImageTextPrefItem(PrefItem):
    def __init__(self, module, varName, items=[]):## items is a list of pairs (imagePath, text)
        self.module = module
        self.varName = varName
        ###
        ls = gtk.ListStore(gdk.Pixbuf, str)
        combo = gtk.ComboBox(ls)
        ###
        cell = gtk.CellRendererPixbuf()
        combo.pack_start(cell, False)
        combo.add_attribute(cell, 'pixbuf', 0)    
        ###
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 1)    
        ###
        self.widget = combo
        self.ls = ls
        for (imPath, label) in items:
            self.append(imPath, label)
        self.get = combo.get_active
        self.set = combo.set_active
    def append(self, imPath, label):
        if imPath=='':
            pix = None
        else:
            if not imPath.startswith(os.sep):
                imPath = join(pixDir, imPath)
            pix = gdk.pixbuf_new_from_file(imPath)
        self.ls.append([pix, label])

class LangPrefItem(PrefItem):
    def __init__(self):
        self.module = scal2.locale_man
        self.varName = 'lang'
        ###
        ls = gtk.ListStore(gdk.Pixbuf, str)
        combo = gtk.ComboBox(ls)
        ###
        cell = gtk.CellRendererPixbuf()
        combo.pack_start(cell, False)
        combo.add_attribute(cell, 'pixbuf', 0)    
        ###
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 1)    
        ###
        self.widget = combo
        self.ls = ls
        self.append(join(pixDir, 'computer.png'), _('System Setting'))
        for (key, data) in langDict.items():
            self.append(data.flag, data.name)
    def append(self, imPath, label):
        if imPath=='':
            pix = None
        else:
            if not imPath.startswith(os.sep):
                imPath = join(pixDir, imPath)
            pix = gdk.pixbuf_new_from_file(imPath)
        self.ls.append([pix, label])
    def get(self):
        i = self.widget.get_active()
        if i==0:
            return ''
        else:
            return langDict.keyList[i-1]
    def set(self, value):
        assert isinstance(value, str)
        if value=='':
            self.widget.set_active(0)
        else:
            try:
                i = langDict.keyList.index(value)
            except ValueError:
                print 'language %s in not in list!'%value
                self.widget.set_active(0)
            else:
                self.widget.set_active(i+1)
    #def updateVar(self):
    #    lang = 




class FontPrefItem(PrefItem):##????????????
    def __init__(self, module, varName, parent):
        self.module = module
        self.varName = varName
        w = MyFontButton(parent)
        self.widget = w
        self.get = w.get_font_name## FIXME
        self.set = w.set_font_name## FIXME

class CheckPrefItem(PrefItem):
    def __init__(self, module, varName, label='', tooltip=None):
        self.module = module
        self.varName = varName
        w = gtk.CheckButton(label)
        if tooltip!=None:
            set_tooltip(w, tooltip)
        self.widget = w
        self.get = w.get_active
        self.set = w.set_active

class CheckStartupPrefItem(PrefItem):### cbStartCommon
    def __init__(self):
        self.module = None
        self.varName = ''
        w = gtk.CheckButton(_('Run on session startup'))
        set_tooltip(w, 'Run on startup of Gnome, KDE, Xfce, LXDE, ...\nFile: %s'%ui.comDesk)
        self.widget = w
        self.get = w.get_active
        self.set = w.set_active
    def updateVar(self):
        if self.widget.get_active():
            if not ui.addStartup():
                self.widget.set_active(False)
        else:
            try:
                ui.removeStartup()
            except:
                pass
    def updateWidget(self):
        self.widget.set_active(ui.checkStartup())


class ColorPrefItem(PrefItem):
    def __init__(self, module, varName, useAlpha=False):
        self.module = module
        self.varName = varName
        w = MyColorButton()
        w.set_use_alpha(useAlpha)
        self.useAlpha = useAlpha
        self.widget = w
        self.set = w.set_color
    def get(self):
        #if self.useAlpha:
        alpha = self.widget.get_alpha()
        if alpha==None:
            return self.widget.get_color()
        else:
            return self.widget.get_color() + (alpha,)
    def set(self, color):
        if self.useAlpha:
            if len(color)==3:
                self.widget.set_color(color)
                self.widget.set_alpha(255)
            elif len(color)==4:
                self.widget.set_color(color[:3])
                self.widget.set_alpha(color[3])
            else:
                raise ValueError
        else:
            self.widget.set_color(color)

class SpinPrefItem(PrefItem):
    def __init__(self, module, varName, min_=-99, max_=99, digits=1, inc1=1, inc2=10):
        self.module = module
        self.varName = varName
        w = gtk.SpinButton()
        self.widget = w
        w.set_range(min_, max_)
        w.set_digits(digits)
        w.set_increments(inc1, inc2)
        w.set_direction(gtk.TEXT_DIR_LTR)
        self.get = w.get_value
        self.set = w.set_value

class RadioListPrefItem(PrefItem):
    def __init__(self, vertical, module, varName, texts, label=None):
        self.num = len(texts)
        assert self.num>0
        self.module = module
        self.varName = varName
        if vertical:
            box = gtk.VBox()
        else:
            box = gtk.HBox()
        self.widget = box
        self.radios = [gtk.RadioButton(label=_(s)) for s in texts]
        first = self.radios[0]
        if label!=None:
            box.pack_start(gtk.Label(label), 0, 0)
            box.pack_start(gtk.Label(''), 1, 1)
        box.pack_start(first, 0, 0)
        for r in self.radios[1:]:
            box.pack_start(gtk.Label(''), 1, 1)
            box.pack_start(r, 0, 0)
            r.set_group(first)
        box.pack_start(gtk.Label(''), 1, 1) ## FIXME
    def get(self):
        for i in range(self.num):
            if self.radios[i].get_active():
                return i
    def set(self, index):
        self.radios[index].set_active(True)

class RadioHListPrefItem(RadioListPrefItem):
    def __init__(self, *args, **kwargs):
        RadioListPrefItem.__init__(self, False, *args, **kwargs)

class RadioVListPrefItem(RadioListPrefItem):
    def __init__(self, *args, **kwargs):
        RadioListPrefItem.__init__(self, True, *args, **kwargs)


class ListPrefItem(PrefItem):
    def __init__(self, vertical, module, varName, items=[]):
        self.module = module
        self.varName = varName
        if vertical:
            box = gtk.VBox()
        else:
            box = gtk.HBox()
        for item in items:
            assert isinstance(item, PrefItem)
            box.pack_start(item.widget, 0, 0)
        self.num = len(items)
        self.items = items
        self.widget = box
    get = lambda self: tuple([item.get() for item in self.items])
    def set(self, valueL):
        assert len(valueL)==self.num
        for i in range(self.num):
            self.items[i].set(valueL[i])
    def append(self, item):
        assert isinstance(item, PrefItem)
        self.widget.pack_start(item.widget, 0, 0)
        self.items.append(item)


class HListPrefItem(ListPrefItem):
    def __init__(self, *args, **kwargs):
        ListPrefItem.__init__(self, False, *args, **kwargs)

class VListPrefItem(ListPrefItem):
    def __init__(self, *args, **kwargs):
        ListPrefItem.__init__(self, True, *args, **kwargs)

class CalPropPrefItem(PrefItem):
    def __init__(self, module, varName, parent, sgroupFont):
        self.module = module
        self.varName = varName
        hbox = gtk.HBox()
        ######
        checkb = gtk.CheckButton()
        set_tooltip(checkb, _('Enable/Disable'))
        self.checkb = checkb
        hbox.pack_start(checkb, 0, 0)
        ####
        combo = gtk.combo_box_new_text()
        for m in core.modules:
            combo.append_text(_(m.desc))
        #if i>0:## FIXME
        #    combo.append_text(_('Julian Day'))
        self.combo = combo
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        label = gtk.Label(_('position'))
        self.label = label
        ###
        hbox.pack_start(label, 0, 0)
        ###
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(-99, 99)
        spin.set_digits(1)
        #spin.set_width_chars(3)
        self.spinX = spin
        spin.set_direction(gtk.TEXT_DIR_LTR)
        hbox.pack_start(spin, 0, 0)
        ###
        spin = gtk.SpinButton()
        spin.set_increments(1, 10)
        spin.set_range(-99, 99)
        spin.set_digits(1)
        #spin.set_width_chars(3)
        self.spinY = spin
        spin.set_direction(gtk.TEXT_DIR_LTR)
        hbox.pack_start(spin, 0, 0)
        ####
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        fontb = MyFontButton(parent)
        self.fontb = fontb
        hbox.pack_start(fontb, 0, 0)
        sgroupFont.add_widget(fontb)
        ####
        colorb = MyColorButton()
        self.colorb = colorb
        hbox.pack_start(colorb, 0, 0)
        #########
        self.widget = hbox
    def get(self):
        return {
            'enable':self.checkb.get_active(),
            'mode'  :self.combo.get_active(),
            'x'     :self.spinX.get_value(),
            'y'     :self.spinY.get_value(),
            'font'  :self.fontb.get_font_name(),
            'color' :self.colorb.get_color()
        }
    def set(self, data):
        self.checkb.set_active(data['enable'])
        self.combo.set_active(data['mode'])
        self.spinX.set_value(data['x'])
        self.spinY.set_value(data['y'])
        self.fontb.set_font_name(data['font'])
        self.colorb.set_color(data['color'])


class WeekDayCheckListPrefItem(PrefItem):### use synopsis (Sun, Mon, ...) FIXME
    def __init__(self, module, varName, vertical=False, homo=True, abbreviateNames=True):
        self.module = module
        self.varName = varName
        if vertical:
            box = gtk.VBox()
        else:
            box = gtk.HBox()
        box.set_homogeneous(homo)
        nameList = core.weekDayNameAb if abbreviateNames else core.weekDayName
        ls = [gtk.ToggleButton(item) for item in nameList]
        s = core.firstWeekDay
        for i in range(7):
            box.pack_start(ls[(s+i)%7], 1, 1)
        self.cbList = ls
        self.widget = box
        self.start = s
    def setStart(self, s):
        b = self.widget
        ls = self.cbList
        for j in range(7):## or range(6)
            b.reorder_child(ls[(s+j)%7], j)
        self.start = s
    def get(self):
        value = []
        cbl = self.cbList
        for j in range(7):
            if cbl[j].get_active():
                value.append(j)
        return tuple(value)
    def set(self, value):
        cbl = self.cbList
        for cb in cbl:
            cb.set_active(False)
        for j in value:
            cbl[j].set_active(True)


"""
class ToolbarIconSizePrefItem(PrefItem):
    def __init__(self, module, varName):
        self.module = module
        self.varName = varName
        ####
        self.widget = gtk.combo_box_new_text()
        for item in iconSizeList:
            self.widget.append_text(item[0])
    def get(self):
        return iconSizeList[self.widget.get_active()][0]
    def set(self, value):
        for (i, item) in enumerate(iconSizeList):
            if item[0]==value:
                self.widget.set_active(i)
                return
"""


class PrefDialog(gtk.Dialog):
    def __init__(self, mainWin):
        self.mainWin = mainWin
        trayMode = mainWin.trayMode
        gtk.Dialog.__init__(self, title=_('Preferences'))
        self.connect('delete-event', self.onDelete)
        self.set_has_separator(False)
        #self.set_skip_taskbar_hint(True)
        cancelB = self.add_button(gtk.STOCK_CANCEL, 1)
        applyB = self.add_button(gtk.STOCK_APPLY, 2)
        okB = self.add_button(gtk.STOCK_OK, 3)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON))
            applyB.set_label(_('_Apply'))
            applyB.set_image(gtk.image_new_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON))
        okB.grab_default()## FIXME
        #okB.grab_focus()## FIXME
        cancelB.connect('clicked', self.cancel)
        applyB.connect('clicked', self.apply)
        okB.connect('clicked', self.ok)
        set_tooltip(okB, _('Apply and Close'))
        ##############################################
        self.localePrefItems = []
        self.corePrefItems = []
        self.uiPrefItems = []
        self.herePrefItems = [] ## FIXME
        ################################ Tab 1 ############################################
        vbox = gtk.VBox()
        vbox1 = vbox
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
        sgroupFont = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        exp = gtk.Expander(_('Shown Calendars'))
        exp.set_expanded(True)
        itemShownCals = VListPrefItem(
            ui,
            'shownCals',
            [CalPropPrefItem(None, '', self.mainWin, sgroupFont) for i in xrange(max(ui.shownCalsNum,3))],
        )
        self.uiPrefItems.append(itemShownCals)
        exp.add(itemShownCals.widget)
        vbox.pack_start(exp, 0, 0)
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
        item = CheckPrefItem(ui, 'showWinController', _('Show Window Controllers'))
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ##
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
        ################################ Tab 2 ################################################
        vbox = gtk.VBox()
        vbox2 = vbox
        hbox = gtk.HBox(spacing=2)
        ########
        item = CheckPrefItem(ui, 'calGrid', _('Grid'))
        self.uiPrefItems.append(item)
        cbGrid = item.widget
        hbox.pack_start(cbGrid, 0, 0)
        ########
        item = ColorPrefItem(ui, 'gridColor', True)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        cbGrid.connect('clicked', lambda wid: item.widget.set_sensitive(wid.get_active()))
        #item.widget.set_sensitive(ui.calGrid)## FIXME
        ########
        hbox.pack_start(gtk.Label(''), 1, 1)
        defaultItem = CheckPrefItem(ui, 'fontUseDefault', _('Use system font'), gfontEncode(ui.fontDefault))
        self.uiPrefItems.append(defaultItem)
        hbox.pack_start(defaultItem.widget, 0, 0)
        ###
        customItem = FontPrefItem(ui, 'fontCustom', self)
        self.uiPrefItems.append(customItem)
        hbox.pack_start(customItem.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        #customItem.widget.connect('clicked', self.checkbFontClicked)
        defaultItem.widget.connect('clicked', lambda w: customItem.widget.set_sensitive(not w.get_active()))## FIXME
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
        hbox = gtk.HBox(spacing=3)
        hbox2 = gtk.HBox(spacing=3)
        self.checkYmArrows = gtk.CheckButton('')
        self.checkYmArrows.connect('clicked', self.checkYmArrowsClicked)
        self.ymArrowHbox = hbox2
        #self.checkYmArrows.connect('clicked', lambda obj: hbox2.set_sensitive(self.checkYmArrows.get_active()))
        hbox.pack_start(self.checkYmArrows, 0, 0)
        hbox2.pack_start(gtk.Label(_('Previous year/month button')), 0, 0)
        im1 = gtk.Image()
        ev1 = gtk.EventBox()
        ev1.set_visible_window(False)
        ev1.add(im1)
        ev1.connect('button-press-event', self.imageClicked, 1)
        hbox2.pack_start(ev1, 0, 0)
        ##
        hbox2.pack_start(gtk.Label(''), 1, 1)
        hbox2.pack_start(gtk.Label(_('Next')), 0, 0)
        im2 = gtk.Image()
        ev2 = gtk.EventBox()
        ev2.set_visible_window(False)
        ev2.add(im2)
        ev2.connect('button-press-event', self.imageClicked, 2)
        hbox2.pack_start(ev2, 0, 0)
        ##
        menu = gtk.Menu()
        for stock in (gtk.STOCK_GO_UP,gtk.STOCK_GO_DOWN,gtk.STOCK_GO_BACK,gtk.STOCK_GO_FORWARD,\
        gtk.STOCK_ZOOM_IN,gtk.STOCK_ZOOM_OUT,gtk.STOCK_ADD,gtk.STOCK_REMOVE):
                menu.add(self.stockMenuItem(stock, self.imageSet, stock))
        for arrow in (gtk.ARROW_LEFT, gtk.ARROW_RIGHT, gtk.ARROW_UP, gtk.ARROW_DOWN):
                menu.add(self.newArrowMenuItem(arrow, self.imageSet, arrow))
        menu.show_all()
        self.menu_im = menu
        self.im1 = im1
        self.im2 = im2
        self.ev1 = ev1
        self.ev2 = ev2
        hbox2.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(hbox2, 1, 1)
        #########
        hbox.pack_start(gtk.Label(_('Left Margin')), 0, 0)
        item = SpinPrefItem(ui, 'calLeftMargin', 0, 99, 0, 1, 10)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        ####
        hbox.pack_start(gtk.Label(_('Top')), 0, 0)
        item = SpinPrefItem(ui, 'calTopMargin', 0, 99, 0, 1, 10)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ####
        vbox.pack_start(hbox, 0, 0)
        ################
        hbox = gtk.HBox(spacing=1)
        label = gtk.Label('<b>%s</b>:'%_('Cursor'))
        label.set_use_markup(True)
        hbox.pack_start(label, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(gtk.Label(_('Diameter')), 0, 0)
        item = SpinPrefItem(ui, 'cursorD', 0, 20, 1, 1, 10)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        ###
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(gtk.Label(_('Round')), 0, 0)
        item = SpinPrefItem(ui, 'cursorR', 0, 20, 1, 1, 10)
        self.uiPrefItems.append(item)
        hbox.pack_start(item.widget, 0, 0)
        #hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox2 = gtk.HBox(spacing=1)
        item = CheckPrefItem(ui, 'cursorFixed', _('Fixed Size'))
        self.uiPrefItems.append(item)
        item.widget.connect('clicked', self.cursorFixedClicked, hbox2)
        hbox2.set_sensitive(ui.cursorFixed)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox.pack_start(item.widget, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        hbox2.pack_start(gtk.Label(_('Width')), 0, 0)
        item = SpinPrefItem(ui, 'cursorW', 0, 99, 0, 1, 10)
        self.uiPrefItems.append(item)
        hbox2.pack_start(item.widget, 0, 0)
        #hbox.pack_start(gtk.Label(''), 1, 1)
        ####
        hbox2.pack_start(gtk.Label(_('Height')), 0, 0)
        item = SpinPrefItem(ui, 'cursorH', 0, 99, 0, 1, 10)
        self.uiPrefItems.append(item)
        hbox2.pack_start(item.widget, 0, 0)
        #hbox2.pack_start(gtk.Label(''), 1, 1)
        ####
        hbox.pack_start(hbox2, 1, 1)
        vbox.pack_start(hbox, 0, 0)
        #############
        item = RadioHListPrefItem(ui, 'dragIconCell',
            (_('Date String'), _('Cell Image')),
            _('Drag & Drop Icon:'))
        self.uiPrefItems.append(item)
        set_tooltip(item.radios[0], 'yyyy/mm/dd')
        item.set(0)
        vbox.pack_start(item.widget, 0, 0)
        ################################ Tab 3 (Advanced) ###########################################
        vbox = gtk.VBox()
        sgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ######
        hbox = gtk.HBox(spacing=5)
        label = gtk.Label(_('Date Format'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sgroup.add_widget(label)
        #hbox.pack_start(gtk.Label(''), 1, 1)
        item = ComboEntryTextPrefItem(None, 'dateFormat', 
            ('%Y/%m/%d', '%Y-%m-%d', '%y/%m/%d', '%y-%m-%d',
            '%OY/%Om/%Od', '%OY-%Om-%Od', '%m/%d', '%m/%d/%Y'))
        self.herePrefItems.append(item)
        hbox.pack_start(item.widget, 1, 1)
        vbox.pack_start(hbox, 0, 0)
        ###
        hbox = gtk.HBox(spacing=5)
        #hbox.pack_start(gtk.Label(''), 1, 1)
        label = gtk.Label(_('Digital Clock Format'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sgroup.add_widget(label)
        item = ComboEntryTextPrefItem(None, 'clockFormat', (
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
        self.herePrefItems.append(item)
        hbox.pack_start(item.widget, 1, 1)
        vbox.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox(spacing=5)
        label = gtk.Label(_('Days maximum cache size'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        ##sgroup.add_widget(label)
        item = SpinPrefItem(ui, 'maxDayCacheSize', 0, 9999, 0, 1, 30)
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
        hbox0.pack_start(gtk.Label(_('Holidays:')+'    '), 0, 0)
        item = WeekDayCheckListPrefItem(core, 'holidayWeekDays')
        self.corePrefItems.append(item)
        self.holiWDItem = item ## Holiday Week Days Item
        hbox0.pack_start(item.widget, 1, 1)
        vbox.pack_start(hbox0, 0, 0)
        #########
        hbox = gtk.HBox(spacing=3)
        hbox.pack_start(gtk.Label(_('First week of year containts:')), 0, 0)
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
        ##################################################
        ################################
        options = []
        for mod in core.modules:
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
        ################################ Tab 4 (Manage DB) ############################################
        #'''
        vbox = gtk.VBox()
        vbox3 = vbox
        #####
        ##extradayTray:
        hbox = gtk.HBox()
        if trayMode==1:
            item = CheckPrefItem(ui, 'extradayTray', _('Show in applet (for today)'))
        else:
            item = CheckPrefItem(ui, 'extradayTray', _('Show in tray (for today)'))
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
        canB = d.add_button(gtk.STOCK_CANCEL, 1)
        okB = d.add_button(gtk.STOCK_OK, 2)
        canB.connect('clicked', self.plugAddDialogClose)
        okB.connect('clicked', self.plugAddDialogOK)
        if ui.autoLocale:
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
            canB.set_label(_('_Cancel'))
            canB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
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
        ###################################################################################################
        notebook = gtk.Notebook()
        self.notebook = notebook
        #####################################
        """### to test
        notebook.set_property('homogeneous', True)
        notebook.set_property('show-tabs', True)
        
        notebook.append_page(vbox1)
        notebook.set_tab_label_packing(vbox1, True, True, gtk.PACK_START)
        notebook.set_tab_label(vbox1, gtk.Label('General'))
        notebook.set_tab_reorderable(vbox1, True)
        
        notebook.append_page(vbox2)
        notebook.set_tab_label_packing(vbox2, True, True, gtk.PACK_START)
        notebook.set_tab_label(vbox2, gtk.Label('Appearance'))
        notebook.set_tab_reorderable(vbox2, True)
        """
        ######################
        l = gtk.Label(_('_General'))
        l.set_use_underline(True)
        #eb = gtk.EventBox()
        vb = gtk.VBox()
        vb.pack_start(imageFromFile('%s/preferences-other.png'%pixDir))
        vb.pack_start(l)
        #eb.add(vb)
        #eb.set_above_child(True)
        #eb.set_visible_window(False)
        #vb.set_extension_events(gtk.gdk.EXTENSION_EVENTS_ALL)
        #vb.set_events(gtk.gdk.ALL_EVENTS_MASK)
        #vb.pack_start(eb, 0, 0)
        #vb.add_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.BUTTON_PRESS_MASK)
        vb.show_all()
        notebook.append_page(vbox1, vb)
        #notebook.set_tab_label_packing(vbox1, False, False, gtk.PACK_START)
        ###
        #notebook.connect('event', show_event)
        #vb.connect('expose-event', show_event)
        #vb.connect('expose-event', lambda obj, ev: vb.show_all())
        #vbox1.connect('event', show_event)
        ###
        l = gtk.Label(_('A_ppearance'))
        l.set_use_underline(True)
        vb = gtk.VBox()
        vb.pack_start(imageFromFile('%s/preferences-desktop-theme.png'%pixDir))
        vb.pack_start(l)
        vb.show_all()
        #vb.set_events(gtk.gdk.ALL_EVENTS_MASK)
        #vb.set_extension_events(gtk.gdk.EXTENSION_EVENTS_ALL)
        notebook.append_page(vbox2, vb)
        #notebook.set_tab_label_packing(vbox2, False, False, gtk.PACK_START)
        #vb.connect('drag-begin', show_event)
        ###
        l = gtk.Label(_('_Manage Plugin'))
        l.set_use_underline(True)
        vb = gtk.VBox()
        vb.pack_start(imageFromFile('%s/preferences-plugin.png'%pixDir))
        vb.pack_start(l)
        vb.show_all()
        notebook.append_page(vbox3, vb)
        #notebook.set_tab_label_packing(vbox3, False, False, gtk.PACK_START)
        ###
        l = gtk.Label(_('A_dvanced'))
        l.set_use_underline(True)
        vb = gtk.VBox()
        vb.pack_start(imageFromFile('%s/applications-system.png'%pixDir))
        vb.pack_start(l)
        vb.show_all()
        notebook.append_page(vbox4, vb)
        #notebook.set_tab_label_packing(vbox4, False, False, gtk.PACK_START)
        #"""
        ###
        try:
            notebook.set_tab_reorderable(vbox1, True)
            notebook.set_tab_reorderable(vbox2, True)
            notebook.set_tab_reorderable(vbox3, True)
            notebook.set_tab_reorderable(vbox4, True)
        except AttributeError:
            pass
        notebook.set_property('homogeneous', True)
        self.vbox.pack_start(notebook)
        self.vbox.show_all()
        self.prefPages = (vbox1, vbox2, vbox3, vbox4)
        for i in ui.prefPagesOrder:
            j = ui.prefPagesOrder[i]
            notebook.reorder_child(self.prefPages[i], j)
    checkYmArrowsClicked = lambda self, check: self.ymArrowHbox.set_sensitive(check.get_active())
    cursorFixedClicked = lambda self, check, hbox: hbox.set_sensitive(check.get_active())
    def comboFirstWDChanged(self, combo):
        f = self.comboFirstWD.get_active() ## 0 means Sunday
        if f==7: ## auto
            try:
                f = core.getLocaleFirstWeekDay()
            except:
                pass
        ## core.firstWeekDay will be later = f
        self.holiWDItem.setStart(f)
    def stockMenuItem(self, stock, func, *args):
        item = gtk.MenuItem()
        item.add(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU))
        item.connect('activate', func, *args)
        return item
    def newArrowMenuItem(self, arrowType, func=None, *args):
        item = gtk.MenuItem()
        #ev = gtk.EventBox()
        #ev.connect('activate', func, *args)
        item.add(gtk.Arrow(arrowType, gtk.SHADOW_IN))
        if func!=None:
            item.connect('activate', func, *args)
        return item
    def imageClicked(self, widget, event, num):
        self.menu_im.popup(None, None, None, event.button, event.time)
        self.im_num = num
    def imageSet(self, widget, stock):
        if isinstance(stock, str):
            if self.im_num==1:
                self.ev1.remove(self.im1)
                self.im1.destroy()
                self.im1 = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_SMALL_TOOLBAR)
                self.im1.type = stock
                self.ev1.add(self.im1)
                self.im1.show()
            elif self.im_num==2:
                self.ev2.remove(self.im2)
                self.im2.destroy()
                self.im2 = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_SMALL_TOOLBAR)
                self.im2.type = stock
                self.ev2.add(self.im2)
                self.im2.show()
        elif isinstance(stock, gtk._gtk.ArrowType):
            if self.im_num==1:
                self.ev1.remove(self.im1)
                self.im1.destroy()
                self.im1 = gtk.Arrow(stock, gtk.SHADOW_IN)
                self.im1.type = stock
                self.ev1.add(self.im1)
                self.im1.show()
            elif self.im_num==2:
                self.ev2.remove(self.im2)
                self.im2.destroy()
                self.im2 = gtk.Arrow(stock, gtk.SHADOW_IN)
                self.im2.type = stock
                self.ev2.add(self.im2)
                self.im2.show()
        else:
            raise ValueError('bad stock or arrow type %s'%stock)
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
                                   self.uiPrefItems + self.herePrefItems
    def apply(self, widget=None):
        global prevStock, nextStock
        ####### ?????????????????
        #print 'fontDefault =', ui.fontDefault
        ui.fontDefault = gfontDecode(gtk.settings_get_default().get_property('gtk-font-name'))
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
                print i, core.plugIndex
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
        ui.showYmArrows = self.checkYmArrows.get_active()
        prevStock = self.im1.type ##?????????
        nextStock = self.im2.type ##?????????
        ######
        ui.cellCache.clear() ## Very important, specially when core.primaryMode will be changed
        core.primaryMode = ui.shownCals[0]['mode']
        #################################################### Saving Preferences
        for mod in core.modules:
            mod.save()
        ##################### Saving locale config
        text = ''
        for item in self.localePrefItems:
            text += item.confStr()
        open(core.localeConfPath, 'w').write(text)        
        ##################### Saving core config
        text = 'allPlugList=%s\n\nplugIndex=%r\n'%(core.getAllPlugListRepr(), core.plugIndex)
        for item in self.corePrefItems:
            text += item.confStr()
        for key in ('firstWeekDayAuto', 'firstWeekDay', 'weekNumberModeAuto', 'weekNumberMode'):
            value = eval('core.'+key)
            text += '%s=%r\n'%(key, value)
        open(core.confPath, 'w').write(text)
        ##################### Saving ui config
        text = ''
        for item in self.uiPrefItems:
            text += item.confStr()
        text += 'showYmArrows=%r\n'%ui.showYmArrows
        text += 'prefPagesOrder=%s'%repr(tuple(
            [self.notebook.page_num(page) for page in self.prefPages]))
        open(ui.confPath, 'w').write(text)
        ##################### Saving here config
        text = ''
        for item in self.herePrefItems:
            text += item.confStr()
        for key in ('prevStock', 'nextStock'):
            text += '%s=%s\n'%(key, stock_arrow_repr(eval(key)))
        text += 'adjustTimeCmd=%r\n'%adjustTimeCmd ##???????????
        open(confPath, 'w').write(text)
        ################################################### Updating Main GUI
        self.mainWin.onConfigChange()
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
            d = gtk.Dialog(_('Need Restart StarCalendar'), self,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
                (gtk.STOCK_CANCEL, 0))
            d.set_keep_above(True)
            label = gtk.Label(_('Some preferences need for restart StarCalendar to apply.'))
            label.set_line_wrap(True)
            d.vbox.pack_start(label)
            resBut = d.add_button(_('_Restart'), 1)
            resBut.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH,gtk.ICON_SIZE_BUTTON))
            resBut.grab_default()
            d.vbox.show_all()
            if d.run()==1:
                self.mainWin.restart()
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
        #######
        self.checkYmArrows.set_active(ui.showYmArrows)
        self.ymArrowHbox.set_sensitive(ui.showYmArrows)
        self.im_num = 1
        self.imageSet(None, prevStock)
        self.im_num = 2
        self.imageSet(None, nextStock)
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
        about = gtk.AboutDialog()
        about.set_transient_for(self)
        about.set_name('')
        #about.set_name(plug.desc) ## or set_program_name
        #about.set_title(_('About ')+plug.desc) ## must call after set_name and set_version !
        about.set_title(_('About Plugin'))
        about.set_authors(plug.authors)
        about.set_comments(plug.about)
        #about.set_license(core.licenseText)
        #about.set_wrap_license(True)
        about.connect('delete-event', lambda w, e: w.destroy())
        about.connect('response', lambda w, e: w.destroy())
        #about.set_resizable(True)
        #about.vbox.show_all()## OR about.vbox.show_all() ; about.run()
        about.present()
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
                menu.add(labelImageMenuItem('Export to iCalendar', 'ical-32.png', self.plugExportToIcsClicked, plug))
                ##
                menu.show_all()
                menu.popup(None, None, None, 3, event.time)
            return True
        return False
    def plugAddClicked(self, button):
        ## ???????????????????????????
        ## Reize window to show all texts
        #self.plugAddTreeview.columns_autosize()#??????????
        (r, x, y, w, h) = self.plugAddTreeview.get_column(0).cell_get_size()
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
        print 'deleting', desc
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


