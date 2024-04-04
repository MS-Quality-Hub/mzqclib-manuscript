#!/usr/bin/env bash
# !!!
# Note: The results will be recorded in $workdir/$submission which is set to /tmp/PXD040621 unless the `Setup` variables are customised
# Note: the $workdir needs to exist and be home to all required raw file images, scripts, and configuration files (github co)
# Note: the required containers must be provided with their fully specified paths in the variables below
# !!!

# Workflow functional variables
rmzqcsimg=rmzqc-usecase.simg 
jmzqcsimg=jmzqc-usecase.simg 
pymzqcsimg=pymzqc-usecase.simg
comsetsimg=biocontainers-comet-ms\:2023010.simg
trfpsimg=biocontainers-thermorawfileparser-1.4.1.simg
fasta=uniprot-ecoli_k12-2023.04.12.fasta
cometparams=comet.params.high-high

# Setup 
workdir=/tmp
submission=PXD040621
cd $workdir

# Convert to mzML for all raw file images
for f in *.raw; do singularity exec trfpsimg ThermoRawFileParser.sh -i=$f -f=2 -b=${f%.*}.mzML; done  

# Identify spectra for each mzML
for f in *.mzML; do singularity exec $cometsimg comet.exe -P$cometparams -D$fasta $f; done

# Calculate metrics for each mzML
for f in *.mzML; do singularity exec $rmzqcsimg rmzqc-cli.sh $f ${f%.*}.rmzqc.mzqc; done
for f in *.mzML; do singularity exec $jmzqcsimg jmzqc-cli.sh -f $f -o ${f%.*}.jmzqc.mzqc; done
for f in *.mzML; do singularity exec $pymzqcsimg python pymzqc-usecase.py $f ${f%.*}.mzid ${f%.*}.pymzqc.mzqc; done

# Merge all 
singularity exec $pymzqcsimg python pymzqc-merge.py $submission.mzqc

# Finish
echo "Data pre-analysis complete. Ready to start the data analysis notebook."