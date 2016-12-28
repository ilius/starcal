
class EventDiff:
	def __init__(self):
		self.clear()

	def clear(self):
		self.byEventId = {}
		'''
			self.byEventId = {
				eid -> (order, action, gid, path)
			}
			actions:
				'+'     add
				'-'     remove
				'e'     edit (modify) in-place
				'v'     move to a new path
		'''
		self.lastOrder = 0

	def add(self, action, event):
		eid = event.id
		gid = event.parent.id
		path = event.getPath()
		try:
			prefOrder, prefAction, prefGid, prefPath = self.byEventId[eid]
		except KeyError:
			self.byEventId[eid] = (self.lastOrder, action, gid, path)
			self.lastOrder += 1
		else:
			if prefAction == '-' or action == '+':
				raise RuntimeError(
					'EventDiff.add: eid=%s, ' % eid +
					'prefAction=%s, ' % prefAction +
					'action=%s' % action
				)
			both = prefAction + action
			if both in ('+e', 'ee', 've'):  # skip the new action
				pass
			elif both == '+-':  # remove the last '+' action
				del self.byEventId[eid]
			elif both in ('e-', 'ev'):  # replace the last edit action
				self.byEventId[eid] = self.lastOrder, action, gid, path
				self.lastOrder += 1
			elif both == 'v-':
				self.byEventId[eid] = prefOrder, prefAction, gid, path

	def __iter__(self):
		for order, action, eid, gid, path in sorted(
			(order, action, eid, gid, path)
			for eid, (order, action, gid, path) in self.byEventId.items()
		):
			if action == 'v':
				yield '-', eid, gid, path
				yield '+', eid, gid, path
			else:
				yield action, eid, gid, path
			del self.byEventId[eid]


def testEventDiff():
	d = EventDiff()
	for action, eid in [
		('+', 1),
		('+', 2),
		('+', 3),
		('-', 4),
		('e', 5),
		('-', 2),
		('e', 3),
		('e', 6),
		('e', 5),
	]:
		d.add(action, eid, None)
	for action, eid, path in d:
		print(action, eid)

if __name__ == '__main__':
	testEventDiff()
