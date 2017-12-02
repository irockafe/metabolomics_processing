import os
import yaml
import glob

# TODO - make sure you run a script to create user_settings.py
# first

# pydoit file to track dependencies
# and automagically update when things become out of date
# based on timestamp, not MD5 sum
# (b/c we have big files, MD5 sums would be a wste of time
DOIT_CONFIG = {'check_file_uptodate': 'timestamp',
               'verbosity': 2}

# Globals ########
LOCAL_PATH = os.getcwd()
# only one line in s3 path
with open(LOCAL_PATH + '/user_input/s3_path.txt') as f:
    S3_PATH = f.readlines()[0].strip()
print S3_PATH

# get studies - redundant for getting oranize files
# study_list_path = LOCAL_PATH + '/user_input/study_list.txt'
# with open(study_list_path) as f:
#     study_list = [line.strip() for line in f.readlines()]

# get a dictionary of {study: [assay1, assay2]}
organize_dir = LOCAL_PATH + '/user_input/organize_raw_data/'
file_organizers = glob.glob(organize_dir + '*.yaml')
STUDY_DICT = {}
for f in file_organizers:
    my_yaml = yaml.load(file(f, 'r'))
    # First entry should be for a single experiment ID
    # i.e. MTBLS315
    STUDY_DICT[my_yaml.keys()[0]] = my_yaml[my_yaml.keys()[0]]
print STUDY_DICT

# Tasks ###############################3
RAW_DIR = LOCAL_PATH + '/data/raw/'


def task_process_data():
    '''Download, organize, xcms process raw data, then clean it up'''
    # for loop over entries in STUDY_DICT
    for study in STUDY_DICT.keys():
        assays = STUDY_DICT[study]['assays'].keys()
        # Download study
        yield {
            'targets': [RAW_DIR + '/{study}/.download_stamp'.format(
                study=study)],
            'file_dep': ['src/data/download_study.py'],
            'actions': ['python %(dependencies)s ' + '--study %s' % study],
            'name': 'download_%s' % study
                }

        # Organize the raw data
        org_script = 'src/data/organize_raw_data.py'
        organize_file = ('{local_dir}/user_input/organize_raw_data/'.format(
                            local_dir=LOCAL_PATH) +
                         'organize_data_{study}.yaml'.format(
                             study=study)
                         )

        # TODO modify organize_raw_data script to use yaml files
        yield {
            'targets': [RAW_DIR + '/{study}/.organize_stamp'.format(
                study=study)],
            'file_dep': [org_script,
                         organize_file,
                         # Need to have downloaded raw data
                         ('{raw_dir}/{study}/.download_stamp'.format(
                             raw_dir=RAW_DIR, study=study))
                         ],
            'actions': ['python {py} -f "{org_file}"'.format(
                            py=org_script, org_file=organize_file),
                        'touch "%(targets)s"'
                        ],
            'name': 'organize_{study}'.format(study=study)
                }
        for assay in assays:
            # xcms task, using xcms() fxn
            '''
            yield {
                'targets':
                'file_dep':
                'actions':
                'name':
            }
            '''
            pass
            # clean-up raw data generator task to remove raw data from local
#
