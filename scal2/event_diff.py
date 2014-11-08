
class EventDiff:
    def __init__(self):
        self.clear()    
    def clear(self):
        self.byEventId = {}
        '''
            self.byEventId = {
                eid -> (order, action, args)
            }
            actions:
                '+'     add
                '-'     remove
                'm'     modify (edit)
                'v'     move to a new path
        '''
        self.lastOrder = 0
    def add(self, action, eid, *args):
        try:
            prefOrder, prefAction, prefArgs = self.byEventId[eid]
        except KeyError:
            self.byEventId[eid] = (self.lastOrder, action, args)
            self.lastOrder += 1
        else:
            if prefAction == '-' or action == '+':
                raise RuntimeError('EventDiff.add: eid=%s, prefAction=%s, action=%s'%(eid, prefAction, action))
            both = prefAction + action
            if both in ('+m', 'mm', 'vm'):## skip the new action
                pass
            elif both == '+-':## remove the last '+' action 
                del self.byEventId[eid]
            elif both in ('m-', 'mv'):## replace the last 'm' action
                self.byEventId[eid] = self.lastOrder, action, args
                self.lastOrder += 1
            elif both == 'v-':
                self.byEventId[eid] = prefOrder, prefAction, args[1:]
    def __iter__(self):
        for order, action, eid, args in sorted([
            (order, action, eid, args)
            for eid, (order, action, args) in self.byEventId.items()
        ]):
            if action == 'v':
                yield '-', eid, args[:1]
                yield '+', eid, args[1:]
            else:
                yield action, eid, args
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
















