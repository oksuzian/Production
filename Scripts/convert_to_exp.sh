#!/bin/bash

# Script to convert numbers to exponential format
# Usage: ./convert_to_exp.sh [input_file]
# Or pipe input: command | ./convert_to_exp.sh

# Function to convert numbers to exponential format
convert_numbers() {
    awk '
    {
        # Process each field in the line
        for (i = 1; i <= NF; i++) {
            # Check if field contains only digits
            if ($i ~ /^[0-9]+$/) {
                # Convert to exponential format with 4 decimal places
                $i = sprintf("%.2e", $i)
            }
        }
        # Print the modified line
        print
    }'
}

# Read from file if provided, otherwise from stdin
if [ $# -eq 1 ]; then
    convert_numbers < "$1"
else
    convert_numbers
fi 