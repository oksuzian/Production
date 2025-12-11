#!/bin/bash

DTS="cosmics_2025.txt" # Edit with file names
TAG="MDS3a" # Edit as needed
rm *.livetime
mu2e -c Offline/Print/fcl/printCosmicLivetime.fcl -S ${DTS} | grep 'Livetime:' | awk -F: '{print $NF}' > ${TAG}.livetime
LIVETIME=$(awk '{sum += $1} END {print sum}' ${TAG}.livetime)
echo ${LIVETIME}
