import FWCore.ParameterSet.Config as cms


process = cms.Process("ICALIB")

process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, '103X_dataRun2_Prompt_v3','')

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
                              StripEarlyQualityLabel = cms.string('MergedBadComponentEarly2018'),
                              StripLateQualityLabel = cms.string('MergedBadComponentLate2018'),
                              )


process.load("CalibTracker.SiStripESProducers.SiStripQualityESProducer_cfi")

process.early2018SiStripQualityProducer = cms.ESProducer('SiStripQualityESProducer',
                                                         ListOfRecordToMerge = cms.VPSet(
                                                            cms.PSet(record = cms.string('SiStripBadModuleRcd'), tag = cms.string(''))
                                                         ),
                                                         ReduceGranularity = cms.bool(False),
                                                         ThresholdForReducedGranularity = cms.double(0.3),
                                                         appendToDataLabel = cms.string('MergedBadComponentEarly2018'),
                                                         PrintDebugOutput = cms.bool(True),
                                                        connect = cms.string("sqlite_file:dbfile_Early_2018.db")
                                                     )


process.late2018SiStripQualityProducer = cms.ESProducer('SiStripQualityESProducer',
                                                        ListOfRecordToMerge = cms.VPSet(
                                                            cms.PSet(record = cms.string('SiStripBadModuleRcd'), tag = cms.string(''))
                                                       ),
                                                       ReduceGranularity = cms.bool(False),
                                                       ThresholdForReducedGranularity = cms.double(0.3),
                                                       appendToDataLabel = cms.string('MergedBadComponentLate2018'),
                                                       PrintDebugOutput = cms.bool(True),
                                                       connect = cms.string("sqlite_file:dbfile_Late_2018.db")
                                                   )


#process.siStripBadComponentInfo = cms.EDProducer("SiStripBadComponentInfo",
#                                                 StripQualityLabel = cms.string('MergedBadComponent')
#                                             )



#process.print = cms.OutputModule("AsciiOutputModule")

process.p = cms.Path(process.prod)
#process.ep = cms.EndPath(process.print)


