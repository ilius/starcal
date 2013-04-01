import gobject

def registerType(cls):
    gobject.type_register(cls)
    return cls

def registerSignals(cls):
    gobject.type_register(cls)
    for name, args in cls.signals:
        gobject.signal_new(name, cls, gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, args)
    return cls

