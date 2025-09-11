#!/usr/bin/env python3

import os
import glob
import shutil
import argparse
from pathlib import Path
from mu2e_poms_util.prod_utils import parse_jobdef_fields, replace_file_extensions
from mu2e_base import Mu2eJobRunner, Mu2eFCLGenerator


class JobDefsRunner(Mu2eJobRunner, Mu2eFCLGenerator):
    """Job runner for processing jobdefs files."""
    
    def __init__(self):
        super().__init__("jobdefs_runner")
    
    def setup_argument_parser(self, description: str) -> argparse.ArgumentParser:
        """Setup argument parser with jobdefs-specific options."""
        parser = super().setup_argument_parser(description)
        parser.add_argument('--jobdefs', required=True, help='Path to the jobdefs_*.txt file')
        parser.add_argument('--ignore-jobdef-setup', action='store_true', help='Ignore the jobdef setup')
        return parser
    
    def run(self, args: argparse.Namespace) -> None:
        """Main execution logic."""
        # Extract job definition fields
        TARF, IND, INLOC, OUTLOC = parse_jobdef_fields(args.jobdefs)
        self.validate_jobdef(TARF)
        
        # Copy jobdef to local directory
        if not args.dry_run:
            self.run_command(f"mdh copy-file -e 3 -o -v -s disk -l local {TARF}")
        else:
            self.logger.info("[DRY RUN] Would run: mdh copy-file -e 3 -o -v -s disk -l local {TARF}")

        # Get input files
        if not args.dry_run:
            infiles = self.run_command(f"mu2ejobiodetail --jobdef {TARF} --index {IND} --inputs", capture=True)
        else:
            self.logger.info("[DRY RUN] Would run: mu2ejobiodetail --jobdef {TARF} --index {IND} --inputs")
            infiles = ""
        
        # Generate FCL
        if args.copy_input and infiles.strip():
            FCL = self.write_fcl(TARF, f"dir:{os.getcwd()}/indir", 'file', IND, dry_run=args.dry_run)
            if not args.dry_run:
                self.run_command(f"mdh copy-file -e 3 -o -v -s {INLOC} -l local {infiles}")
                self.run_command(f"mkdir indir; mv *.art indir/")
            else:
                self.logger.info("[DRY RUN] Would run: mdh copy-file -e 3 -o -v -s {INLOC} -l local {infiles}")
                self.logger.info("[DRY RUN] Would run: mkdir indir; mv *.art indir/")
        else:
            FCL = self.write_fcl(TARF, INLOC, 'root', IND, dry_run=args.dry_run)
        
        # Setup and run mu2e command
        if not args.dry_run:
            jobdef_simjob_setup = self.run_command(f"mu2ejobquery --setup {TARF}", capture=True)
            setup_cmd = f"source {jobdef_simjob_setup}"
            mu2e_cmd = f"mu2e -c {FCL} -n {args.nevts}"

            if not args.ignore_jobdef_setup:
                self.run_command(f"{setup_cmd} && {mu2e_cmd}")
            else:
                self.logger.info("Skipping jobdef setup")
                self.run_command(mu2e_cmd)
        else:
            self.logger.info("[DRY RUN] Would run: mu2ejobquery --setup {TARF}")
            self.logger.info("[DRY RUN] Would run: mu2e -c {FCL} -n {args.nevts}")
        
        # Write parents list
        parents = infiles.split()
        Path("parents_list.txt").write_text("\n".join(parents) + "\n")
        
        # Handle output files
        if not args.dry_run:
            self.push_data(OUTLOC)
            self.push_logs(FCL)
        else:
            self.logger.info("[DRY RUN] Would run: pushOutput output.txt")

        self.run_command("ls -ltra")
    
    def push_data(self, OUTLOC: str) -> None:
        """Handle data file management and submission."""
        out_fnames = glob.glob("*.art") + glob.glob("*.root")
        out_content = "".join(f"{OUTLOC} {fname} parents_list.txt\n" for fname in out_fnames)
        Path("output.txt").write_text(out_content)
        self.run_command("pushOutput output.txt")
    
    def push_logs(self, FCL: str) -> None:
        """Handle log file management and submission."""
        LOGFILE = replace_file_extensions(FCL, "log", "log")
        
        # Copy jobsub log if JSB_TMP is defined
        jsb_tmp = os.getenv("JSB_TMP")
        if jsb_tmp:
            jobsub_log = "JOBSUB_LOG_FILE"
            src = os.path.join(jsb_tmp, jobsub_log)
            self.logger.info(f"Copying jobsub log from {src} to {LOGFILE}")
            shutil.copy(src, LOGFILE)

        Path("log_output.txt").write_text(f"disk {LOGFILE} parents_list.txt\n")
        self.run_command("pushOutput log_output.txt")


def main():
    """Main entry point."""
    JobDefsRunner().main()


if __name__ == "__main__":
    main()
