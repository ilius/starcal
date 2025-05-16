from scal3 import logger
from scal3.ui_gtk.customize import CustomizableCalObj

log = logger.get()

from time import localtime
from time import time as now

from scal3 import ui
from scal3.ui_gtk import timeout_add_seconds

__all__ = ["dateChange"]
dayLen = 24 * 3600


class DateChangeListener:
	def __init__(self, timeout: float = 1) -> None:
		self.timeout = timeout  # seconds
		self.receivers = []
		self.gdate = localtime()[:3]
		self.check()

	def add(self, receiver: CustomizableCalObj) -> None:
		self.receivers.append(receiver)

	def check(self) -> None:
		tm = now()
		gdate = localtime(tm)[:3]
		if gdate != self.gdate:
			self.gdate = gdate
			ui.cells.today = ui.cells.getTodayCell()
			for obj in self.receivers:
				obj.onCurrentDateChange(gdate)
		# timeout_add_seconds(
		# 	int(dayLen - (tm + getUtcOffsetCurrent()) % dayLen) + 1,
		# 	self.check,
		# )
		timeout_add_seconds(self.timeout, self.check)
		if ui.mainWin:
			ui.mainWin.statusIconUpdateTooltip()


# class TimeChangeListener:


dateChange = DateChangeListener()
# timeChange = TimeChangeListener()

if __name__ == "__main__":
	from gi.repository import GLib as glib

	class TestRec:
		def onCurrentDateChange(self, gdate: tuple[int, int, int]) -> None:  # noqa: PLR6301
			log.info(f"current date changed to {gdate!r}")

	dateChange.add(TestRec())
	glib.MainLoop().run()
