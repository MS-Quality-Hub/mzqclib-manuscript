# mzQC Implementation-Cases (formerly usecases)
The main focus of this workflow is not to analyse data, but to showcase the existing implementations of mzQC, how to combine these, and how to quickly create new uses. Basic knowledge of nextflow and singularity is recommended, since you will need both. 

## The Workflow
Execute from the repository base directory:
```nextflow run 'workflow/mzqc-implementationcases.nf' -params-file 'workflow/mzqc-implementationcases-local.yml' -c 'workflow/nf.config' --run 'test_data/20181113_010_autoQC01.raw'```

> NOTE: nextflow 22.04.5 does not escape the input in bash scripts if the param argument is escaped - unfortunate (as are all situations that need escaping, pun intended)

As you can see from the example call above, we use two configuration files. The first, `-c 'workflow/nf.config'` is there only to instruct nextflow to use containers for each workflow step, and use singularity at that. If this is your default setting, then you can skip this input. The `.yml` file specifies for the workflow where each of the containers referenced in the workflow definition are in the local system. It also specifies the amount of memory that should be made available for the respective container and how often retry should be attempted in case of local compute interruption. We refer to the [nextflow documentation](https://www.nextflow.io/docs/latest/config.html) for details. Please make sure to update the `.yml` file to reflect the path to your locally build containers. 

### Workflow Data Input 

1. QC Sample run (BSA + iRT standard)
- File 20181113_010_autoQC01.raw
- MSV000086542: https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?file=f.MSV000086542/raw/20181113_010_autoQC01.raw&forceDownload=true
> This data set contains raw files described in "rawR - Direct access to raw mass spectrometry data in R" available at https://www.biorxiv.org/content/10.1101/2020.10.30.362533v1.full The analyzed sample (autoQC01) consists of the iRT peptide mix (Biognosys) in a tryptic BSA digest (NEB). [doi:10.25345/C5MZ14] 

2. Biological sample in DDA mode + iRT standard
- File QEXI21822_F15.raw 
- PXD013487: https://ftp.pride.ebi.ac.uk/pride/data/archive/2020/08/PXD013487/QEXI21822_F15.raw
> Cerebrospinal fluid samples of patients with Parkinson's disease and healthy controls were used for this study. Part of the samples consisted of fractions that were separated by gel electrophoresis. After tryptic digestion, all samples were spiked with indexed retention time (iRT) peptides and were measured using a DDA mass spectrometry approach. 
> NOTE: Not to be confused with the DIA part of [doi:10.1002/ctm2.357] (which is PXD022234)

3. Metabo QC DDA + internal standards
- File: 20100917_01_TomQC.mzML
- MTBLS36: https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS36/20100917_01_TomQC.mzML
>Application of mass spectrometry enables the detection of metabolic differences between groups of related organisms. Differences in the metabolic fingerprints of wild-type Solanum lycopersicum and three monogenic mutants, ripening inhibitor (rin), non-ripening (nor) and Colourless non-ripening (Cnr), of tomato are captured with regard to ripening behaviour. A high-resolution tandem mass spectrometry system coupled to liquid chromatography produced a time series of the ripening behaviour at discrete intervals with a focus on changes post-anthesis. Internal standards and quality controls were used to ensure system stability. The raw data of the samples and reference compounds including study protocols have been deposited in the open metabolomics database MetaboLights via the metadata annotation tool Isatab to enable efficient re-use of the datasets, such as in metabolomics cross-study comparisons or data fusion exercises.

### Workflow Flowchart 
To make a visualisation from the mermaid file for pretty workflow visualisation
```
nextflow run 'mzqc-usecases.nf'  -with-dag flowchart.mmd --run test.raw -stub
```

## Auto-Input
The container recipes in the container folder of this repository are configured to include workflow necessary files, please refer to the documentation in there.