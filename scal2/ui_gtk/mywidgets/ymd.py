from scal2.locale_man import tr as _
from scal2 import core
from scal2.core import getMonthLen

import gtk



class YearMonthDayBox(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self, spacing=4)
        self.mode = core.primaryMode
        ####
        self.pack_start(gtk.Label(_('Year')), 0, 0)
        spinY = gtk.SpinButton()
        spinY.set_increments(1, 10)
        spinY.set_range(-9999, 9999)
        spinY.set_width_chars(5)
        spinY.set_direction(gtk.TEXT_DIR_LTR)
        self.pack_start(spinY, 0, 0)
        self.spinY = spinY
        ####
        self.pack_start(gtk.Label(_('Month')), 0, 0)
        comboMonth = gtk.combo_box_new_text()
        module = core.modules[self.mode]
        for i in xrange(12):
            comboMonth.append_text(_(module.getMonthName(i+1, None)))## year=None means all months
        comboMonth.set_active(0)
        self.pack_start(comboMonth, 0, 0)
        self.comboMonth = comboMonth
        ####
        self.pack_start(gtk.Label(_('Day')), 0, 0)
        spinD = gtk.SpinButton()
        spinD.set_increments(1, 5)
        spinD.set_range(1, 31)
        spinD.set_width_chars(3)
        spinD.set_direction(gtk.TEXT_DIR_LTR)
        self.pack_start(spinD, 0, 0)
        self.spinD = spinD
        ####
        self.comboMonthConn = comboMonth.connect('changed', self.comboMonthChanged)
        spinY.connect('changed', self.comboMonthChanged) 
    def set_mode(self, mode):
        self.comboMonth.disconnect(self.comboMonthConn)
        self.mode = mode
        module = core.modules[mode]
        combo = self.comboMonth
        for i in xrange(len(combo.get_model())):
            combo.remove_text(0)
        for i in xrange(12):
            combo.append_text(_(module.getMonthName(i+1)))
        self.spinD.set_range(1, module.maxMonthLen)
        self.comboMonthConn = self.comboMonth.connect('changed', self.comboMonthChanged)
    def changeMode(self, mode, newMode):## FIXME naming standard?
        self.set_mode(newMode)
    def set_date(self, date):
        (y, m, d) = date
        self.spinY.set_value(y)
        self.comboMonth.set_active(m-1)
        self.spinD.set_value(d)
    def get_date(self):
        return (
            self.spinY.get_value_as_int(),
            self.comboMonth.get_active() + 1,
            self.spinD.get_value_as_int(),
        )
    def comboMonthChanged(self, widget=None):
        self.spinD.set_range(1, getMonthLen(
            self.spinY.get_value_as_int(),
            self.comboMonth.get_active() + 1,
            self.mode,
        ))








