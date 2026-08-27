#!/bin/bash

myPath="$0"
if [ "${myPath:0:2}" == "./" ] ; then
	myPath=$PWD${myPath:1}
elif [ "${myPath:0:1}" != "/" ] ; then
	myPath=$PWD/$myPath
fi
myDir=$(dirname "$myPath")
sourceDir=$(dirname "$myDir")

export PYTHONPATH=$sourceDir

python3 -m pytest "$sourceDir/scal3/event_lib" -q "$@"
