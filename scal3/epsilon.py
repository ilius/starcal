import sys
# sys.float_info.epsilon == 2.220446049250313e-16


class NumPlusEpsilon(object):
	def __init__(self, num):
		self._num = num

	def getNum(self):
		return self._num

	def __str__(self):
		return "%s + eps" % self._num

	def __repr__(self):
		return "NumPlusEpsilon(%r)" % self._num

	def __hash__(self):
		return hash("%s+eps" % self._num)

	def is_integer(self):
		return False

	def __add__(self, other):
		if isinstance(other, NumPlusEpsilon):
			other = other.getNum()
		return NumPlusEpsilon(self._num + other)

	def __radd__(self, other):
		if isinstance(other, NumPlusEpsilon):
			other = other.getNum()
		return NumPlusEpsilon(other + self._num)

	def __bool__(self):
		return True

	def __eq__(self, other):
		if isinstance(other, NumPlusEpsilon):
			return self._num == other.getNum()
		return False

	def __ne__(self, other):
		if isinstance(other, NumPlusEpsilon):
			return self._num != other.getNum()
		return True

	def __int__(self):
		return int(self._num)

	def __float__(self):
		return float(self._num) + sys.float_info.epsilon

	def __floor__(self):
		return self._num.__floor__()

	def __ceil__(self):
		c = self._num.__ceil__()
		if c == self._num:
			c += 1
		return c

	def __gt__(self, other):
		if isinstance(other, NumPlusEpsilon):
			return self._num > other.getNum()
		return self._num >= other

	def __ge__(self, other):
		if isinstance(other, NumPlusEpsilon):
			return self._num >= other.getNum()
		return self._num >= other

	def __lt__(self, other):
		if isinstance(other, NumPlusEpsilon):
			return self._num < other.getNum()
		return self._num < other

	def __le__(self, other):
		if isinstance(other, NumPlusEpsilon):
			return self._num <= other.getNum()
		return self._num < other

	def __neg__(self):
		return NumMinusEpsilon(-self._num)

	def __abs__(self):
		if self._num >= 0:
			return self
		else:
			return -self


class NumMinusEpsilon(object):
	def __init__(self, num):
		self._num = num

	def getNum(self):
		return self._num

	def __str__(self):
		return "%s - eps" % self._num

	def __repr__(self):
		return "NumMinusEpsilon(%r)" % self._num

	def __hash__(self):
		return hash("%s-eps" % self._num)

	def is_integer(self):
		return False

	def __add__(self, other):
		if isinstance(other, NumMinusEpsilon):
			other = other.getNum()
		return NumMinusEpsilon(self._num + other)

	def __radd__(self, other):
		if isinstance(other, NumMinusEpsilon):
			other = other.getNum()
		return NumMinusEpsilon(other + self._num)

	def __bool__(self):
		return True

	def __eq__(self, other):
		if isinstance(other, NumMinusEpsilon):
			return self._num == other.getNum()
		return False

	def __ne__(self, other):
		if isinstance(other, NumMinusEpsilon):
			return self._num != other.getNum()
		return True

	def __int__(self):
		inum = int(self._num)
		if inum == self._num and inum > 0:
			return inum - 1
		else:
			return inum

	def __float__(self):
		return float(self._num) - sys.float_info.epsilon

	def __floor__(self):
		c = self._num.__floor__()
		if c == self._num:
			c -= 1
		return c

	def __ceil__(self):
		return self._num.__ceil__()

	def __gt__(self, other):
		if isinstance(other, NumMinusEpsilon):
			return self._num > other.getNum()
		return self._num > other

	def __ge__(self, other):
		if isinstance(other, NumMinusEpsilon):
			return self._num >= other.getNum()
		return self._num > other

	def __lt__(self, other):
		if isinstance(other, NumMinusEpsilon):
			return self._num < other.getNum()
		return self._num <= other

	def __le__(self, other):
		if isinstance(other, NumMinusEpsilon):
			return self._num <= other.getNum()
		return self._num <= other

	def __neg__(self):
		return NumPlusEpsilon(-self._num)

	def __abs__(self):
		if self._num >= 0:
			return self
		else:
			return -self
