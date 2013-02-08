import math
from scal2.utils import s_join

from heapq import heappush

class MaxHeap(list):
    add = lambda self, key, value: heappush(self, (-key, value))
    moreThan = lambda self, key: self.moreThanStep(key, 0)
    def moreThanStep(self, key, index):
        if index < 0:
            return []
        try:
            item = self[index]
        except IndexError:
            return []
        if -item[0] <= key:
            return []
        return [
                (-item[0], item[1])
            ] + \
            self.moreThanStep(key, 2*index+1) + \
            self.moreThanStep(key, 2*index+2)
    __str__ = lambda self: ' '.join(['%s:%s'%(-k, v) for k, v in self])
    delete = lambda self, key, value: list.remove(self, (-key, value))
    getAll = lambda self: [(-key, value) for key, value in self]
    def getMax(self):
        if not self:
            raise ValueError('heap empty')
        k, v = self[0]
        return -k, v



