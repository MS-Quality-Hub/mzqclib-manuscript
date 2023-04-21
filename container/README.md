## Building and using containers for the workflow
This folder contains everything needed to build the containers referenced in the workflow definition. You will need to build these locally in order to successfully run the workflow.

Build only requires a local copy of the repository and a working installation of singularity.

The container used for raw-file conversion can be build by simply converting the biocontainer docker image into singularity like so:
```
singularity build --fakeroot trfp.simg docker://quay.io/biocontainers/thermorawfileparser:1.4.1--ha8f3691_0
```

For all other containers referenced, the necessary definition, configuration, and script files are located in the respective sub-folder and are supposed to be built from within the respective folder like so:
```
cd <jmzqc-usecase OR rmzqc-usecase OR pymzqc-usecase>
singularity build --fakeroot <container-image-name.simg> <container-recipe.sdef> 
```

Here are the details to each folder:
- jmzqc:  the folder contains the container recipe and a single small script for convenience of calling the QC. For details see the [jmzqc-usecase repo](https://github.com/nilshoffmann/jmzqc-usecase.git).

- rmzqc: the folder contains the container recipe and a R script exemplifying the ease and brevity with which QC can be calculated and then deposited in mzQC from R.

- pymzqc: the folder contains the container recipe and a python script to showcase how easy it is to add mzQC functionality to an existing tool, in this case ANN-solo. Additionally, the demonstration depends on prebuilt spectral libraries (from the Contaminants-QC folder). Currently, due to unfortunate incompatibilities with pip changes with it's dependency resolution and the ANN-solo package setup, the container build requires a locally patched checkout of ANN-solo. See README there. 

- merge-and-report: the folder contains the container recipe and depends on the two python scripts (from the workflow folder) demonstrating how merging and reporting can be achieved .
