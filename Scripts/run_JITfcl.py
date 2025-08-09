#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import textwrap
import glob
import shutil

# Function: Exit with error.
def exit_abnormal():
    usage()
    sys.exit(1)

# Function: Print a help message.
def usage():
    print("Usage: script_name.py [--copy_input_mdh --copy_input_ifdh]")
    print("e.g. run_JITfcl.py --copy_input_mdh")

# Function to run a shell command and return the output while streaming
def run_command(command, hard_fail=True):
    print(f"Running: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = []  # Collect the command output
    for line in process.stdout:
        print(line, end="")  # Print each line in real-time
        output.append(line.strip())  # Collect the output lines
    process.wait()  # Wait for the command to complete

    if process.returncode != 0:
        print(f"Error running command: {command}")
        if hard_fail:
            exit_abnormal()

    return "\n".join(output)  # Return the full output as a string

# Replace the first and last fields
def replace_file_extensions(input_str, first_field, last_field):
    fields = input_str.split('.')
    fields[0] = first_field
    fields[-1] = last_field
    return '.'.join(fields)

def main():
    parser = argparse.ArgumentParser(description="Process some inputs.")
    parser.add_argument("--copy_input_mdh", action="store_true", help="Copy input files using mdh")
    parser.add_argument("--copy_input_ifdh", action="store_true", help="Copy input files using ifhd")
    parser.add_argument('--dry_run', action='store_true', help='Print commands without actually running pushOutput')
    parser.add_argument('--test_run', action='store_true', help='Run 10 events only')
    parser.add_argument('--save_root', action='store_true', help='Save root and art output files')
    
    args = parser.parse_args()
    copy_input_mdh = args.copy_input_mdh
    copy_input_ifdh = args.copy_input_ifdh

    #check token before proceeding
    run_command(f"httokendecode -H", hard_fail=False)
    
    fname = os.getenv("fname")
    if not fname:
        print("Error: fname environment variable is not set.")
        exit_abnormal()

    print(f"{datetime.now()} starting fclless submission")
    print(f"args: {sys.argv}")
    print(f"fname={fname}")
    print(f"pwd={os.getcwd()}")
    print("ls of default dir")
    run_command("ls -al")        
    
    CONDOR_DIR_INPUT = os.getenv("CONDOR_DIR_INPUT", ".")
    run_command(f"ls -ltr {CONDOR_DIR_INPUT}")

    try:
        IND = int(fname.split('.')[4].lstrip('0') or '0')
    except (IndexError, ValueError) as e:
        print("Error: Unable to extract index from filename.")
        exit_abnormal()

    # Find the mapfile robustly
    mapfiles = sorted(glob.glob(os.path.join(CONDOR_DIR_INPUT, "merged*.txt")))
    if not mapfiles:
        print(f"Error: No 'merged*.txt' files found in {CONDOR_DIR_INPUT}")
        exit_abnormal()
    mapfile = mapfiles[0]
    with open(mapfile, 'r') as f:
        maplines = f.read().splitlines()
        
    print("len(maplines): %d, IND: %d"%(len(maplines), IND))
        
    # Validate index bounds (0-based)
    if IND < 0 or IND >= len(maplines):
        raise ValueError(f"Index {IND} out of range for {len(maplines)} lines in {mapfile}")
    
    # Get the IND-th line (adjusting for Python's 0-index).
    mapline = maplines[IND]
    print(f"The {IND}th line is: {mapline}")

    # Split the line into fields (assuming whitespace-separated).
    fields = mapline.split()
    if len(fields) != 4:
        raise ValueError(f"Expected 4 fields (parfile njobs inloc outloc) in the line, but got: {mapline}")

    # Assign the fields to the appropriate variables.
    TARF = fields[0]
    IND = int(fields[1])  # update IND based on extracted value from the map
    INLOC = fields[2]     # use inloc from map file
    OUTLOC = fields[3]    # use outloc from map file

    run_command(f"mdh copy-file -e 3 -o -v -s disk -l local {TARF}")

    print(f"IND={IND} TARF={TARF} INLOC={INLOC} OUTLOC={OUTLOC}")

    FCL = os.path.basename(TARF)[:-6] + f".{IND}.fcl"

    # Unset BEARER_TOKEN without printing its value
    if 'BEARER_TOKEN' in os.environ:
        os.environ.pop('BEARER_TOKEN', None)
        print("BEARER_TOKEN environment variable unset")
    else:
        print("BEARER_TOKEN not set")

    infiles = run_command(f"mu2ejobiodetail --jobdef {TARF} --index {IND} --inputs")
    # Generate FCL without input if infiles is empty
    if not infiles.strip():
        run_command(f"mu2ejobfcl --jobdef {TARF} --index {IND} > {FCL}")
    elif copy_input_mdh:
        run_command(f"mu2ejobfcl --jobdef {TARF} --index {IND} --default-proto file --default-loc dir:{os.getcwd()}/indir > {FCL}")
        print("infiles: %s"%infiles)
        run_command(f"mdh copy-file -e 3 -o -v -s {INLOC} -l local {infiles}")
        run_command(f"mkdir indir; mv *.art indir/")
    else:
        run_command(f"mu2ejobfcl --jobdef {TARF} --index {IND} --default-proto root --default-loc {INLOC} > {FCL}")

    print(f"{datetime.now()} submit_fclless {FCL} content")
    with open(FCL, 'r') as f:
        print(f.read())

    if args.test_run:
        run_command(f"mu2e -n 10 -c {FCL}")
    else:
        run_command(f"mu2e -c {FCL}")

    run_command(f"ls {fname}")

    if args.save_root:
        out_fnames = glob.glob("*.art") + glob.glob("*.root")
    else:
        out_fnames = glob.glob("*.art")  # Find all .art files

    # Write the list to the file in one line
    parents = infiles.split() + [fname]  # Add {fname} to the list of files
    Path("parents_list.txt").write_text("\n".join(parents) + "\n")

    out_content = ""
    for out_fname in out_fnames:
        out_content += f"{OUTLOC} {out_fname} parents_list.txt\n"

    # In production mode, copy the job submission log file from jsb_tmp to LOGFILE_LOC.
    LOGFILE_LOC = replace_file_extensions(FCL, "log", "log")

    # Copy the jobsub log if JSB_TMP is defined
    jsb_tmp = os.getenv("JSB_TMP")
    if jsb_tmp:
        jobsub_log = "JOBSUB_LOG_FILE"
        src = os.path.join(jsb_tmp, jobsub_log)
        print(f"Copying jobsub log from {src} to {LOGFILE_LOC}")
        shutil.copy(src, LOGFILE_LOC)

    out_content += f"disk {LOGFILE_LOC} parents_list.txt\n"
    Path("output.txt").write_text(out_content)

    # Push output
    run_command(f"httokendecode -H", hard_fail=False)
    if args.dry_run:
        print("[DRY RUN] Would run: pushOutput output.txt")
    else:
        run_command("pushOutput output.txt")

#    run_command("rm -f *.root *.art *.txt")

if __name__ == "__main__":
    main()
