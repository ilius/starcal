
class EventDiff:
    def __init__(self):
        self.clear()    
    def clear(self):
        self.byEventId = {}## eid -> (order, action, path)
        self.lastOrder = 0
    def add(self, action, eid, path):
        try:
            lastOrder, lastAction, lastPath = self.byEventId[eid]
        except KeyError:
            self.byEventId[eid] = self.lastOrder, action, path
            self.lastOrder += 1
        else:
            if lastAction == '-' or action == '+':
                raise RuntimeError('EventDiff.add: eid=%s, lastAction=%s, action=%s'%(eid, lastAction, action))
            both = lastAction + action
            if both in ('+m', 'mm'):## skip the new action
                pass
            elif both == '+-':## remove the last '+' action 
                del self.byEventId[eid]
            elif both == 'm-':## replace the last 'm' action
                self.byEventId[eid] = self.lastOrder, action, path
                self.lastOrder += 1
    def __iter__(self):
        for order, action, eid, path in sorted([
            (order, action, eid, path)
            for eid, (order, action, path) in self.byEventId.items()
        ]):
            yield action, eid, path
            del self.byEventId[eid]

def testEventDiff():
    d = EventDiff()
    for action, eid in [
        ('+', 1),    
        ('+', 2),    
        ('+', 3),    
        ('-', 4),    
        ('m', 5),    
        ('-', 2),    
        ('m', 3),    
        ('m', 6),    
        ('m', 5),    
    ]:
        d.add(action, eid, None)
    for action, eid, path in d:
        print action, eid

if __name__=='__main__':
    testEventDiff()
















