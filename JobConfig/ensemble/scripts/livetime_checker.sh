#!/bin/bash

DTS="onefile.txt"
TAG="MDS2b"
rm *.livetime
mu2e -c Offline/Print/fcl/printCosmicLivetime.fcl -S ${DTS} | grep 'Livetime:' | awk -F: '{print $NF}' > ${TAG}.livetime
LIVETIME=$(awk '{sum += $1} END {print sum}' ${TAG}.livetime)
echo ${LIVETIME}
