import sys
from xml.etree.ElementTree import XML, tostring

sys.path.append('/starcal2')

from scal3 import event_lib
from scal3 import ui


tree = XML(open('/usr/share/apps/libkdeedu/data/elements.xml').read())


def decodeAtomElement(atom):
	data = {'id': atom.attrib['id']}
	for el in atom:
		ref = el.attrib['dictRef']
		if ref.startswith('bo:'):
			ref = ref[3:]
		if ref in (
			'name',
			'atomicNumber',
			'discoveryDate',
			'discoveryCountry',
			'discoverers',
		):  # 'symbol',
			try:
				data[ref] = el.attrib['value']
			except KeyError:
				data[ref] = el.text.strip()
	#assert data['id'] == data['symbol']
	return data


def createDiscoveryEvent(group, atom):
	if 'discoveryDate' not in atom:
		print('no discoveryDate for %s' % atom['id'])
		return
	discoveryDate = int(atom['discoveryDate'])
	if discoveryDate < 1:
		print('empty discoveryDate (%r) for %s' % (
			atom['discoveryDate'],
			atom['id'],
		))
		return
	description = atom['name']
	if 'discoverers' in atom:
		description += ', by %s' % atom['discoverers'].replace(';', ',')
	event = group.createEvent('largeScale')
	event.setData({
		'calType': 'gregorian',
		'summary': 'Element Discovery: %s' % atom['id'],
		'description': description,
		'scale': 1,
		'start': discoveryDate,
		'duration': 1,
	})
	#print(event.id)
	return event


if __name__ == '__main__':
	ui.eventGroups.load()
	group = event_lib.LargeScaleGroup()
	group.setData({
		'calType': 'gregorian',
		'color': [255, 0, 0],
		'title': 'Elements Discovery',

	})
	for atom in tree:
		if not atom.tag.endswith('atom'):
			continue
		atomData = decodeAtomElement(atom)
		event = createDiscoveryEvent(group, atomData)
		if event:
			event.save()
			group.append(event)
	group.save()
	ui.eventGroups.append(group)
	ui.eventGroups.save()
