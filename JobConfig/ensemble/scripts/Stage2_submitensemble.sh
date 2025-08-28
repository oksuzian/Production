#!/usr/bin/bash
usage() { echo "Usage: $0
  e.g. Stage2_submitensemble.sh --tag MDS1a
"
}

# Function: Exit with error.
exit_abnormal() {
  usage
  exit 1
}
OWNER="mu2e"
RELEASE=MDC2020
CURRENT="ba"
TAG=""
VERBOSE=1

DIOVERSION=at
RMCVERSION=at
RPCVERSION=az
IPAVERSION=ax


SETUP=/cvmfs/mu2e.opensciencegrid.org/Musings/SimJob/${RELEASE}${CURRENT}/setup.sh

echo "using" ${RELEASE}${CURRENT}
NJOBS="" #to help calculate the number of events per job
LIVETIME="" #seconds
RUN=1201
DIO_EMIN=95
RPC_EMIN=""
RMC_EMIN=""
IPA_EMIN=""
TMIN=""
BB=""
SAMPLINGSEED=1
COSMICTAG="MDC2020ar"
GEN="CRY"
# Loop: Get the next option;
while getopts ":-:" options; do
  case "${options}" in
    -)
      case "${OPTARG}" in
        owner)
          OWNER=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        tag)
          TAG=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        verbose)
          VERBOSE=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        setup)
          SETUP=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        dioversion)
          DIOVERSION=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        rmcversion)
          RMCVERSION=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        rpcversion)
          RPCVERSION=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        ipaversion)
          IPAVERSION=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        *)
          echo "Unknown option " ${OPTARG}
          exit_abnormal
          ;;
        esac;;
    :)                                    # If expected argument omitted:
      echo "Error: -${OPTARG} requires an argument."
      exit_abnormal                       # Exit abnormally.
      ;;
    *)                                    # If unknown (any other) option:
      exit_abnormal                       # Exit abnormally.
      ;;
    esac
done

# extract config file from disk:
CONFIG=cnf.${OWNER}.ensemble${TAG}.${RELEASE}${CURRENT}.0.txt

mu2eDatasetFileList cnf.${OWNER}.ensemble${TAG}.${RELEASE}${CURRENT}.txt >> config_list.txt
# Read each line (file path) from the input file
while IFS= read -r file_path; do
    if [ -f "$file_path" ]; then
        cp "$file_path" .
    fi
done < config_list.txt

while IFS='= ' read -r col1 col2
do 
    if [[ "${col1}" == "njobs" ]] ; then
      NJOBS=${col2}
    fi
    if [[ "${col1}" == "DIO_emin" ]] ; then
      DIO_EMIN=${col2}
    fi
    if [[ "${col1}" == "RPC_emin" ]] ; then
      RPC_EMIN=${col2}
    fi
    if [[ "${col1}" == "RPC_tmin" ]] ; then
      TMIN=${col2}
    fi
    if [[ "${col1}" == "RMC_emin" ]] ; then
      RMC_EMIN=${col2}
    fi
    if [[ "${col1}" == "RMC_kmax" ]] ; then
      RMC_kmax=${col2}
    fi
    if [[ "${col1}" == "IPA_emin" ]] ; then
      IPA_EMIN=${col2}
    fi
    if [[ "${col1}" == "livetime" ]] ; then
      LIVETIME=${col2}
    fi
    if [[ "${col1}" == "BB" ]] ; then
      BB=${col2}
    fi
    if [[ "${col1}" == "CosmicGen" ]] ; then
      GEN=${col2}
    fi
    if [[ "${col1}" == "CosmicTag" ]] ; then
      COSMICTAG=${col2}
    fi
    
done <${CONFIG}
echo "extracted config from Stage 1"
echo ${LIVETIME} ${DIO_EMIN} ${BB}

rm filenames_${GEN}Cosmic
rm filenames_DIO
rm filenames_RPCInternal
rm filenames_RPCExternal
rm filenames_RMCInternal
rm filenames_RMCExternal
rm filenames_IPAMichel
rm *.tar

echo "accessing files, making file lists"
mu2eDatasetFileList "dts.mu2e.Cosmic${GEN}SignalAll.${COSMICTAG}.art" | head -${NJOBS} > filenames_${GEN}Cosmic
mu2eDatasetFileList "dts.mu2e.DIOtail${DIO_EMIN}.${RELEASE}${DIOVERSION}.art"| head -${NJOBS} > filenames_DIO
mu2eDatasetFileList "dts.mu2e.RPCInternalPhysical.${RELEASE}${RPCVERSION}.art" | head -${NJOBS} > filenames_RPCInternal
mu2eDatasetFileList "dts.mu2e.RPCExternalPhysical.${RELEASE}${RPCVERSION}.art" | head -${NJOBS} > filenames_RPCExternal
mu2eDatasetFileList "dts.mu2e.RMCInternal.${RELEASE}${RMCVERSION}.art" | head -${NJOBS} > filenames_RMCInternal
#mu2eDatasetFileList "dts.mu2e.RMCExternalCat.${RELEASE}${RMCVERSION}.art" | head -${NJOBS} > filenames_RMCExternal
samListLocations --dim "dh.dataset=dts.mu2e.RMCExternalCat.MDC2020at.art and event_count>600" | head -${NJOBS}  &> filenames_RMCExternal 
mu2eDatasetFileList "dts.mu2e.IPAMuminusMichel.${RELEASE}${IPAVERSION}.art" | head -${NJOBS} > filenames_IPAMichel

echo "making template fcl"
make_template_fcl.py --BB=${BB} --release=${RELEASE}${CURRENT}  --tag=${TAG} --verbose=${VERBOSE} --livetime=${LIVETIME} --run=${RUN} --dioemin=${DIO_EMIN} --rpcemin=${RPC_EMIN} --rmcemin=${RMC_EMIN} --rmckmax=${RMC_kmax} --ipaemin=${IPA_EMIN} --tmin=${TMIN} --samplingseed=${SAMPLINGSEED} --prc "DIO" "${GEN}Cosmic" "RPCInternal" "RPCExternal" "RMCInternal" "RMCExternal" "IPAMichel"

##### Below is genEnsemble and Grid:
echo "remove old files"
rm cnf.${OWNER}.ensemble${TAG}.${RELEASE}${INVERSION}.0.tar
rm filenames_${GEN}Cosmic_${NJOBS}.txt
rm filenames_DIO_${NJOBS}.txt
rm filenames_RPCInternal_${NJOBS}.txt
rm filenames_RPCExternal_${NJOBS}.txt
rm filenames_RMCInternal_${NJOBS}.txt
rm filenames_RMCExternal_${NJOBS}.txt
rm filenames_IPAMichel_${NJOBS}.txt

echo "get NJOBS files and list"
samweb list-files "dh.dataset=dts.mu2e.Cosmic${GEN}SignalAll.${COSMICTAG}.art" | head -${NJOBS} > filenames_${GEN}Cosmic_${NJOBS}.txt
samweb list-files "dh.dataset=dts.mu2e.DIOtail${DIO_EMIN}.${RELEASE}${DIOVERSION}.art"  | head -${NJOBS} > filenames_DIO_${NJOBS}.txt
samweb list-files "dh.dataset=dts.mu2e.RPCInternalPhysical.${RELEASE}${RPCVERSION}.art  and availability:anylocation"  | head -${NJOBS}  >  filenames_RPCInternal_${NJOBS}.txt
samweb list-files "dh.dataset=dts.mu2e.RPCExternalPhysical.${RELEASE}${RPCVERSION}.art  and availability:anylocation"  | head -${NJOBS}  >  filenames_RPCExternal_${NJOBS}.txt
samweb list-files "dh.dataset=dts.mu2e.RMCInternal.${RELEASE}${RMCVERSION}.art  and availability:anylocation"  | head -${NJOBS}  >  filenames_RMCInternal_${NJOBS}.txt
samweb list-files "dh.dataset=dts.mu2e.RMCExternalCat.${RELEASE}${RMCVERSION}.art  and availability:anylocation and event_count>600"  | head -${NJOBS}  >  filenames_RMCExternal_${NJOBS}.txt
samweb list-files "dh.dataset=dts.mu2e.IPAMuminusMichel.${RELEASE}${IPAVERSION}.art  and availability:anylocation"  | head -${NJOBS}  >  filenames_IPAMichel_${NJOBS}.txt


DSCONF=${RELEASE}${CURRENT}
# note change setup to code to use a custom tarball
echo "run mu2e jobdef"
cmd="mu2ejobdef --desc=ensemble${TAG} --dsconf=${DSCONF} --run=${RUN} --setup ${SETUP} --sampling=1:DIO:filenames_DIO_${NJOBS}.txt --sampling=1:${GEN}Cosmic:filenames_${GEN}Cosmic_${NJOBS}.txt --sampling=1:RPCInternal:filenames_RPCInternal_${NJOBS}.txt  --embed SamplingInput_sr0.fcl  --sampling=1:RPCExternal:filenames_RPCExternal_${NJOBS}.txt --sampling=1:RMCInternal:filenames_RMCInternal_${NJOBS}.txt --sampling=1:RMCExternal:filenames_RMCExternal_${NJOBS}.txt --sampling=1:IPAMichel:filenames_IPAMichel_${NJOBS}.txt --verb "
echo "Running: $cmd"
$cmd
parfile=$(ls cnf.*.tar)
# Remove cnf.
index_dataset=${parfile:4}
# Remove .0.tar
index_dataset=${index_dataset::-6}

idx=$(mu2ejobquery --njobs cnf.*.tar)
idx_format=$(printf "%07d" $idx)
echo $idx
echo "Creating index definiton with size: $idx"
samweb create-definition idx_${index_dataset} "dh.dataset etc.mu2e.index.000.txt and dh.sequencer < ${idx_format}"
echo "Created definiton: idx_${index_dataset}"
samweb describe-definition idx_${index_dataset}

echo "submit jobs"
cmd="mu2ejobsub --jobdef cnf.${OWNER}.ensemble${TAG}.${RELEASE}${CURRENT}.0.tar --firstjob=0 --njobs=${NJOBS}  --default-protocol ifdh --default-location tape --location dts.mu2e.RPCExternalPhysical.MDC2020az.art:disk "
echo "Running: $cmd"
$cmd
