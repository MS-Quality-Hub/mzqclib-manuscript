#!/usr/local/bin/python
from collections import defaultdict
import os
from mzqc import MZQCFile as qc
import click
import logging

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(short_help='A simple mzQC file merger using pymzqc assuming file metadata is compatible. ')
@click.argument('mzqc_input', nargs=-1, type=click.Path(exists=True,readable=True, dir_okay=False) )  # help="The mzqc files to merge"
@click.argument('mzqc_output', type=click.Path(writable=True, dir_okay=False) )  # help="The output path for the resulting mzqc"
@click.option('--log', type=click.Choice(['debug', 'info', 'warn'], case_sensitive=False),
	default='warn', show_default=True,
	required=False, help="Log detail level. (verbosity: debug>info>warn)")
def simple_mzqc_merger(mzqc_input, mzqc_output, log):
	"""
	A simple mzQC file merger using pymzqc assuming file metadata is compatible. 
	"""
	# set loglevel - switch to match-case for py3.10+
	lev = {'debug': logging.DEBUG,
		'info': logging.INFO,
		'warn': logging.WARN }
	logging.basicConfig(format='%(levelname)s:%(message)s', level=lev[log])

	try:
		jmzqcs = dict()
		for f in [f for f in mzqc_input if "jmzqc" in f ]:
			with open(f, "r") as mzqcfile:
				mzqcobj = qc.JsonSerialisable.FromJson(mzqcfile)
				jmzqcs[os.path.splitext(os.path.splitext(f)[0])[0]]=mzqcobj
		rmzqcs = dict()
		for f in [f for f in mzqc_input if "rmzqc" in f ]:
			with open(f, "r") as mzqcfile:
				mzqcobj = qc.JsonSerialisable.FromJson(mzqcfile)
				rmzqcs[os.path.splitext(os.path.splitext(f)[0])[0]]=mzqcobj
		pmzqcs = dict()
		for f in [f for f in mzqc_input if "pymzqc" in f ]:
			with open(f, "r") as mzqcfile:
				mzqcobj = qc.JsonSerialisable.FromJson(mzqcfile)
				pmzqcs[os.path.splitext(os.path.splitext(f)[0])[0]]=mzqcobj
		other = dict()
		for f in [f for f in mzqc_input if not("pymzqc" in f) and not("jmzqc" in f) and not("rmzqc" in f)]:
			with open(f, "r") as mzqcfile:
				mzqcobj = qc.JsonSerialisable.FromJson(mzqcfile)
				other[os.path.splitext(f)[0]]=mzqcobj
		click.echo("Found {n} mzqc from jmzqc, \n{m} mzqc from rmzqc, \n{l} mzqc from pymzqc, \nand {i} mzqc from undetermined sources.".format(n=len(jmzqcs), m=len(rmzqcs), l=len(pmzqcs), i=len(other)))
	except Exception as e:
		click.echo(e)
		print_help()

	cv = qc.ControlledVocabulary(name="PSI-MS", uri="https://github.com/HUPO-PSI/psi-ms-CV/releases/download/v4.1.130/psi-ms.obo", version="v4.1.130")
	mergedmzqc = qc.MzQcFile(version="1.0.0", 
					description="Demo mzQC merged from dirfferent qc metric calculators", 
					contactName="mwalzer", 
					contactAddress="https://github.com/MS-Quality-Hub/mzqclib-manuscript", 
					runQualities=[*jmzqcs.values(), *rmzqcs.values(), *pmzqcs.values(), *other.values()], 
					controlledVocabularies=[cv]) 

	with open(os.path.join(mzqc_output), "w") as file:
		file.write(qc.JsonSerialisable.ToJson(mergedmzqc, readability=1))

	click.echo("Files merged. Thank you for doing QC!")

if __name__ == '__main__':
	simple_mzqc_merger()