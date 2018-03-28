#!/usr/bin/env python

# Original Author:  Loic Quertenmont


import urllib
import string
import os,sys,time
import SUSYBSMAnalysis.HSCP.LaunchOnCondor as LaunchOnCondor
import glob
import commands
import json
import collections # kind of map

#script parameters #feel free to edit those
#JSON          = '23Sept2016ReReco_Collisions16.json'
JSON             = '2016F.json'
GlobalTag        = '80X_dataRun2_2016LegacyRepro_v4'
LOCALTIER        = 'T2_BE_UCL'
ISLOCAL          = False
JSONDIR          = 'JSONS'
LumisPerJob      = 10
EmptyFileSize    = 3262705
ResubmitOnTheFly = True     # resubmit in a safe way only jobs not currently running

DATASETS = []

DATASETMASKS  = [
   '/MET/',
   '/SingleMuon/',
#   '/DoubleMuon/'
]

datasetSuffixMask = [
#   'Run2016B-18Apr2017*/AOD',
#   'Run2016C-18Apr2017*/AOD',
#   'Run2016D-18Apr2017*/AOD',
#   'Run2016E-18Apr2017*/AOD',
   'Run2016F-18Apr2017*/AOD',
#   'Run2016G-18Apr2017*/AOD',
#   'Run2016H-18Apr2017*/AOD'
]

datasetSuffix_GlobalTag_Map = [
   ['', '']
]

runList = []

def initProxy():
      print "You are going to run on a sample over grid using either CRAB or the AAA protocol, it is therefore needed to initialize your grid certificate"
      os.system('mkdir -p ~/x509_user_proxy; voms-proxy-init --voms cms -valid 192:00 --out ~/x509_user_proxy/x509_proxy')#all must be done in the same command to avoid environement problems.  Note that the first sourcing is only needed in Louvain

def getRunIntervals ():
   toReturn = []
   for mask in DATASETMASKS:
      for suffix in datasetSuffixMask:
         datasets = os.popen('dasgoclient -query=\'dataset dataset=%s%s\'' % (mask, suffix)).read().split()
         for dataset in datasets:
            print 'dasgoclient -query=\'run dataset=%s\'' % dataset
            runs = os.popen('dasgoclient -query=\'run dataset=%s\'' % dataset).read().split()
            if len(runs) < 1:
               print 'No runs found!'
               continue
            toReturn.append([runs[0], runs[len(runs)-1], dataset])
   return toReturn

def splitJSON_forJobs (jsonPath):
   datasetsAndRuns = getRunIntervals()
   if os.path.isdir(JSONDIR): os.system('rm -rf %s && mkdir %s' % (JSONDIR, JSONDIR))
   elif not os.path.isdir(JSONDIR): os.system('mkdir %s' % JSONDIR)
   jsonFile = open(jsonPath, 'r')
   runList  = json.load(jsonFile).items()
   runList.sort()
   jsons = []
   for run in runList:
      correctDataset = ''
      fileList       = []
      for dataset in datasetsAndRuns:
         if int(dataset[0]) <= int(run[0]) and int(run[0]) <= int(dataset[1]):
            correctDataset = str(dataset[2])
            print 'dasgoclient -query=\'file run=%i dataset=%s\'' % (int(run[0]), correctDataset)
            fileList.append(os.popen('dasgoclient -query=\'file run=%i dataset=%s\'' % (int(run[0]), correctDataset)).read().split())
         if len(fileList) == len(DATASETMASKS): break
      print fileList

      for lumi in run[1]:
         interval = []
         for l in lumi:
            interval.append(int(l))
         for i, l in enumerate(range(interval[0], interval[1], LumisPerJob)):
            s = '{"%s": [[%i, %i]]}' % (str(run[0]), l, l+LumisPerJob-1 if l+LumisPerJob-1 <= interval[1] else interval[1])
            jsons.append([str(run[0]), 'Run_%s_block_%i.json' % (str(run[0]), i), fileList])
	    with open ('%s/%s' % (JSONDIR, jsons[len(jsons)-1][1]), 'w') as f:
               f.write(s)
            print s
   return jsons

if sys.argv[1]=='1':

   #get the list of sample to process from das and datasetmask query
   print("Initialize your grid proxy in case you need to access remote samples\n")
   initProxy()
   datasetList = splitJSON_forJobs (JSON)
   #get the list of samples to process from a local file
   #datasetList= open('DatasetList','r')
   JobName = "HSCPEdmProd"
   FarmDirectory = "FARM"
   if os.path.isdir(FarmDirectory): os.system('rm -rf %s' % FarmDirectory)
   LaunchOnCondor.SendCluster_Create(FarmDirectory, JobName)
   LaunchOnCondor.Jobs_Queue = '8nh'

   prefix = 'root://cms-xrd-global.cern.ch/' if not ISLOCAL else ''
   INDEX  = -1
   for sample in datasetList :
      LaunchOnCondor.Jobs_InitCmds = []
      if(not ISLOCAL):LaunchOnCondor.Jobs_InitCmds = ['export HOME=%s' % os.environ['HOME'], 'export X509_USER_PROXY=~/x509_user_proxy/x509_proxy; voms-proxy-init --noregen;']

      run           = sample[0]
      jsonName      = sample[1]
      fileLists     = sample[2]

      os.system("mkdir -p out/%s" % run);

      for m, mask in enumerate(DATASETMASKS):
         if len(fileLists)    == 0: continue
	 if len(fileLists[m]) == 0: continue
         INDEX += 1
         datasetBaseName = string.strip(mask, '/')
         print run, " ", datasetBaseName, " --> ", len(fileLists[m]), "files to process"

	 endFileName = '%s/out/%s/%s_HSCP_%i' % (os.getcwd(), run, datasetBaseName, INDEX)

         with open("HSCParticleProducer_Data_Template_cfg.py", "w") as f:
            f.write("import sys, os\n")
            f.write("import FWCore.ParameterSet.Config as cms\n")
            f.write("\n")
            f.write("isSignal        = False\n" )
            f.write("isBckg          = False\n" )
            f.write("isData          = True\n"  )
            f.write("isSkimmedSample = False\n" )
            f.write("GTAG = '%s'\n" % GlobalTag )
            f.write("OUTPUTFILE = 'out.root'\n" )
            f.write("LUMITOPROCESS = '" +  os.getcwd()+"/"+JSONDIR+"/"+jsonName+"'\n")
            f.write("\n")
            f.write("InputFileList = cms.untracked.vstring( *(\n")
            for fileToProcess in fileLists[m]:
               f.write("'"+prefix+fileToProcess+"',\n")
            f.write(") )\n")
            f.write("\n")
            f.write("#main EDM tuple cfg that depends on the above parameters\n")
            f.write("execfile( os.path.expandvars('${CMSSW_BASE}/src/SUSYBSMAnalysis/HSCP/test/MakeEDMtuples/HSCParticleProducer_cfg.py') )\n")
             
         LaunchOnCondor.Jobs_FinalCmds = ["mv out.root %s.root" % endFileName, "edmLumisInFiles.py %s.root --output=%s.json" % (endFileName, endFileName)]
         LaunchOnCondor.SendCluster_Push  (["CMSSW", ["HSCParticleProducer_Data_Template_cfg.py"] ])

   LaunchOnCondor.SendCluster_Submit()

if sys.argv[1]=='1r': #resubmit
   FarmDirectory = 'FARM'
   shellFiles = [x for x in os.listdir(FarmDirectory+'/inputs/') if x.find('.sh') > 0]

   FinalCmdFile = FarmDirectory+'/inputs/HscpEdmProd.cmd'

   toResubmit = []
   for shellFile in shellFiles:
      with open(FarmDirectory+'/inputs/'+shellFile, 'r') as f:
         lines = f.readlines()
      for line in lines:
         if 'mv out.root' in line:
            outputFile = string.strip(line.split(' ')[2])
            jsonFileEnd = string.replace(outputFile, '.root', '.json')
            if not os.path.isfile(outputFile) or int(os.stat(outputFile).st_size) <= EmptyFileSize:
               print 'File ', outputFile, 'either does not exist, or it is too small ...'
               toResubmit.append(shellFile)
               break
            elif os.path.isfile(outputFile) and os.path.isfile(jsonFileEnd):
               jsonFileBegin = ''
               with open(FarmDirectory+'/inputs/'+string.replace(shellFile, '.sh', '_step_0_cfg.py'), 'r') as F:
                  for i, l in enumerate (F):
                     if 'LUMITOPROCESS' in l:
                        jsonFileBegin = l.split('=')[1].strip('\'\n ')
                        break
               with open(jsonFileEnd, 'r') as f1, open(jsonFileBegin, 'r') as f2:
                  l1 = f1.readline().strip()
                  l2 = f2.readline().strip()
                  if l1 != l2:
                     toResubmit.append(shellFile)
                     print 'File', outputFile, 'does not have correct Lumis ...'
                     break

   if ResubmitOnTheFly: #remove jobs already running
      runningJobs = [os.path.basename(x.strip()) for x in os.popen('squeue -u ' + os.environ['USER'] + ' -o "%o"').read().split() if x.find('.sh') > 0]
      toResubmit = [x for x in toResubmit if x not in runningJobs]
   print len(toResubmit), 'jobs to resubmit ...'
   with open(FinalCmdFile, 'w') as f:
      f.write('#!/bin/bash\n\n')
      for shellFile in toResubmit:
         f.write('sbatch --partition=Def --qos=normal --wckey=cms ' + FarmDirectory + '/inputs/' + shellFile + '\n')

   initProxy()
   os.system('sh ' + FinalCmdFile)

if sys.argv[1]=='2':
   FarmDirectory = "MERGE"
   LaunchOnCondor.SendCluster_Create(FarmDirectory, "HSCPEdmMerge")
   LaunchOnCondor.Jobs_Queue = '8nh'

   jsonFile = open(JSON, 'r')
   runList  = json.load(jsonFile).items()
   runList.sort()
   runs = [int(x) for x[0] in runList]
   for RUN in runs:
        if not os.path.isdir('%s/out/Run2016_%i' % (os.getcwd(), RUN)): continue
        LaunchOnCondor.Jobs_InitCmds   = ['export HOME=%s' % os.environ['HOME']]
        LaunchOnCondor.Jobs_FinalCmds  = ["edmLumisInFiles.py Run2016_%i.root --output=%s/out/Run2016_%i.json" % (RUN, os.getcwd(), RUN)]
        LaunchOnCondor.Jobs_FinalCmds += ["mv Run2016_%i.root %s/out/Run2016_%i.root" % (RUN, os.getcwd(), RUN)]
	LaunchOnCondor.ListToFile(LaunchOnCondor.GetListOfFiles('"file:','%s/out/%i/*_HSCP_*.root' % (os.getcwd(), RUN),'",'), FarmDirectory + "InputFile.txt")
	LaunchOnCondor.SendCMSJobs(FarmDirectory, "HSCPEdmMerge_%i"%RUN, "Merge_cfg.py", FarmDirectory + "InputFile.txt", 1, ['XXX_SAVEPATH_XXX','Run2016_%i.root' % RUN])
        os.system("rm " +  FarmDirectory + "InputFile.txt")

