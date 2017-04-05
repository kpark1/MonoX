#ifndef operators_h
#define operators_h

#include "Objects/interface/EventMonophoton.h"

#include "TH1.h"
#include "TH2.h"
#include "TF1.h"
#include "TRandom3.h"

#include "TDirectory.h"

//#include "jer.h"
#include "eventlist.h"

#include <bitset>
#include <map>
#include <vector>
#include <utility>

//--------------------------------------------------------------------
// Operator catalog
// * = has addBranches
// Operator
//   Cut
//     HLTPhoton165HE10
//     HLTEle27eta2p1WPLooseGs
//     HLTIsoMu27
//     MetFilters
//     GenPhotonVeto
//     PhotonSelection *
//     ElectronVeto
//     MuonVeto
//     TauVeto
//     LeptonMt *
//     Mass *
//     BjetVeto *
//     PhotonMetDPhi *
//     JetMetDPhi *
//     LeptonSelection
//     HighMet
//     MtRange
//     HighPtJetSelection
//     PhotonPtTruncator
//   Modifier
//     JetCleaning *
//     CopyMet
//     PhotonMt *
//     LeptonRecoil *
//     MetVariations *
//     ConstantWeight *
//     PhotonPtWeight *
//     IDSFWeight *
//     NPVWeight
//     NNPDFVariation *
//     GenPhotonDR *
//--------------------------------------------------------------------

enum LeptonFlavor {
  kElectron,
  kMuon,
  nLeptonFlavors
};

enum Collection {
  kPhotons,
  kElectrons,
  kMuons,
  kTaus,
  nCollections
};

enum MetSource {
  kInMet,
  kOutMet
};


const UInt_t NMAX_PARTICLES = 64;

//--------------------------------------------------------------------
// Base classes
//--------------------------------------------------------------------

class Operator {
 public:
  Operator(char const* name) : name_(name) {}
  virtual ~Operator() {}
  char const* name() const { return name_.Data(); }

  virtual bool exec(panda::EventMonophoton const&, panda::EventMonophoton&) = 0;

  virtual void addBranches(TTree& skimTree) {}
  virtual void initialize(panda::EventMonophoton& _event) {}

 protected:
  TString name_;
};

class Cut : public Operator {
 public:
  Cut(char const* name) : Operator(name), result_(false), ignoreDecision_(false) {}
  virtual ~Cut() {}

  bool exec(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  virtual void registerCut(TTree& cutsTree) { cutsTree.Branch(name_, &result_, name_ + "/O"); }
  void setIgnoreDecision(bool b) { ignoreDecision_ = b; }

 protected:
  virtual bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) = 0;

 private:
  bool result_;
  bool ignoreDecision_;
};

class Modifier : public Operator {
 public:
  Modifier(char const* name) : Operator(name) {}
  virtual ~Modifier() {}

  bool exec(panda::EventMonophoton const&, panda::EventMonophoton&) override;

 protected:
  virtual void apply(panda::EventMonophoton const&, panda::EventMonophoton&) = 0;
};

//--------------------------------------------------------------------
// Cuts
//--------------------------------------------------------------------

class HLTFilter : public Cut {
 public:
  HLTFilter(char const* name = "PATHNAME");
  ~HLTFilter();

  void initialize(panda::EventMonophoton& _event) override;
    
 protected:
  bool pass(panda::EventMonophoton const& _event, panda::EventMonophoton&) override;

  TString pathNames_{""};
  std::vector<UInt_t> tokens_;
};


class MetFilters : public Cut {
 public:
  MetFilters(char const* name = "MetFilters") : Cut(name) {}

  // 1->require pass, -1->require fail, 0->ignore
  void setFilter(unsigned filter, int decision) { filterConfig_[filter] = decision; }
  void setEventList(char const* path, int decision);
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  int filterConfig_[6]{1, 1, 1, 1, 1, 1};
  std::vector<std::pair<EventList, int>> eventLists_;
};

class GenPhotonVeto : public Cut {
  /* Veto event if it contains a prompt gen photon */
 public:
  GenPhotonVeto(char const* name = "GenPhotonVeto") : Cut(name) {}

  void setMinPt(double m) { minPt_ = m; }
  void setMinDR(double m) { minDR_ = m; }

 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  double minPt_{130.}; // minimum pt of the gen photon to be vetoed
  double minDR_{0.5}; // minimum dR wrt any parton of the gen photon to be vetoed
};

class PhotonSelection : public Cut {
 public:
  enum Selection {
    HOverE,               // 0
    Sieie,
    NHIso,
    PhIso,
    CHIso,
    CHIsoMax,             // 5
    EVeto,
    CSafeVeto,
    MIP49,
    Time,
    SieieNonzero,         // 10
    SipipNonzero,
    NoisyRegion,
    E2E995,
    Sieie12,
    Sieie15,              // 15
    Sieie20,
    CHIso11,
    CHIsoMax11,
    NHIsoLoose,
    PhIsoLoose,           // 20
    NHIsoTight,
    PhIsoTight,
    Sieie05,
    Sipip05,
    NHIsoS16,             // 25
    PhIsoS16,
    CHIsoS16,
    CHIsoMaxS16,
    NHIsoS16Loose,
    PhIsoS16Loose,        // 30
    CHIsoS16Loose,
    NHIsoS16Tight,
    PhIsoS16Tight,
    nSelections           // 34
  };

  PhotonSelection(char const* name = "PhotonSelection") : Cut(name) {}

  void addBranches(TTree& skimTree) override;
  void registerCut(TTree& cutsTree) override;

  // bool->true: add photon condition "pass one of the selections"
  // bool->false: add photon condition "fail one of the selections"
  // Photons are saved when they match all the conditions
  void addSelection(bool, unsigned, unsigned = nSelections, unsigned = nSelections);
  void resetSelection() { selections_.clear(); }
  void removeSelection(unsigned, unsigned = nSelections, unsigned = nSelections);
  // skip event if there is a photon passing the selection (bool->true) or failing (bool->false)
  void addVeto(bool, unsigned, unsigned = nSelections, unsigned = nSelections);
  void resetVeto() { vetoes_.clear(); }
  void removeVeto(unsigned, unsigned = nSelections, unsigned = nSelections);
  void setMinPt(double minPt) { minPt_ = minPt; }
  void setMaxPt(double maxPt) { maxPt_ = maxPt; }
  void setWP(unsigned wp) { wp_ = wp; }

  double ptVariation(panda::XPhoton const&, bool up);

 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;
  int selectPhoton(panda::XPhoton const&);

  double minPt_{175.};
  double maxPt_{6500.};
  unsigned wp_{0}; // 0 -> loose, 1 -> medium
  float ptVarUp_[NMAX_PARTICLES];
  float ptVarDown_[NMAX_PARTICLES];
  // Will select photons based on the AND of the elements.
  // Within each element, multiple bits are considered as OR.
  typedef std::bitset<nSelections> BitMask;
  typedef std::pair<bool, BitMask> SelectionMask; // pass/fail & bitmask
  std::vector<SelectionMask> selections_;
  std::vector<SelectionMask> vetoes_;
  bool cutRes_[nSelections];

  bool nominalResult_{false};
};

class ElectronVeto : public Cut {
 public:
  ElectronVeto(char const* name = "ElectronVeto") : Cut(name) {}
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;
};

class MuonVeto : public Cut {
 public:
  MuonVeto(char const* name = "MuonVeto") : Cut(name) {}
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;
};

class TauVeto : public Cut {
 public:
  TauVeto(char const* name = "TauVeto") : Cut(name) {}
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;
};

class LeptonMt : public Cut {
 public:
  LeptonMt(char const* name = "LeptonMt") : Cut(name) {}

  void setFlavor(LeptonFlavor flav) { flavor_ = flav; }
  void setMin(double min) { min_ = min; }
  void setMax(double max) { max_ = max; }

 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  LeptonFlavor flavor_;

  double min_{0.};
  double max_{14000.};
};

class Mass : public Cut {
 public:
  Mass(char const* name = "Mass") : Cut(name) {}

  void setPrefix(char const* p) { prefix_ = p; }
  void setCollection1(Collection c) { col_[0] = c; }
  void setCollection2(Collection c) { col_[1] = c; }
  void setMin(double min) { min_ = min; }
  void setMax(double max) { max_ = max; }

  void addBranches(TTree& skimTree) override;

 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  TString prefix_{"generic"};
  Collection col_[2]{nCollections, nCollections};

  float mass_{-1.};
  float pt_{-1.};
  float eta_{-1.};
  float phi_{-1.};
  double min_{0.};
  double max_{14000.};
};

class OppositeSign : public Cut {
 public:
  OppositeSign(char const* name = "OppositeSign") : Cut(name) {}

  void setPrefix(char const* p) { prefix_ = p; }
  void setCollection1(Collection c) { col_[0] = c; }
  void setCollection2(Collection c) { col_[1] = c; }

  void addBranches(TTree& skimTree) override;

 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  TString prefix_{"generic"};
  Collection col_[2]{nCollections, nCollections};

  bool oppSign_{0};
};

class BjetVeto : public Cut {
 public:
  BjetVeto(char const* name = "BjetVeto") : Cut(name), bjets_("bjets") {}

  void addBranches(TTree& skimTree) override;
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  panda::JetCollection bjets_;
};

class MetVariations; // defined below
class JetCleaning; // defined below

class PhotonMetDPhi : public Cut {
 public:
  PhotonMetDPhi(char const* name = "PhotonMetDPhi") : Cut(name) {}
  void addBranches(TTree& skimTree) override;
  void registerCut(TTree& cutsTree) override { cutsTree.Branch(name_, &nominalResult_, name_ + "/O"); }

  void setMetSource(MetSource s) { metSource_ = s; }
  void setMetVariations(MetVariations* v) { metVar_ = v; }
  void invert(bool i) { invert_ = i; }
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  MetSource metSource_{kOutMet};

  float dPhi_{0.};
  float dPhiJECUp_{0.};
  float dPhiJECDown_{0.};
  float dPhiGECUp_{0.};
  float dPhiGECDown_{0.};
  float dPhiUnclUp_{0.};
  float dPhiUnclDown_{0.};
  /* float dPhiJER_{0.}; */
  /* float dPhiJERUp_{0.}; */
  /* float dPhiJERDown_{0.}; */
  MetVariations* metVar_{0};

  bool nominalResult_{false};
  bool invert_{false};
};

class LeptonRecoil;

class JetMetDPhi : public Cut {
 public:
  JetMetDPhi(char const* name = "JetMetDPhi") : Cut(name) {}
  void addBranches(TTree& skimTree) override;
  void registerCut(TTree& cutsTree) override { cutsTree.Branch(name_, &nominalResult_, name_ + "/O"); }

  void setMetSource(MetSource s) { metSource_ = s; }
  void setPassIfIsolated(bool p) { passIfIsolated_ = p; }
  void setMetVariations(MetVariations* v) { metVar_ = v; }
  /* void setJetCleaning(JetCleaning* jcl) { jetCleaning_ = jcl; } */

 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  float dPhi_{0.};
  float dPhiJECUp_{0.};
  float dPhiJECDown_{0.};
  float dPhiGECUp_{0.};
  float dPhiGECDown_{0.};
  float dPhiUnclUp_{0.};
  float dPhiUnclDown_{0.};
  /* float dPhiJER_{0.}; */
  /* float dPhiJERUp_{0.}; */
  /* float dPhiJERDown_{0.}; */

  MetSource metSource_{kOutMet};
  bool passIfIsolated_{true};
  MetVariations* metVar_{0};
  /* JetCleaning* jetCleaning_{0}; */

  bool nominalResult_;
};

class LeptonSelection : public Cut {
 public:
 LeptonSelection(char const* name = "LeptonSelection") : Cut(name) {}

  void setN(unsigned nEl, unsigned nMu) { nEl_ = nEl; nMu_ = nMu; }
  void setStrictMu(bool doStrict) { strictMu_ = doStrict; }
  void setStrictEl(bool doStrict) { strictEl_ = doStrict; }
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  bool strictMu_{true};
  bool strictEl_{true};
  unsigned nEl_{0};
  unsigned nMu_{0};
};

class HighMet : public Cut {
 public:
  HighMet(char const* name = "HighMet") : Cut(name) {}

  void setMetSource(MetSource s) { metSource_ = s; }
  void setThreshold(double min) { min_ = min; }
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton& outEvent) override;

  MetSource metSource_{kOutMet};
  double min_{170.};
};

class PhotonMt;

class MtRange : public Cut {
 public:
  MtRange(char const* name = "MtRange") : Cut(name) {}
  
  void setRange(double min, double max) { min_ = min; max_ = max; }
  void setCalculator(PhotonMt const* calc) { calc_ = calc; }
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  double min_{0.};
  double max_{6500.};
  PhotonMt const* calc_{0};
};

class HighPtJetSelection : public Cut {
 public:
  HighPtJetSelection(char const* name = "HighPtJetSelection") : Cut(name) {}

  void setJetPtCut(double min) { min_ = min; }
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  double min_{100.};
};

class PhotonPtTruncator : public Cut {
 public:
  PhotonPtTruncator(char const* name = "PhotonPtTruncator") : Cut(name) {}

  void setPtMax(double max) { max_ = max; }
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  double max_{500.};
};

class GenParticleSelection : public Cut {
 public:
  GenParticleSelection(char const* name = "GenParticleSelection") : Cut(name) {}
  
  void setPdgId(int pdgId) { pdgId_ = pdgId; }
  void setMinPt(double minPt) { minPt_ = minPt; }
  void setMaxPt(double maxPt) { maxPt_ = maxPt; }
  void setMinEta(double minEta) { minEta_ = minEta; }
  void setMaxEta(double maxEta) { maxEta_ = maxEta; }

 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;
  
  int pdgId_{22};
  double minPt_{140.};
  double maxPt_{6500.};
  double minEta_{0.};
  double maxEta_{5.};
};


class EcalCrackVeto : public Cut {
 public:
  EcalCrackVeto(char const* name = "EcalCrackVeto") : Cut(name) {}
  void addBranches(TTree& skimTree) override;
  void setMinPt(double minPt) { minPt_ = minPt; }

 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;
  
  double minPt_{30.};
  Bool_t ecalCrackVeto_{true};
};

class TagAndProbePairZ : public Cut {
 public:
  enum Species {
    kMuon,
    kElectron,
    kPhoton, // doesn't work currently
    nSpecies 
  };

  TagAndProbePairZ(char const* name = "TagAndProbePairZ");
  ~TagAndProbePairZ();
  void addBranches(TTree& skimTree) override;
  void setTagSpecies(unsigned species) { tagSpecies_ = species; }
  void setProbeSpecies(unsigned species) { probeSpecies_ = species; }

  unsigned getNUniqueZ() const { return nUniqueZ_; }
  float getPhiZ(unsigned idx) const { return zs_[idx].phi(); }
  
 protected:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  unsigned tagSpecies_{0};
  unsigned probeSpecies_{0};

  panda::ParticleCollection* tags_{0};
  panda::ParticleCollection* probes_{0};
  panda::ParticleMCollection zs_;
  bool zOppSign_{0};

  unsigned nUniqueZ_{0};
};

class ZJetBackToBack: public Cut {
 public:
  ZJetBackToBack(char const* name = "ZJetBackToBack") : Cut(name) {}
  
  void setTagAndProbePairZ(TagAndProbePairZ* tnp) {tnp_ = tnp; }
  void setMinDeltaPhi(float dPhiMin) { dPhiMin_ = dPhiMin; }
  void setMinJetPt(float minJetPt) { minJetPt_ = minJetPt; }

 private:
  bool pass(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  float minJetPt_{30.};
  float dPhiMin_{2.5};
  TagAndProbePairZ* tnp_{0};

};


//--------------------------------------------------------------------
// Modifiers
//--------------------------------------------------------------------

class TriggerEfficiency : public Modifier {
 public:
  TriggerEfficiency(char const* name = "TriggerEfficiency") : Modifier(name) {}
  ~TriggerEfficiency() { delete formula_; }
  void addBranches(TTree& skimTree) override;
  void setMinPt(double minPt) { minPt_ = minPt; }
  void setFormula(char const* formula);
  void setUpFormula(char const* formula);
  void setDownFormula(char const* formula);

 protected:
  void apply(panda::EventMonophoton const& event, panda::EventMonophoton& outEvent) override;

  double minPt_{0.};
  TF1* formula_{0};
  TF1* upFormula_{0};
  TF1* downFormula_{0};
  double weight_;
  double reweightUp_;
  double reweightDown_;
};

class ExtraPhotons : public Modifier {
 public:
  ExtraPhotons(char const* name = "ExtraPhotons") : Modifier(name) {}
  void setMinPt(double minPt) { minPt_ = minPt; }

 protected:
  double minPt_{30.};
  
  void apply(panda::EventMonophoton const& event, panda::EventMonophoton& outEvent) override;
};


class JetCleaning : public Modifier {
 public:
  JetCleaning(char const* name = "JetCleaning");
  ~JetCleaning() { /*delete jer_; delete rndm_;*/ }
  void addBranches(TTree& skimTree) override;

  void setCleanAgainst(Collection col, bool c) { cleanAgainst_.set(col, c); }
  //  void setJetResolution(char const* sourcePath);

  /* double ptScaled(unsigned iJ) const { return ptScaled_[iJ]; } */
  /* double ptScaledUp(unsigned iJ) const { return ptScaledUp_[iJ]; } */
  /* double ptScaledDown(unsigned iJ) const { return ptScaledDown_[iJ]; } */
  
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton&) override;
  
  std::bitset<nCollections> cleanAgainst_{};

  // will copy jer branches
  /* float ptScaled_[NMAX_PARTICLES]; */
  /* float ptScaledUp_[NMAX_PARTICLES]; */
  /* float ptScaledDown_[NMAX_PARTICLES]; */

  //  JER* jer_{0};
  //  TRandom3* rndm_{0};
};

class PhotonJetDPhi : public Modifier {
 public:
  PhotonJetDPhi(char const* name = "PhotonJetDPhi") : Modifier(name) {}
  void addBranches(TTree& skimTree) override;

  void setMetVariations(MetVariations* v) { metVar_ = v; }
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  float dPhi_[NMAX_PARTICLES];
  float minDPhi_[NMAX_PARTICLES];
  float minDPhiJECUp_[NMAX_PARTICLES];
  float minDPhiJECDown_[NMAX_PARTICLES];
  MetVariations* metVar_{0};
};

class CopyMet : public Modifier {
 public:
  CopyMet(char const* name = "CopyMet") : Modifier(name) {}
 protected:
  void apply(panda::EventMonophoton const& event, panda::EventMonophoton& outEvent) override { outEvent.t1Met = event.t1Met; }
};

class PhotonMt : public Modifier {
 public:
  PhotonMt(char const* name = "PhotonMt") : Modifier(name) {}
  void addBranches(TTree& skimTree) override;
  
  double getMt(unsigned iP) const { return mt_[iP]; }
 protected:
  void apply(panda::EventMonophoton const& event, panda::EventMonophoton& outEvent) override;

  float mt_[NMAX_PARTICLES];
};

class LeptonRecoil : public Modifier {
 public:
  LeptonRecoil(char const* name = "LeptonRecoil") : Modifier(name), flavor_(nLeptonFlavors) {}
  void addBranches(TTree& skimTree) override;

  void setFlavor(LeptonFlavor flav) { flavor_ = flav; }

  TVector2 realMet() const { TVector2 v; v.SetMagPhi(realMet_, realPhi_); return v; }
  TVector2 realMetCorr(int corr) const;
  TVector2 realMetUncl(int corr) const;

 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  LeptonFlavor flavor_;
  MetVariations* metVar_{0};

  float realMet_;
  float realPhi_;
  float realMetCorrUp_;
  float realPhiCorrUp_;
  float realMetCorrDown_;
  float realPhiCorrDown_;
  float realMetUnclUp_;
  float realPhiUnclUp_;
  float realMetUnclDown_;
  float realPhiUnclDown_;
};

class EGCorrection : public Modifier {
 public:
  EGCorrection(char const* name = "EGCorrection") : Modifier(name) {}
  void addBranches(TTree& skimTree) override;
  
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton&) override;

  float origMet_{0.};
  float origPhi_{0.};
  float corrMag_{0.};
  float corrPhi_{0.};
};

class MetVariations : public Modifier {
 public:
  MetVariations(char const* name = "MetVariations") : Modifier(name) {}
  void addBranches(TTree& skimTree) override;

  void setMetSource(MetSource s) { metSource_ = s; }
  void setPhotonSelection(PhotonSelection* sel) { photonSel_ = sel; }
  /* void setJetCleaning(JetCleaning* jcl) { jetCleaning_ = jcl; } */
  TVector2 gecUp() const { TVector2 v; v.SetMagPhi(metGECUp_, phiGECUp_); return v; }
  TVector2 gecDown() const { TVector2 v; v.SetMagPhi(metGECDown_, phiGECDown_); return v; }
  /* TVector2 jer() const { TVector2 v; v.SetMagPhi(metJER_, phiJER_); return v; } */
  /* TVector2 jerUp() const { TVector2 v; v.SetMagPhi(metJERUp_, phiJERUp_); return v; } */
  /* TVector2 jerDown() const { TVector2 v; v.SetMagPhi(metJERDown_, phiJERDown_); return v; } */

 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton&) override;
  
  PhotonSelection* photonSel_{0};
  JetCleaning* jetCleaning_{0};
  float metGECUp_{0.};
  float phiGECUp_{0.};
  float metGECDown_{0.};
  float phiGECDown_{0.};
  /* float metJER_{0.}; */
  /* float phiJER_{0.}; */
  /* float metJERUp_{0.}; */
  /* float phiJERUp_{0.}; */
  /* float metJERDown_{0.}; */
  /* float phiJERDown_{0.}; */

  MetSource metSource_{kOutMet};
};

class ConstantWeight : public Modifier {
 public:
  ConstantWeight(double weight, char const* name = "ConstantWeight") : Modifier(name), weight_(weight) {}
  void addBranches(TTree& skimTree) override;

  void setUncertaintyUp(double delta) { weightUp_ = 1. + delta; }
  void setUncertaintyDown(double delta) { weightDown_ = 1. - delta; }

 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent) override { _outEvent.weight *= weight_; }
  
  double weight_;
  double weightUp_{-1.};
  double weightDown_{-1.};
};

class PhotonPtWeight : public Modifier {
 public:
  enum PhotonType {
    kReco,
    kParton,
    kPostShower,
    nPhotonTypes
  };

  PhotonPtWeight(TObject* factors, char const* name = "PhotonPtWeight");
  ~PhotonPtWeight();

  void addBranches(TTree& skimTree) override;

  void setPhotonType(unsigned t) { photonType_ = t; }
  void addVariation(char const* suffix, TObject* corr);
  void useErrors(bool); // use errors of the nominal histogram weight for Up/Down variation
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent) override;

  TObject* nominal_;
  double weight_;
  std::map<TString, TObject*> variations_;
  std::map<TString, double*> varWeights_;
  unsigned photonType_{kReco};
  bool useErrors_{false};
};

class IDSFWeight : public Modifier {
 public:
  enum Object {
    kPhoton,
    kElectron,
    kMuon,
    nObjects
  };

  enum Variable {
    kPt,
    kEta,
    kAbsEta,
    kNpv,
    nVariables
  };

  IDSFWeight(Object obj, char const* name = "IDSFWeight") : Modifier(name), object_(obj) {}

  void addBranches(TTree& skimTree) override;
  void setVariable(Variable, Variable = nVariables);
  void setNParticles(unsigned _nP) { nParticles_ = _nP; }
  void addFactor(TH1* factor) { factors_.emplace_back(factor); }
 protected:
  void applyParticle(unsigned iP, panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent);
  void apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent) override;

  Object object_;
  Variable variables_[2];
  unsigned nParticles_{1};
  std::vector<TH1*> factors_;
  double weight_{1.};
  double weightUp_{1.};
  double weightDown_{1.};
};

class NPVWeight : public Modifier {
 // DEPRECATED - USE PUWeight
 public:
  NPVWeight(TH1* factors, char const* name = "NPVWeight") : Modifier(name), factors_(factors) {}
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent) override;

  TH1* factors_;
};

class PUWeight : public Modifier {
 public:
  PUWeight(TH1* factors, char const* name = "PUWeight") : Modifier(name), factors_(factors) {}

  void addBranches(TTree& _skimTree) override;
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent) override;

  TH1* factors_;
  double weight_;
};

class NNPDFVariation : public Modifier {
 public:
  NNPDFVariation(char const* name = "NNPDFVariation") : Modifier(name) {}

  void addBranches(TTree& skimTree) override;
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent) override;

  double weightUp_;
  double weightDown_;
};

class GenPhotonDR : public Modifier {
 public:
  GenPhotonDR(char const* name = "GenPhotonDR") : Modifier(name) {}

  void addBranches(TTree& skimTree) override;
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent) override;

  float minDR_;
};

class PhotonRecoil : public Modifier {
 public:
  PhotonRecoil(char const* name = "PhotonRecoil") : Modifier(name) {}

  void addBranches(TTree& skimTree) override;
 protected:
  void apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent) override;

  float realMet_;
  float realPhi_;
  float realMetCorrUp_;
  float realPhiCorrUp_;
  float realMetCorrDown_;
  float realPhiCorrDown_;
  float realMetUnclUp_;
  float realPhiUnclUp_;
  float realMetUnclDown_;
  float realPhiUnclDown_;
};

#endif
