## 🚀 Bash Script Documentation: Building Known Physics `Stage2_submitensemble.sh`

### **1. Overview**

This script orchestrates the creation and submission of a massive grid job (an "ensemble" production) designed to simulate the final experimental conditions by mixing signal and various background events according to calculated physics rates. It leverages Fermilab's data handling (SAM) and job submission tools (`mu2ejobdef`, `mu2ejobsub`).

| Component | Description |
| :--- | :--- |
| **Purpose** | Reads configuration from Stage 1, gathers input file lists for all physics processes, generates a job configuration (FCL), and submits the ensemble simulation job to the computing grid. |
| **Prerequisites** | Must be run after `Stage1_makeinputs.sh` has successfully created the configuration file (`cnf.<owner>.ensemble<tag>.<release><current>.0.txt`). Requires Mu2e grid tools (`samweb`, `mu2eDatasetFileList`, `mu2ejobdef`, `mu2ejobsub`). |
| **Outcome** | A multi-component simulation job is queued on the grid, ready to process events.  |

### **2. Usage**

The script takes a single required argument: the tag used in Stage 1.

```
Stage2_submitensemble.sh [OPTIONS]
```
### **3. Arguments & Default Parameters**

The following arguments primarily control file naming, software versioning, and job behavior. Physics parameters are generally read from the Stage 1 configuration file.

| Argument | Variable | Default | Description |
| :--- | :--- | :--- | :--- |
| `--tag` | `TAG` | `""` | **REQUIRED.** The project tag (e.g., `MDS1a`) used to locate the Stage 1 config file. |
| `--owner` | `OWNER` | `mu2e` | The owner of the dataset definition (usually `mu2e` or a username). |
| `--verbose` | `VERBOSE` | `1` | Controls verbosity in the FCL template generation. |
| `--setup` | `SETUP` | `/cvmfs/.../setup.sh` | Path to the Mu2e software environment setup script. |
| `--dioversion` | `DIOVERSION` | `at` | Software version tag for DIO events. |
| `--rmcversion` | `RMCVERSION` | `at` | Software version tag for RMC events. |
| `--rpcversion` | `RPCVERSION` | `az` | Software version tag for RPC events. |
| `--ipaversion` | `IPAVERSION` | `ax` | Software version tag for IPA events. |

---

### **4. Execution Flow**

The script executes in three main phases: Configuration Loading, File List Creation, and Job Submission.

#### **Phase A: Load Configuration (Stage 1 Output)**

1.  **Locate Config File:**
    ```bash
    CONFIG=cnf.${OWNER}.ensemble${TAG}.${RELEASE}${CURRENT}.0.txt
    ```
    The script first attempts to locate the configuration file created by `Stage1_makeinputs.sh` based on the provided `TAG`.

2.  **Copy and Parse Config:** It uses `mu2eDatasetFileList` to find the config file on disk, copies it locally, and then parses it line-by-line (`while IFS='= ' read...`) to populate variables like `NJOBS`, `LIVETIME`, `BB`, `DIO_EMIN`, `RPC_EMIN`, etc.

    > **Key Concept:** This step ensures all physics parameters calculated and defined in Stage 1 are consistently used for the ensemble job submission in Stage 2.

#### **Phase B: Create Input File Lists (SAM Queries)**

The script clears previous file lists and then uses two methods (`mu2eDatasetFileList` and `samweb list-files`) to query the data handling system (SAM) for the exact input files needed for the simulation.

1.  **Query by Dataset Tag (using `mu2eDatasetFileList`):** This is used for generating lists of files to be copied locally for initial setup.
2.  **Query by SAM Definition (using `samweb list-files`):** This generates definitive file lists (`filenames_*_<NJOBS>.txt`) which are explicitly embedded into the grid job definition for the final run.

| Physics Process | SAM Dataset Tag Used | Purpose |
| :--- | :--- | :--- |
| **Cosmics** | `dts.mu2e.Cosmic${GEN}SignalAll.${COSMICTAG}.art` | Cosmic ray background events. |
| **DIO** | `dts.mu2e.DIOtail${DIO_EMIN}.${RELEASE}${DIOVERSION}.art` | Decay in Orbit background events. |
| **RPC Internal/External** | `dts.mu2e.RPC*Physical.${RELEASE}${RPCVERSION}.art` | Radiative Pion Capture background events. |
| **RMC Internal/External**| `dts.mu2e.RMC*.${RELEASE}${RMCVERSION}.art` | Radiative Muon Capture background events. |
| **IPA Michel** | `dts.mu2e.IPAMuminusMichel.${RELEASE}${IPAVERSION}.art` | Incoming Particle Decay After Stopping (IPA) background. |

#### **Phase C: Job Definition and Submission**

1.  **Make FCL Template:**
    ```bash
    make_template_fcl.py --BB=${BB} --release=${RELEASE}${CURRENT} ...
    ```
    This Python script generates the FCL (Fermilab Control Language) configuration file, which defines exactly *how* the simulation will mix and process the events. It requires the live time, beam mode, and all energy/time cuts as input, as well as the list of physics processes to include.

2.  **Generate Job Definition (`mu2ejobdef`):**
    ```bash
    mu2ejobdef --desc=ensemble${TAG} ... --sampling=1:PROC:filenames_PROC_${NJOBS}.txt ...
    ```
    This tool packages the FCL configuration, environment setup, and the complete set of input file lists into a single tarball (`cnf.<owner>.*.tar`), creating a formal job definition for the grid.

    > **Key Concept:** The `--sampling` arguments are critical. They instruct the ensemble simulation to draw events from the listed file for each physics process, ensuring the final job samples from all backgrounds.

3.  **Create SAM Definition Index:** An index definition is created using `samweb` to help track the output files of the massive job.

4.  **Submit Job (`mu2ejobsub`):**
    ```bash
    mu2ejobsub --jobdef cnf.*.tar --firstjob=0 --njobs=${NJOBS} ...
    ```
    The final command submits the job definition tarball to the grid, instructing it to run the simulation across the specified number of jobs (`${NJOBS}`).
