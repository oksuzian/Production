#!/usr/bin/env python3
"""
json2jobdef.py: JSON to jobdef generator.

Usage:
    json2jobdef.py --json config.json (--desc DESC --dsconf DSCONF | --index IDX) [--pushout] [--jobs-map FILE] [--verbose]
"""
import argparse
import json
import os
import sys
from pathlib import Path
from prod_utils import *
from mixing_utils import *

def build_jobdef(config, job_args):
    cmd = [
        'mu2ejobdef', '--verbose',
        '--setup', config['simjob_setup'],
        '--dsconf', config['dsconf'],
        '--desc', config['desc'],
        '--dsowner', config['owner'],
        '--embed', 'template.fcl'
    ]
    if config.get('run'):
        cmd += ['--run-number', str(config['run'])]
    if config.get('events'):
        cmd += ['--events-per-job', str(config['events'])]
    if config.get('extra_opts'):
        cmd += config['extra_opts'].split()
    cmd += job_args
    
    parfile = Path(get_parfile_name(config['owner'], config['desc'], config['dsconf']))
    if parfile.exists(): parfile.unlink()
    run(' '.join(cmd), shell=True)

def save_jobdef(config):
    """
    Save job information to a dsconf-specific file with unique entries.
    """
    parfile_name = get_parfile_name(config['owner'], config['desc'], config['dsconf'])
    
    # Query job count if njobs is -1
    njobs = config['njobs']
    if njobs == -1:
        njobs = int(run(f"mu2ejobquery --njobs '{parfile_name}'", capture=True, shell=True))
        print(f"Queried job count: {njobs}")
    
    new_entry = f"{parfile_name} {njobs} {config['inloc']} {config['outloc']}\n"
    dsconf_file = Path(f"jobdefs_{config['dsconf'].split('_')[0]}.txt")
    
    if dsconf_file.exists() and parfile_name in dsconf_file.read_text():
        print(f"Entry already exists in {dsconf_file}")
        return
    
    with open(dsconf_file, 'a') as f:
        f.write(new_entry)
    print(f"Added {new_entry} to {dsconf_file}")

def main():
    p = argparse.ArgumentParser(description='Generate Mu2e job definitions from JSON configuration')
    p.add_argument('--json', required=True, help='Input JSON file')
    p.add_argument('--desc', help='Dataset descriptor')
    p.add_argument('--dsconf', help='Dataset configuration')
    p.add_argument('--index', type=int, help='Entry index in JSON list')
    p.add_argument('--pushout', action='store_true', help='Enable SAM pushOutput')
    p.add_argument('--verbose', action='store_true', help='Verbose logging')
    args = p.parse_args()

    setup_logging(args.verbose)
    
    config = find_json_entry(Path(args.json), args.desc, args.dsconf, args.index)
    print(json.dumps(config, indent=2, sort_keys=True))
    
    for req in ('simjob_setup', 'fcl', 'dsconf', 'outloc'):
        if not config.get(req):
            sys.exit(f"Missing required field: {req}")
    config['owner'] = config.get('owner', os.getenv('USER', 'mu2e').replace('mu2epro', 'mu2e'))
    config['inloc'] = config.get('inloc', 'tape')
    config['njobs'] = config.get('njobs', -1)
    
    write_fcl_template(config['fcl'], config.get('fcl_overrides', {}))
    if config.get('input_data'):
        result = run(f"samweb list-files 'dh.dataset={config['input_data']} and event_count>0'", capture=True, shell=True)
        with open('inputs.txt', 'w') as f:
            f.write(result)
    
    job_args = []
    if 'resampler_name' in config:
        nfiles, nevts = get_def_counts(config['input_data'])
        skip = nevts // nfiles
        with open('template.fcl', 'a') as f:
            f.write(f"physics.filters.{config['resampler_name']}.mu2e.MaxEventsToSkip: {skip}\n")
        job_args = ['--auxinput', f"{config.get('merge_factor',1)}:physics.filters.{config['resampler_name']}.fileNames:inputs.txt"]
    elif 'merge_factor' in config:
        job_args = ['--inputs','inputs.txt','--merge-factor', str(config['merge_factor'])]
    elif 'pbeam' in config:
        merge_factor = calculate_merge_factor(config)
        job_args = ['--inputs','inputs.txt','--merge-factor', str(merge_factor)]
        job_args += build_pileup_args(config)
    
    build_jobdef(config, job_args)
    parfile_name = get_parfile_name(config['owner'], config['desc'], config['dsconf'])
    if args.pushout:
        push_output(parfile_name)
    save_jobdef(config)
    write_fcl(parfile_name, config.get('inloc', 'tape'), 'root')
    print(f"Generated: {parfile_name}")
    
    # Clean up temporary files
    temp_files = ['inputs.txt', 'template.fcl', 'mubeamCat.txt', 'elebeamCat.txt', 'neutralsCat.txt', 'mustopCat.txt']
    for temp_file in temp_files:
        if Path(temp_file).exists():
            Path(temp_file).unlink()
            print(f"Cleaned up: {temp_file}")

if __name__ == '__main__':
    main()
