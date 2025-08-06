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
from prod_utils import make_jobdefs_list, run, push_output, replace_file_extensions, parse_jobdef_fields, write_fcl

def main():
    parser = argparse.ArgumentParser(description="Process some inputs.")
    parser.add_argument("--copy-input", action="store_true", help="Copy input files using mdh")
    parser.add_argument('--dry-run', action='store_true', help='Print commands without actually running pushOutput')
    parser.add_argument('--nevts', type=int, default=-1, help='Number of events to process (-1 for all events, default: -1)')
    parser.add_argument('--jobdefs', required=True, help='Path to the jobdefs_*.txt file')
    parser.add_argument('--ignore-jobdef-setup', action='store_true', help='Ignore the jobdef setup')
    
    args = parser.parse_args()

    # Extract job definition fields
    TARF, IND, INLOC, OUTLOC = parse_jobdef_fields(args.jobdefs)
    
    # Copy jobdef to local directory
    run(f"mdh copy-file -e 3 -o -v -s disk -l local {TARF}", shell=True)

    # List input files
    infiles = run(f"mu2ejobiodetail --jobdef {TARF} --index {IND} --inputs", capture=True, shell=True)
    
    if args.copy_input and infiles.strip():
        # Copy inputs locally
        FCL = write_fcl(TARF, f"dir:{os.getcwd()}/indir", 'file', IND)
        run(f"mdh copy-file -e 3 -o -v -s {INLOC} -l local {infiles}", shell=True)
        run(f"mkdir indir; mv *.art indir/", shell=True)
    else:
        # Use default settings (no inputs or remote inputs)
        FCL = write_fcl(TARF, INLOC, 'root', IND)
    
    # Setup command for clean environment to run using setup from jobdef
    jobdef_simjob_setup = run(f"mu2ejobquery --setup {TARF}", capture=True, shell=True)
    setup_cmd = f"source {jobdef_simjob_setup}"
    mu2e_cmd = f"mu2e -c {FCL} -n {args.nevts}"

    run(f"{setup_cmd} && {mu2e_cmd}", shell=True)
    
    # Write the list to the file in one line
    parents = infiles.split()  # List of input files
    Path("parents_list.txt").write_text("\n".join(parents) + "\n")
    
    # Handle output files and submission
    if args.dry_run:
        print("[DRY RUN] Would run: pushOutput output.txt")
    else:
        push_data(OUTLOC)
        push_logs(FCL)

    run("ls -ltra", shell=True)

def push_data(OUTLOC):
    """Handle data file management and submission."""
    # Find all .art and .root files
    out_fnames = glob.glob("*.art") + glob.glob("*.root")

    out_content = ""
    for out_fname in out_fnames:
        out_content += f"{OUTLOC} {out_fname} parents_list.txt\n"

    Path("output.txt").write_text(out_content)

    # Push output
    run("pushOutput output.txt", shell=True)

def push_logs(FCL):
    """Handle log file management and submission."""
    # In production mode, copy the job submission log file from jsb_tmp to LOGFILE_LOC.
    LOGFILE = replace_file_extensions(FCL, "log", "log")

    # Copy the jobsub log if JSB_TMP is defined
    jsb_tmp = os.getenv("JSB_TMP")
    if jsb_tmp:
        jobsub_log = "JOBSUB_LOG_FILE"
        src = os.path.join(jsb_tmp, jobsub_log)
        print(f"Copying jobsub log from {src} to {LOGFILE}")
        shutil.copy(src, LOGFILE)

    # Create log output content
    log_content = f"disk {LOGFILE} parents_list.txt\n"
    Path("log_output.txt").write_text(log_content)

    # Push log output
    run("pushOutput log_output.txt", shell=True)

if __name__ == "__main__":
    main()
