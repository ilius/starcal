#!/usr/bin/env python3
from scal3 import logger
log = logger.get()

from gi.repository import GObject


def registerType(cls):
	GObject.type_register(cls)
	return cls


def registerSignals(cls):
	GObject.type_register(cls)
	for name, args in cls.signals:
		try:
			GObject.signal_new(
				name,
				cls,
				GObject.SignalFlags.RUN_LAST,
				None,
				args,
			)
		except Exception as e:
			log.error(
				"Failed to create signal %s " % name +
				"for class %s in %s" % (cls.__name__, cls.__module__),
			)
	return cls
