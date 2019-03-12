#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# returns a float number that: 0 <= phase < 2
# 0.0 = no moon
# 1.0 = full moon
def getMoonPhase(jd, southernHemisphere=False):
	from scal3.cal_types import hijri
	_, _, d = hijri.jd_to(jd)
	if d >= 28:
		phase = 0.0
	else:
		phase = d / 14.0
	# 0 <= phase < 2
	if southernHemisphere:
		phase = (2.0 - phase) % 2.0
	return phase


