import random

from scal3.interval_utils import *
from scal3.event_lib import JdOccurSet
from scal3 import core


def parseIntervalList(st, doShuffle=False):
	l = []
	for part in st.split(' '):
		pp = part.split('-')
		if len(pp) == 1:
			start = end = int(pp[0])
		elif len(pp) == 2:
			start = int(pp[0])
			end = int(pp[1])
		else:
			raise ValueError('bad IntervalList string %r' % st)
		l.append((start, end))
	if doShuffle:
		random.shuffle(l)  # in-place
	#print(l)
	return l


def testnormalizeIntervalList():
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
		resList = normalizeIntervalList(inpList)
		resList = humanizeIntervalList(resList)
		if resList == ansList:
			print("OK")
		else:
			print("Failed: %r != %r" % (resList, ansList))


def testIntersection():
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
		answer = parseIntervalList(answerStr, False)# no shuffle
		result = intersectionOfTwoIntervalList(list1, list2)
		if result == answer:
			print('OK')
		else:
			print('Failed')
			print((list1Str, list2Str))
			print(result)
			print()


def testJdRanges():
	pprint.pprint(JdOccurSet([
		1, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 18,
	]).calcJdRanges())


def testSimplifyNumList():
	pprint.pprint(simplifyNumList([
		1, 2, 3, 4, 5, 7, 9, 10, 14, 16, 17, 18, 19, 21, 22, 23, 24,
	]))


def testOverlapsSpeed():
	from random import normalvariate
	from time import time
	N = 2000000
	a0, b0 = -1, 1
	b_mean = 0
	b_sigma = 2
	###
	getRandomPair = lambda: sorted(
		normalvariate(b_mean, b_sigma)
		for i in (0, 1)
	)
	###
	data = []
	for i in range(N):
		a, b = getRandomPair()
		data.append((a, b))
	t0 = time()
	for a, b in data:
		ab_overlaps(a0, b0, a, b)
	print('%.2f' % (time() - t0))


if __name__ == '__main__':
	import pprint
	testnormalizeIntervalList()
	testIntersection()
	testJdRanges()
	testSimplifyNumList()
	core.stopRunningThreads()
