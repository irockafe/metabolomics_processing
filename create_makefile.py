'''
GOAL - Take a list of study names, organize_data_{study}.tsv, and xcms_params_{study}_$(assay)
INPUT - A txt file with unique study names on each line (MTBLS or ST format), from Metabolites or Metabolomics Workbench
OUTPUT - Makefile that does the downloading data, grouping data by assay, processing data, and (eventually TODO) building classifiers
'''

def parse_study_list(path):
    '''
    INPUT - path o file containing study name from metabolites and 
        metabolomics workbench
    OUTPUT - a list of file names
    '''
    with open(path) as f:
        study_list = [line.strip() for line in f.readlines()]
    return study_list


def get_assays(path):
    '''
    INPUT - path to organize_raw_data.tsv, which contains the 
        assays in the first column
    '''
    return assays


def write_makefile_invariant():
    '''
    Just output the part of the makefile that doesn't change with 
    study/assay
    '''
    text = '''
#################################################################################
# GLOBALS                                                                       #
################################################################################
local_path := $(CURDIR)
raw_dir = data/raw/
processed_dir = data/processed/


###########################
all: user_settings.tab process_raw_data

# Get user-specific settings - local path and S3 bucket
user_settings.tab: src/get_user_info.py
        python $<
'''
    return text

def write_makefile(study, assay):

    text = '''
#############################################################################
##                                                                         ##
##                              {study}                                    ##
#############################################################################

###########################
# {study}                 # 
# {assay}                 #
###########################

study = {study}
ms_assay = {assay}
organize_file = $(local_path)/user_input/organize_raw_data/organize_data_{study}.tsv
xcms_params = $(local_path)/user_input/xcms_parameters/xcms_params_{study}_{ms_assay}.tsv


process_raw_data: $(processed_dir)/{study}/{ms_assay}/.processing_complete

# file that tells us we've completed processing steps 
# and synched/deleted raw data files to save space 
$(processed_dir)/{study}/{ms_assay}/.processing_complete: $(raw_dir)/{study}/{ms_assay}/.raw_data_cleaned_up
        touch $@


$(raw_dir)/{study}/{ms_assay}/.raw_data_cleaned_up: delete_sync_raw_data.py
$(raw_dir)/{study}/{ms_assay}/.raw_data_cleaned_up: $(processed_dir)/{study}/{ms_assay}/xcms_output.tsv
        # Write and run delete_sync_raw_data.py
        # Or just do it on command line
        touch $@

# Output of xcms depends on the (user-provided) Rscript & xcms parameters,
# and that the raw data has been organized into appropriate folders
# (makefile along with organize_data summary file will do that part)
# TODO - change mkdir -p to more generalizable thing using 
# python script and os.mkdir()
$(processed_dir)/{study}/{ms_assay}/xcms_output.tsv: src/xcms_wrapper/run_xcms.R $(xcms_params) $(raw_dir)/{study}/.organize_stamp
        mkdir -p $(processed_dir)/{study}/{ms_assay}/
        Rscript $< -s "$(xcms_params)" --data "$(raw_dir)/{study}/{ms_assay}/" --output "$(local_path)/$(processed_dir)/{study}/{ms_assay}/"


# Organizing raw data depends on the organize_file commands, a script,
# and knowledge that we successfully downloaded these files
# TODO - Need to have a way to undo these move commands if
# you wnat to change  folder names...?
$(raw_dir)/{study}/.organize_stamp: src/data/organize_raw_data.py $(organize_file) $(raw_dir)/{study}/.download_stamp
        python $< -f "$(organize_file)"
        touch $@

$(raw_dir)/{study}/.download_stamp: src/data/download_study.py
        python $< --study {study}
        touch $@

'''.format(study=study, ms_assay=assay)
    return text


def stitch_makefile_together(list_of_makefile_text):
    '''
    GOAL - list of text, each entry is some text of the makefile
    '''       
    pass



# TODO iterate through each study, assay, write the makefiles for them

