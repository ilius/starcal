from __future__ import annotations

from typing import TYPE_CHECKING, Self

from scal3 import logger

log = logger.get()

from heapq import heappop, heappush
from math import log2 as math_log2

if TYPE_CHECKING:
	from collections.abc import Iterable

__all__ = ["MaxHeap"]


class MaxHeap[T](list):
	def copy(self) -> Self:
		return MaxHeap(self[:])

	def exch(self, i: int, j: int) -> None:
		self[i], self[j] = self[j], self[i]

	def less(self, i: int, j: int) -> bool:
		return self[i][0] > self[j][0]

	def swim(self, k: int) -> None:
		while k > 0:
			j = (k - 1) // 2
			if self.less(k, j):
				break
			self.exch(k, j)
			k = j

	def sink(self, k: int) -> None:
		N = len(self)
		while 2 * k < N - 1:
			j = 2 * k + 1
			if j < N - 1 and self.less(j, j + 1):
				j += 1
			if self.less(j, k):
				break
			self.exch(k, j)
			k = j

	def push(self, key: int, value: T) -> None:
		heappush(self, (-key, value))

	def pop(self, index: int | None = None) -> tuple[int, T]:
		if index is None:
			mkey, value = heappop(self)
		else:
			N = len(self)
			if index < 0 or index > N - 1:
				raise ValueError("invalid index to pop()")
			if index == N - 1:
				return list.pop(self, index)
			self.exch(index, N - 1)
			mkey, value = list.pop(self, N - 1)
			self.sink(index)
			self.swim(index)
		return -mkey, value

	def moreThan(self, key: int) -> Iterable[tuple[int, T]]:
		return self.moreThanStep(key, 0)

	def moreThanStep(self, key: int, index: int) -> Iterable[tuple[int, T]]:
		if index < 0:
			return
		try:
			item = self[index]
		except IndexError:
			return
		if -item[0] <= key:
			return
		yield -item[0], item[1]
		for k, v in self.moreThanStep(key, 2 * index + 1):
			yield k, v
		for k, v in self.moreThanStep(key, 2 * index + 2):
			yield k, v

	def __str__(self) -> str:
		return " ".join([str(-k) for k, v in self])

	def delete(self, key: int, value: T) -> None:
		try:
			index = self.index((-key, value))  # not optimal FIXME
		except ValueError:
			pass
		else:
			self.pop(index)

	def verify(self) -> bool:
		return self.verifyIndex(0)

	def verifyIndex(self, i: int) -> bool:
		assert i >= 0
		try:
			k = self[i]
		except IndexError:
			return True
		try:
			if self[2 * i + 1] < k:
				log.info(f"[{2 * i + 1}] > [{i}]")
				return False
		except IndexError:
			return True
		try:
			if self[2 * i + 2] < k:
				log.info(f"[{2 * i + 2}] > [{i}]")
				return False
		except IndexError:
			return True
		return self.verifyIndex(2 * i + 1) and self.verifyIndex(2 * i + 2)

	def getAll(self) -> Iterable[tuple[int, T]]:
		for key, value in self:
			yield -key, value

	def getMax(self) -> tuple[int, T]:
		if not self:
			raise ValueError("heap empty")
		k, v = self[0]
		return -k, v

	def getMin(self) -> tuple[int, T]:
		# at least 2 times faster than max(self)
		if not self:
			raise ValueError("heap empty")
		k, v = max(
			self[
				-(
					2
					** int(
						math_log2(len(self)),
					)
				) :
			],
		)
		return -k, v

	"""
	def deleteLessThanStep(self, key, index):
		try:
			key1, value1 = self[index]
		except IndexError:
			return
		key1 = -key1
		#if key
	def deleteLessThan(self, key):
		pass
	"""


def testGetMin(N: int) -> None:
	from random import randint

	h = MaxHeap()
	for _ in range(N):
		x = randint(1, 10 * N)
		h.push(x, 0)
	# t0 = perf_counter()
	k1 = -max(h)[0]
	# t1 = perf_counter()
	k2 = h.getMin()[0]
	# t2 = perf_counter()
	assert k1 == k2
	# log.debug(f"time getMin(h)/min(h) = {(t2-t1)/(t1-t0):.5f}")
	# log.debug(f"min key = {k1}")


def testDeleteStep(N: int, maxKey: int) -> bool:
	from random import randint

	# ---
	h = MaxHeap()
	for _ in range(N):
		h.push(randint(0, maxKey), 0)
	h0 = h.copy()
	rmIndex = randint(0, N - 1)
	rmKey = -h[rmIndex][0]
	rmKey2 = h.pop(rmIndex)
	if not h.verify():
		log.info(f"not verified, {N=}, I={rmIndex}")
		log.info(h0)
		log.info(h)
		log.info("------------------------")
		return False
	print(rmKey, rmKey2)  # noqa: T201
	return True


def testDelete() -> None:
	for N in range(10, 30):
		for _ in range(10000):
			if not testDeleteStep(N, 10000):
				break


# if __name__=="__main__":
# 	testDelete()
