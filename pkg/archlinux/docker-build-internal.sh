#!/bin/bash
set -e

outDir=$1
if [ -z "$outDir" ] ; then
	echo "Usage: $0 OUT_DIR"
	exit 1
fi

pacman -Sy --noconfirm git gettext fakeroot binutils file gawk

mkdir -p "$outDir"
chown build "$outDir"
su build -c "/home/build/starcal/pkg/archlinux/build.sh \"$outDir\" /usr/bin/python3"
