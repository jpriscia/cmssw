import FWCore.ParameterSet.Config as cms

process = cms.Process("ICALIB")
process.MessageLogger = cms.Service("MessageLogger",
                                    cout = cms.untracked.PSet(threshold = cms.untracked.string('INFO')),
                                    destinations = cms.untracked.vstring('cout')
                                    )

process.source = cms.Source("EmptyIOVSource",
                            firstValue = cms.uint64(1),
                            lastValue = cms.uint64(1),
                            timetype = cms.string('runnumber'),
                            interval = cms.uint64(1)
                            )

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(1)
)


process.noiseEarly2018 = cms.ESSource("PoolDBESSource",
        DBParameters = cms.PSet(
            messageLevel = cms.untracked.int32(0),
            authenticationPath = cms.untracked.string('')
        ),
        toGet = cms.VPSet(cms.PSet(
            record = cms.string("SiStripNoisesRcd"),
            label = cms.untracked.string("Early2018"),
            tag = cms.string("SiStripNoise_v2_prompt")
        )),
        connect = cms.string("sqlite_file:noise2018begin_test1.db")
    )


process.noiseLate2018 = cms.ESSource("PoolDBESSource",
        ###
        DBParameters = cms.PSet(
            messageLevel = cms.untracked.int32(0),
            authenticationPath = cms.untracked.string('')
        ),
        toGet = cms.VPSet(cms.PSet(
            record = cms.string("SiStripNoisesRcd"),
            label = cms.untracked.string("Late2018"),
            tag = cms.string("SiStripNoise_v2_prompt")
        )),
        connect = cms.string("sqlite_file:noise2018end_test1.db")
    )



process.PoolDBOutputService = cms.Service("PoolDBOutputService",
                                          BlobStreamerName = cms.untracked.string('TBufferBlobStreamingService'),
                                          DBParameters = cms.PSet(authenticationPath = cms.untracked.string('/afs/cern.ch/cms/DB/conddb')),
                                          timetype = cms.untracked.string('runnumber'),
                                          connect = cms.string('sqlite_file:dbfile_output.db'),
                                          toPut = cms.VPSet(cms.PSet(record = cms.string('SiStripNoisesRcd'),
                                                                     tag = cms.string('SiStripNoise_test')
                                                                     )
                                                            )
                                          )

process.prod = cms.EDAnalyzer("SiStripNoisesRun3Builder",
                              printDebug = cms.untracked.uint32(1),
                              file = cms.untracked.FileInPath('CalibTracker/SiStripCommon/data/SiStripDetInfo.dat'),
                              StripQualityLabel = cms.string('MergedBadComponent')
                              )


process.load("CalibTracker.SiStripESProducers.SiStripQualityESProducer_cfi")

process.siStripQualityESProducer.ListOfRecordToMerge = cms.VPSet(
    cms.PSet(record = cms.string("SiStripDetVOffRcd"), tag = cms.string('')),    # DCS information
    cms.PSet(record = cms.string('SiStripDetCablingRcd'), tag = cms.string('')), # Use Detector cabling information to exclude detectors not connected            
    cms.PSet(record = cms.string('SiStripBadChannelRcd'), tag = cms.string('')), # Online Bad components
    cms.PSet(record = cms.string('SiStripBadFiberRcd'), tag = cms.string('')),   # Bad Channel list from the selected IOV as done at PCL
    cms.PSet(record = cms.string('RunInfoRcd'), tag = cms.string(''))            # List of FEDs exluded during data taking          
    )

process.siStripQualityESProducer.ReduceGranularity = cms.bool(False)
process.siStripQualityESProducer.ThresholdForReducedGranularity = cms.double(0.3)
process.siStripQualityESProducer.appendToDataLabel = 'MergedBadComponent'
process.siStripQualityESProducer.PrintDebugOutput = cms.bool(True)

#process.siStripBadComponentInfo = cms.EDProducer("SiStripBadComponentInfo",
#                                                 StripQualityLabel = cms.string('MergedBadComponent')
#                                             )

#process.print = cms.OutputModule("AsciiOutputModule")

process.p = cms.Path(process.prod)
#process.ep = cms.EndPath(process.print)


