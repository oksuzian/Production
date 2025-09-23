#!/bin/bash

# usage: "combine_ntuples.sh 1 MDS2c" where first arg is ther iteration and second is the known tag
i=$1
KNOWN=$2
CONFIG=${KNOWN}.txt
BB=""
SIGNAL=""
RMUE=""

while IFS='= ' read -r col1 col2
do 
    if [[ "${col1}" == "livetime_combined" ]] ; then
      LIVETIME=${col2}
    fi
    if [[ "${col1}" == "Rmue" ]] ; then
      RMUE=${col2}
    fi
    if [[ "${col1}" == "signal" ]] ; then
      SIGNAL=${col2}
    fi
    if [[ "${col1}" == "BB" ]] ; then
      BB=${col2}
    fi
done <${CONFIG}


INPUT_LIST="filenames_ChosenMixed_$i"
OUTPUT_LIST="merged_list_$i.txt"
OUTPUT_DIR="merged_files_$i"
OUTNAME="nts.mu2e.ensemble${KNOWN}Mix${BB}_${SIGNAL}_${RMUE}_${LIVETIME}.$i"

FILES_PER_MERGE=2 # Set the number of files to merge at a time

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Clear the output list file before starting
> "$OUTPUT_LIST"

# --- Main Logic ---

# Use a while loop to read input files and an array to group them
file_group=()
counter=0
group_counter=1

while IFS= read -r root_file; do
  file_group+=("$root_file")
  counter=$((counter + 1))

  # Merge when the group is full or all files are processed
  if [[ ${#file_group[@]} -eq $FILES_PER_MERGE ]] || [[ -z "$root_file" && ${#file_group[@]} -gt 0 ]]; then
    
    # Define the output file name
    output_filename="${OUTPUT_DIR}/${OUTNAME}_${group_counter}.root"

    echo "Merging group $group_counter: ${#file_group[@]} files into $output_filename"
    hadd -f "$output_filename" "${file_group[@]}"

    # Add the new file to the output list
    echo "$output_filename" >> "$OUTPUT_LIST"

    # Reset for the next group
    file_group=()
    group_counter=$((group_counter + 1))
  fi
done < "$INPUT_LIST"

# Check for any remaining files in the last group
if [[ ${#file_group[@]} -gt 0 ]]; then
  output_filename="${OUTPUT_DIR}/${OUTNAME}_${group_counter}.root"
  echo "Merging final group: ${#file_group[@]} files into $output_filename"
  hadd -f "$output_filename" "${file_group[@]}"
  echo "$output_filename" >> "$OUTPUT_LIST"
fi

echo "Merge process complete. Merged files are in '$OUTPUT_DIR/'."
echo "List of merged files is in '$OUTPUT_LIST'."
