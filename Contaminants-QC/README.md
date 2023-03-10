## speclibs 
- Common name: PRIDE_contaminants
- Taxonomy: Unknown
- Number of spectra: 59891
- Number of peptides: 4548
- File Size: 18M
- FTP: https://ftp.pride.ebi.ac.uk/pub/databases/pride/resources/cluster/spectrum-libraries/2015-04/crap.msp.gz

- Common name: NIST_bsa_IT_2011-04-01
- Taxonomy: Bos bovis
-  Number of Spectra: 725
- Unique Peptide Sequences: 336
- Proteome Coverage: 94.56%
- src: https://chemdata.nist.gov/dokuwiki/doku.php?id=peptidew:lib:bsa_it
- URL: https://chemdata.nist.gov/download/peptide_library/libraries/proteins/ion_trap/bsa/strict/2011_04_01/2011_04_01-_bsa_consensus_final_true_lib.tar.gz

### speclib prep
With TPP container `singularity shell ~/other-tools/singularity_images/TPP_v6.1.0.simg`

```
wget $URL
gunzip crap.msp.gz 
#python3 ../correct_tabs_msp.py crap.msp PRIDE_Contaminants.msp  # not neceessary anymore
cp crap.msp PRIDE_Contaminants.msp
```

```
spectrast -cNPRIDE_Contaminants PRIDE_Contaminants.msp
spectrast -cAB -cNPRIDE_Contaminants_unique PRIDE_Contaminants.splib
spectrast -cAB -cNPRIDE_Contaminants_really_unique PRIDE_Contaminants_unique.splib
spectrast -cAD -cc -cy1 -cNPRIDE_Contaminants_unique_targetdecoy PRIDE_Contaminants_really_unique.splib

```
Note that some spectra needed to be ignored because Peptide ID too short or Too few peaks in spectrum
Note that some mods needed to be ignored (probably the iTRAQ mods)
(see spectrast.log for details)

```
wget $URL
tar -xvzf 2011_04_01_bsa_consensus_final_true_lib.tar.gz
#python3 ../correct_tabs_msp.py bsa_consensus_final_true_lib.msp NIST_bsa_IT_2011-04-01.msp
cp bsa_consensus_final_true_lib.msp NIST_bsa_IT_2011-04-01.msp
```
Note that for NIST BSA from ion trap data (2011) (see spectrast.log)

```
spectrast -cNNIST_bsa_IT NIST_bsa_IT_2011-04-01.msp
spectrast -cAB -cNNIST_bsa_IT_unique NIST_bsa_IT.splib
spectrast -cAD -cc -cy1 -cNNIST_bsa_IT_unique_targetdecoy NIST_bsa_IT_unique.splib
```


