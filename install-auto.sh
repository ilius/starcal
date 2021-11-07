#!/usr/bin/env sh

if [ -f /etc/debian_version ] ; then
	if [ "$(lsb_release -is)" = "Ubuntu" ] ; then
		./distro/ubuntu/install.sh
	else
		./distro/debian/install.sh
	fi

elif [ -f /etc/SUSE-brand ] || [ -f /etc/products.d/openSUSE.prod ] ; then
	./distro/suse/install.sh

elif [ -f /etc/redhat-release ] ; then
	./distro/fedora/install.sh

elif [ -f /etc/arch-release ] ; then
	./distro/archlinux/install.sh

elif [ -f /etc/slackware-version ] ; then
	./distro/slackware/install.sh

elif [ -f /bin/freebsd-version ] ; then
	./distro/freebsd/install.sh

else
	./install-pip
fi
