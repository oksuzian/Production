#!/bin/bash

DTS="MDS2b.txt" # Edit with file names
TAG="MDS2b" # Edit as needed
rm *.livetime
mu2e -c Offline/Print/fcl/printCosmicLivetime.fcl -S ${DTS} | grep 'Livetime:' | awk -F: '{print $NF}' > ${TAG}.livetime
LIVETIME=$(awk '{sum += $1} END {print sum}' ${TAG}.livetime)
echo ${LIVETIME}
