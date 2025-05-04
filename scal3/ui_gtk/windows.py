from scal3.ui_gtk import timeout_add

__all__ = ["setupMenuHideOnLeave"]


def setupMenuHideOnLeave(menu) -> None:
	from time import time as now

	def menuLeaveNotify(m, _e) -> None:
		t0 = now()
		if t0 - m.lastLeaveNotify < 0.001:
			timeout_add(500, m.hide)
		m.lastLeaveNotify = t0

	menu.lastLeaveNotify = 0
	menu.connect("leave-notify-event", menuLeaveNotify)
