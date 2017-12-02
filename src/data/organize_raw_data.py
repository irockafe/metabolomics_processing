import os
import shutil
import glob
import yaml
import argparse
import subprocess
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

yaml = yaml.load(file(yaml_path, 'r'))
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

    # get move commands and run them
    mv_cmds = yaml[study]['assays'][assay]['files']
    print ('commands', mv_cmds)
    for cmd in mv_cmds:
        print ('command', cmd)
        files = glob.glob(cmd)
        print ('\nFiles found', files)
        for fname in files:
            shutil.move(fname, organized_dir)

# Output a .organize_stamp to show that you completed this script
# TODO will these org stamps, when sync'd to S3
# keep the timestamp they have here, or the timestamp from
# when they were downloaded. If timestamp of when downloaded,
# they're likely to be 'up to date' even if I change the scrip
make_organize_stamp = 'touch .organize_stamp'
subprocess.call(make_organize_stamp, shell=True)
#
