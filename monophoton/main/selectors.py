import sys
import os
import array
import logging
import fnmatch

needHelp = False
for opt in ['-h', '--help']:
    if opt in sys.argv:
        needHelp = True
        sys.argv.remove(opt)

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
datadir = basedir + '/data'

if basedir not in sys.path:
    sys.path.append(basedir)

import config

logger = logging.getLogger(__name__)

import ROOT

ROOT.gSystem.Load(config.libobjs)
ROOT.gSystem.Load('libfastjet.so')

# if the objects library is compiled with CLING dictionaries, ROOT must load the
# full library first before compiling the macros.
try:
    e = ROOT.panda.Event
except AttributeError:
    pass

ROOT.gROOT.LoadMacro(thisdir + '/operators.cc+')
try:
    o = ROOT.Operator
except:
    logger.error("Couldn't compile operators.cc. Quitting.")
    sys.exit(1)

ROOT.gROOT.LoadMacro(thisdir + '/selectors.cc+')
try:
    o = ROOT.EventSelectorBase
except:
    logger.error("Couldn't compile selectors.cc. Quitting.")
    sys.exit(1)

## Selector-dependent configurations

selconf = {
    'photonFullSelection': [],
    'photonIDTune': -1,
    'photonWP': 1,
    'photonSF':('', '', [], (1., 0.)), # filename, histname, varlist, pixelveto SF and uncertainty
    'puweightSource': ('', ''), # gROOT directory name, file name
    'hadronTFactorSource': ('', ''), # file name, suffix
    'electronTFactor': '',
    'electronTFactorUnc': '',
    'hadronProxyDef': [],
    'ewkCorrSource': ''
}
ROOT.gROOT.ProcessLine("int idtune;")

if config.year == '16':
    selconf['sphTrigger'] = 'HLT_Photon165_HE10'
    selconf['vbfTrigger'] = 'HLT_Photon75_R9Id90_HE10_Iso40_EBOnly_VBF'
    selconf['vbfCtrlTrigger'] = 'HLT_Photon75_R9Id90_HE10_IsoM'
    selconf['selTrigger'] = 'HLT_Ele27_WPTight_Gsf'
    selconf['smuTrigger'] = 'HLT_IsoMu24_OR_HLT_IsoTkMu24'

elif config.year == '17':
    selconf['sphTrigger'] = 'HLT_Photon200'
    selconf['vbfTrigger'] = 'HLT_Photon75_R9Id90_HE10_Iso40_EBOnly_VBF'
    selconf['vbfCtrlTrigger'] = 'HLT_Photon75_R9Id90_HE10_IsoM'
    selconf['selTrigger'] = 'HLT_Ele35_WPTight_Gsf'
    selconf['smuTrigger'] = 'HLT_IsoMu24_OR_HLT_IsoMu27'

def monophotonSetting():
    logger.info('Applying monophoton setting.')

    selconf['photonFullSelection'] = [
        'HOverE',
        'Sieie',
        'NHIso',
        'PhIso',
        'CHIsoMax',
        'EVeto',
        'MIP49',
        'Time',
        'SieieNonzero',
        'SipipNonzero',
        'NoisyRegion',
        'R9Unity'
    ]
    if config.year == '16':
        ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kGJetsCWIso;")
        selconf['photonIDTune'] = ROOT.idtune
        selconf['photonSF'] = (1.002, 0.007, [ROOT.IDSFWeight.kPt], (0.984, .009)) # , ROOT.IDSFWeight.nVariables)
        selconf['puweightSource'] = ('puweight_fulllumi', datadir + '/pileup.root')
        selconf['hadronTFactorSource'] = (datadir + '/hadronTFactor_GJetsCWIso.root', '_GJetsCWIso')
        selconf['hadronProxyDef'] = ['!CHIsoMax', '+CHIsoMax11']
        selconf['electronTFactor'] = 0.0303
        selconf['electronTFactorUnc'] = 0.0726
        selconf['ewkCorrSource'] = 'ewk_corr.root'
    
    elif config.year == '17':
        ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kGJetsCWIso;")
        selconf['photonIDTune'] = ROOT.idtune
        selconf['photonSF'] = (1.002, 0.007, [ROOT.IDSFWeight.kPt], (0.984, .009)) # , ROOT.IDSFWeight.nVariables)
        selconf['puweightSource'] = ('puweight_fulllumi', datadir + '/pileup.root')
        selconf['hadronTFactorSource'] = (datadir + '/hadronTFactor_GJetsCWIso.root', '_GJetsCWIso')
        selconf['hadronProxyDef'] = ['!CHIsoMax', '+CHIsoMax11']
        selconf['electronTFactor'] = 0.0303
        selconf['electronTFactorUnc'] = 0.0726
        selconf['ewkCorrSource'] = 'ewk_corr.root'

def vbfgSetting():
    logger.info('Applying vbfg setting.')

    selconf['photonFullSelection'] = [
        'HOverE',
        'Sieie',
        'NHIso',
        'PhIso',
        'CHIso',
        'EVeto',
        'ChargedPFVeto'
    ]
    if config.year == '16':
        ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kSpring16;")
        selconf['photonIDTune'] = ROOT.idtune
        selconf['photonSF'] = (0.995, 0.008, [ROOT.IDSFWeight.kPt], (0.993, .006)) # , ROOT.IDSFWeight.nVariables)
        selconf['puweightSource'] = ('puweight_vbf75', datadir + '/pileup_vbf75.root')
        selconf['hadronTFactorSource'] = (datadir + '/hadronTFactor_Spring16_lowpt.root', '_spring16')
        selconf['hadronProxyDef'] = ['!CHIso', '+CHIso11']
        selconf['electronTFactor'] = datadir + '/efakepf_data_lowpt.root/frate_fit'
        selconf['electronTFactorUnc'] = 'frate_fit'
        selconf['ewkCorrSource'] = 'ewk_corr.root'

    elif config.year == '17':
        ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kSpring16;")
        selconf['photonIDTune'] = ROOT.idtune
        selconf['photonSF'] = (0.995, 0.008, [ROOT.IDSFWeight.kPt], (0.993, .006)) # , ROOT.IDSFWeight.nVariables)
        selconf['puweightSource'] = ('puweight_vbf75', datadir + '/pileup_vbf75.root')
        selconf['hadronTFactorSource'] = (datadir + '/hadronTFactor_Spring16_lowpt.root', '_spring16')
        selconf['hadronProxyDef'] = ['!CHIso', '+CHIso11']
        selconf['electronTFactor'] = datadir + '/efakepf_data_lowpt.root/frate_fit'
        selconf['electronTFactorUnc'] = 'frate_fit'
        selconf['ewkCorrSource'] = 'ewk_corr.root'

datadir + '/efakepf_data_ptalt.root'

def gghSetting():
    logger.info('Applying ggh setting.')

    selconf['photonFullSelection'] = [
        'HOverE',
        'Sieie',
        'NHIso',
        'PhIso',
        'CHIso',
        'EVeto',
        'ChargedPFVeto',
        'NoisyRegion'
    ]
    if config.year == '16':
        ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kSpring16;")
        selconf['photonIDTune'] = ROOT.idtune
        selconf['photonSF'] = (0.995, 0.008, [ROOT.IDSFWeight.kPt], (0.993, .006)) # , ROOT.IDSFWeight.nVariables)
        selconf['puweightSource'] = ('puweight_fulllumi', datadir + '/pileup.root')
        selconf['hadronTFactorSource'] = (datadir + '/hadronTFactor_Spring16.root', '_Spring16')
        selconf['hadronProxyDef'] = ['!CHIso', '+CHIso11']
        selconf['electronTFactor'] = datadir + '/efakepf_data_ptalt2.root/frate'
        selconf['electronTFactorUnc'] = 'frate'
        selconf['ewkCorrSource'] = 'ewk_corr.root'

    elif config.year == '17':
        ROOT.gROOT.ProcessLine("idtune = panda::XPhoton::kSpring16;")
        selconf['photonIDTune'] = ROOT.idtune
        selconf['photonSF'] = (0.995, 0.008, [ROOT.IDSFWeight.kPt], (0.993, .006)) # , ROOT.IDSFWeight.nVariables)
        selconf['puweightSource'] = ('puweight_fulllumi', datadir + '/pileup.root')
        selconf['hadronTFactorSource'] = (datadir + '/hadronTFactor_Spring16.root', '_Spring16')
        selconf['hadronProxyDef'] = ['!CHIso', '+CHIso11']
        selconf['electronTFactor'] = datadir + '/efakepf_data_ptalt2.root/frate'
        selconf['electronTFactorUnc'] = 'frate'
        selconf['ewkCorrSource'] = 'ewk_corr.root'

def monophEWKSetting(inflection):
    monophotonSetting()
    logger.info('Changing EWK inflection point to ' + str(int(inflection)))
    
    selconf['ewkCorrSource'] = 'ewk_corr_' + str(int(inflection)) + '.root'
    
## utility functions

def setupPhotonSelection(operator, veto = False, changes = []):
    ##### !!!!! IMPORTANT - NOTE THE RESETS #####
    if veto:
        operator.resetVeto()
    else:
        operator.resetSelection()

    sels = list(selconf['photonFullSelection'])

    for change in changes:
        if change.startswith('-'):
            try:
                sels.remove(change[1:])
            except ValueError:
                pass
        elif change.startswith('+'):
            sels.append(change[1:])
        elif change.startswith('!'):
            try:
                sels.remove(change[1:])
            except ValueError:
                pass

            sels.append(change)

    if veto:
        for sel in sels:
            if sel.startswith('!'):
                operator.addVeto(False, getattr(ROOT.PhotonSelection, sel[1:]))
            else:
                operator.addVeto(True, getattr(ROOT.PhotonSelection, sel))
    else:
        for sel in sels:
            if sel.startswith('!'):
                operator.addSelection(False, getattr(ROOT.PhotonSelection, sel[1:]))
            else:
                operator.addSelection(True, getattr(ROOT.PhotonSelection, sel))
    
# avoid auto-deletion by python
_garbage = []

# Other weights
def getFromFile(path, name, newname = ''):
    if newname == '':
        newname = name

    obj = ROOT.gROOT.Get(newname)
    if obj:
        return obj

    f = ROOT.TFile.Open(path)
    orig = f.Get(name)
    if not orig:
        return None

    ROOT.gROOT.cd()
    obj = orig.Clone(newname)

    f.Close()

    logger.debug('Picked up %s from %s', name, path)
    
    _garbage.append(obj)

    return obj

##################
# BASE SELECTORS #
##################

def monophotonBase(sample, rname, selcls = None):
    """
    Monophoton candidate-like selection (high-pT photon, lepton veto, dphi(photon, MET) and dphi(jet, MET)).
    Base for other selectors.
    """

    monophotonSetting()

    if selcls is None:
        selector = ROOT.EventSelector(rname)
    else:
        selector = selcls(rname)

    selector.setPreskim('superClusters.rawPt > 165. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters'
    ]

    if not sample.data:
        operators.append('MetVariations')
        
    operators += [
        'Met',
        'PhotonMetDPhi',
        'JetMetDPhi',
        'PhotonJetDPhi',
        'PhotonPtOverMet',
        'PhotonMt'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMinPt(175.)
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 0)
    leptonSel.setRequireMedium(False)
    leptonSel.setRequireTight(False)
    # leptonSel.setIgnoreDecision(True)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)

        selector.findOperator('PhotonJetDPhi').setMetVariations(metVar)

        selector.addOperator(ROOT.PartonKinematics())
        
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

        addElectronVetoSFWeight(sample, selector)
        addMuonVetoSFWeight(sample, selector)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)
    selector.findOperator('PhotonPtOverMet').setIgnoreDecision(True)

    return selector

def emjetBase(sample, rname):
    """
    Base selector for EM+Jet control region. For MC, a gen-level photon is required.
    """

    monophotonSetting()

    selector = monophotonBase(sample, rname)

    selector.removeOperator('PhotonMt')

    selector.findOperator('Met').setThreshold(0.)
    selector.findOperator('Met').setCeiling(170.)
    selector.findOperator('Met').setIgnoreDecision(False)

    photonSel = selector.findOperator('PhotonSelection')

    jets = ROOT.HighPtJetSelection()
    jets.setJetPtCut(100.)
    selector.addOperator(jets)

    dijetSel = ROOT.DijetSelection()
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)
    dijetSel.setIgnoreDecision(True)
    selector.addOperator(dijetSel)

    if not sample.data:
        genPhotonSel = ROOT.GenParticleSelection("GenPhotonSelection")
        genPhotonSel.setPdgId(22)
        genPhotonSel.setMinPt(140.)
        genPhotonSel.setMaxEta(1.7)

        # selector.addOperator(genPhotonSel, 1)

    return selector

def leptonBase(sample, rname, flavor, selcls = None):
    """
    Base for n-lepton + photon selection.
    For MC, we could use PartonSelector, but for interest of clarity and comparing cut flow
    with the other groups, we let events with all flavors pass.
    """

    monophotonSetting()

    if selcls is None:
        selector = ROOT.EventSelector(rname)
    else:
        selector = selcls(rname)

    selector.setPreskim('superClusters.rawPt > 165. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))
    else:
        partons = ROOT.PartonFlavor()
        if flavor == ROOT.lElectron:
            partons.setRequiredPdgId(11)
        elif flavor == ROOT.lMuon:
            partons.setRequiredPdgId(13)

        selector.addOperator(partons)

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters',
        'LeptonRecoil',
    ]

    if not sample.data:
        operators.append('MetVariations')
        
    operators += [
        'PhotonMetDPhi',
        'JetMetDPhi',
        'Met',
        'PhotonPtOverMet',
        'PhotonMt'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    jetDPhi = selector.findOperator('JetMetDPhi')
    jetDPhi.setMetSource(ROOT.kInMet)

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setRequireMedium(False)

    setupPhotonSelection(photonSel)

    selector.findOperator('LeptonRecoil').setFlavor(flavor)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        realMetVar = ROOT.MetVariations('RealMetVar')
        realMetVar.setMetSource(ROOT.kInMet)
        realMetVar.setPhotonSelection(photonSel)

        selector.findOperator('PhotonMetDPhi').setMetVariations(metVar)
        
        jetDPhi.setMetVariations(realMetVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        addPUWeight(sample, selector)
        addIDSFWeight(sample, selector)
        addPDFVariation(sample, selector)

        if flavor == ROOT.lElectron:
            addElectronIDSFWeight(sample, selector)
        else:
            addMuonIDSFWeight(sample, selector)

        addElectronVetoSFWeight(sample, selector)
        addMuonVetoSFWeight(sample, selector)

    if not sample.data:
        selector.findOperator('PartonFlavor').setIgnoreDecision(True)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)
    selector.findOperator('PhotonPtOverMet').setIgnoreDecision(True)

    return selector

def zmumu(sample, rname):
    """
    Just dimuon. 
    """

    selconf['puweightSource'] = ('puweight_fulllumi', datadir + '/pileup.root')

    selector = ROOT.EventSelector(rname)

    selector.setPreskim('muons.size > 1')

    selector.addOperator(ROOT.MetFilters())

    leptons = ROOT.LeptonSelection()
    leptons.setN(0, 2)
    leptons.setStrictMu(False)
    leptons.setRequireTight(False)
    selector.addOperator(leptons)

    # LeptonVertex loads pfCandidates - turning it off for speedup
#    vtx = ROOT.LeptonVertex()
#    vtx.setSpecies(ROOT.lMuon)
#    selector.addOperator(vtx)

    mass = ROOT.Mass()
    mass.setPrefix('dimu')
    mass.setMin(60.)
    mass.setMax(120.)
    mass.setCollection1(ROOT.cMuons)
    mass.setCollection2(ROOT.cMuons)
    selector.addOperator(mass)

    jets = ROOT.JetCleaning()
    jets.setCleanAgainst(ROOT.cPhotons, False)
    jets.setCleanAgainst(ROOT.cElectrons, False)
    jets.setCleanAgainst(ROOT.cTaus, False)
    selector.addOperator(jets)

    selector.addOperator(ROOT.CopyMet())

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        addPUWeight(sample, selector)
        addPDFVaraition(sample, selector)

    return selector

def elmu(sample, rname):
    """
    1e, 1mu. mostly ttbar
    """

    monophotonSetting()

    selector = ROOT.EventSelector(rname)

    selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    selector.setPreskim('muons.size > 0 && electrons.size > 0')

    selector.addOperator(ROOT.MetFilters())

    leptons = ROOT.LeptonSelection()
    leptons.setN(1, 1)
    leptons.setStrictMu(False)
    leptons.setStrictEl(False)
    leptons.setRequireTight(False)
    selector.addOperator(leptons)

    # NOTE: photon selection is not cleaned up against leptons and we want it that way - we are interested also in photons overlapping with electrons
    photonSel = ROOT.PhotonSelection()
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])
    setupPhotonSelection(photonSel, changes = ['-EVeto'])
    photonSel.setMinPt(30.)
    photonSel.setIgnoreDecision(True)
    selector.addOperator(photonSel)

    jets = ROOT.JetCleaning()
    jets.setCleanAgainst(ROOT.cTaus, False)
    selector.addOperator(jets)

    selector.addOperator(ROOT.CopyMet())

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

    return selector

def TagAndProbeBase(sample, rname):
    """
    Base for Z->ll tag and probe stuff.
    """

    selconf['puweightSource'] = ('puweight_fulllumi', datadir + '/pileup.root')

    selector = ROOT.EventSelector(rname)

    operators = [
        'MetFilters',
        'LeptonSelection',
        'TauVeto',
        'TagAndProbePairZ',
        'JetCleaning',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters',
        'JetMetDPhi',
        'Met'
    ]
    
    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw))

        addPUWeight(sample, selector)

    selector.findOperator('LeptonSelection').setN(0, 0)

    selector.findOperator('LeptonSelection').setIgnoreDecision(True)
    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    # selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cElectrons, False)
    selector.findOperator('Met').setThreshold(50.)
    selector.findOperator('Met').setIgnoreDecision(True)

    return selector

def tagprobeBase(sample, rname):
    """
    Base for selectors skimming tag & probe input trees.
    """

    selconf['puweightSource'] = ('puweight_fulllumi', datadir + '/pileup.root')

    selector = ROOT.TagAndProbeSelector(rname)

    setSampleId(sample, selector)

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw))
        # addPUWeight(sample, selector)

    return selector

def vbfgBase(sample, rname):
    """
    Base for VBF + photon.
    """

    vbfgSetting()

    selector = ROOT.EventSelector(rname)

    selector.setPreskim('superClusters.rawPt > 80. && Sum$(chsAK4Jets.pt_ > 50.) > 2') # 1 for the photon

    selector.addOperator(ROOT.HLTFilter(selconf['vbfTrigger']))

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'JetCleaning',
        'DijetSelection',
        'BjetVeto',
        'CopyMet'
    ]

    if not sample.data:
        operators.append('MetVariations')

    operators += [
        'AddTrailingPhotons',
        'PhotonMt',
        'PhotonMetDPhi',
        'JetMetDPhi'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setIDTune(1)
    photonSel.setMinPt(80.)

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 0)
    leptonSel.setRequireTight(False)
    leptonSel.setRequireMedium(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)

    jetCleaning = selector.findOperator('JetCleaning')
    jetCleaning.setCleanAgainst(ROOT.cTaus, False)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        # nominal 9.76182e-01 + 1.03735e-04 * x  -> has 43499 entries in efficiency.root ptwide_pass histogram
        # alt 9.82825e-01 + 1.37474e-05 * x  -> 29315 entries
        # taking the sqrt(N)-weighted average for nominal
        triggersf_photon = ROOT.PhotonPtWeight(ROOT.TF1('trigsf_ph_nominal', '0.9792 + 6.317e-05 * x', 80., 1000.), 'trigeff_ph')
        # single photon measurement
        triggersf_photon.addVariation("trigsf_photonUp", ROOT.TF1('trigeff_ph_up', '9.76182e-01 + 1.03735e-04 * x', 80., 1000.))
        # symmetric reflection of Down about nominal
        triggersf_photon.addVariation("trigsf_photonDown", ROOT.TF1('trigeff_ph_down', '0.9822 + 2.260e-05 * x', 80., 1000.))

        selector.addOperator(triggersf_photon)

        triggersf_vbf = ROOT.DEtajjWeight(ROOT.TF1('trigsf_vbf_nominal', '1.00989e+00 - 1.04419e-02 * x', 3., 10.), 'trigeff_vbf')
        triggersf_vbf.setDijetSelection(dijetSel)
        selector.addOperator(triggersf_vbf)

        addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

        addElectronVetoSFWeight(sample, selector)
        addMuonVetoSFWeight(sample, selector)        

        selector.addOperator(ROOT.AddGenJets())

    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)

    return selector

def vbflBase(sample, rname):
    """
    VBF + lepton(s).
    """

    selconf['puweightSource'] = ('puweight_vbf75', datadir + '/pileup_vbf75.root')

    selector = ROOT.EventSelector(rname)

    selector.setPreskim('Sum$(chsAK4Jets.pt_ > 50.) > 1')

    trig = ROOT.HLTFilter(selconf['vbfTrigger'])
    trig.setIgnoreDecision(True)
    selector.addOperator(trig)

    operators = [
        'MetFilters',
        'LeptonSelection',
        'JetCleaning',
        'DijetSelection',
        'BjetVeto',
        'CopyMet',
        'JetMetDPhi',
        'Met'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setRequireMedium(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(0.)
    dijetSel.setMinMjj(0.)

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)

    return selector

def gghgBase(sample, rname, selcls = None):
    """
    For low MT case.
    Monophoton candidate-like selection (high-pT photon, lepton veto, dphi(photon, MET) and dphi(jet, MET)). 
    Base for other selectors.
    """

    gghSetting()

    if selcls is None:
        selector = ROOT.EventSelector(rname)
    else:
        selector = selcls(rname)

    selector.setPreskim('superClusters.rawPt > 165. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'DijetSelection',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters'
    ]

    if not sample.data:
        operators.append('MetVariations')
        
    operators += [
        'Met',
        'PhotonMetDPhi',
        'JetMetDPhi',
        'PhotonJetDPhi',
        'PhotonPtOverMet',
        'PhotonMt'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMinPt(175.)
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 0)
    leptonSel.setRequireMedium(False)
    leptonSel.setRequireTight(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)
    dijetSel.setIgnoreDecision(True)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)

        selector.findOperator('PhotonJetDPhi').setMetVariations(metVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)
    selector.findOperator('Met').setThreshold(100.)
    selector.findOperator('PhotonPtOverMet').setIgnoreDecision(True)

    return selector

def gghlBase(sample, rname, flavor, selcls = None):
    """
    For low MT case.
    Base for n-lepton + photon selection.
    For MC, we could use PartonSelector, but for interest of clarity and comparing cut flow
    with the other groups, we let events with all flavors pass.
    """

    gghSetting()

    if selcls is None:
        selector = ROOT.EventSelector(rname)
    else:
        selector = selcls(rname)

    selector.setPreskim('superClusters.rawPt > 165. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))
    else:
        partons = ROOT.PartonFlavor()
        if flavor == ROOT.lElectron:
            partons.setRequiredPdgId(11)
        elif flavor == ROOT.lMuon:
            partons.setRequiredPdgId(13)

        partons.setIgnoreDecision(True)
        selector.addOperator(partons)

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'DijetSelection',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters',
        'LeptonRecoil',
    ]

    if not sample.data:
        operators.append('MetVariations')
        
    operators += [
        'PhotonMetDPhi',
        'JetMetDPhi',
        'Met',
        'PhotonPtOverMet',
        'PhotonMt'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    jetDPhi = selector.findOperator('JetMetDPhi')
    jetDPhi.setMetSource(ROOT.kInMet)

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setRequireMedium(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)
    dijetSel.setIgnoreDecision(True)

    setupPhotonSelection(photonSel)

    selector.findOperator('LeptonRecoil').setFlavor(flavor)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        realMetVar = ROOT.MetVariations('RealMetVar')
        realMetVar.setMetSource(ROOT.kInMet)
        realMetVar.setPhotonSelection(photonSel)

        selector.findOperator('PhotonMetDPhi').setMetVariations(metVar)
        
        jetDPhi.setMetVariations(realMetVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        addPUWeight(sample, selector)
        addIDSFWeight(sample, selector)
        addPDFVariation(sample, selector)

        if flavor == ROOT.lElectron:
            addElectronIDSFWeight(sample, selector)
        else:
            addMuonIDSFWeight(sample, selector)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('Met').setIgnoreDecision(True)
    selector.findOperator('Met').setThreshold(100.)
    selector.findOperator('PhotonPtOverMet').setIgnoreDecision(True)

    return selector

#####################
# DERIVED SELECTORS #
#####################

def monoph(sample, rname):
    """
    Full monophoton selection.
    """

    selector = monophotonBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    if not sample.data:
        addIDSFWeight(sample, selector)

    return selector

def monophNoE(sample, rname):
    """
    Full monophoton selection filtering out electron events.
    """

    selector = monophotonBase(sample, rname, selcls = ROOT.PartonSelector)
    selector.setRejectedPdgId(11)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    addIDSFWeight(sample, selector)

    return selector

def monophNoLVeto(sample, rname):
    """
    Full monophoton selection without lepton veto (for lepton veto eff. scale factor measurement)
    """

    selector = monoph(sample, rname)

    selector.findOperator('LeptonSelection').setIgnoreDecision(True)

    return selector

def monophNoGSFix(sample, rname):
    """
    Full monophoton selection using originalPt / pt * scRawPt
    """

    selector = monoph(sample, rname)

    # replaces outPhoton.scRawPt with originalPt / pt * scRawPt
    # all downstream operators should be using outPhoton
    selector.findOperator('PhotonSelection').setUseOriginalPt(True)

    # copy metMuOnlyFix instead of t1Met
    selector.findOperator('CopyMet').setUseGSFix(False)

    return selector

def signalRaw(sample, rname):
    """
    Ignore decisions of all cuts to compare shapes for different simulations.
    """

    selector = monoph(sample, rname)

    selector.setPreskim('')

    cuts = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'PhotonMetDPhi',
        'JetMetDPhi',
        'Met'
    ]

    for cut in cuts:
        selector.findOperator(cut).setIgnoreDecision(True)

    selector.findOperator('PhotonSelection').setMinPt(30.)
    selector.findOperator('LeptonSelection').setN(0, 0)
    
    dimuMass = ROOT.Mass()
    dimuMass.setPrefix('dimu')
    dimuMass.setMin(60.)
    dimuMass.setMax(120.)
    dimuMass.setCollection1(ROOT.cMuons)
    dimuMass.setCollection2(ROOT.cMuons)
    dimuMass.setIgnoreDecision(True)
    selector.addOperator(dimuMass)

    dielMass = ROOT.Mass()
    dielMass.setPrefix('diel')
    dielMass.setMin(60.)
    dielMass.setMax(120.)
    dielMass.setCollection1(ROOT.cElectrons)
    dielMass.setCollection2(ROOT.cElectrons)
    dielMass.setIgnoreDecision(True)
    selector.addOperator(dielMass)

    return selector

def efake(sample, rname):
    """
    Candidate-like but with inverted electron veto
    """

    selector = monophotonBase(sample, rname)

    modEfake(selector, selections = ['!EVeto'])

    return selector

def emjet(sample, rname):
    """
    EM Object is candidate-like. used for photon purity measurement and hadronTFactor derivation.
    """

    selector = emjetBase(sample, rname)

    if not sample.data:
        # measure the parton-level dR between gamma and q/g.
        selector.addOperator(ROOT.GJetsDR())

    photonSel = selector.findOperator('PhotonSelection')
    
    setupPhotonSelection(photonSel, changes = ['-Sieie', '+Sieie15', '-CHIsoMax', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose', '-EVeto', '-MIP49', '-Time', '-SieieNonzero', '-SipipNonzero'])
        
    return selector

def hfake(sample, rname):
    """
    Candidate-like but with inverted CHIso.
    """

    selector = monophotonBase(sample, rname)

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyTightWeight = getFromFile(filename, 'tfactTight', 'tfactTight' + suffix)
    hadproxyLooseWeight = getFromFile(filename, 'tfactLoose', 'tfactLoose' + suffix)
    hadproxyPurityUpWeight = getFromFile(filename, 'tfactNomPurityUp', 'tfactNomPurityUp' + suffix)
    hadproxyPurityDownWeight = getFromFile(filename, 'tfactNomPurityDown', 'tfactNomPurityDown' + suffix)

    modHfake(selector)

    weight = selector.findOperator('hadProxyWeight')

    weight.addVariation('proxyDefUp', hadproxyTightWeight)
    weight.addVariation('proxyDefDown', hadproxyLooseWeight)
    weight.addVariation('purityUp', hadproxyPurityUpWeight)
    weight.addVariation('purityDown', hadproxyPurityDownWeight)

    photonSel = selector.findOperator('PhotonSelection')

    # Need to keep the cuts looser than nominal to accommodate proxyDefUp & Down
    # Proper cut applied at plotconfig as variations
    setupPhotonSelection(photonSel, changes = ['!CHIsoMax', '+CHIsoMax11', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def hfakeVtx(sample, rname):
    """
    Candidate-like but with inverted CHIso and vertex-adjusted proxy weighting.
    """

    selector = monophotonBase(sample, rname)

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyTightWeight = getFromFile(filename, 'tfactTight', 'tfactTight' + suffix)
    hadproxyLooseWeight = getFromFile(filename, 'tfactLoose', 'tfactLoose' + suffix)
    hadproxyPurityUpWeight = getFromFile(filename, 'tfactNomPurityUp', 'tfactNomPurityUp' + suffix)
    hadproxyPurityDownWeight = getFromFile(filename, 'tfactNomPurityDown', 'tfactNomPurityDown' + suffix)

    isoTFactor = getFromFile(filename, 'tfactNom', 'tfactNom' + suffix)
    noIsoTFactor = getFromFile(datadir + '/hadronTFactorNoICH.root', 'tfactNom')
    isoVertexScore = getFromFile(datadir + '/vertex_scores.root', 'iso')
    noIsoVertexScore = getFromFile(datadir + '/vertex_scores.root', 'noIso')
    rcProb = getFromFile(datadir + '/randomcone.root', 'chIso')

    vtxWeight = ROOT.VtxAdjustedJetProxyWeight(isoTFactor, isoVertexScore, noIsoTFactor, noIsoVertexScore)

    vtxWeight.setRCProb(rcProb, 1.163)
    vtxWeight.addVariation('proxyDefUp', hadproxyTightWeight)
    vtxWeight.addVariation('proxyDefDown', hadproxyLooseWeight)
    vtxWeight.addVariation('purityUp', hadproxyPurityUpWeight)
    vtxWeight.addVariation('purityDown', hadproxyPurityDownWeight)

    selector.addOperator(vtxWeight)

    photonSel = selector.findOperator('PhotonSelection')

    # Need to keep the cuts looser than nominal to accommodate proxyDefUp & Down
    # Proper cut applied at plotconfig as variations
    setupPhotonSelection(photonSel, changes = ['!CHIsoMax', '+CHIsoMax11', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def gjets(sample, rname):
    """
    For GJets MC study. 
    """
    
    selector = emjetBase(sample, rname)

    if not sample.data:
        # measure the parton-level dR between gamma and q/g.
        selector.addOperator(ROOT.GJetsDR())

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = ['-Sieie', '-CHIsoMax', '+Sieie15', '+CHIsoMax11'])
    photonSel.addSelection(False, ROOT.PhotonSelection.Sieie12, ROOT.PhotonSelection.CHIso)
    setupPhotonSelection(photonSel, veto = True)
    
    return selector

def gjets325(sample, rname):
    """
    For GJets MC study. 
    """
    
    selector = emjetBase(sample, rname)

    selector.setPreskim('superClusters.rawPt > 300. && TMath::Abs(superClusters.eta) < 1.4442')

    jets = selector.findOperator('HighPtJetSelection')
    jets.setIgnoreDecision(True)

    if not sample.data:
        # measure the parton-level dR between gamma and q/g.
        selector.addOperator(ROOT.GJetsDR())

    photonSel = selector.findOperator('PhotonSelection')
    setupPhotonSelection(photonSel)
    photonSel.setMinPt(325.)
    
    return selector

def gjSmeared(sample, rname):
    """
    Candidate-like, with a smeared MET distribution.
    """

    selector = monophotonBase(sample, rname, selcls = ROOT.SmearingSelector)

    params = {}
    paramsFile = file(datadir + '/gjSmearParams_linear.txt', 'r')
    for line in paramsFile:
        param = line.split()
        params[param[0]] = (param[1], param[2])
    paramsFile.close()

    smearing = ROOT.TF1('smearing', 'TMath::Landau(x, [0], [1]*(1. + [2]*x))', 0., 100.)
    mean = params['mean'][0]
    sigmar = params['sigmar'][0]
    alpha = params['alpha'][0]
    smearing.SetParameters(mean, sigmar, alpha) # measured in gjets/smearfit.py
    selector.setNSamples(1)
    selector.setFunction(smearing)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    addIDSFWeight(sample, selector)

    return selector

def dijet(sample, rname):
    """
    Dijet events with no overlap removal for jet vertex score study.
    """

    monophotonSetting()
    
    selector = ROOT.EventSelector(rname)

    selector.setPreskim('superClusters.rawPt > 165. && TMath::Abs(superClusters.eta) < 1.4442')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    photonSel = ROOT.PhotonSelection()
    
    setupPhotonSelection(photonSel, changes = ['!Sieie'])
    setupPhotonSelection(photonSel, veto = True)

    selector.addOperator(photonSel)

    jets = ROOT.JetClustering()
    jets.setMinPt(30.)
    jets.setOverwrite(True)
    selector.addOperator(jets)

    photonSel.setIgnoreDecision(True)

#    jetSel = ROOT.HighPtJetSelection()
#    jetSel.setJetPtCut(150.)
#    jetSel.setNMin(2)
#    jetSel.setNMax(2)
#    selector.addOperator(jetSel)

    selector.addOperator(ROOT.JetScore())

    selector.addOperator(ROOT.CopyMet())

    if not sample.data:
        addPDFVariation(sample, selector)

    return selector

def halo(sample, rname):
    """
    Candidate sample but with inverted MIP cut and halo tag.
    """

    selector = monophotonBase(sample, rname)

    photonSel = selector.findOperator('PhotonSelection')

    # setting up loose to allow variations at plot level
    setupPhotonSelection(photonSel, changes = ['-MIP49', '-Sieie'])
    setupPhotonSelection(photonSel, veto = True)

    selector.findOperator('MetFilters').allowHalo()

    return selector

def trivialShower(sample, rname):
    """
    Candidate sample but with inverted sieie cut.
    """

    selector = monophotonBase(sample, rname)

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = ['-SieieNonzero', '-SipipNonzero'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def diel(sample, rname):
    selector = leptonBase(sample, rname, ROOT.lElectron)
    selector.findOperator('LeptonSelection').setN(2, 0)

    dielMass = ROOT.Mass()
    dielMass.setPrefix('diel')
    dielMass.setMin(60.)
    dielMass.setMax(120.)
    dielMass.setCollection1(ROOT.cElectrons)
    dielMass.setCollection2(ROOT.cElectrons)
    dielMass.setIgnoreDecision(True)
    selector.addOperator(dielMass)

    dielSign = ROOT.OppositeSign()
    dielSign.setPrefix('diel')
    dielSign.setCollection1(ROOT.cElectrons)
    dielSign.setCollection2(ROOT.cElectrons)
    dielSign.setIgnoreDecision(True)
    selector.addOperator(dielSign)

    if not sample.data:
        electronLooseSF = getFromFile(datadir + '/egamma_electron_loose_SF_2016.root', 'EGamma_SF2D', 'electronLooseSF') # x: sc eta, y: pt
        electronTrackSF = getFromFile(datadir + '/egamma_electron_reco_SF_2016.root', 'EGamma_SF2D', 'electronTrackSF') # x: sc eta, y: npv

        idsf = selector.findOperator('ElectronSF')
        idsf.addFactor(electronLooseSF)
        idsf.setNParticles(2)

        track = selector.findOperator('ElectronTrackSF')
        track.addFactor(electronTrackSF)
        track.setNParticles(2)

    return selector

def dielAllPhoton(sample, rname):
    selector = diel(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lElectron)
    selector.addOperator(vtx)

    electrons = selector.findOperator('LeptonSelection')
    electrons.setRequireTight(True)

    photons = selector.findOperator('PhotonSelection')
    photons.resetSelection()
    photons.addSelection(True, ROOT.PhotonSelection.HOverE)

    return selector

def dielHfake(sample, rname):
    selector = diel(sample, rname)
        
    modHfake(selector)

    return selector

def monoel(sample, rname, selcls = None):
    selector = leptonBase(sample, rname, ROOT.lElectron, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(1, 0)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lElectron)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    metCut = ROOT.Met('RealMetCut')
    metCut.setMetSource(ROOT.kInMet)
    metCut.setThreshold(50.)
    metCut.setIgnoreDecision(True)
    selector.addOperator(metCut)

    return selector

def monoelHfake(sample, rname):
    selector = monoel(sample, rname)
    
    modHfake(selector)

    return selector

def monoelEfake(sample, rname):
    selector = monoel(sample, rname, selcls = ROOT.ZeeEventSelector)
    selector.findOperator('LeptonSelection').setStrictEl(False)

    modEfake(selector, selections = ['!EVeto'])

    return selector

def monoelQCD(sample, rname):
    selector = monoel(sample, rname)

    # by inserting FakeElectron before LeptonSelection, electron collection size
    # is already bumped up by the number of fake electrons. LeptonSelection will
    # count the number of output electron collection.
    idx = selector.index('LeptonSelection')
    selector.addOperator(ROOT.FakeElectron(), idx)

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setRequireMedium(False)
    leptonSel.setRequireTight(False)

    return selector

def dimu(sample, rname):
    selector = leptonBase(sample, rname, ROOT.lMuon)
    selector.findOperator('LeptonSelection').setN(0, 2)

    dimuMass = ROOT.Mass()
    dimuMass.setPrefix('dimu')
    dimuMass.setMin(60.)
    dimuMass.setMax(120.)
    dimuMass.setCollection1(ROOT.cMuons)
    dimuMass.setCollection2(ROOT.cMuons)
    dimuMass.setIgnoreDecision(True)
    selector.addOperator(dimuMass)

    dimuSign = ROOT.OppositeSign()
    dimuSign.setPrefix('dimu')
    dimuSign.setCollection1(ROOT.cMuons)
    dimuSign.setCollection2(ROOT.cMuons)
    dimuSign.setIgnoreDecision(True)
    selector.addOperator(dimuSign)

    if not sample.data:
        muonLooseSF = getFromFile(datadir + '/muo_muon_idsf_2016.root', 'Loose_ScaleFactor') # x: abs eta, y: pt
        muonTrackSF = getFromFile(datadir + '/muonpog_muon_tracking_SF_ichep.root', 'htrack2') # x: npv

        idsf = selector.findOperator('MuonSF')
        idsf.addFactor(muonLooseSF)
        idsf.setNParticles(2)

        track = selector.findOperator('MuonTrackSF')
        track.addFactor(muonTrackSF)
        track.setNParticles(2)

    return selector

def dimuAllPhoton(sample, rname):
    selector = dimu(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lMuon)
    selector.addOperator(vtx)

    muons = selector.findOperator('LeptonSelection')
    muons.setRequireTight(False)
    muons.setRequireMedium(True)

    photons = selector.findOperator('PhotonSelection')
    photons.resetSelection()
    photons.addSelection(True, ROOT.PhotonSelection.HOverE)

    return selector

def dimuHfake(sample, rname):
    selector = dimu(sample, rname)

    modHfake(selector)

    return selector

def monomu(sample, rname, selcls = None):
    selector = leptonBase(sample, rname, ROOT.lMuon, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(0, 1)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lMuon)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    return selector

def monomuLowPt(sample, rname, selcls = None):
    selector = leptonBase(sample, rname, ROOT.lMuon, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(0, 1)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lMuon)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    selector.removeOperator(selconf['sphTrigger'])
    selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))
    photons = selector.findOperator('PhotonSelection')
    photons.setMinPt(10.)

    return selector

def monomuAllPhoton(sample, rname):
    selector = monomu(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lMuon)
    selector.addOperator(vtx)

    muons = selector.findOperator('LeptonSelection')
    muons.setRequireMedium(True)

    photons = selector.findOperator('PhotonSelection')
    photons.resetSelection()
    photons.addSelection(True, ROOT.PhotonSelection.HOverE)

    return selector

def monomuHfake(sample, rname):
    selector = monomu(sample, rname)

    modHfake(selector)

    return selector

def monomuEfake(sample, rname):
    selector = monomu(sample, rname)

    modEfake(selector, selections = ['!EVeto'])

    return selector

def wenu(sample, rname):
    """
    Candidate-like selection but for W->enu, no pixel veto on the photon.
    """

    selector = monophotonBase(sample, rname, selcls = ROOT.PartonSelector)
    selector.setRequiredPdgId(11)

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMinPt(15.)

    setupPhotonSelection(photonSel, changes = ['-EVeto'])

    return selector

def monoelVertex(sample, rname):
    """
    Monoel-like selection with e or mu, with LeptonVertex
    """

    selector = monoel(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lElectron)
    selector.addOperator(vtx)

    return selector

def monomuVertex(sample, rname):
    """
    Monomu-like selection with e or mu, with LeptonVertex
    """

    selector = monomu(sample, rname)

    leptons = selector.findOperator('LeptonSelection')
    leptons.setRequireTight(False)
    leptons.setRequireMedium(True)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lMuon)
    selector.addOperator(vtx)

    return selector

def dielVertex(sample, rname):
    """
    Diel-like selection with e or mu, with LeptonVertex
    """

    selector = diel(sample, rname)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lElectron)
    selector.addOperator(vtx)

    return selector

def dimuVertex(sample, rname):
    """
    Dimu-like selection with e or mu, with LeptonVertex
    """

    selector = dimu(sample, rname)

    leptons = selector.findOperator('LeptonSelection')
    leptons.setRequireTight(True)
#    leptons.setRequireMedium(True)

    vtx = ROOT.LeptonVertex()
    vtx.setSpecies(ROOT.lMuon)
    selector.addOperator(vtx)

    return selector

def zeeJets(sample, rname):
    """
    Require Z->ee plus at least one high pt jet.
    """

    selector = TagAndProbeBase(sample, rname)
    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']), 0)

    tnp = selector.findOperator('TagAndProbePairZ')
    tnp.setTagSpecies(ROOT.cElectrons)
    tnp.setProbeSpecies(ROOT.cElectrons)

    b2b = ROOT.ZJetBackToBack()
    b2b.setTagAndProbePairZ(selector.findOperator('TagAndProbePairZ'))
    b2b.setMinJetPt(100.)
    b2b.setMinDeltaPhi(3.)
    selector.addOperator(b2b)

    return selector

def zmmJets(sample, rname):
    """
    Require Z->mumu plus at least one high pt jet.
    """

    selector = TagAndProbeBase(sample, rname)
    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']), 0)

    tnp = selector.findOperator('TagAndProbePairZ')
    tnp.setTagSpecies(ROOT.cMuons)
    tnp.setProbeSpecies(ROOT.cMuons)

    b2b = ROOT.ZJetBackToBack()
    b2b.setTagAndProbePairZ(selector.findOperator('TagAndProbePairZ'))
    b2b.setMinJetPt(100.)
    b2b.setMinDeltaPhi(3.)
    selector.addOperator(b2b)

    return selector

def tpeg(sample, rname):
    """
    Electron + photon tag & probe run on SinglePhoton dataset.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTPEG)

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    tp = ROOT.TPLeptonPhoton(ROOT.kTPEG)
    if sample.data:
        tp.setProbeTriggerMatch(True)
        tp.setYear(int(config.year))

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTPEG))

    return selector

def tpmg(sample, rname):
    """
    Muon + photon tag & probe run on SinglePhoton dataset.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTPMG)

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['sphTrigger']))

    tp = ROOT.TPLeptonPhoton(ROOT.kTPMG)
    if sample.data:
        tp.setProbeTriggerMatch(True)
        tp.setYear(int(config.year))

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTPMG))

    return selector

def tpegLowPt(sample, rname):
    """
    Electron + photon tag & probe run on SingleElectron dataset or MC.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTPEG)

    selector.setPreskim('Sum$(superClusters.rawPt > 25.) != 0')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']))

    tp = ROOT.TPLeptonPhoton(ROOT.kTPEG)
    tp.setMinProbePt(25.)
    if sample.data:
        tp.setMinTagPt(30.)
        tp.setTagTriggerMatch(True)
        tp.setYear(int(config.year))

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTPEG))

    return selector

def tpmgLowPt(sample, rname):
    """
    Muon + photon tag & probe run on SingleMuon dataset or MC.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTPMG)

    selector.setPreskim('Sum$(superClusters.rawPt > 25.) != 0')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    tp = ROOT.TPLeptonPhoton(ROOT.kTPMG)
    tp.setMinProbePt(25.)
    if sample.data:
        tp.setMinTagPt(30.)
        tp.setTagTriggerMatch(True)
        tp.setYear(int(config.year))

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTPMG))

    return selector

def tpmmg(sample, rname):
    """
    Dimuon + photon tag & probe.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTPMMG)

    selector.setPreskim('Sum$(superClusters.rawPt > 25.) != 0')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    tp = ROOT.TPLeptonPhoton(ROOT.kTPMMG)
    tp.setMinProbePt(25.)
    tp.setMinTagPt(30.)
    tp.setTagTriggerMatch(True)
    tp.setYear(int(config.year))

    selector.addOperator(tp)

    # for lepton veto efficiency measurement; just write electron and muon sizes
    veto = ROOT.TPLeptonVeto(ROOT.kTPMMG)
    veto.setIgnoreDecision(True)
    selector.addOperator(veto)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTPMMG))

    return selector

def tp2e(sample, rname):
    """
    Dielectron T&P.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTP2E)

    selector.setPreskim('electrons.size > 1')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']))

    tp = ROOT.TPDilepton(ROOT.kTP2E)
    tp.setMinProbePt(25.)
    tp.setMinTagPt(35.)
    tp.setTagTriggerMatch(True)
    tp.setYear(int(config.year))

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTP2E))

    return selector

def tp2m(sample, rname):
    """
    Dimuon T&P.
    """

    selector = tagprobeBase(sample, rname)
    selector.setOutEventType(ROOT.kTP2M)

    selector.setPreskim('muons.size > 1')

    if sample.data:
        selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    tp = ROOT.TPDilepton(ROOT.kTP2M)
    tp.setMinProbePt(25.)
    tp.setMinTagPt(30.)
    tp.setTagTriggerMatch(True)
    tp.setYear(int(config.year))

    selector.addOperator(tp)

    selector.addOperator(ROOT.TPJetCleaning(ROOT.kTP2M))

    return selector

def vbfg(sample, rname):
    """
    VBF + photon candidate sample.
    """

    selector = vbfgBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    if not sample.data:
        digenjetSel = ROOT.DijetSelection('DigenjetSelection')
        digenjetSel.setMinDEta(0.)
        digenjetSel.setMinMjj(0.)
        digenjetSel.setJetType(ROOT.DijetSelection.jGen)
        selector.addOperator(digenjetSel)

        addIDSFWeight(sample, selector)

#        if sample.name.startswith('gj'):
#            dijetSel = selector.findOperator('DijetSelection')
#            plots = ROOT.TFile.Open('/data/t3home000/yiiyama/monophoton/plots/vbfgloCtrl.root')
#            dijetSel.setDEtajjReweight(plots)

    return selector

def vbfgCtrl(sample, rname):
    """
    VBF + photon control sample.
    """

    selector = vbfg(sample, rname)

    selector.setPreskim('superClusters.rawPt > 80.')

    selector.removeOperator(selconf['vbfTrigger'])
    selector.addOperator(ROOT.HLTFilter(selconf['vbfCtrlTrigger']))

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(0.)
    dijetSel.setMinMjj(0.)

    return selector

def vbfgLJCtrl(sample, rname):
    """
    VBF + photon control sample using leading 2 jets only.
    """

    selector = vbfgCtrl(sample, rname)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setLeadingOnly(True)

    return selector

def vbfgEfake(sample, rname):
    """
    VBF + photon e->photon fake control sample.
    """

    selector = vbfgBase(sample, rname)

    modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def vbfgHfake(sample, rname):
    """
    VBF + photon had->photon fake control sample.
    """

    selector = vbfgBase(sample, rname)

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyTightWeight = getFromFile(filename, 'tfactTight', 'tfactTight' + suffix)
    hadproxyLooseWeight = getFromFile(filename, 'tfactLoose', 'tfactLoose' + suffix)
    hadproxyPurityUpWeight = getFromFile(filename, 'tfactNomPurityUp', 'tfactNomPurityUp' + suffix)
    hadproxyPurityDownWeight = getFromFile(filename, 'tfactNomPurityDown', 'tfactNomPurityDown' + suffix)

    modHfake(selector)

    weight = selector.findOperator('hadProxyWeight')

    weight.addVariation('proxyDefUp', hadproxyTightWeight)
    weight.addVariation('proxyDefDown', hadproxyLooseWeight)
    weight.addVariation('purityUp', hadproxyPurityUpWeight)
    weight.addVariation('purityDown', hadproxyPurityDownWeight)

    photonSel = selector.findOperator('PhotonSelection')

    # Need to keep the cuts looser than nominal to accommodate proxyDefUp & Down
    # Proper cut applied at plotconfig as variations
    setupPhotonSelection(photonSel, changes = ['!CHIso', '+CHIso11', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def vbfgHfakeCtrl(sample, rname):
    """
    VBF + photon had->photon fake control sample (low MET).
    """

    selector = vbfgBase(sample, rname)

    selector.setPreskim('superClusters.rawPt > 80.')

    selector.removeOperator(selconf['vbfTrigger'])
    selector.addOperator(ROOT.HLTFilter(selconf['vbfCtrlTrigger']))

    selector.findOperator('DijetSelection').setIgnoreDecision(True)

    # fake rate function obtained from hadron_fake/direct.py
    hproxyWeight = ROOT.TF1('hproxyWeight', 'TMath::Exp(-0.0173 * x - 0.178)', 80., 600.)

    weight = ROOT.PhotonPtWeight(hproxyWeight, 'vbfhtfactor')
    selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = selconf['hadronProxyDef'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def vbfgWHadCtrl(sample, rname):
    """
    VBF + photon control sample for Wgamma, replacing the lepton and neutrino with jets.
    """

    selector = vbfg(sample, rname)

    selector.setPreskim('superClusters.rawPt > 80.')

    selector.removeOperator(selconf['vbfTrigger'])
    selector.addOperator(ROOT.HLTFilter(selconf['vbfCtrlTrigger']))

    selector.findOperator('DijetSelection').setIgnoreDecision(True)

    ijet = selector.index('JetCleaning')
    selector.addOperator(ROOT.WHadronizer(), ijet)

    return selector

def vbfem(sample, rname):
    """
    VBF + EM jet.
    """

    selector = vbfgBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'), changes = ['-Sieie', '+Sieie15', '-CHIso', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose', '-EVeto'])

    if not sample.data:
        addIDSFWeight(sample, selector)

    return selector

def vbfzee(sample, rname):
    """
    VBF + Zee sample for e-fake validation.
    """

    selector = vbfgBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    if not sample.data:
        addIDSFWeight(sample, selector)

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(1, 0)

    return selector

def vbfzeeEfake(sample, rname):
    """
    VBF + Zee sample for e-fake validation.
    """

    selector = vbfzee(sample, rname)

    modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def vbfe(sample, rname):
    """
    VBF + single electron.
    """

    selector = vbflBase(sample, rname)

    selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']))

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(1, 0)

    return selector

def vbfm(sample, rname):
    """
    VBF + single muon.
    """

    selector = vbflBase(sample, rname)

    selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 1)

    return selector

def vbfee(sample, rname):
    """
    VBF + double electron.
    """

    selector = vbflBase(sample, rname)

    selector.addOperator(ROOT.HLTFilter(selconf['selTrigger']))

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(2, 0)

    return selector

def vbfmm(sample, rname):
    """
    VBF + single muon.
    """

    selector = vbflBase(sample, rname)

    selector.addOperator(ROOT.HLTFilter(selconf['smuTrigger']))

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 2)

    return selector

def ph75(sample, rname):
    selector = ROOT.EventSelector(rname)
    vbfgSetting()

    selector.setPreskim('superClusters.rawPt > 50.')

    selector.addOperator(ROOT.HLTFilter('HLT_Photon50_OR_HLT_Photon75'))

    hltph50 = ROOT.HLTFilter('HLT_Photon50')
    hltph50.setIgnoreDecision(True)
    selector.addOperator(hltph50)
    hltph75 = ROOT.HLTFilter('HLT_Photon75')
    hltph75.setIgnoreDecision(True)
    selector.addOperator(hltph75)
    hltph75vbf = ROOT.HLTFilter(selconf['vbfTrigger'])
    hltph75vbf.setIgnoreDecision(True)
    selector.addOperator(hltph75vbf)

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'BjetVeto',
        'CopyMet',
        'CopySuperClusters'
    ]

    if not sample.data:
        operators.append('MetVariations')
        
    operators += [
        'PhotonMetDPhi',
        'JetMetDPhi',
        'PhotonJetDPhi',
        'PhotonMt',
        'DijetSelection'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMinPt(50.)
    photonSel.setIDTune(selconf['photonIDTune'])
    photonSel.setWP(selconf['photonWP'])
    setupPhotonSelection(photonSel, changes = ['-Sieie', '-CHIso', '+Sieie15', '+CHIso11'])

    leptonSel = selector.findOperator('LeptonSelection')
    leptonSel.setN(0, 0)
    leptonSel.setRequireMedium(False)
    leptonSel.setRequireTight(False)

    dijetSel = selector.findOperator('DijetSelection')
    dijetSel.setMinDEta(3.)
    dijetSel.setMinMjj(500.)
    dijetSel.setIgnoreDecision(True)

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        metVar.setPhotonSelection(photonSel)

        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)

        selector.findOperator('PhotonJetDPhi').setMetVariations(metVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))

        addPUWeight(sample, selector)
        addPDFVariation(sample, selector)

        addElectronVetoSFWeight(sample, selector)
        addMuonVetoSFWeight(sample, selector)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('BjetVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.cTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)

    return selector

def gghg(sample, rname):
    """
    GGH + photon candidate sample.
    """

    selector = gghgBase(sample, rname)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    if not sample.data:
        addIDSFWeight(sample, selector)

    return selector

def gghgNoE(sample, rname):
    """
    Full monophoton selection filtering out electron events.
    """

    selector = gghgBase(sample, rname, selcls = ROOT.PartonSelector)
    selector.setRejectedPdgId(11)

    setupPhotonSelection(selector.findOperator('PhotonSelection'))

    addIDSFWeight(sample, selector)

    return selector

def gghgNoGSFix(sample, rname):
    """
    Full monophoton selection using originalPt / pt * scRawPt
    """

    selector = gghg(sample, rname)

    # replaces outPhoton.scRawPt with originalPt / pt * scRawPt
    # all downstream operators should be using outPhoton
    selector.findOperator('PhotonSelection').setUseOriginalPt(True)

    # copy metMuOnlyFix instead of t1Met
    selector.findOperator('CopyMet').setUseGSFix(False)

    return selector

def fakeMetRandom(sample, rname):
    """
    Full monophoton selection with a random fraction of photon energy lost to MET.
    """

    selector = gghg(sample, rname)

    fakeMet = ROOT.PhotonFakeMet()
    selector.addOperator(fakeMet, selector.index('CopyMet')+1)

    return selector

def fakeMet25(sample, rname):
    """
    Full monophoton selection without with 25% of photon energy lost to MET.
    """

    selector = gghg(sample, rname)

    fakeMet = ROOT.PhotonFakeMet()
    fakeMet.setFraction(0.25)
    selector.addOperator(fakeMet, selector.index('CopyMet')+1)

    return selector

def fakeMet50(sample, rname):
    """
    Full monophoton selection without with 50% of photon energy lost to MET.
    """

    selector = gghg(sample, rname)

    fakeMet = ROOT.PhotonFakeMet()
    fakeMet.setFraction(0.50)
    selector.addOperator(fakeMet, selector.index('CopyMet')+1)

    return selector

def fakeMet75(sample, rname):
    """
    Full monophoton selection without with 75% of photon energy lost to MET.
    """

    selector = gghg(sample, rname)

    fakeMet = ROOT.PhotonFakeMet()
    fakeMet.setFraction(0.75)
    selector.addOperator(fakeMet, selector.index('CopyMet')+1)

    return selector

def gghEfake(sample, rname):
    """
    GGH + photon e->photon fake control sample.
    """

    selector = gghgBase(sample, rname)

    modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def gghHfake(sample, rname):
    """
    GGH + photon had->photon fake control sample.
    """

    selector = gghgBase(sample, rname)

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyTightWeight = getFromFile(filename, 'tfactTight', 'tfactTight' + suffix)
    hadproxyLooseWeight = getFromFile(filename, 'tfactLoose', 'tfactLoose' + suffix)
    hadproxyPurityUpWeight = getFromFile(filename, 'tfactNomPurityUp', 'tfactNomPurityUp' + suffix)
    hadproxyPurityDownWeight = getFromFile(filename, 'tfactNomPurityDown', 'tfactNomPurityDown' + suffix)

    modHfake(selector)

    weight = selector.findOperator('hadProxyWeight')

    weight.addVariation('proxyDefUp', hadproxyTightWeight)
    weight.addVariation('proxyDefDown', hadproxyLooseWeight)
    weight.addVariation('purityUp', hadproxyPurityUpWeight)
    weight.addVariation('purityDown', hadproxyPurityDownWeight)

    photonSel = selector.findOperator('PhotonSelection')

    # Need to keep the cuts looser than nominal to accommodate proxyDefUp & Down
    # Proper cut applied at plotconfig as variations
    setupPhotonSelection(photonSel, changes = ['!CHIso', '+CHIso11', '-NHIso', '+NHIsoLoose', '-PhIso', '+PhIsoLoose'])
    setupPhotonSelection(photonSel, veto = True)

    return selector

def gghe(sample, rname, selcls = None):
    """
    GGH + single electron.
    """

    selector = gghlBase(sample, rname, ROOT.lElectron, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(1, 0)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lElectron)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    metCut = ROOT.Met('RealMetCut')
    metCut.setMetSource(ROOT.kInMet)
    metCut.setThreshold(50.)
    metCut.setIgnoreDecision(True)
    selector.addOperator(metCut)

    return selector

def ggheEfake(sample, rname):
    selector = gghe(sample, rname, selcls = ROOT.ZeeEventSelector)

    modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def ggheHfake(sample, rname):
    selector = gghe(sample, rname)

    modHfake(selector)

    return selector

def gghm(sample, rname, selcls = None):
    """
    GGH + single muon.
    """

    selector = gghlBase(sample, rname, ROOT.lMuon, selcls = selcls)
    selector.findOperator('LeptonSelection').setN(0, 1)

    mtCut = ROOT.LeptonMt()
    mtCut.setFlavor(ROOT.lMuon)
    mtCut.setMax(160.)
    mtCut.setIgnoreDecision(True)
    selector.addOperator(mtCut)

    return selector

def gghmEfake(sample, rname):
    selector = gghm(sample, rname)

    modEfake(selector, selections = ['!CSafeVeto'])

    return selector

def gghmHfake(sample, rname):
    selector = gghm(sample, rname)

    modHfake(selector)

    return selector

def gghee(sample, rname):
    """
    GGH + double electron.
    """

    selector = gghlBase(sample, rname, ROOT.lElectron)
    selector.findOperator('LeptonSelection').setN(2, 0)

    dielMass = ROOT.Mass()
    dielMass.setPrefix('diel')
    dielMass.setMin(60.)
    dielMass.setMax(120.)
    dielMass.setCollection1(ROOT.cElectrons)
    dielMass.setCollection2(ROOT.cElectrons)
    dielMass.setIgnoreDecision(True)
    selector.addOperator(dielMass)

    dielSign = ROOT.OppositeSign()
    dielSign.setPrefix('diel')
    dielSign.setCollection1(ROOT.cElectrons)
    dielSign.setCollection2(ROOT.cElectrons)
    dielSign.setIgnoreDecision(True)
    selector.addOperator(dielSign)

    if not sample.data:
        electronLooseSF = getFromFile(datadir + '/egamma_electron_loose_SF_2016.root', 'EGamma_SF2D', 'electronLooseSF') # x: sc eta, y: pt
        electronTrackSF = getFromFile(datadir + '/egamma_electron_reco_SF_2016.root', 'EGamma_SF2D', 'electronTrackSF') # x: sc eta, y: npv

        idsf = selector.findOperator('ElectronSF')
        idsf.addFactor(electronLooseSF)
        idsf.setNParticles(2)

        track = selector.findOperator('ElectronTrackSF')
        track.addFactor(electronTrackSF)
        track.setNParticles(2)

    return selector

def gghmm(sample, rname):
    """
    GGH + single muon.
    """

    selector = gghlBase(sample, rname, ROOT.lMuon)
    selector.findOperator('LeptonSelection').setN(0, 2)

    dimuMass = ROOT.Mass()
    dimuMass.setPrefix('dimu')
    dimuMass.setMin(60.)
    dimuMass.setMax(120.)
    dimuMass.setCollection1(ROOT.cMuons)
    dimuMass.setCollection2(ROOT.cMuons)
    dimuMass.setIgnoreDecision(True)
    selector.addOperator(dimuMass)

    dimuSign = ROOT.OppositeSign()
    dimuSign.setPrefix('dimu')
    dimuSign.setCollection1(ROOT.cMuons)
    dimuSign.setCollection2(ROOT.cMuons)
    dimuSign.setIgnoreDecision(True)
    selector.addOperator(dimuSign)

    if not sample.data:
        muonLooseSF = getFromFile(datadir + '/muo_muon_looseid_2016.root', 'Loose_ScaleFactor') # x: abs eta, y: pt
        muonTrackSF = getFromFile(datadir + '/muonpog_muon_tracking_SF_ichep.root', 'htrack2') # x: npv

        idsf = selector.findOperator('MuonSF')
        idsf.addFactor(muonLooseSF)
        idsf.setNParticles(2)

        track = selector.findOperator('MuonTrackSF')
        track.addFactor(muonTrackSF)
        track.setNParticles(2)

    return selector

def monoph250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = monoph(sample, rname)
    monophEWKSetting(250)

    return selector

def monoph300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = monoph(sample, rname)
    monophEWKSetting(300)

    return selector

def monoph400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = monoph(sample, rname)
    monophEWKSetting(400)

    return selector

def monoph500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = monoph(sample, rname)
    monophEWKSetting(500)

    return selector

def monoph600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = monoph(sample, rname)
    monophEWKSetting(600)

    return selector

def dimu250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = dimu(sample, rname)
    monophEWKSetting(250)

    return selector

def dimu300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = dimu(sample, rname)
    monophEWKSetting(300)

    return selector

def dimu400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = dimu(sample, rname)
    monophEWKSetting(400)

    return selector

def dimu500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = dimu(sample, rname)
    monophEWKSetting(500)

    return selector

def dimu600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = dimu(sample, rname)
    monophEWKSetting(600)

    return selector

def diel250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = diel(sample, rname)
    monophEWKSetting(250)

    return selector

def diel300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = diel(sample, rname)
    monophEWKSetting(300)

    return selector

def diel400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = diel(sample, rname)
    monophEWKSetting(400)

    return selector

def diel500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = diel(sample, rname)
    monophEWKSetting(500)

    return selector

def diel600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = diel(sample, rname)
    monophEWKSetting(600)

    return selector

def monomu250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = monomu(sample, rname)
    monophEWKSetting(250)

    return selector

def monomu300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = monomu(sample, rname)
    monophEWKSetting(300)

    return selector

def monomu400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = monomu(sample, rname)
    monophEWKSetting(400)

    return selector

def monomu500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = monomu(sample, rname)
    monophEWKSetting(500)

    return selector

def monomu600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = monomu(sample, rname)
    monophEWKSetting(600)

    return selector

def monoel250(sample, rname):
    """
    EWK shape inflection point at 250 GeV
    """
    
    selector = monoel(sample, rname)
    monophEWKSetting(250)

    return selector

def monoel300(sample, rname):
    """
    EWK shape inflection point at 300 GeV
    """
    
    selector = monoel(sample, rname)
    monophEWKSetting(300)

    return selector

def monoel400(sample, rname):
    """
    EWK shape inflection point at 400 GeV
    """
    
    selector = monoel(sample, rname)
    monophEWKSetting(400)

    return selector

def monoel500(sample, rname):
    """
    EWK shape inflection point at 500 GeV
    """
    
    selector = monoel(sample, rname)
    monophEWKSetting(500)

    return selector

def monoel600(sample, rname):
    """
    EWK shape inflection point at 600 GeV
    """
    
    selector = monoel(sample, rname)
    monophEWKSetting(600)

    return selector

######################
# SELECTOR MODIFIERS #
######################

def addPUWeight(sample, selector):
    pudirName, pufileName = selconf['puweightSource']

    pudir = ROOT.gROOT.GetDirectory(pudirName)

    if not pudir:
        pudir = ROOT.gROOT.mkdir(pudirName)
        logger.info('Loading PU weights from %s', pufileName)
        f = ROOT.TFile.Open(pufileName)
        for k in f.GetListOfKeys():
            if k.GetName().startswith('puweight_'):
                logger.info('Saving PU weights %s into ROOT/%s', k.GetName(), pudirName)
                pudir.cd()
                obj = k.ReadObj().Clone(k.GetName().replace('puweight_', ''))
                _garbage.append(obj)
        
        f.Close()

    for hist in pudir.GetList():
        if hist.GetName() in sample.fullname:
            logger.info('Using PU weights %s/%s for %s', pudirName, hist.GetName(), sample.name)
            selector.addOperator(ROOT.PUWeight(hist))
            break
    else:
        raise RuntimeError('Pileup profile for ' + sample.name + ' not defined')

def addIDSFWeight(sample, selector):
    x, y, variables, (pvSF, pvUnc) = selconf['photonSF']

    if type(x) is str and type(y) is str:
        filename, histname = x, y
        logger.info('Adding photon ID scale factor from ' + filename)
    
        idsf = ROOT.IDSFWeight(ROOT.cPhotons, 'photonSF')
        idsf.addFactor(getFromFile(filename, histname, newname = 'photonSF'))
        idsf.setVariable(*variables)
        selector.addOperator(idsf)
    
    else:
        sf, unc = x, y
        logger.info('Adding numeric photon ID scale factor')

        idsf = ROOT.ConstantWeight(sf, 'photonSF')
        idsf.setUncertaintyUp(unc)
        idsf.setUncertaintyDown(unc)
        selector.addOperator(idsf)

    pvsf = ROOT.ConstantWeight(pvSF, 'pixelVetoSF')
    pvsf.setUncertaintyUp(pvUnc)
    pvsf.setUncertaintyDown(pvUnc)
    selector.addOperator(pvsf)

def addElectronIDSFWeight(sample, selector):
    logger.info('Adding electron ID scale factor (ICHEP)')

    electronTightSF = getFromFile(datadir + '/egamma_electron_tight_SF_2016.root', 'EGamma_SF2D', 'electronTightSF') # x: sc eta, y: pt
    electronTrackSF = getFromFile(datadir + '/egamma_electron_reco_SF_2016.root', 'EGamma_SF2D', 'electronTrackSF') # x: sc eta, y: npv

    idsf = ROOT.IDSFWeight(ROOT.cElectrons, 'ElectronSF')
    idsf.addFactor(electronTightSF)
    idsf.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kPt)
    selector.addOperator(idsf)

    track = ROOT.IDSFWeight(ROOT.cElectrons, 'ElectronTrackSF')
    track.addFactor(electronTrackSF)
    track.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kNpv)
    selector.addOperator(track)

def addMuonIDSFWeight(sample, selector):
    logger.info('Adding muon ID scale factor (ICHEP)')

    muonTightSF = getFromFile(datadir + '/muo_muon_idsf_2016.root', 'Tight_ScaleFactor', 'muonTightSF') # x: abs eta, y: pt
    muonTrackSF = getFromFile(datadir + '/muonpog_muon_tracking_SF_ichep.root', 'htrack2', 'muonTrackSF',) # x: npv

    idsf = ROOT.IDSFWeight(ROOT.cMuons, 'MuonSF')
    idsf.addFactor(muonTightSF)
    idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
    selector.addOperator(idsf)

    track = ROOT.IDSFWeight(ROOT.cMuons, 'MuonTrackSF')
    track.addFactor(muonTrackSF)
    track.setVariable(ROOT.IDSFWeight.kNpv)
    selector.addOperator(track)

def addElectronVetoSFWeight(sample, selector):
    logger.info('Adding electron veto scale factor (ICHEP)')

    # made using misc/SFmerge.py
    electronVetoSF = getFromFile(datadir + '/egamma_electron_veto_SF_2016.root', 'EGamma_VetoSF2D', 'electronVetoSF') # x: sc eta, y: pt

    idsf = ROOT.IDSFWeight(ROOT.nCollections, 'ElectronVetoSF')
    failingElectrons = selector.findOperator('LeptonSelection').getFailingElectrons()
    idsf.addCustomCollection(failingElectrons)
    idsf.addFactor(electronVetoSF)
    idsf.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kPt)
    selector.addOperator(idsf)

def addMuonVetoSFWeight(sample, selector):
    logger.info('Adding muon veto scale factor (ICHEP)')

    # made using misc/SFmerge.py
    muonVetoSF = getFromFile(datadir + '/muo_muon_idsf_2016.root', 'LooseVeto_ScaleFactor', 'muonVetoSF') # x: abs eta, y: pt

    idsf = ROOT.IDSFWeight(ROOT.nCollections, 'MuonVetoSF')
    failingMuons = selector.findOperator('LeptonSelection').getFailingMuons()
    idsf.addCustomCollection(failingMuons)
    idsf.addFactor(muonVetoSF)
    idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
    selector.addOperator(idsf)

def addPDFVariation(sample, selector):
    if 'amcatnlo' in sample.fullname or 'madgraph' in sample.fullname: # ouh la la..
        logger.info('Adding PDF variation for %s', sample.name)
        if 'znng' in sample.name or 'zllg' in sample.name:
            pdf = ROOT.NNPDFVariation()
            pdf.setRescale(0.0420942143487 / 0.0769709934685)
            selector.addOperator(pdf)
        elif 'wnlg' in sample.name or 'wglo' in sample.name:
            pdf = ROOT.NNPDFVariation()
            pdf.setRescale(0.0453828335472 / 0.0933792628506)
            selector.addOperator(pdf)
        else:
            selector.addOperator(ROOT.NNPDFVariation())

def addKfactor(sample, selector):
    """
    Apply the k-factor corrections.
    """

    if sample.name in ['znng-130-o', 'zllg-130-o', 'zllg-300-o', 'wnlg-130-o', 'wnlg-130-p']:
        sname = sample.name.replace('-p', '-o').replace('zllg', 'znng').replace('300-o', '130-o')

        print selector
        addQCDKfactor(sample, sname, selector)
        addEWKKfactor(sample, sname, selector)

    elif fnmatch.fnmatch(sample.name, 'gj-*') or fnmatch.fnmatch(sample.name, 'gj04-*') or fnmatch.fnmatch(sample.name, 'gje-*'):
        sname = sample.name.replace('gj04', 'gj').replace('gje', 'gj')

        addQCDKfactor(sample, sname, selector)
    
    elif sample.name == 'wglo':
        corr = ROOT.TF1('kfactor', '1.45', 80., 600.)
        qcd = ROOT.PhotonPtWeight(corr, 'QCDCorrection')
        qcd.setPhotonType(ROOT.PhotonPtWeight.kParton)
        selector.addOperator(qcd)

def addQCDKfactor(sample, sname, selector):
    corr = getFromFile(datadir + '/kfactor.root', sname, newname = sname + '_kfactor')
    if not corr:
        raise RuntimeError('kfactor not found for ' + sample.name)

    qcd = ROOT.PhotonPtWeight(corr, 'QCDCorrection')
    if 'gj-' in sname:
        qcd.setPhotonType(ROOT.PhotonPtWeight.kPostShower)
    else:
        qcd.setPhotonType(ROOT.PhotonPtWeight.kParton)

    for variation in ['renUp', 'renDown', 'facUp', 'facDown', 'scaleUp', 'scaleDown']:
        vcorr = getFromFile(datadir + '/kfactor.root', sname + '_' + variation)
        if vcorr:
            logger.info('applying qcd var %s %s', variation, sample.name)
            qcd.addVariation('qcd' + variation, vcorr)

    selector.addOperator(qcd)

def addEWKKfactor(sample, sname, selector):
    corrFile = selconf['ewkCorrSource']
    print corrFile

    if sname.startswith('znng'):
        logger.info('applying ewk %s', sample.name)

        corr = getFromFile(datadir + '/' + corrFile, sname, newname = sname + '_ewkcorr')
        ewk = ROOT.PhotonPtWeight(corr, 'EWKNLOCorrection')
        ewk.setPhotonType(ROOT.PhotonPtWeight.kParton)

        for variation in ['straightUp', 'straightDown', 'twistedUp', 'twistedDown', 'gammaUp', 'gammaDown']:
            vcorr = getFromFile(datadir + '/' + corrFile, sname + '_' + variation)
            if vcorr:
                logger.info('applying ewk var %s %s', variation, sample.name)
                ewk.addVariation('ewk' + variation, vcorr)

        selector.addOperator(ewk)

    elif sample.name.startswith('wnlg'):
        logger.info('applying ewk %s', sample.name)

        suffix = '_p'
        corrp = getFromFile(datadir + '/' + corrFile, sname + suffix, newname = sname + suffix + '_ewkcorr')
        suffix = '_m'
        corrm = getFromFile(datadir + '/' + corrFile, sname + suffix, newname = sname + suffix + '_ewkcorr')

        ewk = ROOT.PhotonPtWeightSigned(corrp, corrm, 'EWKNLOCorrection')

        for variation in ['straightUp', 'straightDown', 'twistedUp', 'twistedDown', 'gammaUp', 'gammaDown']:
            vcorrp = getFromFile(datadir + '/' + corrFile, sname + '_p_' + variation)
            vcorrm = getFromFile(datadir + '/' + corrFile, sname + '_m_' + variation)
            ewk.addVariation('ewk' + variation, vcorrp, vcorrm)

        selector.addOperator(ewk)

def addGenPhotonVeto(sample, selector):
    veto = ROOT.GenPhotonVeto()
    veto.setMinPt(130.)
    veto.setMinPartonDR(0.5)

    selector.addOperator(veto, 0)

def addPhotonRecoil(sample, selector):
    """Wrapper for diphoton samples to turn them into photon+dark photon
    samples by 'removing' one of the photons and adding it to the MET."""
    selector.addOperator(ROOT.PhotonRecoil())

def setSampleId(sample, selector):
    """Set the sample ID on TagAndProbeSelector."""

    if sample.data:
        selector.setSampleId(0)
    elif sample.name.startswith('dy'):
        selector.setSampleId(1)
    elif sample.name.startswith('tt'):
        selector.setSampleId(2)
    elif sample.name.startswith('wg'):
        selector.setSampleId(3)
    elif sample.name.startswith('gg'):
        selector.setSampleId(4)
    else:
        selector.setSampleId(99)

def modHfake(selector):
    """Append PhotonPtWeight with hadProxyWeight and set up the photon selections."""

    filename, suffix = selconf['hadronTFactorSource']

    hadproxyWeight = getFromFile(filename, 'tfactNom', 'tfactNom' + suffix)

    weight = ROOT.PhotonPtWeight(hadproxyWeight, 'hadProxyWeight')
    weight.setPhotonType(ROOT.PhotonPtWeight.kReco)
    selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = selconf['hadronProxyDef'])
    setupPhotonSelection(photonSel, veto = True)

def modEfake(selector, selections = []):
    """Append PhotonPtWeight with eproxyWeight and set up the photon selections."""

    nom = selconf['electronTFactor']
    unc = selconf['electronTFactorUnc']

    if type(nom) is str:
        # nom = file.root/obj
        filename = nom[:nom.find('.root') + 5]
        objname = nom[nom.find('.root') + 6:]
        logger.info('Adding electron fake rate from %s/%s', filename, objname)
    
        eproxyWeight = getFromFile(filename, objname)
        weight = ROOT.PhotonPtWeight(eproxyWeight, 'egfakerate')
        selector.addOperator(weight)

        if unc:
            if type(unc) is bool:
                weight.useErrors(True) # use errors of eleproxyWeight as syst. variation
            else:
                up = getFromFile(filename, unc + 'Up')
                weight.addVariation('egfakerateUp', up)
                down = getFromFile(filename, unc + 'Down')
                weight.addVariation('egfakerateDown', down)
    
    elif type(nom) is float:
        frate = nom
        logger.info('Adding numeric electron fake rate %f +- %f', frate, unc)

        weight = ROOT.ConstantWeight(frate, 'egfakerate')
        weight.setUncertaintyUp(unc)
        weight.setUncertaintyDown(unc)
        selector.addOperator(weight)

    else:
        logger.info('Adding electron fake rate from TF1 ' + nom.GetTitle())

        # type is TF1
        weight = ROOT.PhotonPtWeight(nom, 'egfakerate')
        selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    setupPhotonSelection(photonSel, changes = selections + ['-EVeto', '-ChargedPFVeto'])
    setupPhotonSelection(photonSel, veto = True)


#######################
# MODIFIER GENERATORS #
#######################

def ptTruncator(minimum = 0., maximum = -1.):
    def addPtCut(sample, selector):
        truncator = ROOT.PhotonPtTruncator()
        truncator.setPtMin(minimum)
        if maximum > 0.:
            truncator.setPtMax(maximum)

        selector.addOperator(truncator, 0)

    return addPtCut

def htTruncator(minimum = 0., maximum = -1.):
    def addHtCut(sample, selector):
        truncator = ROOT.HtTruncator()
        truncator.setHtMin(minimum)
        if maximum > 0.:
            truncator.setHtMax(maximum)

        selector.addOperator(truncator, 0)

    return addHtCut

def genBosonPtTruncator(minimum = 0., maximum = -1.):
    def addGenBosonPtCut(sample, selector):
        truncator = ROOT.GenBosonPtTruncator()
        truncator.setPtMin(minimum)
        if maximum > 0.:
            truncator.setPtMax(maximum)

        selector.addOperator(truncator, 0)

    return addGenBosonPtCut


if needHelp:
    sys.argv.append('--help')
