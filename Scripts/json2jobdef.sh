#!/usr/bin/env bash
# Author: Y. Oksuzian
# json2jobdef.sh: Unified generator for Stage1, Stage2(Resampler, Primaries), or Merge jobs via JSON
# Usage:
#   bash json2jobdef.sh --json config.json --desc <desc> [--owner mu2e] [--pushout] [--jobs-map FILE]

# Defaults
OWNER=${USER/#mu2epro/mu2e}
JSON_FILE=""
JOB_DESC=""
PUSHOUT=false
JOBS_MAP=""

usage() {
  cat <<EOF
Usage: $0 --json FILE --desc NAME [--owner NAME] [--pushout] [--jobs-map FILE] 

  --json       FILE   JSON config with job definitions (required)
  --desc       NAME   description key to select entry (required)
  --owner      NAME   data owner (default: mu2e)
  --pushout           enable pushOutput of results
  --jobs-map   FILE   output file for job info (default: jobs-map)
  --help            show this message
EOF
  exit 1
}

# Parse options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)       JSON_FILE="$2"; shift 2;;
    --desc)       DESC="$2"; shift 2;;
    --dsconf)     DSCONF="$2"; shift 2;;
    --owner)      OWNER="$2";    shift 2;;
    --pushout)    PUSHOUT=true;    shift;;
    --jobs-map)   JOBS_MAP="$2";  shift 2;;    
    --help)       usage;;
    *) echo "Unknown option: $1" >&2; usage;;
  esac
done

# Validate inputs
if [[ -z "$JSON_FILE" || -z "$DESC" ]]; then
  echo "Error: --json and --desc are required." >&2
  usage
fi

# Load JSON entry and ensure uniqueness
count=$(jq --arg d "$DESC" --arg s "$DSCONF" 'map(select(.desc==$d and .dsconf==$s)) | length' "$JSON_FILE")
if (( count != 1 )); then
  echo "Error: found $count entries matching desc='$DESC' and dsconf='$DSCONF'; must be exactly one." >&2
  exit 1
fi
entry=$(jq --arg d "$DESC" --arg s "$DSCONF" 'map(select(.desc==$d and .dsconf==$s))[0]' "$JSON_FILE")

# Common fields
DSCONF=$(jq -r '.dsconf' <<<"$entry")
DESC=$(jq -r '.desc' <<<"$entry")
FCL=$(jq -r '.fcl // empty' <<<"$entry")
SIMJOB_SETUP=$(jq -r '.simjob_setup // empty' <<<"$entry")
INPUT_DATA=$(jq -r '.input_data // empty' <<<"$entry")
EXTRA_OPTS=$(jq -r '.extra_opts // empty' <<<"$entry")
MERGE_FACTOR=$(jq -r '.merge_factor // empty' <<<"$entry")
MERGE_FACTOR_RESAMPLER=$(jq -r '.merge_factor_resampler // 1' <<<"$entry")
RUN=$(jq -r '.run // empty' <<<"$entry")
EVENTS=$(jq -r '.events // empty' <<<"$entry")
RESAMPLER_NAME=$(jq -r '.resampler_name // empty' <<<"$entry")
NJOBS=$(jq -r '.njobs // -1' <<<"$entry")
INLOC=$(jq -r '.inloc // "tape"' <<<"$entry")
OUTLOC=$(jq -r '.outloc // "tape"' <<<"$entry")

# Initialize mu2ejobdef command
declare -a CMD=( mu2ejobdef --verbose --setup "$SIMJOB_SETUP"  --dsconf "$DSCONF" --desc "$DESC" --dsowner "$OWNER" )
# Only add run-number and events-per-job if exist in json
[[ -n "$RUN"    ]] && CMD+=( --run-number    "$RUN" )
[[ -n "$EVENTS" ]] && CMD+=( --events-per-job "$EVENTS" )

echo "Generating template.fcl with #include $FCL"
echo "#include \"$FCL\"" > template.fcl

if [[ -n "$INPUT_DATA" ]]; then
    echo "Listing files for input dataset: $INPUT_DATA"
    samweb list-files "dh.dataset=$INPUT_DATA and event_count>0" > inputs.txt
fi

# Job-specific logic
if [[ -n "$RESAMPLER_NAME" ]]; then
  echo "Resampler job: $DESC (${RESAMPLER_NAME})"
  nfiles=$(samCountFiles.sh "$INPUT_DATA")
  nevts=$(samCountEvents.sh "$INPUT_DATA")
  skip=$((nevts / nfiles))
  echo "physics.filters.${RESAMPLER_NAME}.mu2e.MaxEventsToSkip: $skip" >> template.fcl
  CMD+=( --auxinput "${MERGE_FACTOR_RESAMPLER}:physics.filters.${RESAMPLER_NAME}.fileNames:inputs.txt" )
elif [[ -n "$MERGE_FACTOR" ]]; then
  echo "Merge job: $DESC, factor=$MERGE_FACTOR"
  CMD+=( --inputs inputs.txt --merge-factor "$MERGE_FACTOR" )
else
  echo "S1 job: $DESC"
fi

echo "Applying fcl_overrides to template.fcl"
jq -r --arg d "$DESC" \
  'map(select(.desc==$d))[0].fcl_overrides // {} | to_entries[] | "\(.key): \(.value)"' \
  "$JSON_FILE" >> template.fcl

# Finalize embed
echo "Embedding template.fcl"
CMD+=( --embed template.fcl )
CMD+=( $EXTRA_OPTS )

# Echo and run
parfile="cnf.${OWNER}.${DESC}.${DSCONF}.0.tar"
rm -f $parfile
echo "${CMD[@]}"
"${CMD[@]}"

# pushOutput
echo "Post-processing outputs"
echo "disk $parfile none" > outputs.txt
if [[ "$PUSHOUT" == true ]]; then
  samweb locate-file "$parfile" &>/dev/null && echo "Exists on SAM; not pushing." || pushOutput outputs.txt
else
  echo "PushOutput disabled."
fi

# Save job information to text file
jobs_map="${JOBS_MAP:-jobs-map}"
if [[ -z "$INLOC" ]]; then
  echo "Error: inloc field not found in JSON for $DESC" >&2
  exit 1
fi
if [[ -z "$OUTLOC" ]]; then
  echo "Error: outloc field not found in JSON for $DESC" >&2
  exit 1
fi

# Check if parfile exists in info file and update/append accordingly
pardef="cnf.${OWNER}.${DESC}.${DSCONF}.tar"
if [[ -f "$jobs_map" ]]; then
  if grep -q "^$pardef " "$jobs_map"; then
    # Update existing entry
    sed -i "s|^$pardef .*|$pardef $NJOBS $INLOC $OUTLOC|" "$jobs_map"
  else
    # Append new entry
    echo "$pardef $NJOBS $INLOC $OUTLOC" >> "$jobs_map"
  fi
else
  # Create new file
  echo "$pardef $NJOBS $INLOC $OUTLOC" > "$jobs_map"
fi

# Generate test FCL
test_fcl="${parfile%.tar}.fcl"
mu2ejobfcl --jobdef "$parfile" --index 0 --default-proto root --default-loc "$INLOC" > "$test_fcl"
cat "$test_fcl"
