from typing import reveal_type

from scal3.event_lib.groups import TaskList
from scal3.event_lib.pytypes import AccountType, EventGroupType

taskList: EventGroupType = TaskList()

# from .vcs import VcsCommitEventGroup
# vcsCommitEventGroup: EventGroupType = VcsCommitEventGroup()


from scal3.event_lib.accounts import Account

acc: AccountType = Account()  # type: ignore[abstract]
print(isinstance(acc, AccountType))  # Should be True
reveal_type(acc)


# from scal3.account.starcal import StarCalendarAccount
# acc2: AccountType = StarCalendarAccount()

from inspect import getmembers, isfunction


def compare_protocol_implementation(protocol: type, impl: type) -> None:
	protocol_methods = {
		name: member
		for name, member in getmembers(protocol, isfunction)
		if not name.startswith("_")
	}

	impl_methods = {
		name: member
		for name, member in getmembers(impl, isfunction)
		if not name.startswith("_")
	}

	print("\nMissing methods:")
	for name in protocol_methods.keys() - impl_methods.keys():
		print(f"- {name}")

	print("\nExtra methods:")
	for name in impl_methods.keys() - protocol_methods.keys():
		print(f"- {name}")

	print("\nSignature differences:")
	for name in protocol_methods.keys() & impl_methods.keys():
		proto_sig = str(protocol_methods[name])
		impl_sig = str(impl_methods[name])
		if proto_sig != impl_sig:
			print(f"\n{name}:")
			print(f"Protocol: {proto_sig}")
			print(f"Impl:    {impl_sig}")


compare_protocol_implementation(AccountType, Account)
