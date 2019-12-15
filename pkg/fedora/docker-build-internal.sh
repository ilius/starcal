#!/bin/bash
set -e

outDir=$1
if [ -z "$outDir" ] ; then
	echo "Usage: $0 OUT_DIR"
	exit 1
fi


SHEBANG_FIX='s|#!/usr/bin/env python$|#!/usr/bin/env python3|'
sed -i "$SHEBANG_FIX" /root/starcal/libs/bson/setup.py
sed -i "$SHEBANG_FIX" /root/starcal/libs/bson/bson/network.py


dnf install -y rpm-build git-core desktop-file-utils gettext

mkdir -p "$outDir"
/root/starcal/pkg/fedora/build.sh $outDir /usr/bin/python3.7
