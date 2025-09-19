#!/bin/bash
# usage
if [[ -z "$1" ]]; then
  echo "Usage: $0 <dataset> [--sample-files N]" >&2
  echo "  --sample-files N: Number of files to sample for generated events calculation (default: 10)" >&2
  exit 1
fi

# Get the dataset name
dataset="$1"

# Parse command line arguments
sample_files=10
if [[ "$2" == "--sample-files" && -n "$3" ]]; then
  sample_files="$3"
fi
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

# Calculate total generated events by extrapolating from sampled files
# OPTIMIZATION: Use SAM's metadata query to get dh.gencount directly
sample_sum=$(samweb list-definition-files "$dataset" 2>/dev/null | \
  head -"$sample_files" | while read file; do
    samweb get-metadata "$file" 2>/dev/null | awk '/dh.gencount/ {print $2}'
  done | awk '{sum += $1} END {print sum+0}')

# Extrapolate to total number of files
if (( sample_sum > 0 && sample_files > 0 )); then
  avg_per_file=$((sample_sum / sample_files))
  generated=$((avg_per_file * nfiles))
  echo "Debug: Sampled $sample_files files for dh.gencount, sum=$sample_sum, avg=$avg_per_file, extrapolated=$generated" >&2
else
  generated=0
fi

printf "Triggered: %s\nGenerated: %s\nFiles: %s\nSize: %s\n" "$triggered" "$generated" "$nfiles" "$size"

# append to CSV
echo "${dataset},${triggered},${generated},${nfiles},${size}" >> "samDatasetSummary.csv"
