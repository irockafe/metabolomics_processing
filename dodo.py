import os
import yaml
import glob
import multiprocessing
# my code
import project_fxns.project_fxns as project_fxns
import data.download_study as download_study
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
RAW_DIR = LOCAL_PATH + '/data/raw/'
PROCESSED_DIR = LOCAL_PATH + '/data/processed/'
CORES = multiprocessing.cpu_count() 
# only one line in s3 path
with open(LOCAL_PATH + '/user_input/s3_path.txt') as f:
    S3_PATH = f.readlines()[0].strip()
print S3_PATH
# get studies - redundant for getting oranize files
organize_dir = LOCAL_PATH + '/user_input/study_info/'
file_organizers = glob.glob(organize_dir + '*.yaml')
# get a dictionary of {study: [assay1, assay2]}
# i.e. {MTBLS315: [pos, neg], ...}
STUDY_DICT = {}
for f in file_organizers:
    my_yaml = yaml.load(file(f, 'r'))
    # First entry should be for a single experiment ID
    # i.e. MTBLS315
    study_name = my_yaml.keys()[0]
    STUDY_DICT[study_name] = my_yaml[study_name]['assays'].keys()
print('Study Dicitonary\n', STUDY_DICT)

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
            if not delete_hidden:
                if file[0] != '.':
                    os.remove(os.path.join(root, name))


# Tasks ###############################3

def task_process_data():
    '''Download, organize, xcms process raw data, then clean it up
        Requires presence of a yaml file
        See user_input/*.yaml for example yaml file
        TODO: Concretize the yaml format
    '''
    # for loop over entries in STUDY_DICT
    for study in STUDY_DICT.keys():
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
        yaml_file = ('{local_dir}/user_input/study_info/'.format(
                            local_dir=LOCAL_PATH) +
                         '{study}.yaml'.format(
                             study=study)
                         )
        organize_stamp = RAW_DIR + '/{study}/.organize_stamp'.format(
                            study=study)
        yield {
            'targets': [organize_stamp],
            'file_dep': [org_script,
                         yaml_file,
                         # Need to have downloaded raw data
                         ('{raw_dir}/{study}/.download_stamp'.format(
                             raw_dir=RAW_DIR, study=study))
                         ],
            'actions': ['python {py} -f "{org_file}"'.format(
                            py=org_script, org_file=yaml_file),
                        'touch "{stamp}"'.format(stamp=organize_stamp)
                        ],
            'name': 'organize_{study}'.format(study=study)
                }

        # Run xcms to process the raw data
        assays = STUDY_DICT[study]
        xcms_param_path = (LOCAL_PATH + '/user_input/xcms_parameters/')
        print xcms_param_path
        all_xcms_params = glob.glob(xcms_param_path + 'xcms_params*.tsv')
        print('XCMS params files\n', all_xcms_params)
        for assay in assays:
            # If xcms parameters exist, just run xcms with those parameters
            xcms_param_file = (xcms_param_path +
                               'xcms_params_{study}_{assay}.tsv'.format(
                                  study=study, assay=assay))
            raw_data_path = RAW_DIR + '/%s/%s/' % (study, assay)
            print 'raw data path', raw_data_path
            processed_output_path = PROCESSED_DIR + '{study}/{assay}/'.format(
                study=study, assay=assay)

            # If xcms parameters already exist
            if xcms_param_file in all_xcms_params:
                yield {
                    'targets': [(PROCESSED_DIR +
                                '{study}/{assay}/xcms_result.tsv'.format(
                                    study=study, assay=assay)
                                 )],
                    'file_dep': ['src/xcms_wrapper/run_xcms.R',
                                 (RAW_DIR + '/{study}/.organize_stamp'.format(
                                    study=study)),
                                 xcms_param_file
                                  ],
                    'actions': [('Rscript src/xcms_wrapper/run_xcms.R ' +
                                 '--summaryfile "%s" ' % xcms_param_file +
                                 '--data "%s" ' % raw_data_path +
                                 '--output "{path}" '.format(
                                    path=processed_output_path) +
                                 # TODO how to change cores depending on user?
                                 '--cores %i' % (CORES) 
                                 )],
                    'name': 'run_xcms_{study}_{assay}'.format(study=study,
                                                              assay=assay)
                }

            else:
                # Else, run IPO to generate/optimize params
                yield {
                    'targets': [xcms_param_file],
                    'file_dep': ['src/xcms_wrapper/optimize_xcms_params_ipo.R',
                                 (RAW_DIR + '/{study}/.organize_stamp'.format(
                                   study=study))],
                    'actions': [('Rscript src/xcms_wrapper/' +
                                 'optimize_xcms_params_ipo.R' + 
                                 '--yaml {yaml}'.format(yaml=yaml_file) +
                                 '--output {path}'.format(path=
                                     'user_input/xcms_parameters/') +
                                 '--cores %i' % (CORES)
                                  )],

                    'name': 'optimize_params_ipo_{study}_{assay}'.format(
                        study=study, assay=assay)
                        }
                # then run xcms with the new parameters
                yield {
                    'targets': [(PROCESSED_DIR +
                                '{study}/{assay}/xcms_result.tsv'.format(
                                    study=study, assay=assay)
                                 )],
                    'file_dep': ['src/xcms_wrapper/run_xcms.R',
                                 (RAW_DIR + '/{study}/.organize_stamp'.format(
                                    study=study)),
                                 ('/user_input/xcms_parameters/' +
                                    'xcms_params_' +
                                    '{study}_{assay}.tsv'.format(
                                        study=study, assay=assay))
                                  ],
                    'actions': [('Rscript src/xcms_wrapper/run_xcms.R ' +
                                 '--summaryfile "%s" ' % xcms_param_file +
                                 '--data "%s" ' % raw_data_path +
                                 '--output "{path}" '.format(
                                    path=processed_output_path) +
                                 # TODO how to change cores depending on user?
                                 '--cores %i' % (CORES) 
                                 )],
                    'name': 'run_xcms_{study}_{assay}'.format(study=study,
                                                              assay=assay)
                # write out a warning about the ppm 
                msg = ('\n%s_%s: ppm might need to ' % (study, assay)
                       'be adjusted. I guesstimatedsed the ppm' +
                       'based on the mass-spec listed in the .yaml file ' +
                       'Make sure to check the log files to see if' +
                       'there are errors or warnings\n'
                }
                with open('warnings.log', 'a') as f:
                    f.write(msg)
        
        # Sync raw and processed data back to aws 
        raw_data_path = RAW_DIR + '/' + study
        s3_path = project_fxns.get_s3_path(study)        
        if s3_path:
            # sync raw data
            download_study.s3_sync_to_aws(s3_path, study, 
                raw_data_path)  #path to mtbls315)
        # clean-up raw data folder of everything except dot files
        # means need to traverse directory tree and run rm * in each subfolder
        delete_recursive(raw_data_path, delete_hidden=False)
#
