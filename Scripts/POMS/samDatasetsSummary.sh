#!/bin/bash
# usage
if [[ -z "$1" ]]; then
  echo "Usage: $0 <dataset>" >&2
  exit 1
fi

# Get the dataset name
dataset="$1"
# Obtain summary once
summary_txt=$(samweb list-definition-files --summary "$dataset" 2>/dev/null)
nfiles=$(echo "$summary_txt" | awk '/File count:/ {print $3}')
size=$(echo "$summary_txt" | awk '/Total size:/ {print $3}')
triggered=$(echo "$summary_txt" | awk '/Event count:/ {print $3}')

# Ensure numeric defaults
nfiles=${nfiles:-0}
size=${size:-0}
triggered=${triggered:-0}

# Exit if no files found
if (( nfiles == 0 )); then
    echo "Error: No files found in dataset" >&2
    exit 1
fi

# Calculate total generated events from all files
generated=$(samweb list-definition-files "$dataset" 2>/dev/null | \
  xargs -n1 samweb get-metadata | awk '/dh.gencount/ { sum += $2 } END { print sum+0 }')

printf "Triggered: %s\nGenerated: %s\nFiles: %s\nSize: %s\n" "$triggered" "$generated" "$nfiles" "$size"

# append to CSV
echo "${dataset},${triggered},${generated},${nfiles},${size}" >> "samDatasetSummary.csv"
