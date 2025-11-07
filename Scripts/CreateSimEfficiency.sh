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
sim.mu2e.PiBeamCat.MDC2025ac.art \
sim.mu2e.PiMinusFilter.MDC2025ac.art \
sim.mu2e.PiTargetStops.MDC2025ac.art \
sim.mu2e.PhysicalPionStops.MDC2025ac.art
sed -i -e 's/dts\.mu2e\.//' -e 's/sim\.mu2e\.//' -e 's/\..*\.art//' -e 's/ IOV//' $SIMEFF
#sim.mu2e.IPAMuminusStopsCat.MDC2025ac.art
#sim.mu2e.PiminusStopsCat.MDC2025ac.art
