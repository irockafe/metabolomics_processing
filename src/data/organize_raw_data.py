import os
import shutil
import glob
import yaml as yaml_pkg
import argparse
# import subprocess
# my code
import project_fxns.project_fxns as project_fxns


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--yaml',
                    help='Required. Path to a yaml file'
                    ' containing {study: {assays: {files: [mv command]}}}'
                    ' So, the files dictionary contains mv commands'
                    ' for creating a folder'
                    )
args = parser.parse_args()
yaml_path = args.yaml

yaml = yaml_pkg.load(file(yaml_path, 'r'))
study = yaml.keys()[0]
local_path = project_fxns.get_local_path()
raw_data_path = local_path + 'data/raw/{study}'.format(study=study)
# move into the raw data directory
os.chdir(raw_data_path)

print yaml[study]['assays']
for assay in yaml[study]['assays'].keys():
    # First try to make the new directory for organized files
    organized_dir = raw_data_path + '/{assay}'.format(assay=assay)
    try:
        os.mkdir(organized_dir)
    except OSError as e:
        if e.errno == 17:
            print ('\nDirectory {dir} already exists.'.format(
                    dir=organized_dir) +
                   ' Continuing...\n')
        else:
            print "OS error: {err}".format(err=e)
    
    # Organize commands (unzip, etc) and do them
    # in the current directory (raw data directory)
    org_cmds = yaml[study]['organize']
    for cmd in org_cmds:
        print ('Organize command ', cmd)
        # TODO, this is probably bad security, ppl could insert whatever 
        # commands they wanted here
        subprocess.call(cmd, shell=True)
    # TODO: How to deal with raw files? 

    # Move files from different studies into appropriate folder
    mv_cmds = yaml[study]['assays'][assay]['files']
    print ('commands', mv_cmds)
    for cmd in mv_cmds:
        print ('command', cmd)
        files = glob.glob(cmd)
        print ('\nFiles found', files)
        for fname in files:
            if not os.path.exists(organized_dir + '/' + fname):
                print 'No path exists. Moving file'
                shutil.move(fname, organized_dir)
            else:
                print('File name', fname)
                print 'found existing file. deleting and moving again'
                os.remove(organized_dir + '/' + fname)
                shutil.move(fname, organized_dir)

# Output a .organize_stamp to show that you completed this script
# TODO will these org stamps, when sync'd to S3
# keep the timestamp they have here, or the timestamp from
# when they were downloaded. If timestamp of when downloaded,
# they're likely to be 'up to date' even if I change the scrip

# still in the raw_data directory
# open('.organize_stamp', 'a').close()
# make_organize_stamp = 'touch .organize_stamp'
# subprocess.call(make_organize_stamp, shell=True)
#
