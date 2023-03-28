#!/usr/local/bin/python
import logging
import pandas as pd
from mzqc import MZQCFile as qc
import click

def print_help():
    """
    Print the help of the tool
    :return:
    """
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()

def dedupe(file):
    for r in file.runQualities:
        # pd.Series(r.qualityMetrics).drop_duplicates(keep='first', inplace=False)  # no exact matches anyway
        dupes = pd.Series([m.accession for m in r.qualityMetrics]).duplicated() 
        # N.B. value diff for the dupes might be prudent here
        for i in pd.Series(r.qualityMetrics)[dupes].index[::-1]:  # keep first, inplace
            r.qualityMetrics.pop(i)
    return file

def merge_single_run_files(file_1,file_2,ignore_location=False):
    """
    merge run quality objects if from the same run
    stop if there are more than one runQualities in either file - we don't cover that here
    runs are considerd the same if location, name, and format match
    returns both files back, 
        - first is the merger result or the first input if they dont match, 
        - second is always second input
    """
    if (file_1.runQualities[0].metadata == file_2.runQualities[0].metadata):
        # then just_merge the qualityMetrics
        file_1.runQualities[0].qualityMetrics.extend(file_2.runQualities[0].qualityMetrics) 
        dedupe(file_1)
        logging.debug("dedupe same metadata")
    elif (file_1.runQualities[0].metadata.inputFiles[0].fileFormat == file_2.runQualities[0].metadata.inputFiles[0].fileFormat) and \
    (file_1.runQualities[0].metadata.inputFiles[0].name == file_2.runQualities[0].metadata.inputFiles[0].name):
        if ignore_location:          
            # then merge the metrics but also the software
            file_1.runQualities[0].qualityMetrics.extend(file_2.runQualities[0].qualityMetrics) 
            file_1.runQualities[0].metadata.analysisSoftware.extend(file_2.runQualities[0].metadata.analysisSoftware) 
            dedupe(file_1)
            logging.debug("dedupe consider loc")
        elif (file_1.runQualities[0].metadata.inputFiles[0].location == file_2.runQualities[0].metadata.inputFiles[0].location):
            # in this case merge the metrics only
            file_1.runQualities[0].qualityMetrics.extend(file_2.runQualities[0].qualityMetrics) 
            dedupe(file_1)
            logging.debug("dedupe ignore loc")
        else:
            file_1.runQualities.append(file_2.runQualities[0])
            logging.debug("append runs")
    else:
        file_1.runQualities.append(file_2.runQualities[0])
        logging.debug("append runs")
    return file_1

def match_and_merge_multi_run_files(file_1,file_2):
    pass

def match_and_merge_sets_files(file_1,file_2):
    pass

@click.command(short_help='mzQC fiels will be merged, where possible runs matched and metrics combined.')
@click.argument('left', type=click.Path(exists=True,readable=True) )  # help="The first (or left) mzQC file"
@click.argument('right', type=click.Path(exists=True,readable=True) )  # help="The second (or right) mzQC file"
@click.argument('output', type=click.Path(writable=True) )  # help="The output destination path for the resulting mzqc"
@click.option('--log', type=click.Choice(['debug', 'info', 'warn'], case_sensitive=False),
    default='warn', show_default=True,
    required=False, help="Log detail level. (verbosity: debug>info>warn)")
def merge_mzqc_files(left, right, output, log):
    # set loglevel - switch to match-case for py3.10+
    lev = {'debug': logging.DEBUG,
     'info': logging.INFO,
     'warn': logging.WARN }
    logging.basicConfig(format='%(levelname)s:%(message)s', level=lev[log])

    with open(left, "r") as file:
        file_left = qc.JsonSerialisable.FromJson(file)
    with open(right, "r") as file:
        file_right = qc.JsonSerialisable.FromJson(file)

    if len(file_left.runQualities) > 1 or len(file_right.runQualities) > 1 :
        raise NotImplementedError("Functionality not covered for files that contain multiple runs. Try a different function!")
    else:
        merged = merge_single_run_files(file_left,file_right,True)

    with open(output, "w") as file:
        file.write(qc.JsonSerialisable.ToJson(merged, readability=1))

if __name__ == '__main__':
    merge_mzqc_files()