#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

if (!require("BiocManager", quietly = TRUE)) install.packages("BiocManager")
if (!require("mzR", quietly = TRUE)) BiocManager::install("mzR")
library("mzR")

if (!require("rmzqc", quietly = TRUE)) install.packages("rmzqc")
library(rmzqc)
if (packageVersion("rmzqc") < package_version("0.5.3")) stop("You need a newer rmzqc ... wait for CRAN to update")

if (!require("data.table", quietly = TRUE)) install.packages("data.table")
library(data.table)

# test if there is at least one argument: if not, return an error
if (length(args)==0) {
  stop("At least one argument must be supplied (input file), abort.", call.=FALSE)
} else if (length(args)==1) {
  # default output file, args[1] is input file (must be mzml)
  args[2] = "rmzqc-usecase.mzqc"
}

if (!(endsWith(args[1], ".mzML"))){
	stop("Input file needs to be an mzML standard format file, abort.", call.=FALSE)
}

qcrunname = normalizePath(args[1]) 
ms = openMSfile(qcrunname)
hd = header(ms)

hdt = data.table(hd)
IIS_MS1_mean = hdt[msLevel == 1, mean(injectionTime)]
IIS_MS1_sd = hdt[msLevel == 1, sd(injectionTime)]
IIS_MS2_mean = hdt[msLevel == 2, mean(injectionTime)]
IIS_MS2_sd = hdt[msLevel == 2, sd(injectionTime)]

uri_raw_file = localFileToURI(qcrunname)  ## we need a proper URI (i.e. no backslashes and a scheme, e.g. 'file:') otherwise writing will fail
file_format = getCVTemplate(accession = filenameToCV(uri_raw_file))

software_this_script = toAnalysisSoftware(id = "MS:1000799", version = "0.1") ## custom script (this one right here)
software_mzR = toAnalysisSoftware(id = "MS:1002869", version = as.character(packageVersion("mzR")))

run_qc = MzQCrunQuality$new(
          metadata = MzQCmetadata$new(label = basename(uri_raw_file),
                                      inputFiles = 
                                        list(MzQCinputFile$new(basename(uri_raw_file),
                                          uri_raw_file,
                                          file_format)),
          analysisSoftware = list(software_this_script, software_mzR)),
          qualityMetrics = list(toQCMetric(id = "MS:4000132", value = IIS_MS1_mean), ## MS1 ion collection time mean
                                toQCMetric(id = "MS:4000133", value = IIS_MS1_sd), ## MS1 ion collection time sigma
                                toQCMetric(id = "MS:4000137", value = IIS_MS2_mean), ## MS2 ion collection time mean
                                toQCMetric(id = "MS:4000138", value = IIS_MS2_sd) ## MS2 ion collection time sigma
                               )
  )

run_qc_list = list()
run_qc_list = append(run_qc_list, run_qc)
mzQC_document = MzQCmzQC$new(version = "1.0.0", 
                             creationDate = MzQCDateTime$new(), 
                             contactName = "Chris Bielow", 
                             contactAddress = "chris.bielow@bsc.fu-berlin.de", 
                             description = "Ion Injection times for PXD000455",
                             runQualities = run_qc_list,
                             setQualities = list(), 
                             controlledVocabularies = list(getCVInfo()))
  
cat("Constructed file is valid?", isValidMzQC(mzQC_document), '\n')
writeMZQC(args[2], mzQC_document)
cat(args[2], "written to disk!", '\n')


