'''
Loops on the events and operates the matching between reconstructed and generated taus.
It produces two flat ntuples:
    - one with an entry for each gen tau (useful for efficiencies)
    - one with an entry for each reconstructed tau (useful for fake studies)
'''
import ROOT
from array import array
from collections import OrderedDict
from DataFormats.FWLite import Events, Handle
from PhysicsTools.HeppyCore.utils.deltar import deltaR, deltaPhi
from PhysicsTools.Heppy.physicsutils.TauDecayModes import tauDecayModes
from treeVariables import branches # here the ntuple branches are defined
from utils import isGenHadTau, finalDaughters, printer # utility functions
from pdb import set_trace
##########################################################################################
# initialise output files to save the flat ntuples
outfile_gen = ROOT.TFile('tau_gen_tuple.root', 'recreate')
ntuple_gen = ROOT.TNtuple('tree', 'tree', ':'.join(branches))
tofill_gen = OrderedDict(zip(branches, [-99.]*len(branches))) # initialise all branches to unphysical -99       

outfile_reco = ROOT.TFile('tau_reco_tuple.root', 'recreate')
ntuple_reco = ROOT.TNtuple('tree', 'tree', ':'.join(branches))
tofill_reco = OrderedDict(zip(branches, [-99.]*len(branches))) # initialise all branches to unphysical -99       

##########################################################################################
# Get ahold of the events
events = Events('outputFULL.root') # make sure this corresponds to your file name!
#events = Events('root://cms-xrd-global.cern.ch//store/user/tomc/heavyNeutrinoMiniAOD/Moriond17/displaced/HeavyNeutrino_lljj_M-4_V-0.004472135955_mu_pre2017_leptonFirst_NLO/heavyNeutrino_182.root')
maxevents = -1 # max events to process
totevents = events.size() # total number of events in the files

##########################################################################################
# instantiate the handles to the relevant collections.
# Do this *outside* the event loop
# Reminder: you can see the names of the collections stored in your input file by doing:
# edmDumpEventContent outputFULL.root

#
label_combtaus  = ('combinatoricRecoTaus', '', 'TAURECO')
handle_combtaus = Handle('vector<reco::PFBaseTau>')

# PAT taus
label_taus  = ('patTaus', '', 'TAURECO')
#label_taus  = ('slimmedTaus', '', 'PAT')
handle_taus = Handle('std::vector<pat::Tau>')

# PAT jets
label_jets = ('slimmedJets', '', 'PAT')
handle_jets = Handle('std::vector<pat::Jet>')

# gen particles
label_gen  = ('prunedGenParticles', '', 'PAT')
handle_gen = Handle('std::vector<reco::GenParticle>')

# vertices
handle_vtx = Handle('std::vector<reco::Vertex>')
label_vtx  = ('offlineSlimmedPrimaryVertices','','PAT')

##########################################################################################
# example histogram
histos = OrderedDict()
histos['pull_pt'] = ROOT.TH1F('pull_pt', 'pull_pt', 50, -2, 2)
histos['pull_pt'].GetXaxis().SetTitle('(p_{T}^{off} - p_{T}^{gen})/p_{T}^{gen}')
histos['pull_pt'].GetYaxis().SetTitle('counts')

##########################################################################################
# start looping on the events
for i, ev in enumerate(events):
    
    ######################################################################################
    # controls on the events being processed
    if maxevents>0 and i>maxevents:
        break
        
    if i%100==0:
        print '===> processing %d / %d event' %(i, totevents)
    
    ###############################################
    # access the comb taus
    ev.getByLabel(label_combtaus, handle_combtaus)
    combtaus =  handle_combtaus.product()
    #for i in combtaus:
    #    print i.decayMode()
    #set_trace()
    ######################################################################################
    # access the taus
    ev.getByLabel(label_taus, handle_taus)
    taus = handle_taus.product()
    
    # loosely filter the reco taus 
    taus = [tau for tau in taus if tau.pt()>18.]

    ######################################################################################
    # access the jets
    ev.getByLabel(label_jets, handle_jets)
    jets = handle_jets.product()

    # loosely filter jets
    jets = [jet for jet in jets if jet.pt()>18. and abs(jet.eta())<2.5]

    ######################################################################################
    # access the vertices
    ev.getByLabel(label_vtx, handle_vtx)
    vertices = handle_vtx.product()

    ######################################################################################
    # access the gen taus
    ev.getByLabel (label_gen, handle_gen)
    gen_particles = handle_gen.product()
    
    # select only hadronically decaying taus
    #gen_taus = [pp for pp in gen_particles if abs(pp.pdgId())==15 and pp.status()==2 and isGenHadTau(pp)]
    gen_taus = [pp for pp in gen_particles if ((abs(pp.pdgId()) == 9900012 or abs(pp.pdgId()) == 9900014 or abs(pp.pdgId()) == 9900016) and pp.isLastCopy())]
    if (gen_taus[0].pt()<10 or abs(gen_taus[0].eta())>2.5): continue
    # determine gen decaymode
    for gg in gen_taus:
        gg.decayMode = tauDecayModes.genDecayModeInt([d for d in finalDaughters(gg)])#  if abs(d.pdgId()) not in [12, 14, 16]])
    #print gg.decayMode
    ######################################################################################
    # match reco taus to gen taus
    for tt in taus    : tt.gen_tau  = None # first initialise the matching to None
    for gg in gen_taus: gg.reco_tau = None # first initialise the matching to None
    
    gen_taus_copy = gen_taus # we'll cyclically remove any gen taus that gets matched
    
    for tt in taus:
        matches = [gg for gg in gen_taus_copy if deltaR(tt.p4(), gg.p4())<0.3] #visp4

        #print 'number of daughters ', len(tt.signalCands())
        #for i in tt.signalCands():
        #    print i.pdgId()
        #print 'New Tau'
        #set_trace()
        #print "decayMode: ",tt.decayMode()

        if not len(matches):
            continue
        matches.sort(key = lambda gg : deltaR(tt.p4(), gg.p4()))
        bestmatch = matches[0]
        tt.gen_tau = bestmatch
        bestmatch.reco_tau = tt
        gen_taus_copy = [gg for gg in gen_taus_copy if gg != bestmatch]
        #print tt.gen_tau.decayMode
        #print bestmatch.reco_tau.decayMode
    ######################################################################################
    # match reco taus to reco jets
    for jj in jets : jj.tau = None # first initialise the matching to None

    taus_copy = taus # we'll cyclically remove any tau that gets matched

    for jj in jets:
        matches = [tt for tt in taus_copy if deltaR(jj.p4(), tt.p4())<0.3]
        if not len(matches):
            continue
        matches.sort(key = lambda tt : deltaR(jj.p4(), tt.p4()))
        bestmatch = matches[0]
        jj.tau = bestmatch
        taus_copy = [tt for tt in taus_copy if tt != bestmatch]

    ######################################################################################
    # fill histograms
    for gg in gen_taus:
        if hasattr(gg, 'reco_tau') and gg.reco_tau:
            pull = (gg.reco_tau.pt() - gg.pt())/gg.pt()
            histos['pull_pt'].Fill(pull)
    

    ######################################################################################
    # fill the ntuple: each gen tau makes an entry
    for gg in gen_taus:
        for k, v in tofill_gen.iteritems(): tofill_gen[k] = -99. # initialise before filling
        tofill_gen['run'               ] = ev.eventAuxiliary().run()
        tofill_gen['lumi'              ] = ev.eventAuxiliary().luminosityBlock()
        tofill_gen['event'             ] = ev.eventAuxiliary().event()
        tofill_gen['nvtx'              ] = vertices.size()
        if hasattr(gg, 'reco_tau') and gg.reco_tau:
            tofill_gen['tau_reco_mass'     ] = gg.reco_tau.mass()
            tofill_gen['tau_reco_pt'       ] = gg.reco_tau.pt()
            tofill_gen['tau_reco_eta'      ] = gg.reco_tau.eta()
            tofill_gen['tau_reco_phi'      ] = gg.reco_tau.phi()
            tofill_gen['tau_reco_charge'   ] = gg.reco_tau.charge()
            tofill_gen['tau_reco_decaymode'] = gg.reco_tau.decayMode()
        tofill_gen['tau_gen_pt'        ] = gg.pt()
        tofill_gen['tau_gen_eta'       ] = gg.eta()
        tofill_gen['tau_gen_phi'       ] = gg.phi()
        tofill_gen['tau_gen_charge'    ] = gg.charge()
        tofill_gen['tau_gen_decaymode' ] = gg.decayMode
        #tofill_gen['tau_gen_vis_mass'  ] = gg.vismass()
        #tofill_gen['tau_gen_vis_pt'    ] = gg.vispt()
        #tofill_gen['tau_gen_vis_eta'   ] = gg.viseta()
        #tofill_gen['tau_gen_vis_phi'   ] = gg.visphi()
        #print tofill_gen.values()
        #print tofill_gen.keys(), tofill_gen.values()
        ntuple_gen.Fill(array('f',tofill_gen.values()))

    # fill the ntuple: each gen tau makes an entry
    for jj in jets:
        for k, v in tofill_reco.iteritems(): tofill_reco[k] = -99. # initialise before filling
        tofill_reco['run'        ] = ev.eventAuxiliary().run()
        tofill_reco['lumi'       ] = ev.eventAuxiliary().luminosityBlock()
        tofill_reco['event'      ] = ev.eventAuxiliary().event()
        tofill_reco['nvtx'       ] = vertices.size()
        tofill_reco['jet_mass'   ] = jj.mass()
        tofill_reco['jet_pt'     ] = jj.pt()
        tofill_reco['jet_eta'    ] = jj.eta()
        tofill_reco['jet_phi'    ] = jj.phi()
        tofill_reco['jet_charge' ] = jj.charge()
        if hasattr(jj, 'tau') and jj.tau:
            tofill_reco['tau_reco_mass'     ] = jj.tau.mass()
            tofill_reco['tau_reco_pt'       ] = jj.tau.pt()
            tofill_reco['tau_reco_eta'      ] = jj.tau.eta()
            tofill_reco['tau_reco_phi'      ] = jj.tau.phi()
            tofill_reco['tau_reco_charge'   ] = jj.tau.charge()
            tofill_reco['tau_reco_decaymode'] = jj.tau.decayMode()
            if hasattr(jj.tau, 'gen_tau') and jj.tau.gen_tau:
                tofill_gen['tau_gen_pt'        ] = jj.tau.gen_tau.pt()
                tofill_gen['tau_gen_eta'       ] = jj.tau.gen_tau.eta()
                tofill_gen['tau_gen_phi'       ] = jj.tau.gen_tau.phi()
                tofill_gen['tau_gen_charge'    ] = jj.tau.gen_tau.charge()
                tofill_gen['tau_gen_decaymode' ] = jj.tau.gen_tau.decayMode
                #tofill_gen['tau_gen_vis_mass'  ] = jj.tau.gen_tau.vismass()
                #tofill_gen['tau_gen_vis_pt'    ] = jj.tau.gen_tau.vispt()
                #tofill_gen['tau_gen_vis_eta'   ] = jj.tau.gen_tau.viseta()
                #tofill_gen['tau_gen_vis_phi'   ] = jj.tau.gen_tau.visphi()
        #print tofill_reco.keys() , tofill_reco.values()
        #print tofill_reco
        try:
            ntuple_reco.Fill(array('f',tofill_reco.values()))
        except: set_trace()

    ######################################################################################
    # printout some info, if you want
    # printer(taus, gen_taus)

##########################################################################################
# write the ntuples and close the files
outfile_gen.cd()
ntuple_gen.Write()
outfile_gen.Close()

outfile_reco.cd()
ntuple_reco.Write()
outfile_reco.Close()
