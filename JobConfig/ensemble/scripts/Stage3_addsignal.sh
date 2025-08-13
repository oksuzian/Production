#!/usr/bin/bash
usage() { echo "Usage: $0
  e.g. Stage3_addsignal.sh --known MDS2a --signal CeMLeadingLog --rate 1e-13 --nexp 3
  usage:
  --owner = the username of your account (or mu2e if you are using mu2epro);
  --known = known physics tag e.g. MDS2a
  --rate = chosen rate e.g. 1e-14 (note this could be edited during the process so check print outs)
  --signal = primary name of chosen signal e.g. CeMLeadingLog for the e- ce leadinglog samples
  --release = SimJob tag e.g. MDC2020aw
  --dbpurpose = db purpose of input mcs files e.g. perfect or best
  --dbversion = db version e.g. v1_3
  --nexp = number of sets of mixed samples or 'pseudo experiments' to make default is 1
  --chosenlivetime = chose a livetime in seconds e.g 86000
"
}

# Function: Exit with error.
exit_abnormal() {
  usage
  exit 1
}
OWNER="mu2e"
KNOWN="MDS2a" #background sample tag
RATE=1e-13
SIGNAL="CeMLeadingLog" #name as given to primary during production
RELEASE="MDC2020au"
DBPURPOSE="perfect"
DBVERSION="v1_3"
NEXP=1
CHOOSE=0.
SETUP="" #musing path

while getopts ":-:" options; do
  case "${options}" in
    -)
      case "${OPTARG}" in
        owner)
          OWNER=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        known)
          KNOWN=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        rate)
          RATE=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        signal)
          SIGNAL=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        release)
          RELEASE=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        dbversion)
          DBVERSION=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        dbpurpose)
          DBPURPOSE=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        release)
          RELEASE=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
       nexp)
          NEXP=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
          ;;
        chooselivetime)
          CHOOSE=${!OPTIND} OPTIND=$(( $OPTIND + 1 ))
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

# step 1: check livetime of the tag
GEN_LIVETIME=""
GEN_JOBS=""
CONFIG=${KNOWN}.txt
while IFS='= ' read -r col1 col2
do 
    if [[ "${col1}" == "livetime" ]] ; then
      GEN_LIVETIME=${col2}
      LIVETIME=${col2}
    fi
    if [[ "${col1}" == "njobs" ]] ; then
      GEN_JOBS=${col2}
    fi
    if [[ "${col1}" == "BB" ]] ; then
      BB=${col2}
    fi
    
done <${CONFIG}
echo "extracted config for ${KNOWN}"
echo "found ${GEN_LIVETIME} ${BB}"
rm *.csv
# if user has chosen to sample only a smaller amount of livetime then override
if (awk "BEGIN {exit !(${CHOOSE} != 0)}") ; then
  echo "livetime chosen to be ${CHOOSE} s"
  LIVETIME=$(awk "BEGIN {print ${CHOOSE}}" LIVETIME="${CHOOSE}")
fi
if (awk "BEGIN {exit !(${CHOOSE} > ${GEN_LIVETIME})}") ; then
  echo "ERROR: users chosen livetime is larger than total sample size, defaulting to ${GEN_LIVETIME} s"
  LIVETIME=$(awk "BEGIN {print ${GEN_LIVETIME}}" LIVETIME="${GEN_LIVETIME}")
fi
echo "livetime ${LIVETIME}s is initated, watch for changes...."

# find how many known files are for livetime
N_TOTAL_KNOWN=$(samDatasetsSummary.sh mcs.${OWNER}.${KNOWN}Triggered.v0.art  | awk '/Files/ {print $2}')
LIVETIME_PER_FILE=$(awk "BEGIN {printf \"%.0f\", ${GEN_LIVETIME}/${N_TOTAL_KNOWN}}")
echo "livetime per file ${LIVETIME_PER_FILE}"
N_KNOWN_FILES_TO_USE=$(awk "BEGIN {printf \"%.0f\", ${LIVETIME}/${LIVETIME_PER_FILE}}")
echo "${N_KNOWN_FILES_TO_USE} files of ${KNOWN} to be used with livetime of ${LIVETIME} s"

# actual livetime that will be used for normalization of signal depends on int number of files
LIVETIME=$(awk "BEGIN {printf \"%.0f\", ${N_KNOWN_FILES_TO_USE}*${LIVETIME_PER_FILE}}")
echo "IMPORTANT: livetime ${LIVETIME}s is selected based on need for integar number of files"


# calculate yield of signal for chose rate, if > 0 then proceed --> use python scripts
NSIG=$(calculateEvents.py --livetime ${LIVETIME} --prc ${SIGNAL} --BB ${BB} --rue ${RATE})
echo "${RATE} for ${BB} and ${LIVETIME} s means ${NSIG} events will be sampled"

# understand how many events are present, and what fraction we need to sample
NGEN=(samDatasetsSummary.sh mcs.mu2e.${SIGNAL}OnSpillTriggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art  | awk '/Generated/ {print $2}') # 4980 #FIXME
#
echo "sample mcs.mu2e.${SIGNAL}OnSpillTriggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art contains ${NGEN} gen events"

# figure out fraction of signal dataset to sample:
N_TOTAL_SIGNAL=$(samDatasetsSummary.sh mcs.mu2e.${SIGNAL}OnSpillTriggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art  | awk '/Files/ {print $2}')
EVENTS_PER_FILE=$(awk "BEGIN {printf \"%.0f\", ${NGEN}/${N_TOTAL_SIGNAL}}")
echo "signal sample has ${N_TOTAL_SIGNAL} files with ${EVENTS_PER_FILE} events per file"
N_SIGNAL_FILES_TO_USE=$(awk "BEGIN {printf \"%.0f\", ${NSIG}/${EVENTS_PER_FILE}}")
echo "based on requested rate, will use ${N_SIGNAL_FILES_TO_USE} signal files"
NSIG=$(awk "BEGIN {printf \"%.2f\", ${N_SIGNAL_FILES_TO_USE}*${EVENTS_PER_FILE}}") 

#FIXME - need some poisson stats included
#FIXME - catch when < 1 file

# recheck rate for new Nfiles
RATE=$(calculateEvents.py --livetime ${LIVETIME} --BB ${BB} --nsig ${NSIG} --prc "GetRATE" )
echo "can only sample full files, sampling ${N_SIGNAL_FILES_TO_USE} files so ${NSIG} and ${RATE}"

#need to store this somewhere, amend the .config and make an associated config for combined sample with nexp, rate, livetime_rate added at end of original.
echo "======= combined samples info =========">> ${KNOWN}.txt
echo "signal= ${SIGNAL}">> ${KNOWN}.txt
echo "Rmue= ${RATE}">> ${KNOWN}.txt
echo "livetime_combined= ${LIVETIME}">> ${KNOWN}.txt
echo "npseudo_experiments= ${NEXP}">> ${KNOWN}.txt

# build complete list
rm filenames_All_${SIGNAL}
rm filenames_All_${KNOWN}
echo "looking for mcs.mu2e.${SIGNAL}OnSpillTriggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art"
samweb list-files "dh.dataset=mcs.mu2e.${SIGNAL}OnSpillTriggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art  and availability:anylocation" > filenames_All_${SIGNAL} #FIXME - need to use mixed files
$(tail filenames_All_${SIGNAL})
samweb list-files "dh.dataset=mcs.${OWNER}.${KNOWN}Triggered.v0.art  and availability:anylocation" > filenames_All_${KNOWN}

# step 9: make nexp random lists
i=1
while [ $i -le ${NEXP} ]
do
  rm filenames_Chosen_$i
  shuf -n ${N_SIGNAL_FILES_TO_USE} filenames_All_${SIGNAL} > temp #test sample
  shuf -n ${N_KNOWN_FILES_TO_USE} filenames_All_${KNOWN} >> temp
  shuf temp > filenames_Chosen_$i
  rm temp
  i=$((i + 1))
done

#step 10: configure fcl that will sample at this rate and mix the signal with background
if [[ -n $SETUP ]]; then
  echo "Using user-provided setup $SETUP"
else
  SETUP=/cvmfs/mu2e.opensciencegrid.org/Musings/SimJob/${RELEASE}/setup.sh
fi
OUTFILENAME="mcs.${OWNER}.${KNOWN}${SIGNAL}.DSCONF.SEQ.art" #FIXME - need to include derived rate
i=1
rm *.tar
while [ $i -le ${NEXP} ]
do
  rm template_$i.fcl
echo '#include "Production/JobConfig/common/artcat.fcl"' >> template_$i.fcl # FIXME - make this an EventNtuple job
echo 'outputs.out.fileName: "'${OUTFILENAME}'"' >> template_$i.fcl
  cmd="mu2ejobdef --embed template_$i.fcl --setup ${SETUP} --desc ${KNOWN}${SIGNAL}${RATE} --dsconf ${RELEASE}_${DBPURPOSE}_${DBVERSION}_$i --inputs=filenames_Chosen_$i  --merge-factor=1"
  echo "Running: $cmd"
  $cmd
  rm template_$i.fcl
  i=$((i + 1))
done

#step 11: submit to the grid (will be nexp jobs submitted, need to be careful here)
i=1
NJOBS=$(awk "BEGIN {printf \"%.0f\", ${N_SIGNAL_FILES_TO_USE}+${N_KNOWN_FILES_TO_USE}}")
echo "number of total jobs: ${NJOBS}" # assumes merge is 1
while [ $i -le ${NEXP} ]
do
  cmd="mu2ejobsub --jobdef cnf.${OWNER}.${KNOWN}${SIGNAL}.${RELEASE}_${DBPURPOSE}_${DBVERSION}_$i.0.tar --firstjob=0 --njobs=${NJOBS} --default-protocol ifdh --default-location tape  --disk 40GB"
  echo "Running: $cmd"
  i=$((i + 1))
  #$cmd
done
