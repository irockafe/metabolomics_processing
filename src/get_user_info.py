import os
import pandas as pd
# Goal of this is to define the user-specific things
# Specifically:
# The local path, s3_bucket

# This will run in the makefile the first time it is run, on local machine
# it'll output a dotfile that tells us it has run.


# Get local path
local = '/'.join(os.getcwd().split('/')) + '/'

# Ask for an S3 path
s3 = raw_input('Do you have an S3 bucket? (y/n)' + ' '*10)
if s3 not in ['y', 'n']:
    raise ValueError('You should have typed y or n')
if s3 == 'y':
    s3_path = raw_input('Whats your s3 path? (include the s3://)' + ' '*10)
else:
    s3_path = None

# Create table
df = pd.DataFrame([local, s3_path], index=['local_path', 's3_path'])
df.to_csv(os.getcwd() + '/user_settings.tab', sep='\t', header=False)

# Write out a dotfile that tells us this script has been run before
with open(os.getcwd() + '/.set_user_settings', 'w') as f:
    f.write('I already ran get_user_info.py it created user_settings.tab')
