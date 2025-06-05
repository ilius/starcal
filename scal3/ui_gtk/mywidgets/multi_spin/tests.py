from scal3 import logger

log = logger.get()

from scal3.ui_gtk import Dialog, gtk, pack


def getDateTimeWidget():
	from scal3.ui_gtk.mywidgets.multi_spin.date_time import DateTimeButton

	btn = DateTimeButton()
	btn.set_value((2011, 1, 1))
	btn.set_editable(True)
	return btn


def getIntWidget():
	from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton

	btn = IntSpinButton(0, 99)
	btn.set_value(12)
	btn.set_editable(True)
	return btn


def getFloatWidget():
	from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton

	btn = FloatSpinButton(-10, 10, 1)
	btn.set_value(-3)
	btn.set_editable(True)
	return btn


def getFloatBuiltinWidget():
	btn = gtk.SpinButton()
	btn.set_range(0, 90)
	btn.set_digits(2)
	btn.set_increments(0.01, 1)
	btn.set_editable(True)
	return btn


def getTimerWidget():
	from scal3.ui_gtk.mywidgets.multi_spin.timer import TimerButton

	btn = TimerButton()
	btn.clock_start()
	return btn


if __name__ == "__main__":
	d = Dialog()
	btn = getFloatWidget()
	pack(d.vbox, btn, True, True)
	d.vbox.show_all()
	d.run()
	log.info(btn.get_value())
