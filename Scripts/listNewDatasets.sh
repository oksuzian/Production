#!/bin/bash
set -euo pipefail

# Default values
FILETYPE="art"    # Default filetype is "art"
DAYS=7            # Default days to look back
SUMMARY=false     # Default: do not print summary details
USER="mu2epro"    # Default user is mu2epro
CUSTOM_QUERY=""   # Custom query (overrides default if provided)
SHOW_SIZE=true    # Default: show file sizes

# Process command-line options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --filetype)
      FILETYPE="$2"
      shift 2
      ;;
    --days)
      DAYS="$2"
      shift 2
      ;;
    --summary)
      SUMMARY=true
      shift 1
      ;;
    --no-size)
      SHOW_SIZE=false
      shift 1
      ;;
    --user)
      USER="$2"
      shift 2
      ;;
    --query)
      CUSTOM_QUERY="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--filetype <log|art>] [--days <number>] [--summary] [--no-size] [--user <username>] [--query <custom_query>]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--filetype <log|art>] [--days <number>] [--summary] [--no-size] [--user <username>] [--query <custom_query>]"
      exit 1
      ;;
  esac
done

# Use custom query if provided, otherwise build default query
if [[ -n "$CUSTOM_QUERY" ]]; then
  QUERY="$CUSTOM_QUERY"
  echo "Using custom query: $QUERY"
else
  # Calculate the date DAYS ago (in YYYY-MM-DD format)
  OLDER_DATE=$(date -d "$DAYS days ago" +%Y-%m-%d)
  echo "Checking for $FILETYPE files created after: $OLDER_DATE for user: $USER"
  
  # Build the samweb query string using the chosen file type and user.
  QUERY="Create_Date > $OLDER_DATE and file_format $FILETYPE and user $USER"
fi

# Append a dot before the provided file type.
EXT=".$FILETYPE"

echo "------------------------------------------------"
echo "Grouped file counts:"
if [[ "$SHOW_SIZE" == true ]]; then
  printf "%8s %-100s %10s\n" "COUNT" "DATASET" "FILE SIZE"
  printf "%8s %-100s %10s\n" "-----" "-------" "--------"
else
  printf "%8s %-100s\n" "COUNT" "DATASET"
  printf "%8s %-100s\n" "-----" "-------"
fi
# Run the samweb query and process the output.
samweb list-files "$QUERY" | \
  awk -F. -v ext="$EXT" '{ print $1"."$2"."$3"."$4 ext }' | \
  sort | uniq -c | \
  while read count dataset; do
    if [[ "$SHOW_SIZE" == true ]]; then
      avg_size=$(bash avg_filesize.sh "$dataset" 2>/dev/null || echo "N/A")
      printf "%8s %-100s %7s MB\n" "$count" "$dataset" "$avg_size"
    else
      printf "%8s %-100s\n" "$count" "$dataset"
    fi
  done
echo "------------------------------------------------"

# If the --summary flag is set, print detailed summary for each unique dataset group.
if [[ "$SUMMARY" == true ]]; then
  echo "Printing summary for each dataset group:"
  samweb list-files "$QUERY" | \
    awk -F. -v ext="$EXT" '{ print $1"."$2"."$3"."$4 ext }' | \
    sort | uniq | while read ds; do
      echo "------------------------------------------------"
      echo "Summary for dataset: $ds"
      samweb list-definition-files --summary "$ds"
  done
fi
