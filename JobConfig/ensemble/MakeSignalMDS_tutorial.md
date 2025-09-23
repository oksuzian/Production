# Introduction

# Tutorial 

1. Make a new directory in your working directory. You should ensure you have access to Production (either via a musing or a clone). Call this something like "ensemble_MDS2c_CeMLL_1e-14_2weeks" altering the fields as is applicable to what you want to make.

2. Enter the new directory. Run the following command:

```
Stage3_addsignal_easy.sh --known MDS2c --signal CeMLeadingLog --rate 1e-14 --nexp 10 --chooselivetime 1209600
```

here the parameters are:

* ``known``: the tag of the mixed background sample you wish to sample from.
* ``signal``: must be the primary name of the signal type you want to sample (e.g. CeMLeadingLog)
* ``rate``: chosen signal rate (e.g. 1e-13)
* ``nexp``: how many pseudo experiments (i.e. random samplings) you want to make
* ``chosenlivetime``: in seconds (check the config to ensure you don't try to make more than is available)

The output of this command will include

* a set of nexp mcs files, these contains random sets of expected signal events (sampled from a much larger set) and include Poisson statistical variations.
* a set of nexp nts files that are EventNtuples of the analogous mcs files (names are the same)
* nexp lists ``filename_ChosenMixed_i`` contain random sets of MDS known ntuples and the new signal ntuples
* a new directory called ``fcl`` contains the splitting and ntupling fcls for reference

3. Now you have random sets of ntuples you want to combine these into a merged dataset (for some blinding effect). To do that run a second script:

```
combine_ntuples.sh 1 MDS2c
```

where the first argumenet is the iteration of the list (1 to nexp) and the second arguement is the MDS tag version name (should be the same as before). You will need to run this for every nexp.

In the current directory you will see that for every nexp (i) you will now see a directory: ``merged_files_i``.

In this directory there will be a set of files (merge factor can be altered within the combine_ntuple.sh script). The filenames will be for example:

```
nts.mu2e.ensembleMDS2cMix1BB_CeMLeadingLog_1e-14_1223190.2_16.root
```

where most of this is obvious, the final number (1223190) is the livetime of the sample in seconds.

4. You should be able to analyze this file list as you would any other set of files. If you prefer remote/xrootd etc. file access you will need to upload them to SAM, but I recommend keeping them in you personal directories.






