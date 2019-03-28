#include "CondTools/SiStrip/plugins/SiStripNoisesRun3Builder.h"
#include "CalibTracker/SiStripCommon/interface/SiStripDetInfoFileReader.h"
#include "DataFormats/TrackerCommon/interface/TrackerTopology.h"
#include "CalibTracker/StandaloneTrackerTopology/interface/StandaloneTrackerTopology.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "CondFormats/DataRecord/interface/SiStripCondDataRecords.h"
#include "CalibFormats/SiStripObjects/interface/SiStripQuality.h"
#include "CalibTracker/Records/interface/SiStripQualityRcd.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include <iostream>
#include <fstream>
#include <string>


SiStripNoisesRun3Builder::SiStripNoisesRun3Builder( const edm::ParameterSet& iConfig ):
  fp_(iConfig.getUntrackedParameter<edm::FileInPath>("file",edm::FileInPath("CalibTracker/SiStripCommon/data/SiStripDetInfo.dat"))),
  printdebug_(iConfig.getUntrackedParameter<uint32_t>("printDebug",1)){}


void SiStripNoisesRun3Builder::analyze(const edm::Event& evt, const edm::EventSetup& iSetup, const edm::ParameterSet& iConfig){

  unsigned int run=evt.id().run();

  edm::LogInfo("SiStripNoisesBuilder") << "... creating dummy SiStripNoises Data for Run " << run << "\n " << std::endl;

  ///////////new code//////////////

  TrackerTopology tTopo = StandaloneTrackerTopology::fromTrackerParametersXMLFile(edm::FileInPath("Geometry/TrackerCommonData/data/trackerParameters.xml").fullPath());

  edm::ESHandle<SiStripNoises> early2018NoisesHandle;
  iSetup.get<SiStripNoisesRcd>().get("Early2018", early2018NoisesHandle);
  edm::ESHandle<SiStripNoises> late2018NoisesHandle;
  iSetup.get<SiStripNoisesRcd>().get("Late2018", late2018NoisesHandle);

  std::string  qualityLabel_ = iConfig.getParameter<std::string>("StripQualityLabel");
  edm::ESHandle<SiStripQuality> siStripQualityHandle;   
  iSetup.get<SiStripQualityRcd>().get(qualityLabel_,siStripQualityHandle);

  std::unordered_map<StripSubdetector, std::unordered_map<int, std::vector<float> > > noises[2];// map [subdetector][layer] => noise
  std::unordered_map<StripSubdetector, std::unordered_map<int, float > > noises_avg[2];
  std::unordered_map<StripSubdetector, std::unordered_map<int, float > > noise_SF;

  const SiStripNoises * iovs[2] = {*early2018NoisesHandle, *late2018NoisesHandle};
  
  for(size_t i=0; i<2; ++i){

    std::vector<uint32_t> detid;
    iovs[i]->getDetIds(detid);
    for (const auto & d : detid) {
      int subid = DetId(d).subdetId();
      int layer(-1);
      if(subid==StripSubdetector::TIB){
	layer = tTopo.tibLayer(d);
      } else if(subid==StripSubdetector::TOB){
	layer = tTopo.tobLayer(d);
      } else if (subid==StripSubdetector::TID){
	layer = tTopo.tidWheel(d);
      } else if (subid==StripSubdetector::TEC){
	layer = tTopo.tecWheel(id);
      }
      
      SiStripNoises::Range range=iovs[i]->getRange(d);
      for( int it=0; it < (range.second-range.first)*8/9; ++it ){
	isBad_ = siStripQualityHandle->IsStripBad(siStripQualityHandle->getRange(detid),it);
	if (!isBad_){
	  auto noise = early2018NoisesHandle-->getNoise(it,range);
	}
      }
      if(noises[i].find(subid) == noises[i].end()) noises[i].emplace(subid, std::unordered_map<int, std::vector<float> >{});
      if((noises[i])[subid].find(layer) == (noises[i])[subid].end())  (noises[i])[subid].emplace(layer, std::vector<float>{});
      (noises[i])[subid][layer].push_back(noise);
    }
  
    
    for(auto& entry : noises[i]) {
      for(auto& layer_and_noise : entry.second){ 
	double sum = std::accumulate(layer_and_noises.second.begin(), layer_and_noises.second.end(), 0.0);
	double mean = sum / layer_and_noises.second.size();

	if(noises_avg[i].find(entry.first) == noises_avg[i].end()) noises_avg[i].emplace(entry.first, std::unordered_map<int, std::vector<float> >{});
	if((noises_avg[i])[entry.first].find(layer_and_noise.first) == (noises_avg[i])[entry.first].end())  (noises_avg[i])[entry.first].emplace(layer_and_noise.first, std::vector<float>{});
	(noises_avg[i])[entry.first][layer_and_noise.first].push_back(mean);
      }
    }
  }
  
  // SF_l = [ave(good strip noise ; layer l; end 2018) / ave(good strip noise, layer l ; beginning 2018) ] / lumi(recorded in 2018) * lumi(recorded during run III)
  
  
  double lumi_Run3 = 260;
  double lumi_2018 = 63;
  for(auto& entry : noises_avg[1]) {
    for(auto& layer_and_noise : entry.second){
      if (noises_avg[0].find(entry.first) != noises_avg[0].end() && (noises_avg[0])[entry.first].find(layer_and_noise.first) != (noises_avg[0])[entry.first].end()){
	double SF_l = ((noises_avg[1])[entry.first][layer_and_noise.first].find(layer_and_noise.second)/(noises_avg[0])[entry.first][layer_and_noise.first].find(layer_and_noise.second))/lumi_2018*lumi_Run3;

	if(noise_SF.find(entry.first) == noise_SF.end()) noise_SF.emplace(entry.first, std::unordered_map<int, std::vector<float> >{});
        if((noise_SF)[entry.first].find(layer_and_noise.first) == (noise_SF)[entry.first].end())  (noise_SF)[entry.first].emplace(layer_and_noise.first, std::vector<float>{});
        (noise_SF)[entry.first][layer_and_noise.first].push_back(mean);
      }
    }
  }
  ///////////end new code//////////////

  SiStripNoises* obj = new SiStripNoises();

  SiStripDetInfoFileReader reader(fp_.fullPath());
  
  const std::map<uint32_t, SiStripDetInfoFileReader::DetInfo >& DetInfos  = reader.getAllData();

  int count=-1;
  for(std::map<uint32_t, SiStripDetInfoFileReader::DetInfo >::const_iterator it = DetInfos.begin(); it != DetInfos.end(); it++){    
    count++;

    //this might not work...
    int subid = DetId(it->first).subdetId();
    int layer(-1);
    if(subid==StripSubdetector::TIB){
      layer = tTopo.tibLayer(d);
    } else if(subid==StripSubdetector::TOB){
      layer = tTopo.tobLayer(d);
    } else if (subid==StripSubdetector::TID){
      layer = tTopo.tidWheel(d);
    } else if (subid==StripSubdetector::TEC){
      layer = tTopo.tecWheel(id);
    }

    //Generate Noise for det detid
    SiStripNoises::InputVector theSiStripVector;
    for(int strip=0; strip<128*it->second.nApvs; ++strip){

      float MeanNoise = 5;
      float RmsNoise  = 1;
      float noise =  CLHEP::RandGauss::shoot(MeanNoise,RmsNoise);
      
      noise = noise* noise_SF[entry.first][layer_and_noise.first].find(layer_and_noise.second);
      //double badStripProb = .5;
      //bool disable = (CLHEP::RandFlat::shoot(1.) < badStripProb ? true:false);
	
      obj->setData(noise,theSiStripVector);
      if (count<static_cast<int>(printdebug_))
	edm::LogInfo("SiStripNoisesBuilder") << "detid " << it->first << " \t"
					     << " strip " << strip << " \t"
					     << noise     << " \t" 
					     << theSiStripVector.back()/10 << " \t" 
					     << std::endl; 	    
    }    
      
    if ( ! obj->put(it->first,theSiStripVector) )
      edm::LogError("SiStripNoisesBuilder")<<"[SiStripNoisesBuilder::analyze] detid already exists"<<std::endl;
  }


  //End now write sistripnoises data in DB
  edm::Service<cond::service::PoolDBOutputService> mydbservice;

  if( mydbservice.isAvailable() ){
    if ( mydbservice->isNewTagRequest("SiStripNoisesRcd") ){
      mydbservice->createNewIOV<SiStripNoises>(obj,mydbservice->beginOfTime(),mydbservice->endOfTime(),"SiStripNoisesRcd");
    } else {  
      //mydbservice->createNewIOV<SiStripNoises>(obj,mydbservice->currentTime(),"SiStripNoisesRcd");      
      mydbservice->appendSinceTime<SiStripNoises>(obj,mydbservice->currentTime(),"SiStripNoisesRcd");      
    }
  }else{
    edm::LogError("SiStripNoisesBuilder")<<"Service is unavailable"<<std::endl;
  }
}
     
