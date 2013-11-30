from scal2.locale_man import tr as _
from scal2.cal_types import calTypes
from scal2 import core
from scal2.core import getMonthLen

import gtk

from scal2.ui_gtk.mywidgets.multi_spin_button import YearSpinButton, DaySpinButton

class YearMonthDayBox(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self, spacing=4)
        self.mode = core.primaryMode
        ####
        self.pack_start(gtk.Label(_('Year')), 0, 0)
        self.spinY = YearSpinButton()
        self.pack_start(self.spinY, 0, 0)
        ####
        self.pack_start(gtk.Label(_('Month')), 0, 0)
        comboMonth = gtk.combo_box_new_text()
        module = calTypes[self.mode]
        for i in xrange(12):
            comboMonth.append_text(_(module.getMonthName(i+1, None)))## year=None means all months
        comboMonth.set_active(0)
        self.pack_start(comboMonth, 0, 0)
        self.comboMonth = comboMonth
        ####
        self.pack_start(gtk.Label(_('Day')), 0, 0)
        self.spinD = DaySpinButton()
        self.pack_start(self.spinD, 0, 0)
        self.comboMonthConn = comboMonth.connect('changed', self.comboMonthChanged)
        self.spinY.connect('changed', self.comboMonthChanged) 
    def set_mode(self, mode):
        self.comboMonth.disconnect(self.comboMonthConn)
        self.mode = mode
        module = calTypes[mode]
        combo = self.comboMonth
        for i in xrange(len(combo.get_model())):
            combo.remove_text(0)
        for i in xrange(12):
            combo.append_text(_(module.getMonthName(i+1)))
        self.spinD.set_range(1, module.maxMonthLen)
        self.comboMonthConn = self.comboMonth.connect('changed', self.comboMonthChanged)
    def changeMode(self, mode, newMode):## FIXME naming standard?
        self.set_mode(newMode)
    def set_value(self, date):
        y, m, d = date
        self.spinY.set_value(y)
        self.comboMonth.set_active(m-1)
        self.spinD.set_value(d)
    get_value = lambda self: (
        self.spinY.get_value(),
        self.comboMonth.get_active() + 1,
        self.spinD.get_value(),
    )
    def comboMonthChanged(self, widget=None):
        self.spinD.set_range(1, getMonthLen(
            self.spinY.get_value(),
            self.comboMonth.get_active() + 1,
            self.mode,
        ))








