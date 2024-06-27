#!/bin/bash
set -e
set -x

function focus-to-press() {
	if [ -f "$2" ] ; then
		return
	fi
	cp "$1" "$2"
}

function do-add-press-to-theme() {
	focus-to-press close-focus.svg close-press.svg
	focus-to-press close-focus-light.svg close-press-light.svg

	focus-to-press left-focus.svg left-press.svg
	focus-to-press left-focus-light.svg left-press-light.svg

	focus-to-press maximize-focus.svg maximize-press.svg
	focus-to-press maximize-focus-light.svg maximize-press-light.svg

	focus-to-press minimize-focus.svg minimize-press.svg
	focus-to-press minimize-focus-light.svg minimize-press-light.svg

	focus-to-press right-focus.svg right-press.svg
	focus-to-press right-focus-light.svg right-press-light.svg
}

for theme in default grayscale mc-star ; do
	cd $theme
	do-add-press-to-theme
	cd ..
done

