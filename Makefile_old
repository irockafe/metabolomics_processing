.PHONY: clean data lint requirements sync_data_to_s3 sync_data_from_s3

#################################################################################
# GLOBALS                                                                       #
################################################################################
local_path := $(CURDIR)


######################333
all: user_settings.tab raw_data processed_data

# Get user-specific settings - local path and S3 bucket
user_settings.tab: src/get_user_info.py
	python $<



#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Update conda dependencies
#requirements: environment.yml
#	mv environment.yml environment.yml.bak;\
#	conda env export > environment.yml


#########################
# Testing things out		#
#########################
# How the fuck do you make directories?
# maybe just go and make a new makefile with the only goal being 
# to create a directory

###########################
# MTBLS315                #
###########################
### Download MTBLS315 and sync to S3

# Define paths and name of study
study := MTBLS315
raw_dir := data/raw/
processed_dir := data/processed/
organize_file := $(local_path)/data/raw/organize_data_summary_files/organize_data_$(study).tab

# Set targets and dependencies for raw data processing
# This means downloading from database or S3
#    and organizing files into folders
raw_data: $(raw_dir)/$(study)/.dirstamp 
raw_data: $(raw_dir)/$(study)/.organize_stamp
# create a file after organizing files has occurred

# Download data and create .dirstamp if it doesn't already exist
# TODO - how to avoid deleting .dirstamp when I clean up raw
# directory after processing data?
# TODO - separate the download and synch commands
$(raw_dir)/$(study)/.dirstamp: src/data/download_study.py
	python $< --study $(study) 

### Move files into appropriate foldres so that xcms can 
### $^ expands all the prereqs with spaces between
### so command will be: python file.py blahblah.tab
$(raw_dir)/$(study)/.organize_stamp: src/data/organize_raw_data.py $(organize_file)
	python $< -sf $(organize_commands) 

### TODO - figure out how to run xcms on these data
### Run xcms on the dataset
xcms_params := $(local_path)/$(processed_dir)/$(study)/xcms_params.tab
# Depends on raw data processing, 
processed_data: raw_data 
processed_data: $(processed_dir)/$(study)/.dirstamp
processed_data: $(xcms_params)

# Have to create directory, touch .dirstamp file, run script
$(processed_dir)/$(study)/.dirstamp:
	# Insert shit to touch the right folder 
	# Should probably use a make_dir.py or something
	# since this seems common, and probably shouldn't be in 
	# the generic scripts I write
$(xcms_params): src/xcms_wrapper/generate_xcms_params.R
	# Command goes here (users either use a preset as is,
	# or generate and edit themselves
	# TODO - is it smart to rely on external files here?


# have to take xcms_params, data directories, run script on
# each directory with given parameters
# TODO - change this. xcms_output file should depend on script
# TODO - figure out how to get folder paths (from organize_file.tab)
$(processed_dir)/$(study)/$(folder)/xcms_output.csv: src/xcms_wrapper/run_xcms.R $(folder_path) $(organize_commands)


#########################
# ST000450		#
#########################
#### Positive mode

## Convert from weird dataformats to feature table, class labels, metadata
## as dataframe
data/processed/ST000450/pos/X_raw.csv: src/data/datasets/ST000450/ST000450_pos_preprocess.py data/processed/ST000450/pos/ST000450_AN000705_positive_hilic.txt
	python $< 

data/processed/ST000450/pos/y.csv: src/data/datasets/ST000450/ST000450_pos_preprocess.py data/processed/ST000450/pos/ST000450_AN000705_positive_hilic.txt
	python $< 

data/processed/ST000450/pos/metadata.csv: src/data/datasets/ST000450/ST000450_pos_preprocess.py data/processed/ST000450/pos/ST000450_AN000705_positive_hilic.txt
	python $< 





#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



