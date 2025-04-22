#!/bin/bash

myPath="$0"
if [ "${myPath:0:2}" == "./" ] ; then
	myPath=$PWD${myPath:1}
elif [ "${myPath:0:1}" != "/" ] ; then
	myPath=$PWD/$myPath
fi
myDir=$(dirname "$myPath")
sourceDir=$(dirname "$myDir")

export STARCAL_FULL_IMPORT=1
export PYTHONPATH=$sourceDir

/usr/bin/python3 "$sourceDir/scal3/ui_gtk/full.py"
