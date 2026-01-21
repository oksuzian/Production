## ⚙️ Bash Script Documentation: Building your Configuration `Stage1_makeinputs.sh`

### **1. Overview**

This script handles the first stage of generating inputs for a new mock simulation campaign, referred to as "Stage 1" of the "MDS" (Mock Data Set) production in Mu2e. Its primary function is to:

1.  **Parse Arguments:** Define and set all operational parameters (cosmic type, energy cuts, beam mode).
2.  **File Access:** Locate and create a file list of raw simulation events from the cosmic ray generator.
3.  **Calculate Live Time:** Determine the total live time (in seconds) contained in the selected event files.
4.  **Event Normalization:** Run `calculateEvents.py` multiple times to compute the expected number of events for the signal and all major backgrounds, normalizing them to the calculated live time.
5.  **Output:** Write all parameters and calculated event normalizations into a single output file (`${TAG}.txt`).

### **2. Usage**

The script uses long-form arguments (`--option value`).

```
Stage1_makeinputs.sh [OPTIONS]
```

### **3. Arguments & Parameters**

The following parameters control the script's behavior, file selection, and normalization calculation:

| Argument   | Variable | Default | Description |
| :-----   | :--- | :--- | :--- |
| `--cosmics` | `COSMICS` | `MDC2020ar` | Mu2e dataset tag for the cosmic ray simulation events (e.g., a specific production version). |
| `--njobs` | `NJOBS` | `1` | The number of files/jobs to process from the selected cosmic dataset. |
| `--livetime` | `LIVETIME` | `""` | Optional: Manually set the experiment live time (in seconds). Usually calculated by the script. |
| `--dem_emin` | `DEM_EMIN` | `95` | **DIO/DEM $E_{\text{min}}$:** Minimum energy threshold (in MeV) for the Decay-in-Orbit (DIO) background calculation. |
| `--BB` | `BB` | `1BB` | **Beam Batch:** Operational mode for the accelerator (`1BB` or `2BB`), which affects the duty factor and POT calculation. |
| `--tmin` | `TMIN` | `350` | **Time Cut $T_{\text{min}}$:** Minimum time (in ns) used in the RPC/RMC calculation (though passed, the `calculateEvents.py` logic often handles the time cut internally). |
| `--tag` | `TAG` | `MDS2a_test` | **Output Tag:** The prefix for the output file (e.g., `MDS2a_test.txt`). |
| `--stops` | `STOPS` | `MDC2020p` | The dataset tag used for muon/pion stopping distributions (used for normalization). |
| `--release` | `RELEASE` | `MDC2020` | The main Mu2e software release tag. |
| `--version` | `VERSION` | `aw` | The version sub-tag of the software release. |
| `--gen` | `GEN` | `CRYSignal` | The cosmic ray generator used: `CRYSignal` or `CORSIKASignal`. |

### **4. Execution Flow**

1.  **Cleanup & File List Generation:**
    ```bash
    rm ${TAG}.txt
    rm ${COSMICS}
    mu2eDatasetFileList "dts.mu2e.Cosmic${GEN}All.${COSMICS}.art" | head -${NJOBS} > ${COSMICS}
    ```
    * Clears previous output files (`.txt` and the input file list).
    * Uses the `mu2eDatasetFileList` utility to query the available data files matching the specified cosmic ray generator (`${GEN}`) and dataset tag (`${COSMICS}`).
    * The output is truncated to the desired number of jobs (`-${NJOBS}`) and saved to a file list named after the cosmic tag. 

2.  **Parameter Logging:**
    The script appends all set parameters (NJOBS, CosmicGen, primary release/version, muon stops tag) to the output file (`${TAG}.txt`).

3.  **Live Time Calculation:**
    ```bash
    mu2e -c Offline/Print/fcl/printCosmicLivetime.fcl -S ${COSMICS} | grep 'Livetime:' ... > ${COSMICS}.livetime
    LIVETIME=$(awk '{sum += $1} END {print sum}' ${COSMICS}.livetime)
    ```
    * Runs the Mu2e job control utility (`mu2e`) on the list of input files (`-S ${COSMICS}`).
    * The job runs an FCL configuration designed to read the event headers and extract the recorded "Livetime" for each file.
    * The `awk` command sums the live times from all files to get the total `LIVETIME` (in seconds).

4.  **Normalization Calculations (`calculateEvents.py` calls):**

    The script makes multiple calls to `calculateEvents.py` which uses `normalizations.py` (the Python script documented previously) to calculate the expected event counts for different processes. All results are appended to the output file (`${TAG}.txt`).

    | Process (`--prc`) | Description | Key Parameters |
    | :--- | :--- | :--- |
    | `POT` (implicit) | **Protons on Target (POT)** normalization. | `--printpot "print"` |
    | `${GEN}` | **Cosmic Ray Generator** normalization (e.g., for **CRY** or **CORSIKA**). | |
    | `IPAMichel` | **IPA originating DIO** Michel background. | `--ipaemin 70` |
    | `DIO` | **Decay-in-Orbit (DIO)** electron background. | `--dioemin ${DEM_EMIN}` |
    | `RPC` (Internal = 1) | **Radiative Pion Capture (RPC)** **with** internal conversion. | `--tmin ${TMIN}`, `--internal 1`, `--rpcemin 50` |
    | `RPC` (Internal = 0) | **Radiative Pion Capture (RPC)** **without** internal conversion. | `--tmin ${TMIN}`, `--internal 0`, `--rpcemin 50` |
    | `RMC` (Internal = 1) | **Radiative Muon Capture (RMC)** **with** internal conversion. | `--tmin ${TMIN}`, `--internal 1`, `--rmcemin 85` |
    | `RMC` (Internal = 0) | **Radiative Muon Capture (RMC)** **without** internal conversion. | `--tmin ${TMIN}`, `--internal 0`, `--rmcemin 85` |

**Note on RPC/RMC parameters:** The calculations for RPC and RMC are performed twice, once for the standard capture process (`--internal 0`) and once to estimate the contribution from internal conversion pairs (`--internal 1`).
