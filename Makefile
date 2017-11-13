
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

#############################################################################
##                                                                         ##
##                              MTBLS315                                    ##
#############################################################################

###########################
# MTBLS315                 # 
# uhplc_pos             #
###########################

study = MTBLS315
ms_assay = uhplc_pos
organize_file = $(local_path)/user_input/organize_raw_data/organize_data_$(study).tsv
xcms_params = $(local_path)/user_input/xcms_parameters/xcms_params_$(study)_$(ms_assay).tsv


process_raw_data: $(processed_dir)/$(study)/$(ms_assay)/.processing_complete

# file that tells us we've completed processing steps 
# and synched/deleted raw data files to save space 
$(processed_dir)/$(study)/$(ms_assay)/.processing_complete: $(raw_dir)/$(study)/$(ms_assay)/.raw_data_cleaned_up
	touch $@

# Remove the raw data to save space and note that files cleaned up
# TODO sync back to aws..?
$(raw_dir)/$(study)/$(ms_assay)/.raw_data_cleaned_up: $(processed_dir)/$(study)/$(ms_assay)/xcms_result.tsv
	# Delete everything but hidden files
	rm $(raw_dir)/$(study)/$(ms_assay)/*
	# touch the .rw_data_cleaned_up file to tell make you did it
	touch $@

# Output of xcms depends on the (user-provided) Rscript & xcms parameters,
# and that the raw data has been organized into appropriate folders
# (makefile along with organize_data summary file will do that part)
# TODO - change mkdir -p to more generalizable thing using 
# python script and os.mkdir()
$(processed_dir)/$(study)/$(ms_assay)/xcms_result.tsv: src/xcms_wrapper/run_xcms.R $(xcms_params) $(raw_dir)/$(study)/.organize_stamp
	mkdir -p $(processed_dir)/$(study)/$(ms_assay)/
	Rscript $< -s "$(xcms_params)" --data "$(raw_dir)/$(study)/$(ms_assay)/" --output "$(local_path)/$(processed_dir)/$(study)/$(ms_assay)/"


# Organizing raw data depends on the organize_file commands, a script,
# and knowledge that we successfully downloaded these files
# TODO - Need to have a way to undo these move commands if
# you wnat to change  folder names...?
$(raw_dir)/$(study)/.organize_stamp: src/data/organize_raw_data.py $(organize_file) $(raw_dir)/$(study)/.download_stamp
	python $< -f "$(organize_file)"
	touch $@

$(raw_dir)/$(study)/.download_stamp: src/data/download_study.py
	python $< --study $(study)
	touch $@


#############################################################################
##                                                                         ##
##                              MTBLS315                                    ##
#############################################################################

###########################
# MTBLS315                 # 
# uhplc_neg             #
###########################

study = MTBLS315
ms_assay = uhplc_neg
organize_file = $(local_path)/user_input/organize_raw_data/organize_data_$(study).tsv
xcms_params = $(local_path)/user_input/xcms_parameters/xcms_params_$(study)_$(ms_assay).tsv


process_raw_data: $(processed_dir)/$(study)/$(ms_assay)/.processing_complete

# file that tells us we've completed processing steps 
# and synched/deleted raw data files to save space 
$(processed_dir)/$(study)/$(ms_assay)/.processing_complete: $(raw_dir)/$(study)/$(ms_assay)/.raw_data_cleaned_up
	touch $@

# Remove the raw data to save space and note that files cleaned up
# TODO sync back to aws..?
$(raw_dir)/$(study)/$(ms_assay)/.raw_data_cleaned_up: $(processed_dir)/$(study)/$(ms_assay)/xcms_result.tsv
	# Delete everything but hidden files
	rm $(raw_dir)/$(study)/$(ms_assay)/*
	# touch the .rw_data_cleaned_up file to tell make you did it
	touch $@

# Output of xcms depends on the (user-provided) Rscript & xcms parameters,
# and that the raw data has been organized into appropriate folders
# (makefile along with organize_data summary file will do that part)
# TODO - change mkdir -p to more generalizable thing using 
# python script and os.mkdir()
$(processed_dir)/$(study)/$(ms_assay)/xcms_result.tsv: src/xcms_wrapper/run_xcms.R $(xcms_params) $(raw_dir)/$(study)/.organize_stamp
	mkdir -p $(processed_dir)/$(study)/$(ms_assay)/
	Rscript $< -s "$(xcms_params)" --data "$(raw_dir)/$(study)/$(ms_assay)/" --output "$(local_path)/$(processed_dir)/$(study)/$(ms_assay)/"


# Organizing raw data depends on the organize_file commands, a script,
# and knowledge that we successfully downloaded these files
# TODO - Need to have a way to undo these move commands if
# you wnat to change  folder names...?
$(raw_dir)/$(study)/.organize_stamp: src/data/organize_raw_data.py $(organize_file) $(raw_dir)/$(study)/.download_stamp
	python $< -f "$(organize_file)"
	touch $@

$(raw_dir)/$(study)/.download_stamp: src/data/download_study.py
	python $< --study $(study)
	touch $@

