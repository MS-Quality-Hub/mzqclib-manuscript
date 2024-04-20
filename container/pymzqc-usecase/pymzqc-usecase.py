#!/usr/local/bin/python
from collections import defaultdict
import os
import numpy as np
import pandas as pd
import tempfile
from lxml import etree
from pyteomics import mzml, parser as fastaparser
from typing import List, Dict, Union, Tuple, Any
from dataclasses import dataclass, field
import pronto
from datetime import datetime, timedelta
import hashlib
from mzqc import MZQCFile as qc
import click
import logging
import crema

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
	tide_target_file: str = ""  # tide-search target results file
	tide_decoy_file: str = ""  # tide-search decoy results file
	tide_td_pair_file: str = ""  # tide-index target|decoy pair file
	crema_fdr: int = 100  # FDR chosen for crema confidence filter, init default is no filter
	n_pep: int = 0
	n_prot: int = 0
	instrument_type: pronto.Term = None
	checksum: str = ""

def print_help():
	"""
	Print the help of the tool
	"""
	ctx = click.get_current_context()
	click.echo(ctx.get_help())
	ctx.exit()

def pad_lists(listdict: Dict[str,List[Any]], padlist: List[str]): 
	"""
	helper function to make mzML consumption more accessible
	"""
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
	base["scan_id"] = base.native_id.str.extract("scan=(\d+)$").astype(int)

	# some things need to come from the mzml directly via xpath
	# Instrument Type
	psi_ms_url = "https://github.com/HUPO-PSI/psi-ms-CV/releases/download/v4.1.146/psi-ms.obo"
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

def load_ids(run: Run, crux_tide_index:str, crux_tide_search:str, tide_index:str, tide_search:str, fdr: int=1) -> Run:
	"""
	load_ids will load the tide identifications from file and perform FDR with crema and document all the provided Run dataclass
	 
	The function will also add experimentalMassToCharge and calculatedMassToCharge columns , 

	Parameters
	----------
	crux_tide_index : str
			Path of the tide index folder
	
	crux_tide_search : str
			Path of the tide search results folder
	
	tide_index : str
			The file name for the target decoy pairs file in the specified tide index folder

	tide_search : str
			The file name prefix for tide search results in the specified tide search results folder
	
	fdr : int
			The FDR level choice in percent, defaults to 1

	Returns
	-------
	Run
			The Run dataclass with added spectrum identification details

	"""
	PROTON_AMU = 1.0073 
	tide_target_file = os.path.join(crux_tide_search,tide_search+'.target.txt')
	tide_decoy_file = os.path.join(crux_tide_search,tide_search+'.decoy.txt')
	tide_td_pair_file = os.path.join(crux_tide_index,tide_index)

	with open(tide_target_file, 'r') as targets, open(tide_decoy_file, 'r') as decoys:
		#filter all but best PSM per scan
		filtered_tide_target = pd.read_csv(targets, sep='\t').sort_values(by='xcorr score', ascending=False).groupby('scan').head(1)
		filtered_tide_decoy = pd.read_csv(decoys, sep='\t').sort_values(by='xcorr score', ascending=False).groupby('scan').head(1)
		#crema fdr
		psms = crema.read_tide(pd.concat([filtered_tide_target, filtered_tide_decoy]), 
							pairing_file_name=tide_td_pair_file,
							decoy_prefix='DECOY_')
		results =  psms.assign_confidence(score_column="xcorr score", desc=True, pep_fdr_type="peptide-only", threshold=fdr/100)
		prt_df = results.confidence_estimates['proteins']
		#add delta ppm per peptide and fix column names
		pep_df = results.confidence_estimates['peptides'].rename(columns={"scan": "scan_id"}).merge(filtered_tide_target.rename(columns={"scan": "scan_id"})[['scan_id', 'sequence','charge','peptide mass', 'spectrum precursor m/z']], how="inner", on=['scan_id', 'sequence']).rename(columns={"spectrum precursor m/z": "experimentalMassToCharge"})
		pep_df['calculatedMassToCharge'] = (pep_df['peptide mass']+PROTON_AMU*pep_df['charge'])/pep_df['charge']

	run.tide_target_file = tide_target_file
	run.tide_decoy_file = tide_decoy_file
	run.tide_td_pair_file = tide_td_pair_file
	run.crema_fdr = fdr
	run.id_df = pep_df[pep_df['accept']==True]
	run.n_prot = prt_df[prt_df['accept']==True]["protein id"].nunique()
	run.n_pep = run.id_df["sequence"].nunique()

	logging.debug("Registered proteins "+str(run.n_prot))
	logging.debug("Registered peptides "+str(run.n_pep))
	return run

def construct_mzqc(run: Run, quality_metric_values: List[qc.QualityMetric]):
	infi1 = qc.InputFile(name=run.mzml_path, location=run.mzml_path, fileFormat=qc.CvParameter("MS:1000584", "mzML format"))
	infi1.fileProperties.append(qc.CvParameter("MS:1003151", "SHA-256", run.checksum))
	infi1.fileProperties.append(qc.CvParameter(run.instrument_type.id, run.instrument_type.name))
	infi1.fileProperties.append(qc.CvParameter("MS:1000747", "completion time", run.completion_time))
	infi2 = qc.InputFile(name=run.tide_target_file, location=run.tide_target_file, fileFormat=qc.CvParameter("MS:1000914", "tab delimited text format"))
	anso1 = qc.AnalysisSoftware(accession="MS:1002575", name="Tide", version="4.2", uri="https://crux.ms/")
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
	ids_only["MS:1003044"] = [len(fastaparser.cleave(seq, 'trypsin'))-1 for seq in ids_only['sequence'].to_list()]

	mc_or_greater = 3  # i.e. 3 missed cleavages or greater
	ids_only["mc_group"] = np.where(ids_only["MS:1003044"] >= mc_or_greater, str(mc_or_greater), ids_only["MS:1003044"])
	mc_agg = ids_only.groupby("mc_group").agg({'native_id': 'count'}).reset_index().rename(columns={"native_id":"NCIT:C150827", "mc_group": "MS:1003044"})

	metric_value = qc.QualityMetric(accession="MS:4000180", name="table of missed cleavage counts", value={
						"MS:1003044": mc_agg["MS:1003044"].to_list(),
						"NCIT:C150827": mc_agg["NCIT:C150827"].to_list()})
	return metric_value

def calc_metric_deltam(run) -> Tuple[qc.QualityMetric]:
	ids_only = run.base_df.merge(run.id_df, how="inner", on='scan_id')
	SEARCH_ENGINE_FILTER_SETTINGS = 50

	ids_only['mass_error_ppm'] = ids_only.apply(lambda row : 
									getMassError(row['calculatedMassToCharge'], 
						 						 row['experimentalMassToCharge']), axis = 1)\
													.clip(-SEARCH_ENGINE_FILTER_SETTINGS,SEARCH_ENGINE_FILTER_SETTINGS)
	
	logging.debug("theor. "+str(ids_only['calculatedMassToCharge'].to_list()[:10]))
	logging.debug("measu. "+str(ids_only['experimentalMassToCharge'].to_list()[:10]))

	metric_value_mean = qc.QualityMetric(accession="MS:4000178", name="precursor ppm deviation mean", value=ids_only['mass_error_ppm'].mean())
	metric_value_std = qc.QualityMetric(accession="MS:4000179", name="precursor ppm deviation sigma", value=ids_only['mass_error_ppm'].std())
	return metric_value_mean, metric_value_std

def calc_metric_idrtquarters(run) -> qc.QualityMetric:
	ids_only = run.base_df.merge(run.id_df, how="inner", on='scan_id')

	idf_rtsort = ids_only.sort_values(by='RT')
	quarter_ids = idf_rtsort.shape[0] // 4
	idf_rtsort['quarter'] = np.repeat(np.arange(1, 5), [quarter_ids]*3 + [idf_rtsort.shape[0] - quarter_ids*3])  # label row with quarter

	quarter_interval_durations = idf_rtsort.groupby('quarter')['RT'].max() - idf_rtsort.groupby('quarter')['RT'].min()
	ratios = quarter_interval_durations / run.base_df['RT'].max()

	metric_value = qc.QualityMetric(accession="MS:4000181", 
								 name="identified MS2 quarter RT fraction",
								 value=ratios.to_list())
	return metric_value

def calc_metric_idrate(run) -> Tuple[qc.QualityMetric]:
	ids_only = run.base_df.merge(run.id_df, how="inner", on='scan_id')
	cid = qc.QualityMetric(accession="MS:1003251", 
				 			name="count of identified spectra", 
							value= int(ids_only['native_id'].nunique()))
	cms = qc.QualityMetric(accession="MS:4000060", 
							name="number of MS2 spectra", 
							value= int(run.base_df['native_id'].nunique()))
	return cid,cms

def calc_metric_idcounts(run) -> Tuple[qc.QualityMetric]:
	peptide_id = qc.QualityMetric(accession="MS:1003250", 
				 			name="count of identified peptidoforms", 
							value= run.n_pep)
	accession_id = qc.QualityMetric(accession="MS:1002404", 
							name="count of identified proteins", 
							value= run.n_prot)
	return peptide_id,accession_id


@click.command(short_help='correct_mgf_tabs will correct the peak data tab separation in any spectra of the mgf')
@click.argument('mzml_input', type=click.Path(exists=True,readable=True) )  # help="The file with the spectra to analyse"
@click.argument('crux_tide_index', type=click.Path(exists=True,readable=True) )  # help="The file with the spectrum identifications to analyse"
@click.argument('crux_tide_search', type=click.Path(exists=True,readable=True) )  # help="The file with the spectrum identifications to analyse"
@click.argument('mzqc_output', type=click.Path(writable=True, dir_okay=False) )  # help="The output path for the resulting mzqc"
@click.option('--fdr', show_default=True, default=1, help="The FDR value in percent.")
@click.option('--tide_index', show_default=True, default="tide-index.peptides.txt", help="The tide index peptide-pair filename. (Needs to be inside the tide-index directory!)")
@click.option('--tide_search', show_default=True, default="tide-search", help="The tide search file name root (ending in .target.txt and .decoy.txt respectively).")
@click.option('--dev', is_flag=True, show_default=True, default=False, help="Add dataframes to the mzQC (as unofficial 'metrics', which produces a pymzqc readable though non-standard-conform mzqc file).")
@click.option('--log', type=click.Choice(['debug', 'info', 'warn'], case_sensitive=False),
	default='warn', show_default=True,
	required=False, help="Log detail level. (verbosity: debug>info>warn)")
def simple_qc_metric_calculator(mzml_input, crux_tide_index, crux_tide_search, mzqc_output, fdr, tide_index, tide_search, dev, log):
	"""
	main function controlling command-line call parameters and calling high-level functions
	"""
	# set loglevel - switch to match-case for py3.10+
	lev = {'debug': logging.DEBUG,
		'info': logging.INFO,
		'warn': logging.WARN }
	logging.basicConfig(format='%(levelname)s:%(message)s', level=lev[log])


	try:
		logging.debug("starting")
		logging.debug("loading "+str(mzml_input))
		run = load_mzml(mzml_input)
		logging.debug("loaded mzml")
		logging.debug("loading "+str(crux_tide_index)+"@"+str(tide_index))
		logging.debug("loading "+str(crux_tide_search)+"@"+str(tide_search))
		run = load_ids(run, crux_tide_index, crux_tide_search, tide_index, tide_search, fdr)
		logging.debug("loaded ids")
	except Exception as e:
		click.echo(e)
		print_help()
	
	quality_metric_values = [*calc_metric_deltam(run), calc_metric_ioncollection(run), 
						  calc_metric_missedcleavage(run), *calc_metric_idrate(run),
						  *calc_metric_idcounts(run), calc_metric_idrtquarters(run)]
	if dev:
		for n,df in [("base data frame", run.base_df), ("identifications data frame", run.id_df)]:
			quality_metric_values.append(
				qc.QualityMetric(accession="MS:4000005", name=n, value=df.where((pd.notnull(df)), None).to_dict(orient='list'))
			)
	mzqc = construct_mzqc(run, quality_metric_values)

	with open(os.path.join(mzqc_output), "w") as file:
		file.write(qc.JsonSerialisable.ToJson(mzqc, readability=1))
	
if __name__ == '__main__':
	simple_qc_metric_calculator()