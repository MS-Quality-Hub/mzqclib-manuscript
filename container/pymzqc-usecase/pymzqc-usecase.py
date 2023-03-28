#!/usr/local/bin/python
"""exported from ann-solo+mzqc.ipynb"""
""" TODO-s: 
* get accessions into splib
* fix all mods in splib
* directly access ann-solo results 
"""

from mzqc import MZQCFile as qc
import ann_solo
from ann_solo import reader, spectral_library
from ann_solo.config import config
import pandas as pd
from pyteomics import mztab
import tempfile
import fileinput
import sys, os
import shutil
import click
import logging

#python3 spectre_of_spectra.py ${mgf} ${splib} ${mgf.baseName}.pymzqc.mzqc

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
INFO = '''
The selected mgf file has {n} spectra, of which {m} were caught with contaminants. 
'''

#  """using the 'raw' ann-solo command output here"""
# -c /opt/annsolo.ini does not get recognised
#ann_solo /tmp/speclibs/PRIDE_Contaminants_unique_targetdecoy.splib /tmp/tmpe2crfj7g.mgf /tmp/out.mztab --precursor_tolerance_mode ppm --precursor_tolerance_mass 5 --fragment_mz_tolerance 0.47

# ann_solo naughties:
# ann_solo: error: Unable to open config file: /opt/annsolo.ini. Error: No such file or directory
# OSError: [Errno 30] Read-only file system: '/opt/speclibs/PRIDE_Contaminants_unique_targetdecoy_8d8eea4.spcfg' [writing in dir w/o asking]
# AttributeError: module 'scipy.stats' has no attribute 'PearsonRConstantInputWarning' [scipy<1.9 necessary]
# ERROR [root/MainProcess] reader.verify_extension : Unrecognized file format: /tmp/tmpe2crfj7g [needs .mgf extension]
# INFO [root/MainProcess] writer.write_mztab : Save identifications to file /tmp/tmpn4ptoyet.mztab [with call ann_solo.ann_solo(.., ..,	/tmp/tmpn4ptoyet, ..)] 
# reading the mztab ValueError: 22 columns passed, passed data had 21 columns

def print_help():
    """
    Print the help of the tool
    :return:
    """
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()

def use_ann_solo(speclib_input, mgf_input):
    with tempfile.TemporaryDirectory() as dir:
        speclib_input_rw =os.path.join(dir,os.path.basename(speclib_input))
        shutil.copy(speclib_input, os.path.join(dir,os.path.basename(speclib_input)))
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.mzTab') as mztp:
            res = ann_solo.ann_solo(speclib_input_rw,
                mgf_input,
                mztp.name,
                precursor_tolerance_mass=20,
                precursor_tolerance_mode="ppm",
                fragment_mz_tolerance=0.5,
                fdr=0.01,
            )
            for line in fileinput.input([mztp.name], inplace=True):
                if line.strip().startswith('PSH'):
                    line = '\t'.join(line.split('\t')[:-1]) + '\n'
                sys.stdout.write(line)
            spec_catch = mztab.MzTab(mztp.name)
    return spec_catch.spectrum_match_table

def construct_mzqc(run_name, qm):
    infi = qc.InputFile(name=run_name, location=run_name, fileFormat=qc.CvParameter("MS:1001062", "mgf format"))
    anso = qc.AnalysisSoftware(accession="MS:1000xx1", name="ANN-SoLo", version="0.3.3", uri="https://github.com/bittremieux/ANN-SoLo")
    meta = qc.MetaDataParameters(inputFiles=[infi],analysisSoftware=[anso], label="implementation-case demo")
    rq = qc.RunQuality(metadata=meta, qualityMetrics=[qm])
    # sq = qc.SetQuality(metadata=meta, qualityMetrics=[qm])
    cv = qc.ControlledVocabulary(name="PSI-MS", uri="https://raw.githubusercontent.com/HUPO-PSI/psi-ms-CV/master/psi-ms.obo")
    mzqc = qc.MzQcFile(version="1.0.0", runQualities=[rq], controlledVocabularies=[cv]) 
    return mzqc

def calc_contaminant_metric(psms):
    df_unmod = psms[["PSM_ID","retention_time","sequence"]][~psms.sequence.str.contains('\[')]
    df_mod = psms[["PSM_ID","retention_time","sequence"]][psms.sequence.str.contains('\[')]
    
    sequence_counts = df_unmod.sequence.value_counts().reset_index(name = 'count').rename(columns={"index": "contaminant sequence"})
    sequence_counts_sans_ohw = sequence_counts[sequence_counts["count"] > 1]
    fig = sequence_counts_sans_ohw.plot.barh(x="contaminant sequence",y='count',figsize=(6,9))

# [Term]
# id: MS:4000xxx
# name: identified contaminants
# def: "Tabular representation of the peptide sequences associated with of a series of mass spectra of a given run and their respective counts." [PSI:MS]
# is_a: MS:4000005 ! table
# comment: In case the optional native spectrum identifier format column is used the table is expected to be in long format (i.e. the count per spectrum is 1)
# relationship: has_metric_category MS:4000008 ! ID based metric
# relationship: has_metric_category MS:4000012 ! single run based metric
# relationship: has_column MS:1003169 ! proforma peptidoform sequence
# relationship: has_column MS:1002733 ! peptide-level spectral count
# relationship: has_optional_column MS:1000767 ! native spectrum identifier format
    
    metric_txt_1 = "Identified Contaminants\n" + str(sequence_counts_sans_ohw)
    sequence_counts_sans_ohw.columns = ['MS:1003169', 'MS:1002733']
    qm = qc.QualityMetric(accession="MS:4000xx3", name="identified contaminants", 
            value={col: sequence_counts_sans_ohw[col].to_list() for col in sequence_counts_sans_ohw.columns})
        
    one_hit_wonders = ', '.join(sequence_counts[sequence_counts["count"] > 1]["contaminant sequence"].to_list())
    metric_txt_2 = ("Additionally to the above contaminants, we found these each once: {}".format(one_hit_wonders))
    print(metric_txt_1,'\n',metric_txt_2)
    return qm, fig


@click.command(short_help='correct_mgf_tabs will correct the peak data tab separation in any spectra of the mgf')
@click.argument('speclib_input', type=click.Path(exists=True,readable=True) )  # help="The splib file path for the mgf to be searched against")
@click.argument('mgf_input', type=click.Path(exists=True,readable=True) )  # help="The mgf file path to be searched against the splib")
@click.argument('output_filepath', type=click.Path(writable=True) )  # help="The output destination path for the resulting mzqc")
@click.option('-f', '--fig', 'figure', type=click.Path(exists=False,writable=True),
    required=False, help="A visualisation of the contaminant fishing.")
@click.option('--log', type=click.Choice(['debug', 'info', 'warn'], case_sensitive=False),
    default='warn', show_default=True,
    required=False, help="Log detail level. (verbosity: debug>info>warn)")
def fish_for_contaminants(speclib_input, mgf_input, output_filepath, figure, log):
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
        psms = use_ann_solo(speclib_input, mgf_input)
    except Exception as e:
        click.echo(e)
        print_help()
    
    qm,fig = calc_contaminant_metric(psms)
    if figure:
        fig.figure.savefig(figure, dpi=300, bbox_inches='tight')
    
    mzqc = construct_mzqc(mgf_input,qm)
    with open(output_filepath, "w") as file:
        file.write(qc.JsonSerialisable.ToJson(mzqc, readability=1))
    
if __name__ == '__main__':
    fish_for_contaminants()