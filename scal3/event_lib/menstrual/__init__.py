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

"""
Menstrual cycle calendar: period, fertile window and ovulation tracking.

Domain model (see ``doc/ovulation-cal/proposal.md``):

- Ovulation is estimated to happen ``cycleLength - lutealPhase`` days after the
  first day of the period (the luteal phase is the stable ~14-day part).
- The fertile window is the 6-day span ending on the estimated ovulation day
  (5 days before + ovulation day), following Wilcox 1995.
- The day-specific probability of conception relative to ovulation is taken
  from the Wilcox 1995 study (10% at -5 days up to 33% on ovulation day).

The group maintains recorded period-start events and automatically generates
derived events for the fertile window, the ovulation day, and predicted
future periods, so that each phase shows its own icon in the calendar cells
without changing the cell background color.
"""

from __future__ import annotations

from scal3.event_lib.menstrual._events import (
	MenstrualFertileEvent,
	MenstrualObservationEvent,
	MenstrualOvulationEvent,
	MenstrualPeriodEvent,
)
from scal3.event_lib.menstrual._group import MenstrualCycleGroup
from scal3.event_lib.menstrual._stats import (
	computeCycleStats,
	dayProbabilityRelativeToOvulation,
	fertileWindowDays,
	observationFlowLabels,
	observationMucusLabels,
	observationOpkLabels,
	observationRecordedByLabels,
	predictNextPeriod,
	predictOvulation,
)

__all__ = [
	"MenstrualCycleGroup",
	"MenstrualFertileEvent",
	"MenstrualObservationEvent",
	"MenstrualOvulationEvent",
	"MenstrualPeriodEvent",
	"computeCycleStats",
	"dayProbabilityRelativeToOvulation",
	"fertileWindowDays",
	"observationFlowLabels",
	"observationMucusLabels",
	"observationOpkLabels",
	"observationRecordedByLabels",
	"predictNextPeriod",
	"predictOvulation",
]
