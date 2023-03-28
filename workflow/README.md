# mzQC implementation-cases (formerly usecases)
showcasing the existing implementations of mzQC

## the workflow
nextflow_22.04.5 run 'workflow/mzqc-implementationcases.nf' -params-file 'workflow/mzqc-implementationcases-local.yml' -c 'workflow/nf.config' --run 'test_data/20181113_010_autoQC01.raw'

NOTE nextflow 22.04.5 does not escape the input in bash scripts if the param argument is escaped - sucks (as do things that need to be escaped)

### workflow input 
See the test_data folder

1. QC Sample run (BSA+iRT)
- File 20181113_010_autoQC01.raw
- MSV000086542: https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?file=f.MSV000086542/raw/20181113_010_autoQC01.raw&forceDownload=true
> This massive data set contains raw files described in "rawR - Direct access to raw mass spectrometry data in R" available at https://www.biorxiv.org/content/10.1101/2020.10.30.362533v1.full The analyzed sample (autoQC01) consists of the iRT peptide mix (Biognosys) in a tryptic BSA digest (NEB). [doi:10.25345/C5MZ14] 

2. Biological sample in DDA mode + iRT
- File QEXI21822_F15.raw 
- PXD013487: https://ftp.pride.ebi.ac.uk/pride/data/archive/2020/08/PXD013487/QEXI21822_F15.raw
> Cerebrospinal fluid samples of patients with Parkinson's disease and healthy controls were used for this study. Part of the samples consisted of fractions that were separated by gel electrophoresis. After tryptic digestion, all samples were spiked with indexed retention time (iRT) peptides and were measured using a DDA mass spectrometry approach. 

Not to be confused with the DIA part PXD022234

3. Metabo QC DDA + internal standards
- File: 20100917_01_TomQC.mzML
- MTBLS36: https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS36/20100917_01_TomQC.mzML
>Application of mass spectrometry enables the detection of metabolic differences between groups of related organisms. Differences in the metabolic fingerprints of wild-type Solanum lycopersicum and three monogenic mutants, ripening inhibitor (rin), non-ripening (nor) and Colourless non-ripening (Cnr), of tomato are captured with regard to ripening behaviour. A high-resolution tandem mass spectrometry system coupled to liquid chromatography produced a time series of the ripening behaviour at discrete intervals with a focus on changes post-anthesis. Internal standards and quality controls were used to ensure system stability. The raw data of the samples and reference compounds including study protocols have been deposited in the open metabolomics database MetaboLights via the metadata annotation tool Isatab to enable efficient re-use of the datasets, such as in metabolomics cross-study comparisons or data fusion exercises.

### workflow flowchart 
make a mermaid file for pretty workflow visualisation
```
~/other-tools/nextflow_22.04.5 run 'mzqc-usecases.nf'  -with-dag flowchart.mmd --run test.raw -stub
```

## auto-input
The respective containers include workflow necessary files, too. Details in the container folder, here a summary:
- pymzqc: the QC script `specter_of_spectra.py` in /opt/, the spectral libraries (from the Contaminants-QC folder) in /opt/speclibs/ , see container/pymzqc-usecase/pymzqc-usecase.sdef container definition for details
- rmzqc: the QC script, see container/rmzqc-usecase/rmzqc-usecase.sdef container definition for details
- jmzqc:  the QC script, see container/jmzqc-usecase/jmzqc-usecase.sdef container definition for details
