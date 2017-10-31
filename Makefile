.PHONY: clean data lint requirements sync_data_to_s3 sync_data_from_s3

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUCKET = almlab.bucket/isaac/revo_healthcare_data
PROFILE = default
PROJECT_NAME = revo_healthcare
PYTHON_INTERPRETER = python

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Update conda dependencies
#requirements: environment.yml
#	mv environment.yml environment.yml.bak;\
#	conda env export > environment.yml

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



