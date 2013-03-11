from math import log
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
    keyCmp = lambda x1, x2: cmp(x1[0], x2[0])
    def delete(self, key, value):
        try:
            list.remove(self, (-key, value))
        except ValueError:
            pass
    getAll = lambda self: [(-key, value) for key, value in self]
    def getMax(self):
        if not self:
            raise ValueError('heap empty')
        k, v = self[0]
        return -k, v
    def getMin(self):
        ## at least 2 times faster than max(self)
        if not self:
            raise ValueError('heap empty')
        k, v = max(
            self[-2**int(
                log(len(self), 2)
            ):]
        )
        return -k, v



def getMinTest(N):
    from random import randint
    from time import time
    h = MaxHeap()
    for i in range(N):
        x = randint(1, 10*N)
        h.add(x, 0)
    t0 = time()
    k1 = -max(h)[0]
    t1 = time()
    k2 = h.getMin()[0]
    t2 = time()
    assert k1 == k2
    #print 'time getMin(h)/min(h) = %.5f'%((t2-t1)/(t1-t0))
    #print 'min key = %s'%k1

#if __name__=='__main__':
#    for i in range(10000):
#        getMinTest(100)




