from time import localtime
from time import time as now
from typing import Any

from scal3.time_utils import clockWaitMilliseconds
from scal3.ui_gtk import timeout_add
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton
from scal3.ui_gtk.signals import SignalHandlerBase, registerSignals

__all__ = ["TimerButton"]


@registerSignals
class SignalHandler(SignalHandlerBase):
	signals: list[tuple[str, list[Any]]] = [
		("time-elapse", []),
	]


class TimerButton(TimeButton):
	Sig = SignalHandler

	def __init__(self, **kwargs) -> None:
		TimeButton.__init__(self, **kwargs)
		# self.timer = False
		# self.clock = False
		self.delay = 1.0  # timer delay
		self.tPlus = -1  # timer plus (step)
		self.elapse = 0

	def timer_start(self) -> None:
		self.clock = False
		self.timer = True
		# self.delay = 1.0 # timer delay
		# self.tPlus = -1 # timer plus (step)
		# self.elapse = 0
		# ---------
		self.tOff = now() * self.tPlus - self.get_seconds()
		self.set_editable(False)
		self.timer_update()

	def timer_stop(self) -> None:
		self.timer = False
		self.set_editable(True)

	def timer_update(self) -> None:
		if not self.timer:
			return
		sec = int(now() * self.tPlus - self.tOff)
		self.set_seconds(sec)
		if self.tPlus * (sec - self.elapse) >= 0:
			self.emit("time-elapse")
			self.timer_stop()
		else:
			timeout_add(
				int(self.delay * 1000),
				self.timer_update,
			)

	def clock_start(self) -> None:
		self.timer = False
		self.clock = True
		self.set_editable(False)
		self.clock_update()

	def clock_stop(self) -> None:
		self.clock = False
		self.set_editable(True)

	def clock_update(self) -> None:
		if self.clock:
			timeout_add(
				clockWaitMilliseconds(),
				self.clock_update,
			)
			self.set_value(localtime()[3:6])
