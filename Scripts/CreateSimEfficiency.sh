#!/usr/bin/bash
#
# setup mu2efiletools before executing this script
#
SIMEFF=MDC2025_SimEff.txt
if [ -f "$SIMEFF" ]; then
  rm -f $SIMEFF
fi
mu2eGenFilterEff --out=MDC2025_SimEff.txt --chunksize=100 \
sim.mu2e.MuBeamCat.MDC2025ab.art sim.mu2e.EleBeamCat.MDC2025ab.art sim.mu2e.NeutralsCat.MDC2025ab.art \
sim.mu2e.MuminusStopsCat.MDC2025ac.art sim.mu2e.MuplusStopsCat.MDC2025ac.art \
dts.mu2e.MuBeamFlashCat.MDC2025ac.art dts.mu2e.EleBeamFlashCat.MDC2025ac.art dts.mu2e.NeutralsFlashCat.MDC2025ac.art \
dts.mu2e.MuStopPileupCat.MDC2025ac.art \
dts.mu2e.EarlyMuBeamFlashCat.MDC2025ac.art dts.mu2e.EarlyEleBeamFlashCat.MDC2025ac.art dts.mu2e.EarlyNeutralsFlashCat.MDC2025ac.art \
sim.mu2e.IPAStopsCat.MDC2025ac.art\
sim.mu2e.PiBeamCat.MDC2025ac.art \
sim.mu2e.PiMinusFilter.MDC2025ac.art \
sim.mu2e.PiTargetStops.MDC2025ac.art \
sim.mu2e.PhysicalPionStops.MDC2025ac.art
sed -i -e 's/dts\.mu2e\.//' -e 's/sim\.mu2e\.//' -e 's/\..*\.art//' -e 's/ IOV//' $SIMEFF
#sim.mu2e.IPAMuminusStopsCat.MDC2025ac.art
#sim.mu2e.PiminusStopsCat.MDC2025ac.art

mu2eDatasetFileList sim.mu2e.PiMinusFilter.MDC2025ac.art > filenames_pionfilter

TOTALWEIGHT_FILTER=$(getWeights.py --weight "total" --files filenames_pionfilter --tag "filter")
SELECTEDWEIGHT_FILTER=$(getWeights.py  --weight "selected" --files filenames_pionfilter --tag "filter")

rm filenames_pionfilter
mu2eDatasetFileList sim.mu2e.PhysicalPionStops.MDC2025ac.art > filenames_pionfilter

SELECTEDWEIGHT_SAMPLER=$(getWeights.py  --weight "selected" --files filenames_pionfilter --tag "sampler")

rm filenames_pionfilter

echo "PiTotalLifetimeWeight_filter, 0, 0, ${TOTALWEIGHT_FILTER}" >> MDC2025_SimEff.txt
echo "PiSelectedLifetimeWeight_filter, 0, 0, ${SELECTEDWEIGHT_FILTER}" >> MDC2025_SimEff.txt
echo "PiSelectedLifetimeWeight_sampler, 0, 0, ${SELECTEDWEIGHT_SAMPLER}" >> MDC2025_SimEff.txt
