
from scal3 import logger
log = logger.get()

import time
from time import time as now

from scal3.types_starcal import CompiledTimeFormat
from scal3.cal_types import calTypes, gregorian, to_jd
from scal3 import core
from scal3.format_time import compileTmFormat
from scal3 import ui


def formatTime(
	compiledFmt: CompiledTimeFormat,
	calType: int,
	jd: int,
	tm: float,
) -> str:
	cell = ui.cellCache.getCell(jd)
	pyFmt, funcs = compiledFmt
	return pyFmt % tuple(f(cell, calType, tm) for f in funcs)


def testSpeed():
	from time import strftime
	# fmt1 = "Date: %Y/%m/%d - Time: %H:%M:%S - %a %A %C %B %b %g %G %V"
	fmt1 = "%Y/%m/%d - %H:%M:%S"
	fmt2 = "%OY/%Om/%Od - %OH:%OM:%OS"
	n = 1000
	########
	compiledFmt = compileTmFormat(fmt1)
	calType = core.GREGORIAN
	tm = list(time.localtime())
	jd = to_jd(tm[0], tm[1], tm[2], calType)
	########
	t0 = now()
	for i in range(n):
		strftime(fmt1)
	t1 = now()
	log.info(f"Python strftime: {int(n / (t1 - t0)):7d} op/sec")
	########
	jd = to_jd(tm[0], tm[1], tm[2], calType)
	t0 = now()
	for i in range(n):
		formatTime(compiledFmt, calType, jd, tm)
	t1 = now()
	log.info(f"My strftime:     {int(n / (t1 - t0)):7d} op/sec")


def testOutput():
	from time import strftime
	compiledFmt = compileTmFormat("%Y/%m/%d")
	year = 2010
	month = 1
	day = 4
	jd = to_jd(year, month, day, core.GREGORIAN)
	tm = (year, month, day, 12, 10, 0, 15, 1, 1)
	log.info(formatTime(compiledFmt, core.GREGORIAN, jd, tm))
	log.info(strftime("%OY/%Om/%Od", tm))


if __name__ == "__main__":
	import sys
	testSpeed()
	# testOutput()
