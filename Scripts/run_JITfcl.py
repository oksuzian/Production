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
from mu2e_poms_util.prod_utils import make_jobdefs_list, run, push_output, replace_file_extensions

def main():
    parser = argparse.ArgumentParser(description="Process some inputs.")
    parser.add_argument("--copy_input", action="store_true", help="Copy input files using mdh")
    parser.add_argument('--dry_run', action='store_true', help='Print commands without actually running pushOutput')
    parser.add_argument('--test_run', action='store_true', help='Run 10 events only')
    parser.add_argument('--save_root', action='store_true', help='Save root and art output files')
    
    args = parser.parse_args()
    copy_input = args.copy_input

    #check token before proceeding
    run(f"httokendecode -H", shell=True)
    
    fname = os.getenv("fname")
    if not fname:
        print("Error: fname environment variable is not set.")
        sys.exit(1)

    print(f"{datetime.now()} starting fclless submission")
    print(f"args: {sys.argv}")
    print(f"fname={fname}")
    print(f"pwd={os.getcwd()}")
    print("ls of default dir")
    run("ls -al", shell=True)        
    
    CONDOR_DIR_INPUT = os.getenv("CONDOR_DIR_INPUT", ".")
    run(f"ls -ltr {CONDOR_DIR_INPUT}", shell=True)

    try:
        IND = int(fname.split('.')[4].lstrip('0') or '0')
    except (IndexError, ValueError) as e:
        print("Error: Unable to extract index from filename.")
        sys.exit(1)

    mapfile = run(f"ls {CONDOR_DIR_INPUT}/jobdefs_*.txt", capture=True, shell=True).strip()
    jobdefs_list = make_jobdefs_list(Path(mapfile))
    
    print(f"len(jobdefs_list): {len(jobdefs_list)}, IND: {IND}")
        
    # Check that there are at least IND job definitions.
    if len(jobdefs_list) < IND:
        raise ValueError(f"Expected at least {IND} job definitions, but got only {len(jobdefs_list)}")
    
    # Get the IND-th job definition (adjusting for Python's 0-index).
    jobdef = jobdefs_list[IND]
    print(f"The {IND}th job definition is: {jobdef}")

    # Split the job definition into fields (parfile job_index inloc outloc).
    fields = jobdef.split()
    if len(fields) != 4:
        raise ValueError(f"Expected 4 fields (parfile job_index inloc outloc) in the job definition, but got: {jobdef}")

    # Assign the fields to the appropriate variables.
    TARF = fields[0]
    IND = int(fields[1])  # update IND based on extracted value from the map
    INLOC = fields[2]     # use inloc from map file
    OUTLOC = fields[3]    # use outloc from map file

    run(f"mdh copy-file -e 3 -o -v -s disk -l local {TARF}", shell=True)

    print(f"IND={IND} TARF={TARF} INLOC={INLOC} OUTLOC={OUTLOC}")

    FCL = os.path.basename(TARF)[:-6] + f".{IND}.fcl"

    #unset BEARER_TOKEN
    print(f"BEARER_TOKEN before unset: {os.environ.get('BEARER_TOKEN')}")
    os.environ.pop('BEARER_TOKEN', None)
    # Check if the variable is unset
    print(f"BEARER_TOKEN after unset: {os.environ.get('BEARER_TOKEN')}")

    infiles = run(f"mu2ejobiodetail --jobdef {TARF} --index {IND} --inputs", capture=True, shell=True)
    # Generate FCL without input if infiles is empty
    if not infiles.strip():
        run(f"mu2ejobfcl --jobdef {TARF} --index {IND} > {FCL}", shell=True)
    elif copy_input:
        run(f"mu2ejobfcl --jobdef {TARF} --index {IND} --default-proto file --default-loc dir:{os.getcwd()}/indir > {FCL}", shell=True)
        print("infiles: %s"%infiles)
        run(f"mdh copy-file -e 3 -o -v -s {INLOC} -l local {infiles}", shell=True)
        run(f"mkdir indir; mv *.art indir/", shell=True)
    else:
        run(f"mu2ejobfcl --jobdef {TARF} --index {IND} --default-proto root --default-loc {INLOC} > {FCL}", shell=True)

    print(f"{datetime.now()} submit_fclless {FCL} content")
    with open(FCL, 'r') as f:
        print(f.read())

    if args.test_run:
        run(f"mu2e -n 10 -c {FCL}", shell=True)
    else:
        run(f"mu2e -c {FCL}", shell=True)

    run(f"ls {fname}", shell=True)

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
    run(f"httokendecode -H", shell=True)
    if args.dry_run:
        print("[DRY RUN] Would run: pushOutput output.txt")
    else:
        run("pushOutput output.txt", shell=True)

#    run_command("rm -f *.root *.art *.txt")

if __name__ == "__main__":
    main()
