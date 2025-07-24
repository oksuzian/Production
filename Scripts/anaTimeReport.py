#!/usr/bin/env python3
"""
Summarize Mu2e log performance metrics per dataset (no pandas).
Reads a list of datasets, gathers CPU/Real time, memory, and SAM summary
numbers via samDatasetsSummary.sh, and writes JSON output.
"""
import sys, subprocess, argparse, re, json, shutil, os
from pathlib import Path

# Regex patterns
TIMEREPORT_REGEX = re.compile(r"TimeReport CPU = ([0-9]*\.?[0-9]+) Real = ([0-9]*\.?[0-9]+)")
MEMREPORT_REGEX = re.compile(r"MemReport\s+VmPeak\s*=\s*([0-9]*\.?[0-9]+)\s+VmHWM\s*=\s*([0-9]*\.?[0-9]+)")

SECONDS_PER_HOUR = 3600.0
MB_PER_GB = 1024.0

# ------------------------- helper functions -----------------------------

def run_cmd(cmd:list, **kwargs):
    """Run command, capture output, ignore non-zero exit unless check=True provided."""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)


def get_sam_summary(dataset:str):
    """Return dict with triggered, generated, files, size_bytes using samDatasetsSummary.sh."""
    summary = {}
    script = "samDatasetsSummary.sh"
    if not shutil.which(script):
        print("[ERROR] samDatasetsSummary.sh not found in PATH", file=sys.stderr)
        return summary
    proc = run_cmd([script, dataset], check=False)
    for line in proc.stdout.splitlines():
        if m := re.match(r"Triggered:\s*(\d+)", line):
            summary["Triggered"] = int(m.group(1)); continue
        if m := re.match(r"Generated:\s*(\d+)", line):
            summary["Generated"] = int(m.group(1)); continue
        if m := re.match(r"Files:\s*(\d+)", line):
            summary["Files"] = int(m.group(1)); continue
        if m := re.match(r"Size:\s*(\d+)", line):
            summary["Size [GB]"] = round(int(m.group(1))/1e9,1)
    return summary


def mu2e_file_list(dataset:str):
    """Return list of log file paths using mu2eDatasetFileList (switch family to log)."""
    parts = dataset.split('.')
    parts[0]  = 'log'   # family
    parts[-1] = 'log'   # extension
    dataset = '.'.join(parts)
    proc = run_cmd(["mu2eDatasetFileList", dataset], check=False)
    if proc.returncode != 0:
        print(f"[WARN] mu2eDatasetFileList failed for {dataset}: {proc.stderr}", file=sys.stderr)
        return []
    return [l.strip() for l in proc.stdout.splitlines() if l.startswith('/')]

def parse_log(fp:Path):
    """Extract CPU (h), Real (h), VmPeak (MB), VmHWM (MB) from log file."""
    cpu = real = vmp = vmh = None
    try:
        with open(fp, errors='ignore') as f:
            for line in f:
                if (m := TIMEREPORT_REGEX.search(line)):
                    cpu = float(m.group(1))/SECONDS_PER_HOUR
                    real = float(m.group(2))/SECONDS_PER_HOUR
                elif (m := MEMREPORT_REGEX.search(line)):
                    vmp = float(m.group(1))
                    vmh = float(m.group(2))
    except Exception as e:
        print(f"[WARN] cannot read {fp}: {e}", file=sys.stderr)
    return cpu, real, vmp, vmh

# ------------------------- main -----------------------------

def main():
    ap = argparse.ArgumentParser(description="Summarize Mu2e logs (no pandas)")
    ap.add_argument('-l','--list-file', required=True, help='File containing dataset names')
    ap.add_argument('-J','--json-output', default='summary.json', help='Output JSON file')
    ap.add_argument('-n','--max-logs', type=int, default=1, help='Max logs to parse per dataset (default 1)')
    args = ap.parse_args()

    try:
        datasets = [ln.strip() for ln in open(args.list_file) if ln.strip() and not ln.startswith('#')]
    except IOError as e:
        print(f"[ERROR] cannot read {args.list_file}: {e}", file=sys.stderr)
        sys.exit(1)

    results = []
    for ds in datasets:
        print(f"Processing {ds}", file=sys.stderr)
        sam = get_sam_summary(ds)
        files = mu2e_file_list(ds)[:args.max_logs]
        if not files:
            print(f"[WARN] no log files found for {ds}", file=sys.stderr)
        acc = { 'CPU':[], 'Real':[], 'VmPeak':[], 'VmHWM':[] }
        for fp in files:
            cpu, real, vmp, vmh = parse_log(fp)
            if cpu is not None: acc['CPU'].append(cpu)
            if real is not None: acc['Real'].append(real)
            if vmp is not None: acc['VmPeak'].append(vmp)
            if vmh is not None: acc['VmHWM'].append(vmh)
        # compute means and maxes rounded to 2 decimals
        def mean(lst): return round(sum(lst)/len(lst),2) if lst else None
        def maxv(lst): return round(max(lst),2) if lst else None

        record = {
            'dataset': ds,
            'CPU [h]': mean(acc['CPU']),
            'CPU_max [h]': maxv(acc['CPU']),
            'Real [h]': mean(acc['Real']),
            'Real_max [h]': maxv(acc['Real']),
            'VmPeak [GB]': round(mean(acc['VmPeak'])/MB_PER_GB,2) if acc['VmPeak'] else None,
            'VmPeak_max [GB]': round(maxv(acc['VmPeak'])/MB_PER_GB,2) if acc['VmPeak'] else None,
            'VmHWM [GB]': round(mean(acc['VmHWM'])/MB_PER_GB,2) if acc['VmHWM'] else None,
            'VmHWM_max [GB]': round(maxv(acc['VmHWM'])/MB_PER_GB,2) if acc['VmHWM'] else None,
        }
        record.update(sam)  # merge SAM summary fields
        results.append(record)

    # pretty print to console
    for r in results:
        print(json.dumps(r, indent=2))

    # write JSON
    with open(args.json_output,'w') as f:
        json.dump(results, f, indent=2)
    print(f"[INFO] wrote {args.json_output}", file=sys.stderr)

if __name__ == '__main__':
    main() 