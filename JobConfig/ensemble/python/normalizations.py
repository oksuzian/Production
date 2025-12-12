#! /usr/bin/env
import DbService
import argparse
import ROOT
import math
import random
import os
import numpy as np


#-------------------------------------------------------------------------------------#  
# Constants related to muon and pion interactions.
# References for these values can be found in the referenced documentation.

# --- Muon Interactions ---
# Fraction of stopped muons that undergo nuclear capture
CAPTURES_PER_STOPPED_MUON = 0.609
# Rate of radiative muon capture (RMC) events resulting in a gamma ray > 57 MeV, per capture event
RMC_GT_57_PER_CAPTURE  = 1.43e-5 # Source: Phys. Rev. C 59, 2853 (1999)
# Fraction of stopped muons that undergo standard DIO (Decay In Orbit)
DIO_PER_STOPPED_MUON = 0.391 # Calculated as: 1 - CAPTURES_PER_STOPPED_MUON
# Rate of Incoming Particle Decay After Stopping (IPA)
IPA_DECAYS_PER_STOPPED_MUON  = 0.92990

# --- Pion Interactions ---
# Fraction of stopped pions that result in a Radiative Pion Capture (RPC)
RPC_PER_STOPPED_PION = 0.0215 # Source: Reference uploaded on DocDB-469
# --- Internal Conversion Ratios ---
# Ratio of internal conversion events per RMC event (assuming RPC value is applicable)
INTERNAL_PER_RMC = 0.00690
# Ratio of internal conversion events per RPC event
INTERNAL_RPC_PER_RPC = 0.00690 # Source: Reference uploaded on DocDB-717


# --- Configuration Placeholders (Mutable Variables) ---
# These values get overwritten later in the script or during runtime.

# Expected rates per Proton on Target (POT)
target_stopped_muons_per_pot = 1.0
target_stopped_pions_per_pot = 1.0
ipa_stopped_mu_per_POT = 1.0
ipa_stopping_rate = 1.0

# Event counters (initialized to zero)
num_pion_stops = 0.0
num_pion_resamples = 0.0
num_pion_filters = 0.0
selected_sum_of_weights = 0.0

# Rate and operational parameters
rate = 1.0
dutyfactor = 1.0
total_pot = 0.

#-------------------------------------------------------------------------------------#

# --- Database Interaction ---

# Establish a connection and retrieve simulation efficiencies from the database.

# Initialize the database tool
db_tool = DbService.DbTool()
db_tool.init()

# Define arguments for the database query
query_arguments = [
    "print-run",
    "--purpose", "Sim_best",
    "--version", "v1_1",
    "--run", "1430",
    "--table", "SimEfficiencies2",
    "--content"
]

# Execute the database query
db_tool.setArgs(query_arguments)
db_tool.run()

# Store the raw result for further processing
rr = db_tool.getResult()

# Fill varaibles associated with muon stops in target
lines= rr.split("\n")
for line in lines:
    words = line.split(",")
    if words[0] == "MuminusStopsCat" or words[0] == "MuBeamCat" :
        #print(f"Including {words[0]} with rate {words[3]}")
        rate = rate * float(words[3])
        target_stopped_muons_per_pot = rate * 1000 


# Fill variables associated with pion stops in target
lines= rr.split("\n")
for line in lines:
    words = line.split(",")
    if words[0] == "PiBeamCat" or words[0] == "PiTargetStops":
        target_stopped_pions_per_pot *= float(words[3]) # 0.001880093 * 0.5165587875
    if words[0] == "PiTargetStops":
        num_pion_stops = words[1]    #41324703
    if words[0] == "PiMinusFilter" :
        num_pion_filters = words[1] # 6634478
    if words[0] == "PhysicalPionStops" :
        num_pion_resamples= words[2]  # 10000000000
    if words[0] == "PiSelectedLifeimeWeight_sampler" :
        selected_sum_of_weights = words[3] #2393.604874

# Fill variables associated with IPA stopped muons
lines= rr.split("\n")
for line in lines:
    words = line.split(",")
    if words[0] == "IPAStopsCat" or words[0] == "MuBeamCat" :
        ipa_stopping_rate = ipa_stopping_rate * float(words[3])
        ipa_stopped_mu_per_POT = ipa_stopping_rate
print("IPAStopMuonRate=", ipa_stopped_mu_per_POT)
    
#-------------------------------------------------------------------------------------#    
def get_duty_factor(run_mode='1BB'):
    """
    Returns the estimated duty factor based on the operational run mode (beam structure).

    Args:
        run_mode (str): The operational mode, either '1BB' (1 beam batch)
                        or '2BB' (2 beam batches). Defaults to '1BB'.

    Returns:
        float: The corresponding duty factor for the specified mode.
    """
    if run_mode == '1BB':
        # Duty factor for a single beam batch operation
        duty_factor = 0.323
    elif run_mode == '2BB':
        # Duty factor for two beam batch operation
        duty_factor = 0.246
    else:
        # Handle unrecognized modes or provide a default fallback if necessary
        # print(f"Warning: Unknown run mode '{run_mode}'. Using default duty factor.")
        duty_factor = 0.323

    return duty_factor

def get_pot(on_spill_time, run_mode='1BB', printout=False, frac=1):
    """
    Calculates the total number of Protons on Target (POT) for a given live time.

    Args:
        on_spill_time (float): The actual time the beam was on spill (in seconds).
        run_mode (str): The operational mode ('1BB', '2BB', or 'custom').
                        Defaults to '1BB'.
        printout (bool): If True, prints calculation details. Defaults to False.
        frac (float): Used only in 'custom' mode as a scaling fraction.

    Returns:
        float: The calculated total number of Protons on Target (total_pot).
    """
    # Numbers based on SU2020 analysis.
    # See https://github.com/Mu2e/su2020/blob/master/analysis/pot_normalization.org

    # Initialize variables that will be dynamically assigned
    mean_pbi = 0.0
    t_cycle = 0.0
    pot_per_cycle = 0.0

    if run_mode == 'custom':
        # Assume some fraction of 1BB
        mean_pbi = 1.6e7 * frac
        t_cycle = 1.33 # seconds
        pot_per_cycle = 4e12 * (1 - frac)

    elif run_mode == '1BB':
        # Single beam batch operation
        mean_pbi = 1.6e7
        t_cycle = 1.33 # seconds
        pot_per_cycle = 4e12

    elif run_mode == '2BB':
        # Two beam batch operation
        mean_pbi = 3.9e7
        t_cycle = 1.4 # seconds
        pot_per_cycle = 8e12

    else:
        raise ValueError(f"Unknown run_mode specified: {run_mode}")

    # --- Common Calculation Steps ---
    num_cycles = on_spill_time / t_cycle
    total_pot = num_cycles * pot_per_cycle

    if printout:
        current_duty_factor = get_duty_factor(run_mode) if run_mode != 'custom' else 'N/A'
        
        print(f"Tcycle= {t_cycle}")
        print(f"POT_per_cycle= {pot_per_cycle:.2e}")
        # 'Livetime' here seems to mean 'Total experiment duration accounting for gaps'
        print(f"Total_Duration= {on_spill_time / current_duty_factor}")
        print(f"NPOT= {total_pot:.2e}")

    return total_pot

#-------------------------------------------------------------------------------------# 


# get CE normalization:
def ce_normalization(on_spill_time, rue, run_mode='1BB'):
    """
    Calculates the expected number of Coherent Electron (CE) events
    for a given live time and efficiency, sampled from a Poisson distribution.

    Args:
        on_spill_time (float): The actual time the beam was on spill (in seconds).
        rue (float): Reconstructed Unfiltered Efficiency (RUE).
        run_mode (str): The operational mode ('1BB' or '2BB'). Defaults to '1BB'.

    Returns:
        int: The number of expected CE events, sampled from a Poisson distribution.
    """
    # 1. Calculate total Protons on Target (POT) for the given live time
    total_pot = get_pot(on_spill_time, run_mode)

    # 2. Calculate the expected mean number of CE events (lambda)
    # The formula combines:
    # Total POT * Muons stopped/POT * Muon captures/stopped muon * RUE
    mean_expected_events = (
        total_pot *
        target_stopped_muons_per_pot *
        CAPTURES_PER_STOPPED_MUON *
        rue
    )

    # 3. Sample from a Poisson distribution to get the observed event count
    observed_event_count = np.random.poisson(lam=mean_expected_events)

    return observed_event_count


# get DIO normalization:
def dio_normalization(on_spill_time, e_min, run_mode='1BB'):
    """
    Calculates the expected number of Decay in Orbit (DIO) events above a given
    minimum energy (e_min) threshold for a specified run time.

    Args:
        on_spill_time (float): The actual time the beam was on spill (in seconds).
        e_min (float): The minimum energy threshold for the DIO spectrum cut (MeV).
        run_mode (str): The operational mode ('1BB' or '2BB'). Defaults to '1BB'.

    Returns:
        float: The expected number of DIO physics events passing the energy cut.
    """
    # 1. Calculate total Protons on Target (POT) for the given live time
    total_pot = get_pot(on_spill_time, run_mode)

    # 2. Load the DIO energy spectrum data from the configuration file
    # This assumes the environment variable MUSE_WORK_DIR is set
    spectrum_file_path = os.path.join(
        os.environ["MUSE_WORK_DIR"],
        "Production/JobConfig/ensemble/tables/heeck_finer_binning_2016_szafron.tbl"
    )
    
    energies = []
    values = []

    try:
        with open(spectrum_file_path, 'r') as spec_file:
            for line in spec_file:
                if not line.strip() or line.strip().startswith('#'): continue # Skip empty/comment lines
                try:
                    energy, value = map(float, line.split())
                    energies.append(energy)
                    values.append(value)
                except ValueError:
                    print(f"Warning: Could not parse line in spectrum file: {line.strip()}")

    except FileNotFoundError:
        raise FileNotFoundError(f"DIO spectrum file not found at: {spectrum_file_path}")

    # 3. Calculate normalization (fraction of spectrum above e_min)
    total_norm = sum(values)
    cut_norm = 0

    for i in range(len(values)):
        if energies[i] >= e_min:
            cut_norm += values[i]

    # Handle case where total_norm might be zero to avoid ZeroDivisionError
    if total_norm == 0:
        fraction_sampled = 0.0
    else:
        fraction_sampled = cut_norm / total_norm

    # 4. Calculate the total number of expected physics events
    # Total POT * Muons stopped/POT * DIO events/stopped muon
    base_physics_events = total_pot * target_stopped_muons_per_pot * DIO_PER_STOPPED_MUON

    # 5. Apply the energy cut fraction
    expected_events_above_emin = base_physics_events * fraction_sampled
    
    print("DIO_emin=",e_min)
    print("DIO_fraction_sampled=",fraction_sampled )
    return expected_events_above_emin



def rpc_normalization(on_spill_time, t_min, internal, e_min, run_mode='1BB'):
    """
    Calculates the expected number of Radiative Pion Capture (RPC) events
    above a given energy (e_min) and time (t_min) threshold.

    Handles both standard RPC and internal conversion events based on the 'internal' flag.

    Args:
        on_spill_time (float): Time the beam was on spill (seconds).
        t_min (float): Minimum time threshold (seconds) (Note: not used in current logic).
        internal (int/bool): Flag (1 or 0) to include internal conversion scaling.
        e_min (float): Minimum energy threshold for spectrum cut (MeV).
        run_mode (str): The operational mode ('1BB' or '2BB'). Defaults to '1BB'.

    Returns:
        float: The expected number of RPC physics events passing the cuts.
    """
    # 1. Calculate total Protons on Target (POT)
    total_pot = get_pot(on_spill_time, run_mode)

    # 2. Load the RPC energy spectrum data (Bistrilich source)
    spectrum_file_path = os.path.join(
        os.environ["MUSE_WORK_DIR"],
        "Production/JobConfig/ensemble/tables/rpcspectrum.tbl"
    )
    
    energies = []
    values = []

    try:
        with open(spectrum_file_path, 'r') as spec_file:
            for line in spec_file:
                if not line.strip() or line.strip().startswith('#'): continue
                try:
                    energy, value = map(float, line.split())
                    energies.append(energy)
                    values.append(value)
                except ValueError:
                    print(f"Warning: Could not parse line in spectrum file: {line.strip()}")

    except FileNotFoundError:
        raise FileNotFoundError(f"RPC spectrum file not found at: {spectrum_file_path}")

    # 3. Calculate normalization (fraction of spectrum above e_min)
    total_norm = sum(values)
    cut_norm = 0
    for i in range(len(values)):
        if energies[i] >= float(e_min):
            cut_norm += values[i]

    if total_norm == 0:
        rpc_e_sample_frac = 0.0
    else:
        rpc_e_sample_frac = cut_norm / total_norm

    # 4. Calculate base physics events rate before final cuts

    # Calculate efficiency terms based on simulation globals
    filter_efficiency = float(num_pion_filters) / float(num_pion_stops)
    survival_probability_weight = float(selected_sum_of_weights) / float(num_pion_resamples) 

    base_physics_events = (
        total_pot *
        target_stopped_pions_per_pot *
        filter_efficiency *
        survival_probability_weight *
        RPC_PER_STOPPED_PION *
        rpc_e_sample_frac
    )

    # 5. Apply internal conversion scaling if requested
    is_internal_conversion = bool(int(internal)) # Ensure robust boolean check

    if is_internal_conversion:

        print("RPC_emin=",e_min)
        print("RPC_tmin=",t_min)
        print("RPC_fraction_sampled=",rpc_e_sample_frac)
        print("pistoprate=",target_stopped_pions_per_pot)
    
        base_physics_events *= INTERNAL_RPC_PER_RPC
    
    return base_physics_events

def rmc_normalization(on_spill_time, internal, e_min, k_max=90.1, run_mode='1BB'):
    """
    Calculates the expected number of Radiative Muon Capture (RMC) events
    above a given energy (e_min) threshold.

    The gamma spectrum is generated internally using the closure approximation
    formula adapted from the MuonCaptureSpectrum.cc implementation.

    Args:
        on_spill_time (float): Time the beam was on spill (seconds).
        internal (int/bool): Flag (1 or 0) to include internal conversion scaling.
        e_min (float): Minimum energy threshold for spectrum cut (MeV).
        k_max (float): Maximum possible RMC energy (MeV). Defaults to 90.1 MeV.
        run_mode (str): The operational mode ('1BB' or '2BB'). Defaults to '1BB'.

    Returns:
        float: The expected number of RMC physics events passing the cuts.
    """
    # 1. Calculate total Protons on Target (POT)
    total_pot = get_pot(on_spill_time, run_mode)

    # 2. Generate the RMC energy spectrum internally using the closure approximation
    energies = []
    values = []
    
    # Spectrum starts at 57.05 MeV, with 0.1 MeV bins
    start_energy = 57.05
    bin_width = 0.1
    num_bins = int((float(k_max) - start_energy) / bin_width)
    
    for i in range(num_bins):
        temp_e = start_energy + i * bin_width
        # Normalize energy by the maximum possible energy for the formula
        x_fit = temp_e / float(k_max)
        # Spectrum shape formula: (1 - 2*x + 2*x^2) * x * (1 - x)^2
        spectrum_value = (1 - 2*x_fit + 2*x_fit*x_fit) * x_fit * (1 - x_fit) * (1 - x_fit)
        
        energies.append(temp_e)
        values.append(spectrum_value)
  
    # 3. Calculate normalization (fraction of spectrum above e_min threshold)
    total_norm = sum(values)
    cut_norm = 0
    
    # We compare the energy threshold (e_min) to the *center* of the energy bin
    for i in range(len(values)):
        bin_center = energies[i]
        
        if (bin_center - bin_width / 2.0) >= float(e_min):
            cut_norm += values[i]

    if total_norm == 0:
        fraction_sampled = 0.0
    else:
        fraction_sampled = cut_norm / total_norm
        
    # 4. Calculate the base number of RMC physics events
    # POT * Muons stopped/POT * Muon captures/stopped muon * RMC_GT_57 rate
    base_physics_events = (
        total_pot *
        target_stopped_muons_per_pot *
        CAPTURES_PER_STOPPED_MUON *
        RMC_GT_57_PER_CAPTURE
    )
    
    # Apply the energy spectrum sampling fraction
    base_physics_events *= fraction_sampled

    # 5. Apply internal conversion scaling if requested
    is_internal_conversion = bool(int(internal)) # Ensure robust boolean check

    if is_internal_conversion:
        print("RMC_emin=",e_min)
        print("RMC_kmax=",k_max)
        print("RMC_fraction_sampled=",fraction_sampled)

        base_physics_events *= INTERNAL_PER_RMC
        
    return base_physics_events

# get IPA Michel normalization:
def ipaMichel_normalization(on_spill_time, ipa_de_min, run_mode='1BB'):
    """
    Calculates the expected number of IPA (Incoming Particle Decay After Stopping)
    Michel events above a given minimum energy (ipa_de_min) threshold.

    The function reads an efficiency table to find the fraction of events
    passing the specified energy cut.

    Args:
        on_spill_time (float): The actual time the beam was on spill (in seconds).
        ipa_de_min (float): Minimum energy threshold for the IPA spectrum cut (MeV).
        run_mode (str): The operational mode ('1BB' or '2BB'). Defaults to '1BB'.

    Returns:
        float: The expected number of IPA Michel events passing the energy cut.
    """
    # 1. Calculate total Protons on Target (POT)
    total_pot = get_pot(on_spill_time, run_mode)

    # 2. Load the IPA spectrum efficiency data
    spectrum_file_path = os.path.join(
        os.environ["MUSE_WORK_DIR"],
        "Production/JobConfig/ensemble/tables/ipa_spec_eff.tbl"
    )
    
    fraction_sampled = 1.0 # Default to 1 (100%) if no cut is found or file is empty

    try:
        with open(spectrum_file_path, 'r') as spec_file:
            for line in spec_file:
                if not line.strip() or line.strip().startswith('#'): continue # Skip empty/comment lines
                try:
                    # File expected format: [Energy_Threshold (MeV)] [Fraction_Passing_Cut]
                    energy_threshold, efficiency_fraction = map(float, line.split())
                    
                    
                    if energy_threshold > float(ipa_de_min):
                        fraction_sampled = efficiency_fraction
                        print("IPA_emin=", ipa_de_min)
                        print("IPA_fraction_sampled=", fraction_sampled)
                        # Calculate and return the result immediately upon finding the match
                        n_ipa = (
                            total_pot *
                            ipa_stopped_mu_per_POT *
                            IPA_DECAYS_PER_STOPPED_MUON *
                            fraction_sampled
                        )
                        return n_ipa
                except ValueError:
                    print(f"Warning: Could not parse line in spectrum file: {line.strip()}")

    except FileNotFoundError:
        raise FileNotFoundError(f"IPA spectrum file not found at: {spectrum_file_path}")

    print(f"Warning: No specific efficiency found for E_min > {ipa_de_min}. Using default fraction 1.0")
    n_ipa = (
        total_pot *
        ipa_stopped_mu_per_POT *
        IPA_DECAYS_PER_STOPPED_MUON *
        fraction_sampled
    )
    return n_ipa

# work from signal to rmue  
def get_ce_rmue(onspilltime, nsig, run_mode = '1BB'):
    POT = get_pot(onspilltime, run_mode)
    rmue = nsig/(POT * target_stopped_muons_per_pot * CAPTURES_PER_STOPPED_MUON)
    return  rmue


"""
The following section derives the cosmic yield for on spill/off spill for two specific generators (CRY/CORSIKA)
The cosmics are normalized according to the livetime fraction which overlaps with beam (Depends on duty factor and BB mode)
"""
# note this returns CosmicLivetime not # of generated events
def cry_onspill_normalization(livetime, run_mode = '1BB'):
    return livetime
  
# note this returns CosmicLivetime not # of generated events
def corsika_onspill_normalization(livetime, run_mode = '1BB'):
    return livetime


if __name__ == '__main__':
  tst_1BB = get_pot(9.52e6)
  tst_2BB = get_pot(1.58e6)
  tst_rpc = rpc_normalization(3.77e19,350,1,1)
  print("SU2020", tst_1BB, tst_2BB)
