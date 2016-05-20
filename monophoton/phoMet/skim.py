#!/usr/bin/env python

import sys
import os
import ROOT

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
from datasets import allsamples
import config

ROOT.gSystem.Load(config.libsimpletree)
ROOT.gSystem.AddIncludePath('-I' + config.dataformats + '/interface')

skim = 'zee' # 'phi' # sys.argv[1]
sname = sys.argv[1]

samples = [allsamples[sname]] # for sname in snames ] 

npvSource = ROOT.TFile.Open(basedir + '/data/npv.root')
npvweight = npvSource.Get('npvweight')

source = ROOT.TChain('events')
for sample in samples:
    sampleString = config.ntuplesDir + sample.book + '/' + sample.directory + '/simpletree_*.root'
    print sampleString
    source.Add(sampleString)

ROOT.gROOT.LoadMacro(thisdir + '/' + skim + '.cc+')

## names after last samples
outName = '/scratch5/ballen/hist/monophoton/phoMet/' + skim +'_' + sname + '.root'

if sample.data:
    getattr(ROOT, skim)(source, outName)
else:
    getattr(ROOT, skim)(source, outName, sample.crosssection / sample.sumw, npvweight)
