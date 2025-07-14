
from scal3.event_lib.groups import TaskList
from scal3.event_lib.pytypes import EventGroupType
from scal3.filesystem import FileSystem  # noqa: F401

taskList: EventGroupType = TaskList()

# from .vcs import VcsCommitEventGroup
# vcsCommitEventGroup: EventGroupType = VcsCommitEventGroup()


from scal3.event_lib.accounts import Account
from scal3.event_lib.pytypes import AccountType

acc: AccountType = Account()
print(isinstance(acc, AccountType))  # Should be True
# from typing import reveal_type
# reveal_type(acc)

from scal3.event_lib.notifiers import AlarmNotifier
from scal3.event_lib.pytypes import EventNotifierType

notif: EventNotifierType = AlarmNotifier(None)  # type: ignore[arg-type]


# from scal3.account.starcal import StarCalendarAccount
# acc2: AccountType = StarCalendarAccount()

# from inspect import getmembers, isfunction
# from typing import get_type_hints


# def compare_protocol_implementation(protocol, impl) -> None:
# 	# Get all protocol attributes with their types
# 	protocol_attrs = {}
# 	for name, attr in getmembers(protocol, lambda x: not isfunction(x)):
# 		if not name.startswith("_"):
# 			attr_type = get_type_hints(protocol.__dict__[name])
# 			protocol_attrs[name] = {
# 				"type": attr_type.get(name),
# 				"is_property": isinstance(attr, property),
# 				"is_descriptor": isinstance(
# 					attr, (property, classmethod, staticmethod)
# 				),
# 			}

# 	# Get implementation attributes
# 	impl_attrs = {}
# 	for name, attr in getmembers(impl):
# 		if not name.startswith("_"):
# 			attr_type = get_type_hints(getattr(impl, name).__dict__)
# 			impl_attrs[name] = {
# 				"type": attr_type.get(name),
# 				"is_property": isinstance(attr, property),
# 				"is_descriptor": isinstance(
# 					attr, (property, classmethod, staticmethod)
# 				),
# 			}

# 	# Compare attributes
# 	print("\nMissing attributes:")
# 	for name in protocol_attrs.keys() - impl_attrs.keys():
# 		attr_info = protocol_attrs[name]
# 		print(f"- {name} ({attr_info['type']})")
# 		if attr_info["is_property"]:
# 			print("  Expected: property")
# 		elif attr_info["is_descriptor"]:
# 			print("  Expected: descriptor")

# 	print("\nExtra attributes:")
# 	for name in impl_attrs.keys() - protocol_attrs.keys():
# 		attr_info = impl_attrs[name]
# 		print(f"- {name} ({attr_info['type']})")
# 		if attr_info["is_property"]:
# 			print("  Found: property")
# 		elif attr_info["is_descriptor"]:
# 			print("  Found: descriptor")

# 	print("\nType mismatches:")
# 	for name in protocol_attrs.keys() & impl_attrs.keys():
# 		proto_info = protocol_attrs[name]
# 		impl_info = impl_attrs[name]

# 		if proto_info != impl_info:
# 			print(f"\n{name}:")
# 			print(
# 				f"Protocol: {proto_info['type']} "
# 				f"({'property' if proto_info['is_property'] else 'descriptor'})"
# 			)
# 			print(
# 				f"Impl:     {impl_info['type']} "
# 				f"({'property' if impl_info['is_property'] else 'descriptor'})"
# 			)


# compare_protocol_implementation(AccountType, Account)
