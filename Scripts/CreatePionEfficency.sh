#!/usr/bin/bash
#
# Script to create the SimEfficiency proditions content from a beam campaign.  The campaign 'configuration' field must be provided
# stopped pion campaign is the argument
rm $1_SimEff.txt
mu2eGenFilterEff --out=$1_SimEff.txt --chunksize=100 --firstLine "PionSimEfficiencies" --verbosity 3 sim.mu2e.IPAStopsCat.$1.art sim.mu2e.PiBeamCat.$1.art sim.mu2e.PiTargetStops.$1.art sim.mu2e.PiMinusFilter.$1.art sim.mu2e.PhysicalPionStops.$1.art

mu2eDatasetFileList sim.mu2e.PiMinusFilter.$1.art > filenames_pionfilter

TOTALWEIGHT_FILTER=$(getWeights.py --weight "total" --files filenames_pionfilter --tag "filter")
SELECTEDWEIGHT_FILTER=$(getWeights.py  --weight "selected" --files filenames_pionfilter --tag "filter")

rm filenames_pionfilter
mu2eDatasetFileList sim.mu2e.PhysicalPionStops.$1.art > filenames_pionfilter

SELECTEDWEIGHT_SAMPLER=$(getWeights.py  --weight "selected" --files filenames_pionfilter --tag "sampler")

rm filenames_pionfilter

echo "PiTotalLifeimeWeight_filter, 0, 0, ${TOTALWEIGHT_FILTER}" >> $1_SimEff.txt
echo "PiSelectedLifeimeWeight_filter, 0, 0, ${SELECTEDWEIGHT_FILTER}" >> $1_SimEff.txt
echo "PiSelectedLifeimeWeight_sampler, 0, 0, ${SELECTEDWEIGHT_SAMPLER}" >> $1_SimEff.txt

