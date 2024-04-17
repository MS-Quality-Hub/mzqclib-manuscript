## usecase application notes
This is a simple qc metric calculator that expects mzML and mzID as input.
```
Usage: pymzqc-usecase.py [OPTIONS] MZML_INPUT MZID_INPUT OUTPUT_FILEPATH
Try 'pymzqc-usecase.py --help' for help.
```
Specifically, it is designed to accomodate the input of the usecase, which is the iPRG2015 data,
processed with comet-ms into corresponding mzid files with the comet.params.high-high preset plus
combined decoy search option on the provided fasta sequence database.

The `--log` parameter lets you choose the level of detail for the pymzqc-usecase's execution log.

The with the `--dev` flag set, pymzqc-usecase will also export the base and identifications data 
frames created from reading and compacting the relevant input data. The resulting mzQC are only 
supposed to be 'valid' with the exception of the two data frames added as 'fake' qc metric elements.

### to improve
The missed cleavage metric does not have a proper qc metric term yet. For now it is produced as 
"enzyme digestion parameters" of accession "MS:4000005" ('table') and has the following columns:
"MS:1003169" ('PeptideSequence'), "MS:1000767" ('native_id'), "MS:1000927" (missed cleavages per spectrum identification) 
                                            
