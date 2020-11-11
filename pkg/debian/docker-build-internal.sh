#!/bin/bash

outDir=$1
if [ -z "$outDir" ] ; then
	echo "Usage: $0 OUT_DIR"
	exit 1
fi

apt update

apt-get install --yes git

mkdir -p "$outDir"
/root/starcal/pkg/debian/build.sh $outDir
