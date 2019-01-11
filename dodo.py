import os
import errno
import yaml
import glob
import multiprocessing
import logging
import doit
# my code
import src.project_fxns.project_fxns as project_fxns

# To run: >> doit study={study_name}
# where study_name is from Metabolights or Metabolomics Workbench.
# doit will run IPO to generate decent xcms parameters and then xcms
# using those parameters

# TODO!!! when Rscript fails, it doesn't crash doit. This is annoying and dumb
#       If next tasks depend on that file, fine. it'll crash eventually, but
#       figuring out that it's because of the shitty task that failed is annoying
#       Maybe a task dependency is in order?
# TODO!!! S3 sync ends up updating the timestamps on everything
#  to the most recent sync date. That's annoying. Try to
#  figure out how to make the timestamps be modified time instead
# TODO - make sure you run a script to create user_settings.py
# first
# TODO - CAMERA

# pydoit file to track dependencies
# and automagically update when things become out of date
# based on timestamp, not MD5 sum
# (b/c we have big files, MD5 sums would be a wste of time

DOIT_CONFIG = {'check_file_uptodate': 'timestamp_newer',
               'verbosity': 2}

# Globals ########
LOCAL_PATH = os.getcwd()  # In container, this is /home/
RAW_DIR = LOCAL_PATH + '/data/raw/'
PROCESSED_DIR = LOCAL_PATH + '/data/processed/'
CORES = multiprocessing.cpu_count()
USER_INFO = project_fxns.Storage()
CLOUD_PATH = USER_INFO.cloud_url_base
organize_dir = LOCAL_PATH + '/user_input/study_info/'

# Get the study name from command line
# raise an error if they leave out the study parameter
study_name = doit.get_var('study')
if study_name == None:
    raise ValueError, ('\nYou need to pass the parameter "study"'+
            ' to doit.\n\tExample: doit study=MTBLS315')


# Get the summary file for the study & raise error if doesn't exist
summary_file = os.path.join(organize_dir + '%s.yaml' % study_name)
if not os.path.isfile(summary_file):
    raise IOError(('\nCould not find file {sf} \nRemember, you need' +
            ' to provide the yaml file in /user_input/study_info/'+
            ' for proper processing').format(sf=summary_file))
# get a dictionary of {study: [assay1, assay2]}
# i.e. {MTBLS315: [pos, neg], ...}
STUDY_DICT = {}
my_yaml = yaml.load(file(summary_file, 'r'))
# First entry should be for a single experiment ID
# i.e. MTBLS315
study_name = my_yaml.keys()[0]
STUDY_DICT[study_name] = my_yaml[study_name]['assays'].keys()


# Useful Functions ################
# TODO move these into their own folder, maybe? less cluttered?
def delete_recursive(path, delete_hidden=False):
    '''
    Walk down a directory and delete files recursively
    '''
    for root, dirs, files in os.walk(path):
        for name in files:
            if delete_hidden:
                os.remove(os.path.join(root, name))
            # ignore dotfiles
            if not delete_hidden:
                if name[0] != '.':
                    os.remove(os.path.join(root, name))


def write_warning(path, study, assay):
    msg = ('\n%s_%s: ppm might need to ' % (study, assay) +
           'be adjusted. I guesstimatedsed the ppm' +
           'based on the mass-spec listed in the .yaml file ' +
           'Make sure to check the log files to see if' +
           'there are errors or warnings\n'
           )
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    with open('{path}/warnings.log'.format(path=path), 'a') as f:
        f.write(msg)

# Tasks ###############################
def task_clean_up():
    # Will delete files, while leaving empty directories behind.
    for study in STUDY_DICT.keys():
        assays = STUDY_DICT[study]
        xcms_outputs = [os.path.join(PROCESSED_DIR, study,
                                assay, 'xcms_result.tsv')
                        for assay in assays]
        #delete_processed = ['rm -r /home/data/processed/{study}/{assay}/*'.format(
        #    study=study, assay=assay) for assay in assays]

        yield {'targets': [],
               'file_dep': xcms_outputs,  # is a list - proves that ran xcms properly
               # Only delete data if synced to cloud
               'task_dep':['sync_to_cloud:%s' % study],
               # delete the contents of data/raw/{stud}
               # and data/processed/study/{assay}/*
               'actions':['rm -r data/raw/%s/*' % study], # + delete_processed,
               'name': '%s' % study,
               }


def task_sync_to_cloud():
    # for loop over en tries in STUDY_DICT
    for study in STUDY_DICT.keys():
        path_raw_data = RAW_DIR + '/{study}/'.format(
                study=study)
        assays = STUDY_DICT[study]
        xcms_param_path = '/home/user_input/xcms_parameters/'
        assays = STUDY_DICT[study]
        xcms_param_path = (LOCAL_PATH + '/user_input/xcms_parameters/')
        all_xcms_params = glob.glob(xcms_param_path + 'xcms_params*.yml')
        # go through assays (uplc_pos, uplc_neg, etc)
        # Sync raw and processed data back to aws
        raw_data_path = os.path.join(RAW_DIR, study)
        processed_data_path = os.path.join(PROCESSED_DIR, study)
        # Only sync if sync if in a supported cloud
        if USER_INFO.cloud_provider in ['amazon', 'google']:
            # the xcms output files
            xcms_outputs = [os.path.join(PROCESSED_DIR, study,
                                assay, 'xcms_result.tsv')  for assay in assays]
            storage_fxns = project_fxns.Storage()
            yield {# Should I have targets for this?
                   'targets': [],
                   # adding two lists of strings makes another list
                   # Should add project_fxns to this, but
                   # don't want to rerun everything until finalized
                   'file_dep': xcms_outputs + ['src/data/download_study.py'],
                   'task_dep': ['xcms:run_xcms_{study}_{assay}'.format(study=study,
                                                          assay=assay)],
                   # Sync to cloud storage - raw data, processed data,
                   # and newly defined parameters (user_input folder)
                   'actions': [
                       (storage_fxns.sync_to_storage, [raw_data_path,
                           raw_data_path.replace('/home/', '')]),
                       (storage_fxns.sync_to_storage, [processed_data_path,
                           processed_data_path.replace('/home/', '')]),
                       (storage_fxns.sync_to_storage, ['/home/user_input',
                           'user_input'])
                       ],
                   'name': '%s' % study
                   }
        else:   # If no cloud storage bucket, don't try to sync to it.
            pass


def task_xcms():
    # loop over studies in STUDY_DICT
    for study in STUDY_DICT.keys():
        path_raw_data = RAW_DIR + '/{study}/'.format(
                study=study)
        yaml_file = 'user_input/study_info/{study}.yaml'.format(
                             study=study)
        # Run xcms to process the raw data
        assays = STUDY_DICT[study]
        xcms_param_path = (LOCAL_PATH + '/user_input/xcms_parameters/')
        all_xcms_params = glob.glob(xcms_param_path + 'xcms_params*.yml')
        # Optimize parameters for each assay, unless a
        # parameters file already exists, then run
        # xcms with those parameters
        for assay in assays:
            xcms_param_file = (xcms_param_path +
                               'xcms_params_{study}_{assay}.yml'.format(
                                  study=study, assay=assay))
            raw_data_path = RAW_DIR + '/%s/%s/' % (study, assay)
            processed_output_path = PROCESSED_DIR + '{study}/{assay}/'.format(
                study=study, assay=assay)
            # If no xcms parameters exist, get them with IPO
            if xcms_param_file not in all_xcms_params:
                yield {
                    'targets': [xcms_param_file],
                    'file_dep': ['src/xcms_wrapper/optimize_xcms_params_ipo.R',
                        yaml_file],
                    'task_dep': ['organize_data:%s' % study],
                    'actions': ['mkdir -p "{path}"'.format(
                                    path=processed_output_path),
                                ('Rscript src/xcms_wrapper/optimize_xcms_params_ipo.R' +
                                 ' --yaml {yaml}'.format(yaml=yaml_file) +
                                 ' --assay {assay}'.format(assay=assay) +
                                 ' --output {path}'.format(
                                     path='user_input/xcms_parameters/') +
                                 ' --cores %i' % (CORES) +
                                 ' > "{path}/ipo.log" 2> {path}/ipo.error'.format(
                                     path=processed_output_path)
                                  )],

                    'name': 'optimize_params_ipo_{study}_{assay}'.format(
                        study=study, assay=assay)
                    }
            # Now that xcms parameters exist, run xcms
            yield {
                'targets': [(PROCESSED_DIR +
                            '{study}/{assay}/xcms_result.tsv'.format(
                                study=study, assay=assay)
                             )],
                'file_dep': ['src/xcms_wrapper/run_xcms.R',
                             xcms_param_file
                              ],
                # Don't depend on optimize params task,
                # b/c you might import params from elsewhere,
                # without needing to run IPO
                'task_dep': ['organize_data:%s' % study],
                'actions': ['mkdir -p "{path}"'.format(path=processed_output_path),
                            ('Rscript src/xcms_wrapper/run_xcms.R ' +
                             ' --summaryfile "%s" ' % xcms_param_file +
                             ' --data "%s" ' % raw_data_path +
                             ' --output "{path}" '.format(
                                path=processed_output_path) +
                             ' --cores %i' % (CORES) +
                             ' > "{path}/xcms.log" 2> {path}/xcms.error'.format(
                                 path=processed_output_path)
                             )],
                'name': 'run_xcms_{study}_{assay}'.format(study=study,
                                                          assay=assay)
            }




def task_organize_data():
    for study in STUDY_DICT.keys():
        path_raw_data = RAW_DIR + '/{study}/'.format(
                study=study)

        # Organize the raw data
        org_script = 'src/data/organize_raw_data.py'
        yaml_file = ('/home/user_input/study_info/{study}.yaml'.format(
                             study=study)
                         )
        yield {
            # TODO how to target the moved files..?
            'targets': [],
            # TODO should this depend on having the downloaded files?
            # Otherwise, i can delete the downloaded things, and
            # pydoit won't know that it happened
            'file_dep': [org_script, yaml_file,
                         ],
            # Need to have downloaded raw data
            'task_dep': ['download_data:%s' % study],
            'actions': ['python "{py}" -f "{org_file}"'.format(
                            py=org_script, org_file=yaml_file)
                        ],
            'name': '%s' % study
                }


def task_download_data():
# for loop over entries in STUDY_DICT
    for study in STUDY_DICT.keys():
        path_raw_data = RAW_DIR + '/{study}/'.format(
                study=study)
        # Download study
        yield {
                #TODO How to target the (unknown) downloaded files?
            'targets': [path_raw_data],
            'file_dep': ['src/data/download_study.py'],
            # No task_deps, should be first thing
            'task_dep':[],
            'actions': ['mkdir -p "%s"' % path_raw_data,
                        ('python "%(dependencies)s" ' + '--study %s' % study
                         )],
            'name': '%s' % study
                }




'''
def task_process_data():
    # for loop over entries in STUDY_DICT
    for study in STUDY_DICT.keys():
        path_raw_data = RAW_DIR + '/{study}/'.format(
                study=study)
        assays = STUDY_DICT[study]
        xcms_param_path = '/home/user_input/xcms_parameters/'
        print xcms_param_path
        all_xcms_params = glob.glob(xcms_param_path + 'xcms_params*.tsv')
        print('XCMS params files\n', all_xcms_params)
        # go through assays (uplc_pos, uplc_neg, etc)
        for assay in assays:
            xcms_param_file = (xcms_param_path +
                               'xcms_params_{study}_{assay}.tsv'.format(
                                  study=study, assay=assay))
            raw_data_path = RAW_DIR + '/%s/%s/' % (study, assay)
            print 'raw data path', raw_data_path
            processed_output_path = PROCESSED_DIR + '{study}/{assay}/'.format(
                study=study, assay=assay)
'''

# TODO tasks to process xcms_results files
#
