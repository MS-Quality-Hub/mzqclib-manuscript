#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

library(rmzqc)
library(dplyr)
library(tidyr)
library(readr)
library(ggplot2)
library(MSnbase)

# test if there is at least one argument: if not, return an error
if (length(args)==0) {
  stop("At least one argument must be supplied (input file), abort.", call.=FALSE)
} else if (length(args)==1) {
  # default output file, args[1] is input file (must be mzml)
  args[2] = "rmzqc-usecase.mzqc"
}

qcrunname = args[1] 
if (!(endsWith(qcrunname, ".mzML"))){
	stop("Input file needs to be an mzML standard format file, abort.", call.=FALSE)
}

#irt input processing
irts <- readr::read_delim("https://gist.github.com/mwalzer/518e70ca01238a540552929a54bacaa6/raw/4e2ae214cb106ad4bb2d234580dcbd0bd0ced686/biognosis_irts.csv", 
                            delim = ",", escape_double = FALSE, 
                            col_names = TRUE)
irts <- irts %>% 
  mutate(tol_10r = abs(5*(`Precursor m/z` * 1e-6) + `Precursor m/z`)) %>% 
  mutate(tol_10l = abs(5*(`Precursor m/z` * 1e-6) - `Precursor m/z`))

#mzml processing
run_msnbase <- readMSData(qcrunname, mode = "inMemory", verbose = FALSE, msLevel = 1)
chrs <- chromatogram(run_msnbase, mz = as.matrix(irts %>% select(`tol_10l`,`tol_10r`)))  # , rt = rtr
rrt <- sapply(chrs, function(x) as.data.frame(clean(x))$rtime[which.max(as.data.frame(clean(x))$intensity)][1])
fit <- lm(rrt ~ irts$iRT)

rtr <- data.frame(rRT = rrt, iRT = irts$iRT)
plt <- ggplot(rtr %>% mutate(fits=fit$fitted.values, se=fit$residuals^2), aes(x=iRT, y=rRT)) +
  geom_point() +
  geom_smooth(method = "lm") + 
  geom_segment(aes(x = iRT, y = rRT,
                   xend = iRT, yend = fits), 
               alpha = 0.3) +
  labs(x="iRT score", y="RT [s]") + 
  geom_text(aes(x = min(iRT), y = max(rRT)-30, hjust = 0, parse =TRUE,
      #label = bquote(paste("adj. R^2 =", format(summary(fit)$adj.r.squared,digits=4), sep = " ", collapse = NULL))
      label = paste("adj. R^2 =", format(summary(fit)$adj.r.squared,digits=4), sep = " ", collapse = NULL)
       )) +
  geom_text(aes(x = min(iRT), y = max(rRT), hjust = 0,
      label = paste("y =",format(round(fit$coefficients[[1]],2), nsmall = 2), "+", format(round(fit$coefficients[[2]],2), nsmall = 2), "x", 
                    sep = " ", collapse = NULL)))

ggsave("rmzqc-usecase.png", plot=plt)

#"""metrics:
#   * iRT calibration formula
#   * iRT calibration adjusted r-squared
#"""
mes_qc <- MzQCcvParameter$new(accession="MS:4000149", 
													name="iRT calibration formula", 
													value=paste("y =", format(round(fit$coefficients[[1]],2), nsmall = 2), "+", 
																		format(round(fit$coefficients[[2]],2), nsmall = 2), "x", sep = " ", collapse = NULL))
																		
meq_qc <- MzQCqualityMetric$new(accession="MS:4000150", 
													name="iRT calibration adjusted r-squared", 
													value=format(summary(fit)$adj.r.squared,digits=4))

sw <- MzQCanalysisSoftware$new(uri="https://github.com/MS-Quality-hub/rmzqc", 
                               version=paste("v0","1","0", sep=".", collapse = " "),
                               accession="MS:1000531", name="software")

file_format = getCVTemplate(accession = filenameToCV(qcrunname))
inp <- MzQCinputFile$new(basename(qcrunname), qcrunname, file_format)
isValidMzQC(inp)

rq <- MzQCrunQuality$new(metadata = MzQCmetadata$new(label = "implementation-case demo",
                                    inputFiles = list(inp),
                                    analysisSoftware = list(sw)),
                                qualityMetrics = list(mes_qc, meq_qc))
isValidMzQC(rq)

mymzqc <- MzQCmzQC$new(version = "1.0.0", 
                        creationDate = MzQCDateTime$new(), 
                        contactName = paste(Sys.info()["user"]), 
                        contactAddress = "test@user.info", 
                        description = "An rmzqc-usecase demonstration result.",
                        runQualities = list(rq),
                        setQualities = list(), 
                    controlledVocabularies = list(getDefaultCV()))

# mymzqc$runQualities <- list(rq)
cat("Constructed file is valid?", isValidMzQC(mymzqc), '\n')
writeMZQC(args[2], mymzqc)
cat(args[2], "written to disk!", '\n')


