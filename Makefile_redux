.PHONY: clean data lint requirements sync_data_to_s3 sync_data_from_s3

#################################################################################
# GLOBALS                                                                       #
################################################################################
local_path := $(CURDIR)


###########################
all: user_settings.tab process_raw_data

# Get user-specific settings - local path and S3 bucket
user_settings.tab: src/get_user_info.py
        python $<

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Update conda dependencies
#requirements: environment.yml
#       mv environment.yml environment.yml.bak;\
#       conda env export > environment.yml

###########################
# MTBLS315                #
###########################
study = MTBLS315
raw_dir = data/raw/
processed_dir = data/processed/
folder = uhplc_pos
organize_file = $(local_path)/$(raw_dir)/organize_data_summary_files/organize_data_$(study).tab
xcms_params = $(local_path)/$(processed_dir)/$(study)/xcms_params.tab

# file that tells us we've completed processing steps 
# and synched/deleted raw data files to save space 
$(processed_dir)/$(study)/$(folder)/.processing_complete: $(raw_dir)/$(study)/$(folder)/.raw_data_cleaned_up


$(raw_dir)/$(study)/$(folder)/.raw_data_cleaned_up: delete_sync_raw_data.py
$(raw_dir)/$(study)/$(folder)/.raw_data_cleaned_up: $(processed_dir)/$(study)/$(folder)/xcms_output.tsv
	# Write and run delete_sync_raw_data.py
	# Or just do it on command line

$(processed_dir)/$(study)/$(folder)/xcms_output.tsv: src/xcms_wrapper/run_xcms.R 	











