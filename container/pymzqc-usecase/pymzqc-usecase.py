#!/usr/local/bin/python
from collections import defaultdict
import os
import numpy as np
import pandas as pd
from pyteomics import mzml, mzid, parser as fastaparser
from typing import List, Dict, Union, Any
from dataclasses import dataclass, field
import pronto
from lxml import etree
from datetime import datetime, timedelta
import hashlib
from mzqc import MZQCFile as qc
import click
import logging

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
INFO = '''
A simple QC metric calculator in python using pymzqc to write mzQC output. 
'''

@dataclass
class Run:
	run_name: str = ""
	start_time: datetime = datetime.now()
	completion_time: datetime = datetime.now()
	base_df: pd.DataFrame = pd.DataFrame()
	id_df: pd.DataFrame = pd.DataFrame()
	mzml_path: str = ""
	mzid_path: str = ""
	instrument_type: pronto.Term = None
	checksum: str = ""

def print_help():
	"""
	Print the help of the tool
	:return:
	"""
	ctx = click.get_current_context()
	click.echo(ctx.get_help())
	ctx.exit()

def pad_lists(listdict: Dict[str,List[Any]], padlist: List[str]): 
	for pl in padlist:
		listdict[pl].append(np.nan)

def sha256fromfile(abs_file_path: str) -> str:
	"""
	sha256fromfile will create a sha256 digest from the file at given path.

	To preserve memory and speed up the digest,
	the file is digested with the help of a memoryview and hashlib.sha256().update.

	Parameters
	----------
	abs_file_path : str
			The absolute path to the file to digest

	Returns
	-------
	str
			The cast or unchanged argument

	Raises
	------
	FileNotFoundError
			If abs_file_path is not a file  
	"""
	sha = hashlib.sha256()
	b = bytearray(128 * 1024)
	mv = memoryview(b)

	with open(abs_file_path, 'rb', buffering=0) as f:
		for n in iter(lambda: f.readinto(mv), 0):
			sha.update(mv[:n])
	return sha.hexdigest()

def getMassError(theo_mz: float, exp_mz: float, use_ppm: bool = True) -> float:
	"""
	getMassError convenience function to easily switch the delta mass to either [ppm] or [Da] format.

	Given two masses, the calculated result will be the delta mass, in [ppm] if requested.
	The difference is **not** absolute.

	Parameters
	----------
	theo_mz : float
			First mass
	exp_mz : float
			Second mass
	use_ppm : bool, optional
			switch from simple [Da] difference to [ppm], by default True

	Returns
	-------
	float
			[description]
	"""
	error: float = (exp_mz - theo_mz)
	if use_ppm:
		error = error / (theo_mz * 1e-6)
	return error

def comet_evalue(psm):
	return next(iter(psm.get("SpectrumIdentificationItem"))).get("Comet:expectation value")

def getMetricSourceFramesIdent(fdr) -> pd.DataFrame:
	data_acquisition: Dict[str,List[Any]] = defaultdict(list)
	for qvt in fdr:
		psm_rep = next(iter(qvt[3]['SpectrumIdentificationItem']))
		data_acquisition['scan_id'].append(qvt[3]['spectrumID'])		
		data_acquisition['fd-ratio'].append(qvt[0])		
		data_acquisition['q-value'].append(qvt[2])		
		data_acquisition['chargeState'].append(psm_rep['chargeState'])
		data_acquisition['experimentalMassToCharge'].append(psm_rep['experimentalMassToCharge'])
		data_acquisition['calculatedMassToCharge'].append(psm_rep['calculatedMassToCharge'])
		data_acquisition['isDecoy'].append(qvt[1])
		data_acquisition['PeptideSequence'].append(psm_rep['PeptideSequence'])
		data_acquisition['accession'].append(next(iter(psm_rep['PeptideEvidenceRef']))['accession'])
		data_acquisition['number_matched_peaks'].append(psm_rep['number of matched peaks'])
		data_acquisition['number_unmatched_peak'].append(psm_rep['number of unmatched peaks'])
		data_acquisition['Comet:xcorr'].append(psm_rep['Comet:xcorr'])
		data_acquisition['Comet:deltacn'].append(psm_rep['Comet:deltacn'])
		data_acquisition['Comet:spscore'].append(psm_rep['Comet:spscore'])
		data_acquisition['Comet:sprank'].append(psm_rep['Comet:sprank'])
		data_acquisition['Comet:expectation value'].append(psm_rep['Comet:expectation value'])
	return pd.DataFrame(data_acquisition)

def getMetricSourceFramesBase(run: mzml.MzML) -> pd.DataFrame:     
	data_acquisition: Dict[str,List[Any]] = defaultdict(list)
	mslevelcounts: Dict[int,int] = defaultdict(int)
	ms2_only_padlist = ['precursor_int','precursor_c','precursor_mz','activation_method','activation_energy','isolation_window_target_mz','isolation_window_lower_offset','isolation_window_upper_offset']
	for spectrum in run:
		nid = spectrum['id']
		# NOTE this __ONLY__ considers the first scan each, and the first scan window each!		
		if len(spectrum['scanList']['scan']) < 1:
			logging.warn("Scan {} empty, ignoring.".format(nid))
			continue
		if len(spectrum['scanList']['scan']) > 1:
			logging.warn("Scan {} has more than one spectrum, ignoring all but first.".format(nid))			
		if next(iter(spectrum['scanList']['scan']))['scanWindowList']['count'] < 1:
			logging.warn("Scan {} has no window, ignoring.".format(nid))
			continue
		if next(iter(spectrum['scanList']['scan']))['scanWindowList']['count'] > 1:
			logging.warn("Scan {} has more than one window, ignoring all but first.".format(nid))

		preset_min_mz = next(iter(next(iter(spectrum['scanList']['scan']))['scanWindowList']['scanWindow']))['scan window lower limit']
		preset_max_mz = next(iter(next(iter(spectrum['scanList']['scan']))['scanWindowList']['scanWindow']))['scan window upper limit']
		actual_min_mz = spectrum['lowest observed m/z']
		actual_max_mz = spectrum['highest observed m/z']

		rt_sec = next(iter((spectrum['scanList']['scan'])))['scan start time']
		inj_msec = next(iter((spectrum['scanList']['scan'])))['ion injection time']

		mslevelcounts[spectrum['ms level']] += 1
	
		data_acquisition['RT'].append(rt_sec)
		data_acquisition['native_id'].append(nid)
		data_acquisition['peakcount'].append(spectrum['intensity array'].size)
		data_acquisition['int_sum'].append(spectrum['intensity array'].sum())
		data_acquisition['traptime'].append(inj_msec)
		data_acquisition['ms_level'].append(spectrum['ms level'])

		if "MSn spectrum" in spectrum:
			if len(spectrum["precursorList"]['precursor']) < 1:
				logging.warn("Scan {} empty, ignoring.".format(nid))
				pad_lists(data_acquisition, ms2_only_padlist)
				continue
			if len(spectrum["precursorList"]['precursor']) > 1:
				logging.warn("Scan {} has more than one spectrum, ignoring all but first.".format(nid))
			
			if len(next(iter(spectrum["precursorList"]['precursor']))["selectedIonList"]['selectedIon']) > 1: 
				logging.warn("Scan {} has more than one selected ion, ignoring all but first.".format(nid))
			
			data_acquisition['precursor_int'].append(next(iter(next(iter(spectrum["precursorList"]['precursor']))["selectedIonList"]['selectedIon'])).get('peak intensity', np.nan))
			data_acquisition['precursor_c'].append(next(iter(next(iter(spectrum["precursorList"]['precursor']))["selectedIonList"]['selectedIon']))['charge state'])
			data_acquisition['precursor_mz'].append(next(iter(next(iter(spectrum["precursorList"]['precursor']))["selectedIonList"]['selectedIon']))['selected ion m/z'])
			data_acquisition['activation_method'].append(next(iter([x[0] for x in next(iter(spectrum["precursorList"]['precursor']))['activation'].items() if x[1] == ''])))
			data_acquisition['activation_energy'].append(next(iter(spectrum["precursorList"]['precursor']))['activation']['collision energy'])
			data_acquisition['isolation_window_target_mz'].append(next(iter((spectrum["precursorList"]['precursor'])))['isolationWindow']['isolation window target m/z'])
			data_acquisition['isolation_window_lower_offset'].append(next(iter((spectrum["precursorList"]['precursor'])))['isolationWindow']['isolation window lower offset'])
			data_acquisition['isolation_window_upper_offset'].append(next(iter((spectrum["precursorList"]['precursor'])))['isolationWindow']['isolation window upper offset'])

		else:
			pad_lists(data_acquisition, ms2_only_padlist)
		
	return pd.DataFrame(data_acquisition)

def load_mzml(mzml_path: str) -> Run:
	name = os.path.splitext(os.path.basename(mzml_path))[0]

	with mzml.read(mzml_path) as reader:
		base = getMetricSourceFramesBase(reader)
	base["scan_id"] = base.native_id.str.extract("scan=(\d+)$")

	# some things need to come from the mzml directly via xpath
	# Instrument Type
	psi_ms_url = "https://github.com/HUPO-PSI/psi-ms-CV/releases/download/v4.1.130/psi-ms.obo"
	doc = etree.parse(mzml_path)
	r = doc.xpath('/x:indexedmzML/x:mzML/x:referenceableParamGroupList/x:referenceableParamGroup/x:cvParam', namespaces={'x': "http://psi.hupo.org/ms/mzml"})
	ms = pronto.Ontology(psi_ms_url, import_depth=0)
	cv_instruments  = {x.id for x in ms['MS:1000031'].subclasses().to_set()}
	mzml_instrument = {tag.attrib.get("accession",None) for tag in r if tag.attrib.get("accession",None) in cv_instruments}
	if len(mzml_instrument) > 1:
		logging.warn("Provided mzML has more than one instrument registered, ignoring all but first.")
	itype = ms.get(next(iter(mzml_instrument)))
	# Start time
	s = doc.xpath('/x:indexedmzML/x:mzML/x:run[@startTimeStamp]', namespaces={'x': "http://psi.hupo.org/ms/mzml"})
	strt = pd.to_datetime(s[0].attrib.get('startTimeStamp',datetime.now().isoformat()))

	cmplt = strt + timedelta(seconds=base["RT"].max())
	chksm = sha256fromfile(mzml_path)

	return Run(run_name=name, start_time=strt, completion_time=cmplt, base_df=base, mzml_path=mzml_path, instrument_type=itype, checksum=chksm)

def load_ids(run: Run, mzid_path:str, fdr: int=5) -> Run:
	# idf = mzid.DataFrame(mzid_path)  # does not work as input to qvalues
	# pre_fdr = mzid.qvalues(idf, key='Comet:expectation value', reverse=False)  # KeyError: 'SpectrumIdentificationItem'
	try:
		pre_fdr = mzid.qvalues(mzid_path, key=comet_evalue, reverse=False, full_output=True)
		ids = getMetricSourceFramesIdent(pre_fdr)
		# filtered = ids[(ids['isDecoy'] == True) & (ids['q-value'] < 0.01)].drop_duplicates(subset='scan_id', keep='first')
		if 0 < fdr < 100: 
			ids = ids[(ids['isDecoy'] == True) & (ids['q-value'] < fdr/100 )].drop_duplicates(subset='scan_id', keep='first')
	except:
		ids = None
	run.mzid_path = mzid_path
	run.id_df = ids
	return run

def construct_mzqc(run: Run, quality_metric_values: List[qc.QualityMetric]):
	infi1 = qc.InputFile(name=run.mzml_path, location=run.mzml_path, fileFormat=qc.CvParameter("MS:1000584", "mzML format"))
	infi1.fileProperties.append(qc.CvParameter("MS:1003151", "SHA-256", run.checksum))
	infi1.fileProperties.append(qc.CvParameter(run.instrument_type.id, run.instrument_type.name))
	infi1.fileProperties.append(qc.CvParameter("MS:1000747", "completion time", run.completion_time))
	infi2 = qc.InputFile(name=run.mzid_path, location=run.mzid_path, fileFormat=qc.CvParameter("MS:1002073", "mzIdentML format"))
	anso1 = qc.AnalysisSoftware(accession="MS:1002251", name="Comet", version="version 2023.01 rev. 0", uri="https://github.com/UWPR/Comet")
	anso2 = qc.AnalysisSoftware(accession="MS:1003357", name="simple qc metric calculator", version="0", uri="https://github.com/MS-Quality-Hub/mzqclib-manuscript")
	meta = qc.MetaDataParameters(inputFiles=[infi1, infi2],analysisSoftware=[anso1, anso2], label="implementation-case demo")
	rq = qc.RunQuality(metadata=meta, qualityMetrics=quality_metric_values)
	cv = qc.ControlledVocabulary(name="PSI-MS", uri="https://github.com/HUPO-PSI/psi-ms-CV/releases/download/v4.1.130/psi-ms.obo", version="v4.1.130")
	mzqc = qc.MzQcFile(version="1.0.0", description="Demo mzQC created from a simple qc metric calculator", contactName="mwalzer", 
		    contactAddress="https://github.com/MS-Quality-Hub/mzqclib-manuscript", runQualities=[rq], controlledVocabularies=[cv]) 
	return mzqc

def calc_metric_ioncollection(run) -> qc.QualityMetric:
	ids_only = run.base_df.merge(run.id_df, how="inner", on='scan_id')
	metric_value = qc.QualityMetric(accession="MS:4000105", name="ion injection parameters", value={
											"MS:1000767": ids_only['native_id'].to_list(), 
											"MS:1000927": ids_only['traptime'].to_list(),
											"MS:1000511": ids_only['ms_level'].to_list(),
											"MS:1000500": (ids_only['isolation_window_target_mz'] + ids_only['isolation_window_upper_offset']).to_list(),
											"MS:1000501": (ids_only['isolation_window_target_mz'] - ids_only['isolation_window_lower_offset']).to_list()})
	return metric_value

def calc_metric_missedcleavage(run) -> qc.QualityMetric:
	ids_only = run.base_df.merge(run.id_df, how="inner", on='scan_id')
	mcs =[len(fastaparser.cleave(seq, 'trypsin'))-1 for seq in ids_only['PeptideSequence'].to_list()]
	metric_value = qc.QualityMetric(accession="MS:4000005", name="enzyme digestion parameters", value={
											'MS:1003169': ids_only['PeptideSequence'].to_list(),
											"MS:1000767": ids_only['native_id'].to_list(), 
											"MS:1000927": mcs})
	return metric_value

def calc_metric_deltam(run) -> qc.QualityMetric:
	ids_only = run.base_df.merge(run.id_df, how="inner", on='scan_id')
	ids_only['mass_error_ppm'] = ids_only.apply(lambda row : getMassError(row['calculatedMassToCharge'], row['experimentalMassToCharge']), axis = 1).abs()
	metric_value = qc.QualityMetric(accession="MS:4000078", name="QC2 sample mass accuracies", value={
											'MS:1003169': ids_only['PeptideSequence'].to_list(), 
										    "MS:4000072": ids_only['mass_error_ppm'].to_list()})
	return metric_value
			    
@click.command(short_help='correct_mgf_tabs will correct the peak data tab separation in any spectra of the mgf')
@click.argument('mzml_input', type=click.Path(exists=True,readable=True) )  # help="The file with the spectra to analyse"
@click.argument('mzid_input', type=click.Path(exists=True,readable=True) )  # help="The file with the spectrum identifications to analyse"
@click.argument('output_filepath', type=click.Path(writable=True) )  # help="The output destination path for the resulting mzqc"
@click.option('--dev',  is_flag=True, show_default=True, default=False, help="Add dataframes to the mzQC (as unofficial 'metrics').")
@click.option('--log', type=click.Choice(['debug', 'info', 'warn'], case_sensitive=False),
	default='warn', show_default=True,
	required=False, help="Log detail level. (verbosity: debug>info>warn)")
def simple_qc_metric_calculator(mzml_input, mzid_input, output_filepath, dev, log):
	"""
	...
	"""
	# set loglevel - switch to match-case for py3.10+
	lev = {'debug': logging.DEBUG,
		'info': logging.INFO,
		'warn': logging.WARN }
	logging.basicConfig(format='%(levelname)s:%(message)s', level=lev[log])

	if not any([mzml_input, mzid_input, output_filepath]):
		print_help()

	# mzml_input = "test_data/iPRG2015/JD_06232014_sample3_C.mzML"
	# mzid_input = "test_data/iPRG2015/JD_06232014_sample3_C.mzid"
	try:
		run = load_mzml(mzml_input)
		run = load_ids(run, mzid_input)
	except Exception as e:
		click.echo(e)
		print_help()
	
	quality_metric_values = [calc_metric_deltam(run), calc_metric_ioncollection(run), calc_metric_missedcleavage(run)]
	if dev:
		for n,df in [("base data frame", run.base_df), ("identifications data frame", run.id_df)]:
			quality_metric_values.append(
				qc.QualityMetric(accession="MS:4000005", name=n, value=df.to_dict(orient='list'))
			)
	mzqc = construct_mzqc(run, quality_metric_values)
	with open(os.path.join(output_filepath, run.run_name+".mzQC"), "w") as file:
		file.write(qc.JsonSerialisable.ToJson(mzqc, readability=1))
	
if __name__ == '__main__':
	simple_qc_metric_calculator()