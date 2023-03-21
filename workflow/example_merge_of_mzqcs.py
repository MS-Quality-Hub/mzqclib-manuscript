from mzqc import MZQCFile as qc

def merge_single_run_files(file_1,file_2,ignore_location=False):
    """
    merge run quality objects if from the same run
    stop if there are more than one runQualities in either file - we don't cover that here
    runs are considerd the same if location, name, and format match
    returns both files back, 
        - first is the merger result or the first input if they dont match, 
        - second is always second input
    """
    if len(file_1.runQualities) > 1 or len(file_2.runQualities):
        raise NotImplementedError("Functionality not covered for files that contain multiple runs. Try a different function!")
    if (file_1.runQualities[0].metadata == file_2.runQualities[0].metadata):
        # then just_merge the qualityMetrics
        file_1.runQualities[0].qualityMetrics.extend(file_2.runQualities[0].qualityMetrics) 
        # TODO dedupe
    elif (file_1.runQualities[0].metadata.inputFiles[0].fileFormat == file_2.runQualities[0].metadata.inputFiles[0].fileFormat) and \
            (file_1.runQualities[0].metadata.inputFiles[0].name == file_2.runQualities[0].metadata.inputFiles[0].name):
        if not ignore_location and (file_1.runQualities[0].metadata.inputFiles[0].location == file_2.runQualities[0].metadata.inputFiles[0].location) :
            # then merge the QMs but also the software
            file_1.runQualities[0].qualityMetrics.extend(file_2.runQualities[0].qualityMetrics) 
            file_1.runQualities[0].analysisSoftware.extend(file_2.runQualities[0].analysisSoftware) 
            # TODO dedupe
    return file_1, file_2

def match_and_merge_multi_run_files(file_1,file_2):
    pass

def match_and_merge_sets_files(file_1,file_2):
    pass

with open("tests/examples/jmzqc-usecase.mzqc", "r") as file:
            file_1 = qc.JsonSerialisable.FromJson(file)

with open("tests/examples/rmzqc-usecase.mzqc", "r") as file:
            file_2 = qc.JsonSerialisable.FromJson(file)
