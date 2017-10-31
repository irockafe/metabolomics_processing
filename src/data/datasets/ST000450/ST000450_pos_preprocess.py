import numpy as np
import os
# My code
import data.preprocessing as preproc

# Make local path based on repository name
# Should be able to search and replace if any of this changes
repo_name = 'revo_healthcare'
local_path = os.getcwd().split(repo_name)[0]
project_path = '/%s/data/processed/ST000450/pos/' % repo_name
fname = '/ST000450_AN000705_positive_hilic.txt'
mwtab_path = local_path+project_path+fname

# get feature table,
# class labels (y)
# and metadata from mwtab file
df_raw, y, metadata = preproc.mwtab_to_feature_table(mwtab_path)

# Preprocess feature table
# Replace NaNs
df_raw = df_raw.replace('\N', np.nan)
df_raw = df_raw.astype(float)
# Correct for dilution factors

# write df_raw, metadata, and y to file
df_raw.to_csv(local_path + project_path + 'X_raw.csv')
metadata.to_csv(local_path + project_path + 'metadata.csv')
np.savetxt(local_path + project_path + 'y.csv',
           y, delimiter=',')

#
