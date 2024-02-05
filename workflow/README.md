# mzQC Implementation-Cases (formerly usecases)
The main focus of this workflow is not to analyse data, but to showcase the existing implementations of mzQC, how to combine these, and how to quickly create new uses. Basic knowledge of nextflow and singularity is recommended, since you will need both. 

## The Workflow

Execute from the repository base directory:
```nextflow
nextflow run 'workflow/mzqc-implementationcases.nf' -params-file 'workflow/mzqc-implementationcases-local.yml' -c 'workflow/nf.config' --run 'test_data/20181113_010_autoQC01.raw'
```

> NOTE: nextflow 22.04.5 does not escape the input in bash scripts if the param argument is escaped - unfortunate (as are all situations that need escaping, pun intended)

As you can see from the example call above, we use two configuration files. The first, `-c 'workflow/nf.config'` is there only to instruct nextflow to use containers for each workflow step, and use singularity at that. If this is your default setting, then you can skip this input. The `.yml` file specifies for the workflow where each of the containers referenced in the workflow definition are in the local system. It also specifies the amount of memory that should be made available for the respective container and how often retry should be attempted in case of local compute interruption. We refer to the [nextflow documentation](https://www.nextflow.io/docs/latest/config.html) for details. Please make sure to update the `.yml` file to reflect the path to your locally build containers. 

### Bash
In case you want to use bash (or other cmdl), I assume you know what you're doing, so take following command hint _as is_; you need to take care of all the local paths in the commands anyway.

```
for f in *.mzML; do bsub singularity exec /tmp/biocontainers-comet-ms\:2023010.simg comet.exe -Pcomet.params.high-high -Duniprot-ecoli_k12-10-2023.fasta $f; done
```

```
for f in *.mzML; do bsub singularity exe /tmp/pymzqc-usecase.simg pymzqc-usecase.py $f ${f%.*}.mzid ${f%.*}.pymzqc.mzqc; done
for f in *.mzML; do bsub singularity exec /tmp/rmzqc-usecase.simg rmzqc-cli.sh $f ${f%.*}.rmzqc.mzqc; done
for f in *.mzML; do bsub singularity exe /tmp/jmzqc-usecase.simg jmzqc-cli.sh -f $f -o ${f%.*}.jmzqc.mzqc; done
```

### Workflow Data Input 
We tested several data sets to most effectively demonstrate the capabilities of the mzQC implemntations in a short form. Pease see the last entry for the current, i.e.latest test input.

1. QC Sample run (BSA + iRT standard) from rawR
- Folder autoQC
- File 20181113_010_autoQC01.raw
> This data set contains raw files described in "rawR - Direct access to raw mass spectrometry data in R" available at https://www.biorxiv.org/content/10.1101/2020.10.30.362533v1.full The analyzed sample (autoQC01) consists of the iRT peptide mix (Biognosys) in a tryptic BSA digest (NEB). [doi:10.25345/C5MZ14] 

2. Biological samples in DDA mode + iRT standard
- Folder N/A
- File QEXI21822_F15.raw 
- PXD013487: https://ftp.pride.ebi.ac.uk/pride/data/archive/2020/08/PXD013487/QEXI21822_F15.raw
> Cerebrospinal fluid samples of patients with Parkinson's disease and healthy controls were used for this study. Part of the samples consisted of fractions that were separated by gel electrophoresis. After tryptic digestion, all samples were spiked with indexed retention time (iRT) peptides and were measured using a DDA mass spectrometry approach. 
> NOTE: Not to be confused with the DIA part of [doi:10.1002/ctm2.357] (which is PXD022234)

3. Metabo QC DDA + internal standards
- Folder: N/A
- File: 20100917_01_TomQC.mzML
- MTBLS36: https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS36/20100917_01_TomQC.mzML
>Application of mass spectrometry enables the detection of metabolic differences between groups of related organisms. Differences in the metabolic fingerprints of wild-type Solanum lycopersicum and three monogenic mutants, ripening inhibitor (rin), non-ripening (nor) and Colourless non-ripening (Cnr), of tomato are captured with regard to ripening behaviour. A high-resolution tandem mass spectrometry system coupled to liquid chromatography produced a time series of the ripening behaviour at discrete intervals with a focus on changes post-anthesis. Internal standards and quality controls were used to ensure system stability. The raw data of the samples and reference compounds including study protocols have been deposited in the open metabolomics database MetaboLights via the metadata annotation tool Isatab to enable efficient re-use of the datasets, such as in metabolomics cross-study comparisons or data fusion exercises.

4. Drosophila
- Folder: PXD000455
- File: all
- PXD000455: https://ftp.pride.ebi.ac.uk/pride/data/archive/2013/11/PXD000455/
>Self-described high coverage dataset of whole Drosophila melanogaster Canton-S. Difference of reanlysis and original insurmountable.

5. Broccoli
- Folder: PXD040621
- File: all
- PXD040621: https://ftp.pride.ebi.ac.uk/pride/data/archive/2023/07/PXD040621/
> Study on broccoli derived sulforaphane influencing bacteria of the gut-microbiome. Includes a simple proteomics experiment, 8 batches of E. coli grown in two groups of media, measured with QExactive+, label-free quantitative analysis with MQ followed. As a bonus, the publication also has a related metabolomics experiment.

### Workflow Flowchart 

## Current capability:
```mermaid
flowchart TD
    p0([Channel.fromPath])
    p1[rawfileconversion]
    p2[jmzqc]
    p3[rmzqc]
    p4[pymzqc]
    p5[Report or Archival]
    p0 -->|run_channel| p1
    p1 -->|mzml_channel| p2
    p1 -->|mzml_channel| p3
    p2 -->|mzqc_channel| p4
    p3 -->|mzqc_channel| p4
    p4 -->|mzqc_channel| p5    
```
For more details on the flowchart generation for the workflow, see [here](workflow-usecase.md)
