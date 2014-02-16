__all__ = [
    'rules',
    'notifiers',
    'occurrenceViews',
]

############################################

from scal2 import event_lib


modPrefix = 'scal2.ui_gtk.event.'


def makeWidget(obj):## obj is an instance of Event, EventRule, EventNotifier or EventGroup
    if hasattr(obj, 'WidgetClass'):
        widget = obj.WidgetClass(obj)
        try:
            widget.show_all()
        except AttributeError:
            widget.show()
        widget.updateWidget()## FIXME
        return widget
    else:
        return None


for cls in event_lib.classes.event:
    try:
        module = __import__(modPrefix + 'event.' + cls.name, fromlist=['EventWidget'])
        cls.WidgetClass = module.EventWidget
    except:
        myRaise()

for cls in event_lib.classes.rule:
    try:
        module = __import__(modPrefix + 'rule.' + cls.name, fromlist=['RuleWidget'])
    except:
        #if not cls.name.startswith('ex_'):
        myRaise()
        continue
    try:
        cls.WidgetClass = module.RuleWidget
    except AttributeError:
        print('no class RuleWidget defined in module "%s"'%cls.name)

for cls in event_lib.classes.notifier:
    try:
        module = __import__(modPrefix + 'notifier.' + cls.name, fromlist=['NotifierWidget', 'notify'])
        cls.WidgetClass = module.NotifierWidget
        cls.notify = module.notify
    except:
        myRaise()

for cls in event_lib.classes.group:
    try:
        module = __import__(modPrefix + 'group.' + cls.name, fromlist=['GroupWidget'])
    except:
        myRaise()
        continue
    try:
        cls.WidgetClass = module.GroupWidget
    except AttributeError:
        print('no class GroupWidget defined in module "%s"'%cls.name)

    for actionDesc, actionName in cls.actions:
        try:
            func = getattr(module, actionName)
        except AttributeError:
            print('no function %s defined in module "%s"'%(actionName, cls.name))
        else:
            setattr(cls, actionName, func)



for cls in event_lib.classes.account:
    try:
        module = __import__(modPrefix + 'account.' + cls.name, fromlist=['AccountWidget'])
    except:
        myRaise()
        continue
    try:
        cls.WidgetClass = module.AccountWidget
    except AttributeError:
        print('no class AccountWidget defined in module "%s"'%cls.name)


event_lib.EventRule.makeWidget = makeWidget
event_lib.EventNotifier.makeWidget = makeWidget
event_lib.Event.makeWidget = makeWidget
event_lib.EventGroup.makeWidget = makeWidget
event_lib.Account.makeWidget = makeWidget



### Load accounts, groups and trash? FIXME



import scal2.ui_gtk.event.import_customday ## opens a dialog if neccessery


