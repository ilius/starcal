#!/bin/bash
set -e

outDir=$1
if [ -z "$outDir" ] ; then
	echo "Usage: $0 OUT_DIR"
	exit 1
fi

# echo 'nameserver 1.1.1.1' >> /etc/resolv.conf

dnf install --assumeyes rpm-build git-core desktop-file-utils gettext

mkdir -p "$outDir"
/root/starcal/distro/fedora/build.sh "$outDir" /usr/bin/python3
