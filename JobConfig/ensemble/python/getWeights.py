#! /usr/bin/env python
from string import Template
import argparse
import sys
import random
import os
import glob
import ROOT
import subprocess

def main(args):

    # open file list from the filelists directory
    ffns = open(os.path.join(args.files))
    totalSum = 0
    selectedSum = 0
    # loop over files in list
    for line in ffns:
          
      # find a given filename
      fn = line.strip()
      
     
      # use ROOT to get the events in that file
      fin = ROOT.TFile(fn)
      te = fin.Get("Events")

      # determine total number of events generated
      t = fin.Get("SubRuns")
      
      
      # get sum of weights
      bl = t.GetListOfBranches()
      bn = ""
      tag = "filter"
      
      if args.tag == "filter":
        for i in range(bl.GetEntries()):
            if bl[i].GetName().startswith("mu2e::SumOfWeights_PionFilter_total"):
                bn = bl[i].GetName()
        for i in range(t.GetEntries()):
            t.GetEntry(i)
            
            totalSum +=getattr(t,bn).product().sum()
        
        
        for i in range(bl.GetEntries()):
            if bl[i].GetName().startswith("mu2e::SumOfWeights_PionFilter_selected"):
                bn = bl[i].GetName()
        for i in range(t.GetEntries()):
            t.GetEntry(i)
            
            selectedSum +=getattr(t,bn).product().sum()
            
      if args.tag == "sampler":
        for i in range(bl.GetEntries()):
            if bl[i].GetName().startswith("mu2e::SumOfWeights_StopSelection_total_PhysicalPionStops"):
                bn = bl[i].GetName()
        for i in range(t.GetEntries()):
            t.GetEntry(i)
            
            totalSum +=getattr(t,bn).product().sum()
        
        
        for i in range(bl.GetEntries()):
            if bl[i].GetName().startswith("mu2e::SumOfWeights_StopSelection_sampled_PhysicalPionStops"):
                bn = bl[i].GetName()
        for i in range(t.GetEntries()):
            t.GetEntry(i)
            
            selectedSum +=getattr(t,bn).product().sum()
    if(args.weight == "selected"):
      print(selectedSum)
    if(args.weight == "total"):
      print(totalSum)
              
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="verbose")
    parser.add_argument("--weight", help="total or selected")
    parser.add_argument("--files", help="filelist")
    parser.add_argument("--tag", help="either filter or sampler - relates to file name")
    args = parser.parse_args()
    (args) = parser.parse_args()
    main(args)
