void CrvCalibration(const std::string &inputFileName, const std::string &outputFileName)
{
    TFile *inputFile = TFile::Open(inputFileName.c_str());
    inputFile->cd("CrvCalibration");
    TTree *treePedestals = (TTree*)gDirectory->FindObjectAny("crvPedestals");
    size_t channel;
    double pedestal;
    treePedestals->SetBranchAddress("channel", &channel);
    treePedestals->SetBranchAddress("pedestal", &pedestal);
    std::map<size_t,double> pedestals;  //first need to fill this map to filter out multiple entries of the same channel due to $ROOTSYS/bin/hadd
    for(int i=0; i<treePedestals->GetEntries(); ++i)
    {
      treePedestals->GetEntry(i);
      pedestals[channel]=pedestal;
    }

    TF1 funcCalib("f0", "gaus");

    std::ofstream outputFile;
    outputFile.open(outputFileName);
    outputFile<<"TABLE CRVSiPM "<<std::endl;
    outputFile<<"#channel, pedestal, calibPulseHeight, calibPulseArea"<<std::endl;

    for(auto iter=pedestals.begin(); iter!=pedestals.end(); ++iter)
    {
      channel=iter->first;
      pedestal=iter->second;

      TH1F *hist;
      double calibValue[2];
      for(int i=0; i<2; ++i) //loop over hisograms with pulse areas and pulse heights
      {
        if(i==1) hist=(TH1F*)gDirectory->FindObjectAny(Form("crvCalibrationHistPulseArea_%zu",channel));
        else hist=(TH1F*)gDirectory->FindObjectAny(Form("crvCalibrationHistPulseHeight_%zu",channel));

        if(hist->GetEntries()<100) //not enough data
        {
          calibValue[i]=-1;
          continue;
        }

/*
        int n=hist->GetNbinsX();
        double overflow=hist->GetBinContent(0)+hist->GetBinContent(n+1);
        if(overflow/((double)hist->GetEntries())>0.1) //too much underflow/overflow. something may be wrong.
        {
          calibValue[i]=-1;
          continue;
        }
*/

        int maxbinCalib = hist->GetMaximumBin();
        double peakCalib = hist->GetBinCenter(maxbinCalib);
//FIXME        funcCalib.SetRange(peakCalib*0.8,peakCalib*1.2);
        funcCalib.SetRange(peakCalib*0.7,peakCalib*1.3);
        funcCalib.SetParameter(1,peakCalib);
        hist->Fit(&funcCalib, "0QR");
        calibValue[i]=funcCalib.GetParameter(1);
      }

      outputFile<<channel<<","<<pedestal<<","<<calibValue[0]<<","<<calibValue[1]<<std::endl;
    }

    outputFile<<std::endl;

    //time offsets
    TTree *treeTimeOffsets = (TTree*)gDirectory->FindObjectAny("crvTimeOffsets");
    double offset;
    treeTimeOffsets->SetBranchAddress("channel", &channel);
    treeTimeOffsets->SetBranchAddress("timeOffset", &offset);
    std::map<size_t,double> timeOffsets;  //first need to fill this map to filter out multiple entries of the same channel due to $ROOTSYS/bin/hadd
    for(int i=0; i<treeTimeOffsets->GetEntries(); ++i)
    {
      treeTimeOffsets->GetEntry(i);
      timeOffsets[channel]=offset;
    }

    outputFile<<"TABLE CRVTime"<<std::endl;
    outputFile<<"#channel, timeOffset"<<std::endl;
    for(auto iter=timeOffsets.begin(); iter!=timeOffsets.end(); ++iter)
    {
      outputFile<<iter->first<<","<<iter->second<<std::endl;
    }

    outputFile.close();
    inputFile->Close();
}
