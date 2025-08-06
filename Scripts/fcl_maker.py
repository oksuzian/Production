#!/usr/bin/env python3
import argparse
import os
from prod_utils import *

def main():
    p = argparse.ArgumentParser(description='Generate FCL from dataset name or target file')
    p.add_argument('--dataset', help='Dataset name (art: dts.mu2e.RPCInternalPhysical.MDC2020az.art or jobdef: cnf.mu2e.ExtractedCRY.MDC2020av.tar)')
    p.add_argument('--proto', default='root')
    p.add_argument('--loc', default='tape')
    p.add_argument('--index', type=int, default=0)
    p.add_argument('--target', help='Target file (e.g., dts.mu2e.RPCInternalPhysical.MDC2020az.001202_00000296.art)')
    args = p.parse_args()

    # Require either dataset or target
    if not args.dataset and not args.target:
        p.error("Either --dataset or --target must be provided")

    # Use dataset if provided, otherwise use target
    source = args.dataset or args.target
    fields = extract_dataset_fields(source)
    jobdef = f"cnf.{fields[1]}.{fields[2]}.{fields[3]}.0.tar"  # owner, desc, dsconf
    # Copy jobdef to local directory
    run(f"mdh copy-file -e 3 -o -v -s disk -l local {jobdef}", shell=True)    
    write_fcl(jobdef, args.loc, args.proto, args.index, args.target)
    os.remove(jobdef) if os.path.exists(jobdef) else None

if __name__ == '__main__':
    main()