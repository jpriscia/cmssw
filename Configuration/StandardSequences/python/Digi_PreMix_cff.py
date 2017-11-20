import FWCore.ParameterSet.Config as cms

# fragment to turn off ZS in Hcal:
#from Configuration.StandardSequences.Digi_cff import *
from Configuration.StandardSequences.DigiNZS_cff import *

# modifications to the digi sequences defined above (DigiNZS imports the central Digi_cff)

#simMuonCSCDigis.strips.doNoise = False
#simMuonCSCDigis.wires.doNoise = False
#simMuonDTDigis.onlyMuHits = True

simMuonRPCDigis.doBkgNoise = False


# Note: the other noise is turned of in the DigitizersNoNoise sequence defined in the MixingModule
# because the MM holds/controls all of the other digitizers.

# Turn off SR in Ecal
simEcalDigis.UseFullReadout = cms.bool(True)
# This is extra, since the configuration skips it anyway.  Belts and suspenders.
pdigi.remove(simEcalPreshowerDigis)
# remove HCAL TP sim - not needed, sometimes breaks
hcalDigiSequence.remove(simHcalTriggerPrimitiveDigis)
hcalDigiSequence.remove(simHcalTTPDigis)

# no need for the aliases for usual mixing
import FastSimulation.Configuration.DigiAliases_cff as _fastSim_DigiAliases_cff
_fastSim_DigiAliases_cff._enableDigiAliases = False
#else:
#no need for this hack running at Nebraska
##hack - our code is too fast at large scale - lets slow it down and idle for 15 seconds
#    cpuSpender=cms.EDAnalyzer("CPUSpender")
#    cpuSpender.secPerEvent=cms.untracked.int32(20)
#   
#    pdigi.insert(0,cpuSpender)
