.PHONY: clean data lint requirements sync_data_to_s3 sync_data_from_s3

#################################################################################
# GLOBALS                                                                       #
#################################################################################
all: raw_data user_settings.tab

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
# Download MTBLS315 and sync to S3
study := MTBLS315
dir := data/raw/
raw_data: $(dir)/$(study)/.dirstamp
# Download data and create .dirstamp if it doesn't already exist
# TODO - how to avoid deleting .dirstamp when I clean up raw
# directory after processing data?
$(dir)/$(study)/.dirstamp: src/data/download_study.py
	python $< --study $(study) 



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



