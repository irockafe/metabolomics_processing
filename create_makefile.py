import argparse
import pandas as pd
# My code
import project_fxns.project_fxns as project_fxns

'''
GOAL - Take a list of study names, organize_data_$(study).tsv, and xcms_params_$(study)_$(assay)
INPUT - A txt file with unique study names on each line (MTBLS or ST format), from Metabolites or Metabolomics Workbench
OUTPUT - Makefile that does the downloading data, grouping data by assay, processing data, and (eventually TODO) building classifiers
'''

# argparse to accept shit
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--studies',
    help= ('Path to a file containing study names from Metabolites or' + 
        'Metabolomics Workbench (MTBLS... or ST...)') 
    )

args = parser.parse_args()


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
    df = pd.read_csv(path, header=None, sep='\t', comment='#',
        skip_blank_lines=True)
    # skip first row if only contains the path to raw data
    assays = (df.iloc[1:,0]
                .tolist() )
    return assays


def get_makefile_txt_invariant():
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
\tpython $<
'''
    return text

def get_makefile_txt(study, assay):
    print study, assay
    text = '''
#############################################################################
##                                                                         ##
##                              {study}                                    ##
#############################################################################

###########################
# {study}                 # 
# {ms_assay}             #
###########################

study = {study}
ms_assay = {ms_assay}
organize_file = $(local_path)/user_input/organize_raw_data/organize_data_$(study).tsv
xcms_params = $(local_path)/user_input/xcms_parameters/xcms_params_$(study)_$(ms_assay).tsv


process_raw_data: $(processed_dir)/$(study)/$(ms_assay)/.processing_complete

# file that tells us we've completed processing steps 
# and synched/deleted raw data files to save space 
$(processed_dir)/$(study)/$(ms_assay)/.processing_complete: $(raw_dir)/$(study)/$(ms_assay)/.raw_data_cleaned_up
\ttouch $@

# Remove the raw data to save space and note that files cleaned up
# TODO sync back to aws..?
$(raw_dir)/$(study)/$(ms_assay)/.raw_data_cleaned_up: $(processed_dir)/$(study)/$(ms_assay)/xcms_result.tsv
\t# Delete everything but hidden files
\trm $(raw_dir)/$(study)/$(ms_assay)/*
\t# touch the .rw_data_cleaned_up file to tell make you did it
\ttouch $@

# Output of xcms depends on the (user-provided) Rscript & xcms parameters,
# and that the raw data has been organized into appropriate folders
# (makefile along with organize_data summary file will do that part)
# TODO - change mkdir -p to more generalizable thing using 
# python script and os.mkdir()
$(processed_dir)/$(study)/$(ms_assay)/xcms_result.tsv: src/xcms_wrapper/run_xcms.R $(xcms_params) $(raw_dir)/$(study)/.organize_stamp
\tmkdir -p $(processed_dir)/$(study)/$(ms_assay)/
\tRscript $< -s "$(xcms_params)" --data "$(raw_dir)/$(study)/$(ms_assay)/" --output "$(local_path)/$(processed_dir)/$(study)/$(ms_assay)/"


# Organizing raw data depends on the organize_file commands, a script,
# and knowledge that we successfully downloaded these files
# TODO - Need to have a way to undo these move commands if
# you wnat to change  folder names...?
$(raw_dir)/$(study)/.organize_stamp: src/data/organize_raw_data.py $(organize_file) $(raw_dir)/$(study)/.download_stamp
\tpython $< -f "$(organize_file)"
\ttouch $@

$(raw_dir)/$(study)/.download_stamp: src/data/download_study.py
\tpython $< --study $(study)
\ttouch $@

'''.format(study=study, ms_assay=assay)
    return text


def stitch_makefile_together(list_of_makefile_text):
    '''
    GOAL - list of text, each entry is some text of the makefile
    '''       
    pass



# get local path (location of user_settings.tab)
local_path = project_fxns.get_local_path() 
# path to user_input files
organize_path = local_path + 'user_input/organize_raw_data/'  

# Collect everything to create final makefile
make_list = []
make_list.append(get_makefile_txt_invariant())

# TODO iterate through each study, assay, write the makefiles for them
if __name__ == "__main__":
    print args.studies
    study_list = parse_study_list(args.studies) 
    print study_list
    for study in study_list:
        path = organize_path + 'organize_data_{study}.tsv'.format(study=study)
        assays = get_assays(path) 
        print assays
        for assay in assays:
            make_list.append(get_makefile_txt(study, assay))

with open('Makefile', 'w') as f:
    for txt in make_list:
        f.write(txt)




