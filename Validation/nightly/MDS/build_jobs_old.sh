#!/usr/bin/bash
#
# Fixed nightly validation jobs for MDS - uses existing nightly build
#
# Set the date to use an existing nightly build
export DATE="2025-08-30"

# dts -> dig validation
Production/Scripts/nightly_jobs_fixed.sh --dir MDS --script digitize --dataset dts.mu2e.ensembleMDS1e.MDC2020ar.art

# dig -> mcs(rec) validation  
Production/Scripts/nightly_jobs_fixed.sh --dir MDS --script reconstruct --dataset dig.mu2e.ensembleMDS1eMix1BBTriggered.MDC2020ai_perfect_v1_3.art
