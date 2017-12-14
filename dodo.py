import os
import yaml
import glob
import multiprocessing
# my code
import project_fxns.project_fxns as project_fxns
import data.download_study as download_study

# TODO!!! when Rscript fails, it doesn't crash doit. This is annoying and dumb
#       If next tasks depend on that file, fine. it'll crash eventually, but
#       figuring out that it's because of the shitty task that failed is annoying
# TODO!!! S3 sync ends up updating the timestamps on everything
#  to the most recent sync date. That's annoying. Try to 
#  figure out how to make the timestamps be modified time instead
# TODO - make sure you run a script to create user_settings.py
# first

# pydoit file to track dependencies
# and automagically update when things become out of date
# based on timestamp, not MD5 sum
# (b/c we have big files, MD5 sums would be a wste of time
DOIT_CONFIG = {'check_file_uptodate': 'timestamp_newer',
               'verbosity': 2}

# Globals ########
LOCAL_PATH = os.getcwd()
RAW_DIR = LOCAL_PATH + '/data/raw/'
PROCESSED_DIR = LOCAL_PATH + '/data/processed/'
CORES = multiprocessing.cpu_count()
# only one line in s3 path
# TODO make sure this works if they don't provide a path
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


def sync_to_s3(study, raw_data_path):
    if S3_PATH:
        # sync raw data
        download_study.s3_sync_to_aws(S3_PATH, study,
            raw_data_path)  #path to mtbls315)


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

            # If xcms parameters already exist, run xcms
            if xcms_param_file in all_xcms_params:
                print 'params file', xcms_param_file
                print 'all params files', all_xcms_params
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
                print 'Didnt find xcms params. Generating with IPO'
                yield {
                    'targets': [xcms_param_file],
                    'file_dep': ['src/xcms_wrapper/optimize_xcms_params_ipo.R',
                                 (RAW_DIR + '/{study}/.organize_stamp'.format(
                                   study=study))],
                    'actions': [('Rscript src/xcms_wrapper/optimize_xcms_params_ipo.R' +
                                 ' --yaml {yaml}'.format(yaml=yaml_file) +
                                 ' --assay {assay}'.format(assay=assay) +
                                 ' --output {path}'.format(path=
                                      'user_input/xcms_parameters/') +
                                 ' --cores %i' % (CORES)
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
                    'actions': [('Rscript src/xcms_wrapper/run_xcms.R' +
                                 ' --summaryfile "%s" ' % xcms_param_file +
                                 ' --data "%s" ' % raw_data_path +
                                 ' --output "{path}" '.format(
                                    path=processed_output_path) +
                                 # TODO how to change cores depending on user?
                                 ' --cores %i' % (CORES)
                                 )],
                    'name': 'run_xcms_{study}_{assay}'.format(study=study,
                                                              assay=assay)
                         }
                # write out a warning about the ppm
                msg = ('\n%s_%s: ppm might need to ' % (study, assay) +
                       'be adjusted. I guesstimatedsed the ppm' +
                       'based on the mass-spec listed in the .yaml file ' +
                       'Make sure to check the log files to see if' +
                       'there are errors or warnings\n'
                       )

                with open('warnings.log', 'a') as f:
                    f.write(msg)

        # Sync raw and processed data back to aws
        raw_data_path = RAW_DIR + '/' + study
        if S3_PATH:  # sync to s3
            # target paths
            sync_stamp = '.s3_sync_stamp'
            raw_sync_stamp = raw_data_path + '/' + sync_stamp
            proc_sync_stamp = processed_output_path + '/' + sync_stamp
            # file_dep
            xcms_outputs = [os.path.join(PROCESSED_DIR, study,
                            i, 'xcms_result.tsv')  for i in assays]
            yield {# targets are dotfiles that claim we succeeded at this task
                   'targets': [raw_sync_stamp, proc_sync_stamp],
                   # adding two lists of strings makes another list
                   'file_dep': xcms_outputs + ['src/data/download_study.py'],
                   # action is a python function! :)
                   # see python-action in pydoit documentation
                   'actions': [(download_study.s3_sync_to_aws,
                                   [S3_PATH, study, raw_data_path]),
                               (download_study.s3_sync_to_aws,
                                   [S3_PATH, study, processed_output_path]),
                               'touch {raw} {proc}'.format(
                                   raw = (raw_data_path +
                                       '/' + '.s3_sync_stamp'),
                                   proc = (processed_output_path +
                                           '/' + '.s3_sync_stamp')
                                )
                               ],
                   'name': 'sync_to_aws_{study}'.format(study=study)
                   }

        # clean-up raw data folder of everything except dot files
        # means need to traverse directory tree and run rm * in each subfolder
        cleaned_stamp = raw_data_path + '/' + '.cleaned_up'
        yield {'targets': [cleaned_stamp],
               'file_dep': xcms_outputs,  # is a list
               'actions': [(delete_recursive, [], {'path': raw_data_path,
                               'delete_hidden': False}),
                           'touch {clean_up}'.format(clean_up=cleaned_stamp)
                           ],
               'name': 'clean_up_{study}'.format(study=study)
               }

# TODO tasks to process xcms_results files
#
