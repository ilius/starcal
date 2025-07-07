from __future__ import annotations

import random

from scal3 import core
from scal3.event_lib import JdOccurSet
from scal3.interval_utils import (
	CLOSED_END,
	CLOSED_START,
	OPEN_END,
	ab_overlaps,
	getIntervalListByPoints,
	humanizeIntervalList,
	intersectionOfTwoIntervalList,
	log,
	simplifyNumList,
)


# TODO: remove this, test getIntervalPoints2 and getIntervalPoints3
def getIntervalPoints(
	lst: list[tuple[int, int] | tuple[int, int, bool]]
	| list[tuple[int, int]]
	| list[tuple[int, int, bool]],
	lst_index: int = 0,
) -> list[tuple[int, int, int]]:
	"""
	Lst is a list of (start, end, closedEnd) or (start, end) tuples
		start (int)
		end (int)
		closedEnd (bool).

	returns a list of (pos, ptype, lst_index) tuples
	ptype is one of (CLOSED_START, OPEN_START, OPEN_END, CLOSED_END)
	"""
	points: list[tuple[int, int, int]] = []
	for row in lst:
		start = row[0]
		end = row[1]
		if len(row) > 2:
			closedEnd = row[2]
		else:
			closedEnd = start == end
		points += [
			(
				start,
				CLOSED_START,
				lst_index,
			),
			(
				end,
				CLOSED_END if closedEnd else OPEN_END,
				lst_index,
			),
		]
	return points


def normalizeIntervalList(
	lst: list[tuple[int, int] | tuple[int, int, bool]],
) -> list[tuple[int, int, bool]]:
	return getIntervalListByPoints(sorted(getIntervalPoints(lst)))


def parseIntervalList(st: str, doShuffle: bool = False) -> list[tuple[int, int]]:
	ls = []
	for part in st.split(" "):
		pp = part.split("-")
		if len(pp) == 1:
			start = end = int(pp[0])
		elif len(pp) == 2:
			start = int(pp[0])
			end = int(pp[1])
		else:
			raise ValueError(f"bad IntervalList string {st!r}")
		ls.append((start, end))
	if doShuffle:
		random.shuffle(ls)  # in-place
	# log.debug(ls)
	return ls


def testnormalizeIntervalList() -> None:
	testDict = {
		"10-20 20": "10-20 20",
		"10-20 20 20": "10-20 20",
		"10-20 20-30": "10-30",
		"10-20 20-30 30-40": "10-40",
		"10-20 20-30 25-40": "10-40",
		"1-10 14 2-5 9-13 16-18 17-20 15-16 25-30": "1-13 14 15-20 25-30",
		"60-70 0-40 10-50 20-30 80-90 70-80 85-100 110 55": "0-50 55 60-100 110",
	}

	for inpStr, ansStr in testDict.items():
		inpList = parseIntervalList(inpStr, True)
		ansList = parseIntervalList(ansStr, False)
		resList = normalizeIntervalList(inpList)  # type: ignore[arg-type]
		resList = humanizeIntervalList(resList)  # type: ignore[assignment]
		if resList == ansList:  # type: ignore[comparison-overlap]
			log.info("OK")
		else:
			log.error(f"Failed: {resList!r} != {ansList!r}")


def testIntersection() -> None:
	testDict = {
		(
			"0-20",
			"10-30",
		): "10-20",
		(
			"10-30 40-50 60-80",
			"25-45",
		): "25-30 40-45",
		(
			"10-30 40-50 60-80",
			"25-45 50-60",
		): "25-30 40-45",
		(
			"10-30 40-50 60-80",
			"25-45 50-60 60",
		): "25-30 40-45 60",
		(
			"10-30 40-50 60-80",
			"25-45 48-70 60",
		): "25-30 40-45 48-50 60-70",
		(
			"10-30 40-50 60-80",
			"25-45 48-70",
		): "25-30 40-45 48-50 60-70",
		(
			"0-10 20-30 40-50 60-70",
			"1-2 6-7 11-12 16-17 21-22 26-27 27",
		): "1-2 6-7 21-22 26-27 27",
		(
			"0-15 16 17 30-50 70-90 110-120",
			"10-35 40-75 80-100 110",
		): "10-15 16 17 30-35 40-50 70-75 80-90 110",
	}

	for (list1Str, list2Str), answerStr in testDict.items():
		list1 = parseIntervalList(list1Str, True)
		list2 = parseIntervalList(list2Str, True)
		answer = parseIntervalList(answerStr, False)
		# ^ no shuffle
		result = intersectionOfTwoIntervalList(list1, list2)
		if result == answer:
			log.info("OK")
		else:
			log.error("Failed")
			log.info(f"{list1Str=}, {list2Str=}")
			log.info(f"{result=}")
			log.info("")


def testJdRanges() -> None:
	from pprint import pprint

	pprint(
		JdOccurSet(
			{
				1,
				3,
				4,
				5,
				7,
				9,
				10,
				11,
				12,
				13,
				14,
				18,
			},
		).calcJdRanges(),
	)


def testSimplifyNumList() -> None:
	from pprint import pprint

	pprint(
		simplifyNumList(
			[
				1,
				2,
				3,
				4,
				5,
				7,
				9,
				10,
				14,
				16,
				17,
				18,
				19,
				21,
				22,
				23,
				24,
			],
		),
	)


def testOverlapsSpeed() -> None:
	from random import normalvariate
	from time import perf_counter

	N = 2000000
	a0, b0 = -1, 1
	b_mean = 0
	b_sigma = 2

	def getRandomPair() -> tuple[float, float]:
		a = normalvariate(b_mean, b_sigma)
		b = normalvariate(b_mean, b_sigma)
		return min(a, b), max(a, b)

	# ---
	data = []
	for _i in range(N):
		a, b = getRandomPair()
		data.append((a, b))
	t0 = perf_counter()
	for a, b in data:
		ab_overlaps(a0, b0, a, b)
	log.info(f"{perf_counter() - t0:.2f}")


if __name__ == "__main__":
	testnormalizeIntervalList()
	testIntersection()
	testJdRanges()
	testSimplifyNumList()
	core.stopRunningThreads()
