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
JSON          = '23Sept2016ReReco_Collisions16.json'
#JSON          = 'test.json'
GlobalTag     = '80X_dataRun2_2016LegacyRepro_v4'
LOCALTIER     = 'T2_BE_UCL'
ISLOCAL       = False
JSONDIR       = 'JSONS'
LumisPerJob   = 15

DATASETMASKS  = [
   '/MET/',
   '/SingleMuon/',
#   '/DoubleMuon/'
]

datasetSuffix = [
   'Run2016B-18Apr2017*/AOD',
   'Run2016C-18Apr2017*/AOD',
   'Run2016D-18Apr2017*/AOD',
   'Run2016E-18Apr2017*/AOD',
   'Run2016F-18Apr2017*/AOD',
   'Run2016G-18Apr2017*/AOD',
   'Run2016H-18Apr2017*/AOD'
]

datasetSuffix_GlobalTag_Map = [
   ['', '']
]

def initProxy():
      print "You are going to run on a sample over grid using either CRAB or the AAA protocol, it is therefore needed to initialize your grid certificate"
      os.system('mkdir -p ~/x509_user_proxy; voms-proxy-init --voms cms -valid 192:00 --out ~/x509_user_proxy/x509_proxy')#all must be done in the same command to avoid environement problems.  Note that the first sourcing is only needed in Louvain

def getRunIntervals ():
   toReturn = []
   for suffix in datasetSuffix:
      dataset = DATASETMASKS[0]+suffix
      print 'dasgoclient -query=\'run dataset=%s\'' % dataset
      runs    = os.popen('dasgoclient -query=\'run dataset=%s\'' % dataset).read().split()
      if len(runs) < 1:
         print 'No runs found!'
         continue
      toReturn.append([runs[0], runs[len(runs)-1], suffix])
   return toReturn

def splitJSON_forJobs (jsonPath):
   datasetsAndRuns = getRunIntervals()
   if os.path.isdir(JSONDIR): os.system('rm -rf %s' % JSONDIR)
   if not os.path.isdir(JSONDIR): os.system('mkdir %s' % JSONDIR)
   jsonFile = open(jsonPath, 'r')
   runList  = json.load(jsonFile).items()
   runList.sort()
   jsons = []
   for run in runList:
      correctDataset = ''
      fileList       = []
      for dataset in datasetsAndRuns:
         if int(run[0]) >= int(dataset[0]) and int(run[0]) <= int(dataset[1]):
            correctDataset = str(dataset[2])
            for mask in DATASETMASKS:
               print 'dasgoclient -query=\'file run=%i dataset=%s%s\'' % (int(run[0]), mask, correctDataset)
               fileList.append(os.popen('dasgoclient -query=\'file run=%i dataset=%s%s\'' % (int(run[0]), mask, correctDataset)).read().split())
            print fileList
            break

      for lumi in run[1]:
         interval = []
         for l in lumi:
            interval.append(int(l))
         for i, l in enumerate(range(interval[0], interval[1], LumisPerJob)):
            s = '{%s: [%i, %i]}' % (str(run[0]), l, l+LumisPerJob-1 if l+LumisPerJob-1 <= interval[1] else interval[1])
            jsons.append([str(run[0]), 'Run_%s_block_%i.json' % (str(run[0]), i), correctDataset, fileList])
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
   LaunchOnCondor.SendCluster_Create(FarmDirectory, JobName)
   LaunchOnCondor.Jobs_Queue = '8nh'

   prefix = 'root://cms-xrd-global.cern.ch//' if not ISLOCAL else ''
   INDEX  = -1
   for sample in datasetList :
      LaunchOnCondor.Jobs_InitCmds = []
      if(not ISLOCAL):LaunchOnCondor.Jobs_InitCmds = ['export HOME=%s' % os.environ['HOME'], 'export X509_USER_PROXY=~/x509_user_proxy/x509_proxy; voms-proxy-init --noregen;']

      run           = sample[0]
      jsonName      = sample[1]
      datasetSuffix = sample[2]
      fileLists     = sample[3]

      os.system("mkdir -p out/%s" % run);

      for m, mask in enumerate(DATASETMASKS):
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
            f.write("InputFileList = cms.untracked.vstring(\n")
            for fileToProcess in fileLists[m]:
               f.write("'"+prefix+fileToProcess+"',\n")
            f.write(")\n")
            f.write("\n")
            f.write("#main EDM tuple cfg that depends on the above parameters\n")
            f.write("execfile( os.path.expandvars('${CMSSW_BASE}/src/SUSYBSMAnalysis/HSCP/test/MakeEDMtuples/HSCParticleProducer_cfg.py') )\n")
             
         LaunchOnCondor.Jobs_FinalCmds = ["mv out.root %s.root" % endFileName, "edmLumisInFiles.py %s.root --output=%s.json" % (endFileName, endFileName)]
         LaunchOnCondor.SendCluster_Push  (["CMSSW", ["HSCParticleProducer_Data_Template_cfg.py"] ])

#   LaunchOnCondor.SendCluster_Submit()



if sys.argv[1]=='2':
   FarmDirectory = "MERGE"
   LaunchOnCondor.SendCluster_Create(FarmDirectory, "HSCPEdmMerge")
   LaunchOnCondor.Jobs_Queue = '8nh'
   for RUN in goodLumis:
        LaunchOnCondor.Jobs_InitCmds   = ['export HOME=%s' % os.environ['HOME']]
        LaunchOnCondor.Jobs_FinalCmds  = ["edmLumisInFiles.py Run2016_%i.root --output=%s/out/Run2016_%i.json" % (RUN, os.getcwd(), RUN)]
        LaunchOnCondor.Jobs_FinalCmds += ["mv Run2016_%i.root %s/out/Run2016_%i.root" % (RUN, os.getcwd(), RUN)]
	LaunchOnCondor.ListToFile(LaunchOnCondor.GetListOfFiles('"file:','%s/out/%i/*_HSCP_*.root' % (os.getcwd(), RUN),'",'), FarmDirectory + "InputFile.txt")
	LaunchOnCondor.SendCMSJobs(FarmDirectory, "HSCPEdmMerge_%i"%RUN, "Merge_cfg.py", FarmDirectory + "InputFile.txt", 1, ['XXX_SAVEPATH_XXX','Run2016_%i.root' % RUN])
        os.system("rm " +  FarmDirectory + "InputFile.txt")

if sys.argv[1]=='3':
   stuff = getRunIntervals()
   for s in stuff:
      print s


#
#def filesFromDataset(dataset):
#   ISLOCAL=False
#   command_out = commands.getstatusoutput('das_client --limit=0 --query "site dataset='+dataset+' | grep site.name,site.dataset_fraction"')
#   for site in command_out[1].split('\n'):
#      if(LOCALTIER in site and '100.00%' in site): 
#         ISLOCAL=True
#         break
#
#   Files = {}
#   command_out = commands.getstatusoutput('das_client --limit=0 --query "file dataset='+dataset+'"')
#   for f in command_out[1].split():
##      run = GetRunFromFile(f)
#      if(not IsGoodRun(run)):continue
#      if(run not in Files):  Files[run] = [] #make sure that we have a collection for this run
#      
#      if(ISLOCAL and LOCALTIER=='T2_CH_CERN'): Files[run] += ["root://eoscms//eos/cms"+f]
#      elif(ISLOCAL):                           Files[run] += [f]
#      else       :                             Files[run] += ['root://cms-xrd-global.cern.ch/' + f]
#   return Files
  


