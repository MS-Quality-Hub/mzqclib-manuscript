#!/usr/bin/env nextflow
nextflow.enable.dsl = 1
/*
===============================================================================
            mzqc-usecase workflow v0.0.1
===============================================================================
 @authors
 Mathias Walzer <walzer@ebi.ac.uk>
-------------------------------------------------------------------------------
Pipeline overview:
 - 0:   Converting the RAW data into mzML file
 - 1:   jmzqc squeezes the necessary details out of a mzML file
 - 2:   pymzqc sifts the spectra for known contaminants
 - 3:   rmzqc devises the iRT calibration
 - 4:   a report appears
-------------------------------------------------------------------------------

*/
def helpMessage() {
    log.info"""
    =========================================
    Usage:

    """.stripIndent()
}


/*
 * Config Variables
 */
// show help message if requested
params.help = false
if (params.help){
    helpMessage()
    exit 0
}

if (params.run){
    println("Analysing ${params.run}!")
    raw_file = file(params.run)
}
else{
    helpMessage()
    exit 0
}

/*
 * Process definitions
 */
process rawfileconversion {
    container "${params.thermo_converter.container}"
    memory { params.thermo_converter.memory.GB * task.attempt }
    errorStrategy 'retry'
    maxRetries { params.thermo_converter.maxRetries }
    
	input:
    //file raw_file from "${params.raw_file}"
	
    output:
    file "${raw_file.baseName}.mzML" into mzml_channel_pt1,mzml_channel_pt2,mzml_channel_pt3
    file "${raw_file.baseName}.mgf" into mgf_channel
 
    script:
    """
    ThermoRawFileParser.sh -i=$raw_file -f=2 -b ${raw_file.baseName}.mzML
    ThermoRawFileParser.sh -i=$raw_file -f=0 -b ${raw_file.baseName}.mgf
    """
}


process jmzqc {
    container "${params.jmzqc.container}"
    memory { params.jmzqc.memory.GB * task.attempt }
    errorStrategy 'retry'
    
    input:
    file mzml from mzml_channel_pt1

    output:
    file "${mzml.baseName}.jmzqc.mzqc" into mzqc_channel_pt1

    script:
    """
	jmzqc-cli.sh -f ${mzml} -o ${mzml.baseName}.jmzqc.mzqc
    """
	// alt.: java -jar jmzqc-usecase-1.0.0-SNAPSHOT-cli.jar -f ${mzml} -o ${mzml.baseName}.jmzqc.mzqc
}


process rmzqc {
    container "${params.rmzqc.container}"
    memory { params.rmzqc.memory.GB * task.attempt }
    errorStrategy 'retry'

    input:
    file mzml from mzml_channel_pt2
    file mzqc from mzqc_channel_pt1

    output:
    file "${mzml.baseName}.rmzqc.mzqc" into mzqc_channel_pt2
    //file('test.mztab') into mztab_channel_pt2
	
    """
    rmzqc-cli.sh ${mzml} ${mzml.baseName}.rmzqc.mzqc
	"""
	// alt.: Rscript <path-to-script>/rmzqc-cli.R ${mzml} ${mzml.baseName}.mzqc
}

process pymzqc {
    container "${params.pymzqc.container}"
    memory { params.pymzqc.memory.GB * task.attempt }
    errorStrategy 'retry'

    input:
    file mgf from mgf_channel
    file mzqc from mzqc_channel_pt2

    output:
    file "${mgf.baseName}.pymzqc.mzqc" into mzqc_channel_pt3

    """
	specter_of_spectra.py /opt/speclibs/PRIDE_Contaminants_unique_targetdecoy.splib  ${mgf} ${mgf.baseName}.pymzqc.mzqc
	"""
}


/* process report {
    container "${params.report.container}"
    memory { params.report.memory.GB * task.attempt }
    errorStrategy 'retry'
    publishDir "${params.out_dir}/" , mode: 'copy', pattern: "*.pdf"
    publishDir "${params.out_dir}/" , mode: 'copy', pattern: "*.mzqc"

    input:
    file mzqc from mzqc_channel_pt3

    output:
    file('*.pdf') into report_channel

    script:
    """
    markup_magic.sh -in ${mzqc} -out ${mzqc.baseName}.pdf
	"""
	
	stub:
	"""
	touch test.pdf
    """
} */