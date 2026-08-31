#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING

from scal3.locale_man import tr as _

if TYPE_CHECKING:
	from collections.abc import Sequence

__all__ = [
	"_menstrualIcon",
	"_percent",
	"computeCycleStats",
	"dayProbabilityRelativeToOvulation",
	"defaultCycleLength",
	"defaultLutealPhase",
	"defaultPeriodLength",
	"fertileWindowDays",
	"observationFlowLabels",
	"observationMucusLabels",
	"observationOpkLabels",
	"observationRecordedByLabels",
	"predictNextPeriod",
	"predictOvulation",
]

#: day-specific probability of conception given intercourse on that day,
#: keyed by days before ovulation (Wilcox et al., NEJM 1995;333:1517-21)
WILCOX_DAY_PROBABILITY: dict[int, float] = {
	5: 0.10,
	4: 0.16,
	3: 0.14,
	2: 0.27,
	1: 0.31,
	0: 0.33,
}

#: fertile window begins this many days before the estimated ovulation day
FERTILE_WINDOW_DAYS_BEFORE = 5

#: fertile window extends this many days after the estimated ovulation day
FERTILE_WINDOW_DAYS_AFTER = 1

defaultPeriodLength = 5
defaultLutealPhase = 14
defaultCycleLength = 28

#: translated labels for observation field values
observationRecordedByLabels: dict[str, str] = {
	"woman": _("Woman"),
	"partner": _("Partner"),
}
observationFlowLabels: dict[str, str] = {
	"none": _("None"),
	"light": _("Light"),
	"medium": _("Medium"),
	"heavy": _("Heavy"),
}
observationMucusLabels: dict[str, str] = {
	"": _("Not observed"),
	"dry": _("Dry"),
	"sticky": _("Sticky"),
	"creamy": _("Creamy"),
	"watery": _("Watery"),
	"eggwhite": _("Egg White"),
}
observationOpkLabels: dict[str, str] = {
	"": _("Not tested"),
	"negative": _("Negative"),
	"positive": _("Positive"),
}


def _menstrualIcon(name: str) -> str:
	"""Return the relative SVG icon path for an event type."""
	return f"event/{name}.svg"


def computeCycleStats(
	periodStartJds: Sequence[int],
) -> tuple[int | None, int | None, int | None]:
	"""
	Return (avgCycle, minCycle, maxCycle) in days for sorted period start JDs.

	The average is a recency-weighted mean of the measured cycle lengths.
	Returns (None, None, None) when fewer than two starts are given.
	"""
	if len(periodStartJds) < 2:
		return None, None, None
	lengths = [b - a for a, b in pairwise(periodStartJds)]
	minCycle = min(lengths)
	maxCycle = max(lengths)
	weights = list(range(1, len(lengths) + 1))
	totalWeight = sum(weights)
	avgCycle = round(
		sum(length * weight for length, weight in zip(lengths, weights, strict=True))
		/ totalWeight,
	)
	return avgCycle, minCycle, maxCycle


def predictOvulation(
	periodStartJd: int,
	cycleLength: int,
	lutealPhase: int,
) -> int:
	"""Estimate the ovulation Julian day for a cycle starting at periodStartJd."""
	return periodStartJd + (cycleLength - lutealPhase)


def predictNextPeriod(
	periodStartJd: int,
	cycleLength: int,
) -> int:
	"""Estimate the next period-start Julian day for a given cycle."""
	return periodStartJd + cycleLength


def fertileWindowDays(
	ovulationJd: int | None,
	*,
	mode: str = "fixed",
	periodStartJd: int | None = None,
	minCycle: int | None = None,
	maxCycle: int | None = None,
) -> list[int]:
	"""
	Return the fertile-window Julian days for a cycle.

	fixed mode: the days around the estimated ovulation day (5 days before and
	1 day after), excluding the ovulation day itself which is shown by the
	ovulation event.

	oginoKnaus mode: the classic Knaus-Ogino range derived from the shortest
	and longest recorded cycle lengths (first fertile day = minCycle - 18,
	last fertile day = maxCycle - 11, counted from ``periodStartJd``).
	"""
	if mode == "oginoKnaus":
		assert minCycle is not None
		assert maxCycle is not None
		assert periodStartJd is not None
		first = periodStartJd + (minCycle - 18)
		last = periodStartJd + (maxCycle - 11)
		return list(range(first, last + 1))
	assert ovulationJd is not None
	days = list(
		range(
			ovulationJd - FERTILE_WINDOW_DAYS_BEFORE,
			ovulationJd + FERTILE_WINDOW_DAYS_AFTER + 1,
		),
	)
	# exclude the ovulation day, it is marked by the ovulation event
	days.remove(ovulationJd)
	return days


def dayProbabilityRelativeToOvulation(
	daysBeforeOvulation: int,
	includeDayAfterProbability: float = 0.0,
) -> float:
	"""
	Return the estimated probability of conception given intercourse on a day
	``daysBeforeOvulation`` days before the estimated ovulation day (positive
	values are before ovulation, 0 is ovulation day, negative values are after).
	"""
	if daysBeforeOvulation in WILCOX_DAY_PROBABILITY:
		return WILCOX_DAY_PROBABILITY[daysBeforeOvulation]
	if daysBeforeOvulation == -1:
		return includeDayAfterProbability
	return 0.0


def _percent(value: float) -> int:
	"""Return a whole percent (0-100) for a probability fraction."""
	return round(value * 100)
