#!/usr/bin/env nextflow

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
    run_channel = Channel.fromPath( "${params.run}" )
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
    file raw from run_channel

    output:
    file '*.mzML' into mzml_channel

    script:
    """
    ThermoRawFileParser.sh -i ${raw} -o ${raw.baseName}.mzML
    """
}


process jmzqc {
    container "${params.jmzqc.container}"
    memory { params.jmzqc.memory.GB * task.attempt }
    errorStrategy 'retry'
    
    input:
    file mzml from mzml_channel

    output:
    file('*.mzqc') into mzqc_channel
    file('*.mztab') into mztab_channel
    file(mzml) into mzml_channel

    script:
    """
    java -jar decimator_of_msruns.jar --in ${mzml} --out ${mzml.baseName}.mzqc --extra ${mzml.baseName}.mztab
    """
}


process pymzqc {
    container "${params.pymzqc.container}"
    memory { params.pymzqc.memory.GB * task.attempt }
    errorStrategy 'retry'

    input:
    file mzml from mzml_channel
    file mzqc from mzqc_channel

    output:
    file('*.mzqc') into mzqc_channel
    file('*.mztab') into mztab_channel
    file(mzml) into mzml_channel

    script:
    """
    python3 spectre_of_spectra.py --in ${mzml} --mzqc ${mzqc} --out ${mzqc} --extra ${mzml.baseName}.mztab
    """
}


process rmzqc {
    container "${params.rmzqc.container}"
    memory { params.rmzqc.memory.GB * task.attempt }
    errorStrategy 'retry'
    publishDir "${params.out_dir}/" , mode: 'copy', pattern: "*.mzqc"

    input:
    file mzml from mzml_channel
    file mzqc from mzqc_channel

    output:
    file('*.mzqc') into mzqc_channel
    file('*.mztab') into mztab_channel
    file(mzml) into mzml_channel

    """
    Rscript retention_rectifier.R --in ${mzml} --out ${mzml.baseName}.mzqc--mzqc ${mzqc} --out ${mzqc} --extra ${mzml.baseName}.mztab
    """
}


process report {
    container "${params.report.container}"
    memory { params.report.memory.GB * task.attempt }
    errorStrategy 'retry'
    publishDir "${params.out_dir}/" , mode: 'copy', pattern: "*.pdf"

    input:
    file mzqc from mzqc_channel

    output:
    file('*.pdf') into report_channel

    script:
    """
    markup_magic.sh -in ${mzqc} -out ${mzqc.baseName}.pdf
    """
}