#!/usr/bin/env python3
def setupMenuHideOnLeave(menu):
	from time import time as now

	def menuLeaveNotify(m, e):
		t0 = now()
		if t0 - m.lastLeaveNotify < 0.001:
			timeout_add(500, m.hide)
		m.lastLeaveNotify = t0

	menu.lastLeaveNotify = 0
	menu.connect("leave-notify-event", menuLeaveNotify)
