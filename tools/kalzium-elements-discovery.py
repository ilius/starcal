import sys
from xml.etree.ElementTree import XML

sys.path.append("/starcal2")

from scal3 import event_lib, logger

log = logger.get()

from scal3.event_lib import ev

with open("/usr/share/apps/libkdeedu/data/elements.xml", encoding="utf-8") as _file:
	tree = XML(_file.read())


def decodeAtomElement(atom):
	data = {"id": atom.attrib["id"]}
	for el in atom:
		ref = el.attrib["dictRef"]
		ref = ref.removeprefix("bo:")
		if ref in {
			"name",
			"atomicNumber",
			"discoveryDate",
			"discoveryCountry",
			"discoverers",
		}:  # "symbol",
			try:
				data[ref] = el.attrib["value"]
			except KeyError:
				data[ref] = el.text.strip()
	# assert data["id"] == data["symbol"]
	return data


def createDiscoveryEvent(group, atom):
	if "discoveryDate" not in atom:
		log.info(f"no discoveryDate for {atom['id']}")
		return
	discoveryDate = int(atom["discoveryDate"])
	if discoveryDate < 1:
		log.info(f"empty discoveryDate ({atom['discoveryDate']!r}) for {atom['id']}")
		return
	description = atom["name"]
	if "discoverers" in atom:
		description += ", by " + atom["discoverers"].replace(";", ",")
	event = group.createEvent("largeScale")
	event.setDict(
		{
			"calType": "gregorian",
			"summary": "Element Discovery: " + atom["id"],
			"description": description,
			"scale": 1,
			"start": discoveryDate,
			"duration": 1,
		},
	)
	# log.debug(event.id)
	return event


if __name__ == "__main__":
	ev.groups.load()
	group = event_lib.LargeScaleGroup()
	group.setDict(
		{
			"calType": "gregorian",
			"color": [255, 0, 0],
			"title": "Elements Discovery",
		},
	)
	for atom in tree:
		if not atom.tag.endswith("atom"):
			continue
		atomData = decodeAtomElement(atom)
		event = createDiscoveryEvent(group, atomData)
		if event:
			event.save()
			group.append(event)
	group.save()
	ev.groups.append(group)
	ev.groups.save()
