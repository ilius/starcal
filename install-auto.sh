#!/usr/bin/env sh
set -x

if [ -f /etc/debian_version ] ; then
	if [ "$(lsb_release -is)" = "Ubuntu" ] ; then
		./distro/ubuntu/install.sh
	else
		./distro/debian/install.sh
	fi

elif [ -f /etc/SUSE-brand ] || [ -f /etc/products.d/openSUSE.prod ] ; then
	./distro/suse/install.sh

elif [ -f /etc/fedora-release ] ; then
	./distro/fedora/install.sh

elif [ -f /etc/arch-release ] ; then
	./distro/archlinux/install.sh

elif [ -f /etc/slackware-version ] ; then
	./distro/slackware/install.sh

elif [ "$(lsb_release -is)" = "NuTyX" ] ; then
	# or [ -f /bin/cards ]
	./distro/nutyx/install.sh

elif [ -f /etc/almalinux-release ] ; then
	./distro/almalinux/install.sh

elif [ -f /bin/freebsd-version ] ; then
	./distro/freebsd/install.sh

elif [ -f /bin/midnightbsd-version ] ; then
	./distro/midnightbsd/install.sh

else
	./install-pip
fi
