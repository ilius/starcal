from os.path import join

from scal2.paths import *
from scal2 import core
from scal2 import ui
from scal2.format_time import compileTmFormat

import gobject

import gtk
from gtk import gdk

from scal2.ui_gtk.font_utils import gfontDecode

class IntegratedCalObj(gtk.Object):
    name = ''
    desc = ''
    items = [] ## FIXME
    def initVars(self, name, desc):
        self._name = name
        self.desc = desc
        self.items = []
        self.enable = True
    def onConfigChange(self, sender=None, emit=True):
        if emit:
            self.emit('config-change')
        for item in self.items:
            if item.enable and item is not sender:
                item.onConfigChange(emit=False)
    def onDateChange(self, sender=None, emit=True):
        if emit:
            self.emit('date-change')
        for item in self.items:
            if item.enable and item is not sender:
                item.onDateChange(emit=False)
    def __getitem__(self, key):
        for item in self.items:
            if item.name == key:
                return item
    def connectItem(self, item):
        item.connect('config-change', self.onConfigChange)
        item.connect('date-change', self.onDateChange)
    def insertItem(self, index, item):
        self.items.insert(index, item)
        self.connectItem(item)
    def appendItem(self, item):
        self.items.append(item)
        self.connectItem(item)
    @classmethod
    def registerSignals(cls):
        gobject.type_register(cls)
        gobject.signal_new('config-change', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
        gobject.signal_new('date-change', cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])


class IntegatedWindowList(IntegratedCalObj):
    def __init__(self):
        gtk.Object.__init__(self)
        self.initVars('windowList', 'Window List')
    def onConfigChange(self, *a, **ka):
        IntegratedCalObj.onConfigChange(self, *a, **ka)
        self.onDateChange()

####################################################

#IntegratedCalObj.registerSignals()
IntegatedWindowList.registerSignals()

windowList = IntegatedWindowList()

###########

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

#if not ui.fontUseDefault:## FIXME
#    settings.set_property('gtk-font-name', fontCustom)


dateFormat = '%Y/%m/%d'
clockFormat = '%X' ## '%T', '%X' (local), '<b>%T</b>', '%m:%d'

dateBinFmt = compileTmFormat(dateFormat)
clockFormatBin = compileTmFormat(clockFormat)

adjustTimeCmd = ''

prevStock = gtk.STOCK_GO_BACK
nextStock = gtk.STOCK_GO_FORWARD

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




