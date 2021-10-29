#!/bin/sh

for SZ in 16 22 24 32 48 ; do
	inkscape svg/starcal.svg \
		-w $SZ -h $SZ \
		--export-overwrite \
		--export-filename "icons/hicolor/${SZ}x${SZ}/apps/starcal.png"
done
