from time import localtime

from gobject import timeout_add

from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

@registerSignals
class TimerButton(TimeButton):
	signals = [
		('time-elapse', []),
	]
	def __init__(self, **kwargs):
		TimeButton.__init__(self, **kwargs)
		#self.timer = False
		#self.clock = False
		self.delay = 1.0 # timer delay
		self.tPlus = -1 # timer plus (step)
		self.elapse = 0
	def timer_start(self):
		self.clock = False
		self.timer = True
		#self.delay = 1.0 # timer delay
		#self.tPlus = -1 # timer plus (step)
		#self.elapse = 0
		#########
		self.tOff = now()*self.tPlus - self.get_seconds()
		self.set_editable(False)
		self.timer_update()
	def timer_stop(self):
		self.timer = False
		self.set_editable(True)
	def timer_update(self):
		if not self.timer:
			return
		sec = int(now()*self.tPlus - self.tOff)
		self.set_seconds(sec)
		if self.tPlus*(sec-self.elapse) >= 0:
			self.emit('time-elapse')
			self.timer_stop()
		else:
			timeout_add(int(self.delay*1000), self.timer_update)
	def clock_start(self):
		self.timer = False
		self.clock = True
		self.set_editable(False)
		self.clock_update()
	def clock_stop(self):
		self.clock = False
		self.set_editable(True)
	def clock_update(self):
		if self.clock:
			timeout_add(time_rem(), self.clock_update)
			self.set_value(localtime()[3:6])


