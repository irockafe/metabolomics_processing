import os
import shutil 
import glob
import pandas as pd
import argparse

# Each project can have a summary-file instructing how to move raw data into 
# subfolders for easier xcms processing or organization.
# Essentially, want a tab-delimited file with following conventions:
# The file's name is 'organize_data.tab'
# First line is:
#     PATH {tab} repo_name/path/to/data 
# We need to use a relative path starting with the git repo_name because
# you're testing stuff on multiple computers, and paths change.
#
# All other lines:
#     dir_name {tab} mv_command_1 {tab} mv_command_1 {tab} ...

# Each line (after the first line) of the summary file contains move commands that will organize the data
# Can imagine finding all the organize_data.tab files and running them
# fairly easily (use find, then iterate through each file with this script.

parser = argparse.ArgumentParser()
parser.add_argument('-sf', '--summary-file', 
		    help='Required. Path to a tab-delim summary file that has'
		    ' the path to raw data on the top line. Each successive'
 		    ' row is structured as: "folder_name {tab} command_1'
		    ' {tab} command_2." The commands are simply move'
		    ' commands to move appropriate files into new folders.')

args = parser.parse_args()
summary_file_path = args.summary_file
print summary_file_path
# load summary file to pandas.
df = pd.read_csv(summary_file_path, header=None, 
		 sep='\t', comment='#', skip_blank_lines=True)

print df

# Local paths will vary before the revo_healthcare foldername. Deal with it.
# iterate through each row, making the necessary folder and then
# running the commands
for row_num, vals in df.iterrows():
    # first row is path to raw data. Change to that directory
    if row_num == 0:  
        path_data_invariant = vals[1]
        print path_data_invariant
        repo_name = 'revo_healthcare/'
        path_local = os.getcwd().split(repo_name)[0]
        path = path_local + path_data_invariant
        print path
        os.chdir(path)
        # print glob.glob('*.txt')
    
    # Rest of the rows contain directory names and mv commands
    else:
        # The first column of rows 2-? contain a directory name
        # create the directory
        dir_name = vals[0]
        print dir_name
        try:
            os.mkdir(dir_name)
        except OSError as e:
            if e.errno == 17:
                print '\nDirectory {dir} already exists.'\
                      ' Continuting...\n'.format(dir=dir_name)
        # Run the mv commands
        for val in vals[1:]:
            # if NaN, skip it
            if pd.isnull(val):
                continue
            files = glob.glob(val)
            print files
            for fname in files:
                shutil.move(fname, dir_name)
        
