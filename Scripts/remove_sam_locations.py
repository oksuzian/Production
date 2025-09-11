# Examples of usage:
# python /exp/mu2e/app/users/oksuzian/muse_080224/Production/Scripts/remove_bad_locations.py --file /exp/mu2e/app/users/mu2epro/production_manager/current_datasets/mc/datasets_evntuple_an.txt --dry-run
# or
# python /exp/mu2e/app/users/oksuzian/muse_080224/Production/Scripts/remove_bad_locations.py --definition nts.mu2e.CosmicCORSIKASignalAllOnSpillTriggered.MDC2020an_v06_01_01_perfect_v1_3.root

import argparse
from mu2e_poms_util.samweb_wrapper import list_definition_files, locate_file, remove_file_location

# Function to get file list from a definition
def get_files_from_definition(definition_name):
    try:
        return list_definition_files(definition_name)
    except Exception as e:
        print(f"Error fetching file list: {e}")
        return []

# Function to get file list from a text file containing definitions
def get_files_from_definitions_file(file_path):
    files = []
    try:
        with open(file_path, "r") as file:
            definitions = [line.strip() for line in file if line.strip()]
        for definition in definitions:
            files.extend(get_files_from_definition(definition))
    except Exception as e:
        print(f"Error reading definitions file {file_path}: {e}")
    return files

# Function to get locations for a file
def get_file_locations(file_name):
    try:
        result = locate_file(file_name)
        # Handle the case where locate_file returns a dict
        if isinstance(result, dict):
            return [result.get('location', '')]
        elif isinstance(result, str):
            return [result] if result else []
        else:
            return []
    except Exception as e:
        print(f"Error fetching locations for {file_name}: {e}")
        return []

# Function to remove a specific location for a file
def remove_file_location_wrapper(file_name, location):
    try:
        remove_file_location(file_name, location)
        print(f"Removed location {location} for file {file_name}")
    except Exception as e:
        print(f"Error removing location {location} for file {file_name}: {e}")

# Main script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove file locations containing a specific keyword.")
    parser.add_argument("--definition", help="The SAM definition name.")
    parser.add_argument("--file", help="Path to a text file containing a list of definitions.")
    parser.add_argument("--keyword", default="override_me", help="Keyword to identify locations to remove (default: override_me).")
    parser.add_argument("--dry-run", action="store_true", help="If set, only print the actions without executing them.")
    args = parser.parse_args()

    override_keyword = args.keyword

    # Get the list of files from the definition or a file containing definitions
    if args.definition:
        files = get_files_from_definition(args.definition)
    elif args.file:
        files = get_files_from_definitions_file(args.file)
    else:
        print("Error: You must provide either a SAM definition name or a file containing a list of definitions.")
        exit(1)

    for file_name in files:
        # Get locations for the current file
        locations = get_file_locations(file_name)

        for location in locations:
            if override_keyword in location:
                if args.dry_run:
                    print(f"[Dry Run] Would remove location {location} for file {file_name}")
                else:
                    remove_file_location_wrapper(file_name, location)

    print("Processing complete.")
