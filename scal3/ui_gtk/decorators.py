from gi.repository import GObject

def registerType(cls):
	GObject.type_register(cls)
	return cls

def registerSignals(cls):
	GObject.type_register(cls)
	for name, args in cls.signals:
		GObject.signal_new(name, cls, GObject.SignalFlags.RUN_LAST, None, args)
	return cls

