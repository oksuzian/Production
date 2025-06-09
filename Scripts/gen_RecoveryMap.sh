#!/bin/bash

# Script to find missing output files from mix parfiles
# Example: gen_RecoveryMap.sh /exp/mu2e/app/users/mu2epro/production_manager/poms_map/mdc2020aw_mix.txt


# Default values
INPUT_FILE="${1}"
OUTPUT_FILE="missing_files.txt"

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Error: Input file '$INPUT_FILE' not found."
  exit 1
fi

RECOVER_FILE=$(basename $INPUT_FILE | sed 's/\.txt$/_recovery.txt/')
# Clear output file and show status
> "$RECOVER_FILE"
> "$OUTPUT_FILE"
echo "Reading POMS map file: $INPUT_FILE"
echo "Writing missing files to: $OUTPUT_FILE"
echo "Writing recovery POMS map to: $RECOVER_FILE"

# Loop through each line
while IFS= read -r line || [[ -n "$line" ]]; do
  read -ra columns <<< "$line"
  # Skip empty lines
  if [[ ${#columns[@]} -eq 0 ]]; then
    continue
  fi
  
  # Check if we have at least 2 columns
  if [[ ${#columns[@]} -lt 4 ]]; then
    echo "Error: Expected at least 4 columns in input file"
    exit 1
  fi

  inloc=${columns[2]}
  outloc=${columns[3]}

  parfile=$(echo "${columns[0]}" | sed 's/\.tar$/.0.tar/')
  parloc=$(samweb locate-file $parfile | sed 's/^dcache://')
  echo "parfile: $parloc/$parfile"
  
  # Get output datasets and loop through them
  datasets=$(mu2ejobquery --output-datasets  $parloc/$parfile)
  if [[ -z "$datasets" ]]; then
    echo "No output datasets found for $parfile"
    exit 1
  fi

  while IFS= read -r dataset; do
    echo "Checking dataset: $dataset"
    
    # Get expected files from job configuration
    expected_files=$(mktemp)
    mu2ejobquery --output-files "$dataset" "$parloc/$parfile" > "$expected_files"
    
    # Get actual files in the dataset
    actual_files=$(mktemp)
    samweb list-definition-files "$dataset" > "$actual_files" 2>/dev/null || touch "$actual_files"
    
    # Find missing files (expected but not in actual)
    missing_files=$(mktemp)
    comm -23 <(sort "$expected_files") <(sort "$actual_files") > "$missing_files"
    
    # Process missing files - find their index in the expected list
    while IFS= read -r file; do
      if [[ -n "$file" ]]; then
        # Find the line number (index) of this file in the expected files
        idx=$(grep -n "^${file}$" "$expected_files" | cut -d: -f1)
        if [[ -n "$idx" ]]; then
          # Convert to 0-based index
          idx=$((idx - 1))
          echo "$file" >> "$OUTPUT_FILE"
          echo "Missing file: $file"
          echo "$parfile" "$idx" "$inloc" "$outloc" >> "$RECOVER_FILE"
        fi
      fi
    done < "$missing_files"
    
    # Cleanup temp files
    rm -f "$expected_files" "$actual_files" "$missing_files"
  done <<< "$datasets"
done < "$INPUT_FILE"

# Remove duplicate lines from recovery map
sort -u "$RECOVER_FILE" -o "$RECOVER_FILE"
echo "Removed duplicate entries from recovery map"