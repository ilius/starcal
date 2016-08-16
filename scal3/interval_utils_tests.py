import random

from scal3.interval_utils import *

def parseIntervalList(st, doShuffle=False):
	l = []
	for part in st.split(' '):
		pp = part.split('-')
		if len(pp)==1:
			start = end = int(pp[0])
		elif len(pp)==2:
			start = int(pp[0])
			end = int(pp[1])
		else:
			raise ValueError('bad IntervalList string %r' % st)
		l.append((start, end))
	if doShuffle:
		random.shuffle(l) # in-place
	#print(l)
	return l

def testnormalizeIntervalList():
	p = parseIntervalList
	assert normalizeIntervalList(p(
		'60-70 0-40 10-50 20-30 80-90 70-80 85-100 110 55',
		True,
	))==p('0-50 55 60-100 110')

	assert normalizeIntervalList(p(
		'10-20 20',
		True,
	))==p('10-20')# '10-20 20' FIXME



def testIntersection():
	p = parseIntervalList
	assert intersectionOfTwoIntervalList(
		p('0-15 16 17 30-50 70-90 110-120', True),
		p('10-35 40-75 80-100 110', True),
	)==p('10-15 16 17 30-35 40-50 70-75 80-90 110')

def testJdRanges():
	pprint.pprint(JdListOccurrence([1, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 18]).calcJdRanges())

def testSimplifyNumList():
	pprint.pprint(simplifyNumList([1, 2, 3, 4, 5, 7, 9, 10, 14, 16, 17, 18, 19, 21, 22, 23, 24]))

def testOverlapsSpeed():
	from random import normalvariate
	from time import time
	N = 2000000
	a0, b0 = -1, 1
	b_mean = 0
	b_sigma = 2
	###
	getRandomPair = lambda: sorted([normalvariate(b_mean, b_sigma) for i in (0, 1)])
	###
	data = []
	for i in range(N):
		a, b = getRandomPair()
		data.append((a, b))
	t0 = time()
	for a, b in data:
		ab_overlaps(a0, b0, a, b)
	print('%.2f'%(time()-t0))

if __name__=='__main__':
	import pprint
	testnormalizeIntervalList()
	testIntersection()


