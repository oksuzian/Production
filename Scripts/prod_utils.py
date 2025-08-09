import subprocess
import sys
import logging
import json
import os
from pathlib import Path

def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="[%(levelname)s] %(message)s"
    )

def run(cmd, capture=False, shell=False):
    """
    Run a shell command. If capture=True, return stdout. If shell=True, cmd is a string.
    """
    print(f"Running: {cmd}")
    try:
        res = subprocess.run(cmd, shell=shell, capture_output=capture, text=True, check=True)
        return res.stdout.strip() if capture else None
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        sys.exit(1)

def extract_dataset_fields(ds):
    """
    Extract fields from a Mu2e dataset name.
    Example: dts.mu2e.RPCInternalPhysical.MDC2020az.art -> ("dts", "mu2e", "RPCInternalPhysical", "MDC2020az", "art")
    """
    parts = ds.split('.')
    if len(parts) < 5:
        sys.exit(f"Invalid dataset: {ds}")
    return tuple(parts)

def locate_parfile(parfile):
    """
    Locate the parfile using samweb.
    Returns the full path to the parfile.
    """
    loc = run(f"samweb locate-file {parfile}", capture=True, shell=True)
    if not loc:
        sys.exit(f"Parfile not found: {parfile}")
    return (loc[7:] if loc.startswith('dcache:') else loc) + '/' + parfile

def write_fcl(jobdef, inloc='tape', proto='root', index=0, target=None):
    """
    Generate and write an FCL file using mu2ejobfcl.
    """
    # Extract fcl filename from jobdef
    fcl = jobdef.replace('.0.tar', f'.{index}.fcl')  # cnf.mu2e.RPCInternalPhysical.MDC2020az.{index}.fcl
    
    cmd = f"mu2ejobfcl --jobdef '{jobdef}' --default-proto {proto} --default-loc {inloc}"
    if target:
        cmd += f" --target {target}"
    else:
        cmd += f" --index {index}"
    
    result = run(cmd, capture=True, shell=True)
    print(f"Wrote {fcl}")
    with open(fcl, 'w') as f:
        f.write(result + '\n')
    
    # Print the FCL content
    print(f"\n--- {fcl} content ---")
    print(result + '\n')

    return fcl

def get_def_counts(dataset, include_empty=False):
    """
    Get file count and event count for a dataset.
    """
    # Count files
    if include_empty:
        query = f"defname: {dataset}"
    else:
        query = f"defname: {dataset} and event_count>0"
    
    nfiles = int(run(f"samweb count-files '{query}'", capture=True, shell=True))
    
    # Count events
    result = run(f"samweb list-files --summary 'dh.dataset={dataset}'", capture=True, shell=True)
    nevts = 0
    for line in result.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "Event":
            nevts = int(parts[2])
            break
    
    if nfiles == 0:
        sys.exit(f"No files found in dataset {dataset}")
    return nfiles, nevts

def calculate_merge_factor(fields):
    """
    Calculate merge factor based on dataset counts and requested merge_events.
    """
    nfiles, nevts = get_def_counts(fields['input_data'])
    if nfiles == 0: return 1
    return (nevts // nfiles) // fields['merge_events'] + 1

def find_json_entry(json_path, desc, dsconf, index):
    """
    Find a matching JSON entry from configuration file.
    
    Args:
        json_path: Path to JSON file
        desc: Description to match
        dsconf: Dataset configuration to match  
        index: Index to return (if not None)
        
    Returns:
        Matching configuration dictionary
    """
    json_text = json_path.read_text()
    configs = json.loads(json_text)
    if 'pbeam' in json_text:
        from mixing_utils import expand_mix_config
        configs = expand_mix_config(json_path)
    if index is not None:
        try: return configs[index]
        except IndexError: sys.exit(f"Index {index} out of range.")
    matches = [e for e in configs if e.get('desc') == desc and e.get('dsconf') == dsconf]
    if len(matches) != 1:
        sys.exit(f"Expected 1 match for desc={desc}, dsconf={dsconf}; found {len(matches)}.")
    return matches[0]

def write_fcl_template(base, overrides):
    """
    Write FCL template file with base include and overrides.
    
    Args:
        base: Base FCL file to include
        overrides: Dictionary of FCL overrides
    """
    with open('template.fcl', 'w') as f:
        print(f'#include "{base}"', file=f)
        for key, val in overrides.items():
            if key == '#include':
                includes = val if isinstance(val, list) else [val]
                for inc in includes:
                    print(f'#include "{inc}"', file=f)
            else:
                print(f"{key}: {json.dumps(val)}", file=f)

def push_output(file, location='disk'):
    """
    Push a file to SAM if it doesn't already exist there.
    """
    with open('outputs.txt', 'w') as f:
        f.write(f"{location} {file} none\n")
    
    # Check if file exists on SAM without exiting on failure
    try:
        proc = subprocess.run(f"samweb locate-file {file}", shell=True, capture_output=True, text=True, check=False)
        exists = proc.returncode == 0 and bool(proc.stdout.strip())
    except Exception:
        exists = False
    
    if not exists:
        # File doesn't exist on SAM, push it
        print(f"Pushing {file} to SAM...")
        run('pushOutput outputs.txt', shell=True)
    else:
        # File exists on SAM, don't push
        print(f"File {file} already exists on SAM, skipping push")

def parse_jobdef_fields(jobdefs_file, index=None):
    """
    Extract job definition fields from a jobdefs file and index.
    
    Args:
        jobdefs_file: Path to the jobdefs file
        index: Index of the job definition to extract (optional, will extract from fname env var if not provided)
        
    Returns:
        tuple: (tarfile, job_index, inloc, outloc)
    """

    #check token before proceeding
    try:
        run(f"httokendecode -H", shell=True)
    except SystemExit:
        print("Warning: Token validation failed. Please check your token.")
    run("pwd", shell=True)
    run("ls -ltr", shell=True)

    # Extract index from fname environment variable if not provided
    if index is None:
        fname = os.getenv("fname")
        if not fname:
            print("Error: fname environment variable is not set.")
            sys.exit(1)
        try:
            index = int(fname.split('.')[4].lstrip('0') or '0')
        except (IndexError, ValueError) as e:
            print("Error: Unable to extract index from filename.")
            sys.exit(1)

    if not os.path.exists(jobdefs_file):
        print(f"Error: Jobdefs file {jobdefs_file} does not exist.")
        sys.exit(1)
    
    jobdefs_list = make_jobdefs_list(Path(jobdefs_file))
    
    if len(jobdefs_list) < index:
        print(f"Error: Expected at least {index} job definitions, but got only {len(jobdefs_list)}")
        sys.exit(1)
    
    # Get the index-th job definition (adjusting for Python's 0-index).
    jobdef = jobdefs_list[index]
    print(f"The {index}th job definition is: {jobdef}")

    # Split the job definition into fields (parfile job_index inloc outloc).
    fields = jobdef.split()
    if len(fields) != 4:
        print(f"Error: Expected 4 fields (parfile job_index inloc outloc) in the job definition, but got: {jobdef}")
        sys.exit(1)

    # Return the fields: (tarfile, job_index, inloc, outloc)
    print(f"IND={fields[1]} TARF={fields[0]} INLOC={fields[2]} OUTLOC={fields[3]}")
    return fields[0], int(fields[1]), fields[2], fields[3]

def make_jobdefs_list(input_file):
    """
    Create a list of individual job definitions from a jobdef map file.
    
    Args:
        input_file: Path to jobdef map file
        
    Returns:
        List of individual job definition strings: parfile job_index inloc outloc
    """
    if not input_file.exists():
        sys.exit(f"Input file not found: {input_file}")
    
    jobdefs_list = []
    for line in input_file.read_text().splitlines():
        parfile, njobs, inloc, outloc = line.strip().split()
        for i in range(int(njobs)):
            jobdefs_list.append(f"{parfile} {i} {inloc} {outloc}")
    print(f"Generated the list of {len(jobdefs_list)} jobdefs from {input_file}")
    return jobdefs_list

def replace_file_extensions(input_str, first_field, last_field):
    """
    Replace the first and last fields in a dot-separated string.
    
    Args:
        input_str: Input string with dot-separated fields
        first_field: New value for the first field
        last_field: New value for the last field
        
    Returns:
        String with first and last fields replaced
    """
    fields = input_str.split('.')
    fields[0] = first_field
    fields[-1] = last_field
    return '.'.join(fields)

def create_index_definition(output_index_dataset, job_count, input_index_dataset="etc.mu2e.index.000.txt"):
    """
    Create a SAM index definition for job processing.
    
    Args:
        output_index_dataset: output index definition name
        job_count: Number of jobs to process
        input_index_dataset: input index definition name
    """
    idx_format = f"{job_count:07d}"
    try:
        run(f"samweb delete-definition idx_{output_index_dataset}", shell=True)
    except SystemExit:
        pass  # Definition doesn't exist, which is fine
    run(f"samweb create-definition idx_{output_index_dataset} 'dh.dataset {input_index_dataset} and dh.sequencer < {idx_format}'", shell=True)
    run(f"samweb describe-definition idx_{output_index_dataset}", shell=True)