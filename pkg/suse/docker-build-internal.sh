#!/bin/bash

outDir=$1
if [ -z "$outDir" ] ; then
	echo "Usage: $0 OUT_DIR"
	exit 1
fi

zypper refresh

zypper --no-refresh install -y rpm-build
zypper --no-refresh install -y git-core

mkdir -p "$outDir"
/root/starcal/pkg/suse/build.sh $outDir /usr/bin/python3.7
