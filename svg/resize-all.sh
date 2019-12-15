#!/bin/bash

if [ -n "$1" ] ; then
	FILES="$@"
else
	FILES=*.svg
fi

for old in $FILES ; do
    new="$(echo "$old" | sed -e 's/svg$/new.svg/')"
    rsvg-convert "$old" -w 320 -h 320 -f svg -o "$new"
    cp "$new" "$old"
    rm "$new"
done
