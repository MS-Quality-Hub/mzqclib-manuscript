#!/usr/local/bin/python

from mzqc import MZQCFile as qc
import click
import logging

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
INFO = '''
A simple QC metric calculator in python using pymzqc to write mzQC output. 
'''

def print_help():
    """
    Print the help of the tool
    :return:
    """
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()


def construct_mzqc(run_name, quality_metric_values):
    infi = qc.InputFile(name=run_name, location=run_name, fileFormat=qc.CvParameter("MS:1001062", "mgf format"))
    anso = qc.AnalysisSoftware(accession="MS:1003357", name="simple_qc_metric_calculator", version="0", uri="https://github.com/MS-Quality-Hub/mzqclib-manuscript")
    meta = qc.MetaDataParameters(inputFiles=[infi],analysisSoftware=[anso], label="implementation-case demo")
    rq = qc.RunQuality(metadata=meta, qualityMetrics=[qm])
    # sq = qc.SetQuality(metadata=meta, qualityMetrics=[qm])
    cv = qc.ControlledVocabulary(name="PSI-MS", uri="https://github.com/HUPO-PSI/psi-ms-CV/releases/download/v4.1.130/psi-ms.obo", version=v4.1.130)
    mzqc = qc.MzQcFile(version="1.0.0", runQualities=[rq], controlledVocabularies=[cv]) 
    return mzqc

def calc_metric():
    pass

@click.command(short_help='correct_mgf_tabs will correct the peak data tab separation in any spectra of the mgf')
@click.argument('mzml_input', type=click.Path(exists=True,readable=True) )  # help="The file with the spectra to analyse"
@click.argument('mzid_input', type=click.Path(exists=True,readable=True) )  # help="The file with the spectrum identifications to analyse"
@click.argument('output_filepath', type=click.Path(writable=True) )  # help="The output destination path for the resulting mzqc"
@click.option('--log', type=click.Choice(['debug', 'info', 'warn'], case_sensitive=False),
    default='warn', show_default=True,
    required=False, help="Log detail level. (verbosity: debug>info>warn)")
def simple_qc_metric_calculator(mzml_input, mzid_input, output_filepath, log):
    """
    ...
    """
    # set loglevel - switch to match-case for py3.10+
    lev = {'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARN }
    logging.basicConfig(format='%(levelname)s:%(message)s', level=lev[log])

    if not any([speclib_input, mgf_input, output_filepath]):
        print_help()

    try:
        pass  # reading the inputs goes here
    except Exception as e:
        click.echo(e)
        print_help()
    
    qm = calc_metric()
    
    mzqc = construct_mzqc(mgf_input,qm)
    with open(output_filepath, "w") as file:
        file.write(qc.JsonSerialisable.ToJson(mzqc, readability=1))
    
if __name__ == '__main__':
    simple_qc_metric_calculator()