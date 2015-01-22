from scal2.ui_gtk import *

def getDateTimeWidget():
    from scal2.ui_gtk.mywidgets.multi_spin.date_time import DateTimeButton
    btn = DateTimeButton()
    btn.set_value((2011, 1, 1))
    return btn

def getIntWidget():
    from scal2.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
    btn = IntSpinButton(0, 99)
    btn.set_value(12)
    return btn

def getFloatWidget():
    from scal2.ui_gtk.mywidgets.multi_spin.float import FloatSpinButton
    btn = FloatSpinButton(-3.3, 5.5, 1)
    btn.set_value(3.67)
    return btn

def getFloatBuiltinWidget():
    btn = gtk.SpinButton()
    btn.set_range(0, 90)
    btn.set_digits(2)
    btn.set_increments(0.01, 1)
    return btn


if __name__=='__main__':
    d = gtk.Dialog()
    btn = getFloatWidget()
    btn.set_editable(True)
    pack(d.vbox, btn, 1, 1)
    d.vbox.show_all()
    d.run()
    print(btn.get_value())


