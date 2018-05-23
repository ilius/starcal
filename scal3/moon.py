# -*- coding: utf-8 -*-

# returns a float number that: 0 <= phase < 2
# 0.0 = no moon
# 1.0 = full moon
def getMoonPhase(jd):
	from scal3.cal_types import hijri
	_, _, d = hijri.jd_to(jd)
	if d >= 28:
		return 0.0
	return d / 14.0


