import math
from scal2.utils import s_join

import heapq

class MaxHeap(list):
    add = lambda self, key, value: heapq.heappush(self, (-key, value))
    moreThan = lambda self, key: self.moreThanStep(key, 0)
    def moreThanStep(self, key, index):
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
    __str__ = lambda self: ' '.join(['%s:%s'%(-k,v) for k,v in self])
    delete = lambda self, key, value: list.remove(self, (-key, value))
    getAll = lambda self: [(-key, value) for key, value in self]
    def getMax(self):
        if not self:
            raise ValueError('heap empty')
        k,v = self[0]
        return -k, v

def test():
    import random
    toAdd = [
        (1, 101),
        (1, 102),
        (1, 103),
        (2, 104),
        (2, 105),
        (3, 106),
        (4, 107),
        (5, 108),
        (6, 109),
        (7, 110),
        (7, 111),
        (7, 112),
        (7, 113),
        (7, 114),
        (8, 115),
        (8, 116),
        (9, 117),
        (9, 118),
    ]
    random.shuffle(toAdd)
    h = MaxHeap()
    for key, val in toAdd:
        h.add(key, val)
    print h
    for key, val in sorted(h.moreThan(7)):
        print key, val


if __name__=='__main__':
    test()



