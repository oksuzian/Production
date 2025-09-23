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
  --chooselivetime = chose a livetime in seconds e.g 86000
  
  NOTE: assumes signal and known are the same versions
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
RELEASE="MDC2020ba"
DBPURPOSE="best"
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
# extract config file from disk:
CONFIG=${KNOWN}.txt

echo "running: mu2eDatasetFileList cnf.${OWNER}.ensemble${KNOWN}.${RELEASE}${CURRENT}.txt"

mu2eDatasetFileList cnf.${OWNER}.ensemble${KNOWN}.${RELEASE}${CURRENT}.txt >> config.txt
# Read each line (file path) from the input file
while IFS= read -r file_path; do
    if [ -f "$file_path" ]; then
        cp "$file_path" ${KNOWN}.txt
    fi
done < config.txt

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
N_TOTAL_KNOWN=$(samDatasetsSummary.sh mcs.${OWNER}.ensemble${KNOWN}Mix${BB}Triggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art  | awk '/Files/ {print $2}')
LIVETIME_PER_FILE=$(awk "BEGIN {printf \"%.0f\", ${GEN_LIVETIME}/${N_TOTAL_KNOWN}}")
echo "livetime per file ${LIVETIME_PER_FILE}"
N_KNOWN_FILES_TO_USE=$(awk "BEGIN {printf \"%.0f\", ${LIVETIME}/${LIVETIME_PER_FILE}}")
echo "${N_KNOWN_FILES_TO_USE} files of ${KNOWN} to be used with livetime of ${LIVETIME} s"

# actual livetime that will be used for normalization of signal depends on int number of files
LIVETIME=$(awk "BEGIN {printf \"%.0f\", ${N_KNOWN_FILES_TO_USE}*${LIVETIME_PER_FILE}}")
echo "IMPORTANT: livetime ${LIVETIME}s is selected based on need for integar number of files"

# understand how many events are present, and what fraction we need to sample
echo "accessing " mcs.${OWNER}.${SIGNAL}Mix${BB}Triggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art
NGEN=10000000
#(samDatasetsSummary.sh mcs.${OWNER}.${SIGNAL}Mix${BB}Triggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art  | awk '/Generated/ {print $2}') #FIXME

echo "sample mcs.${OWNER}.${SIGNAL}Mix${BB}Triggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art contains ${NGEN} gen events"

# recheck rate for new Nfiles
#RATE=$(calculateEvents.py --livetime ${LIVETIME} --BB ${BB} --nsig ${NSIG} --prc "GetRATE" )
#echo "can only sample full files, sampling ${N_SIGNAL_FILES_TO_USE} files so ${NSIG} and ${RATE}"

#need to store this somewhere, amend the .config and make an associated config for combined sample with nexp, rate, livetime_rate added at end of original.
echo "======= combined samples info =========">> ${KNOWN}.txt
echo "signal= ${SIGNAL}">> ${KNOWN}.txt
echo "Rmue= ${RATE}">> ${KNOWN}.txt
echo "livetime_combined= ${LIVETIME}">> ${KNOWN}.txt
echo "npseudo_experiments= ${NEXP}">> ${KNOWN}.txt

# build complete list
rm filenames_All_${SIGNAL}
rm filenames_All_${KNOWN}
rm filenames_*
echo "looking for mcs.${OWNER}.${SIGNAL}Mix${BB}Triggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art"
mu2eDatasetFileList "mcs.${OWNER}.${SIGNAL}Mix${BB}Triggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art" > filenames_All_${SIGNAL} 

mu2eDatasetFileList nts.mu2e.ensemble${KNOWN}Mix${BB}Triggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}_v06_06_00.root > filenames_All_${KNOWN}

# step: split the signal files to get an exact number:
i=1
while [ $i -le ${NEXP} ]
do
  # remove old files
  rm ntuple_$i.fcl
  rm splitter_$i.fcl
  
  # calculate yield of signal for chose rate, if > 0 then proceed --> use python scripts
  NSIG=$(calculateEvents.py --livetime ${LIVETIME} --prc ${SIGNAL} --BB ${BB} --rue ${RATE})
  echo "${RATE} for ${BB} and ${LIVETIME} s means ${NSIG} events will be sampled"
  NSIG=$(awk "BEGIN {printf \"%.0f\", ${NSIG}}")

  # calculate number of files
  N_TOTAL_SIGNAL=$(samDatasetsSummary.sh mcs.${OWNER}.${SIGNAL}Mix${BB}Triggered.${RELEASE}_${DBPURPOSE}_${DBVERSION}.art  | awk '/Files/ {print $2}')
  EVENTS_PER_FILE=$(awk "BEGIN {printf \"%.0f\", ${NGEN}/${N_TOTAL_SIGNAL}}")
  echo "signal sample has ${N_TOTAL_SIGNAL} files with ${EVENTS_PER_FILE} events per file"
  N_SIGNAL_FILES_TO_USE=$(awk "BEGIN {printf \"%.0f\", ${NSIG}/${EVENTS_PER_FILE}}")
  
  # if its < 1 file the above will be 0, so we need to make sure we use at least 1 file here
  if (( N_SIGNAL_FILES_TO_USE == 0 )); then
    N_SIGNAL_FILES_TO_USE=1
  fi
  echo "based on requested rate, will use ${N_SIGNAL_FILES_TO_USE} signal files"
  
  # build the splitter .fcl file and run on the chosen samples
  echo "will sample ${N_SIGNAL_FILES_TO_USE} signal files"
  # randomly select a file here
  shuf -n ${N_SIGNAL_FILES_TO_USE} filenames_All_${SIGNAL} > temp
  shuf temp > filenames_ChosenSig_$i
  rm temp
  # construct .fcl
  echo "#include \"Production/JobConfig/ensemble/fcl/split.fcl\"" > splitter_$i.fcl
  echo "source.fileNames: [" >> splitter_$i.fcl
  while IFS= read -r line; do
    echo "adding file: " $line
    echo "\"$line\"" >> splitter_$i.fcl
    if (( ${N_SIGNAL_FILES_TO_USE} > 1 )); then
      echo "," >> splitter_$i.fcl
    fi
  done < "filenames_ChosenSig_$i"
  echo "]" >> splitter_$i.fcl
  echo "source.maxEvents: ${NSIG}" >> splitter_$i.fcl
  echo "outputs.out.fileName: \"mcs.${OWNER}.${SIGNAL}Mix${BB}TriggeredSplit.${RELEASE}_${DBPURPOSE}_${DBVERSION}.${i}.art\"" >> splitter_$i.fcl
  cmd=$(mu2e -c splitter_$i.fcl)
  echo "Running: $cmd"
  # run the splitting function
  $cmd
  
  # make the ntuples
  echo "#include \"EventNtuple/fcl/from_mcs-mockdata.fcl\"" >> ntuple_$i.fcl
  echo "services.TFileService.fileName: \"nts.${OWNER}.${SIGNAL}Mix${BB}TriggeredSplit.${RELEASE}_${DBPURPOSE}_${DBVERSION}.${i}.root\"" >> ntuple_$i.fcl
  cmd=$(mu2e -c ntuple_$i.fcl mcs.${OWNER}.${SIGNAL}Mix${BB}TriggeredSplit.${RELEASE}_${DBPURPOSE}_${DBVERSION}.${i}.art)
  echo "Running: $cmd"
  $cmd
  ls nts.${OWNER}.${SIGNAL}Mix${BB}TriggeredSplit.${RELEASE}_${DBPURPOSE}_${DBVERSION}.${i}.root > temp

  # create randomly mixed list of ntuples
  shuf -n ${N_KNOWN_FILES_TO_USE} filenames_All_${KNOWN} >> temp
  shuf temp > filenames_ChosenMixed_$i
  rm temp
  i=$((i + 1))

done
mkdir fcl
mv *.fcl fcl
echo "finished compiling list of chosen ntuples"
rm *.csv
