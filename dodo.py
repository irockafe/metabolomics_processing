import os
import errno
import yaml
import glob
import multiprocessing
# my code
import sys
src_path = '/home/'
if src_path not in sys.path:
    sys.path.append(src_path)
import src.project_fxns.project_fxns as project_fxns

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

# Tasks ###############################3

def task_process_data():
    '''Download, organize, xcms process raw data, then clean it up
        Requires presence of a yaml file
        See user_input/*.yaml for example yaml file
        TODO: Concretize the yaml format
    '''
    # for loop over entries in STUDY_DICT
    for study in STUDY_DICT.keys():
        path_raw_data = RAW_DIR + '/{study}/'.format(
                study=study)
        # Download study
        yield {
            'targets': [path_raw_data],
            'file_dep': ['src/data/download_study.py'],
            'actions': ['mkdir -p "%s"' % path_raw_data,
                        ('python "%(dependencies)s" ' + '--study %s' % study +
                         ' &> "{path}/.download.log"'.format(path=path_raw_data)
                         )],
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
            'actions': ['python "{py}" -f "{org_file}"'.format(
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

            # If no xcms parameters exist, get them with IPO
            if xcms_param_file not in all_xcms_params:
                yield {
                    'targets': [xcms_param_file],
                    'file_dep': ['src/xcms_wrapper/optimize_xcms_params_ipo.R',
                                 (RAW_DIR + '/{study}/.organize_stamp'.format(
                                   study=study))],
                    'actions': ['mkdir -p "{path}"'.format(path=processed_output_path),
                                ('Rscript src/xcms_wrapper/optimize_xcms_params_ipo.R' +
                                 ' --yaml {yaml}'.format(yaml=yaml_file) +
                                 ' --assay {assay}'.format(assay=assay) +
                                 ' --output {path}'.format(path=
                                      'user_input/xcms_parameters/') +
                                 ' --cores %i' % (CORES) +
                                 ' > "{path}/ipo.log" 2> {path}/ipo.error'.format(
                                     path=processed_output_path)
                                  )],

                    'name': 'optimize_params_ipo_{study}_{assay}'.format(
                        study=study, assay=assay)
                        }
                
                # write out a warning about how the ppm is guesstimated
                warning_file = os.path.join(processed_output_path,
                                            'warnings.log')
                yield {
                    'targets': [warning_file],
                    'actions': [(write_warning, [], {
                        'path': processed_output_path,
                        'study': study, 'assay': assay})],
                    'name': 'warning_file_%s_%s' % (study, assay)
                       }
            # Now that xcms parameters exist, run xcms
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
                'actions': ['mkdir -p "{path}"'.format(path=processed_output_path),
                            ('Rscript src/xcms_wrapper/run_xcms.R ' +
                             '--summaryfile "%s" ' % xcms_param_file +
                             '--data "%s" ' % raw_data_path +
                             '--output "{path}" '.format(
                                path=processed_output_path) +
                             # TODO how to change cores depending on user?
                             '--cores %i' % (CORES) +
                             ' > "{path}/xcms.log" 2> {path}/xcms.error'.format(
                                 path=processed_output_path)
                             )],
                'name': 'run_xcms_{study}_{assay}'.format(study=study,
                                                          assay=assay)
            }

        # Sync raw and processed data back to aws
        raw_data_path = RAW_DIR + '/' + study
        processed_data_path = PROCESSED_DIR + '/' + study
        if S3_PATH:  # sync to s3
            # target paths
            sync_stamp = '.s3_sync_stamp'
            raw_sync_stamp = raw_data_path + '/' + sync_stamp
            proc_sync_stamp = processed_data_path + '/' + sync_stamp
            # file_dep
            xcms_outputs = [os.path.join(PROCESSED_DIR, study,
                            i, 'xcms_result.tsv')  for i in assays]
            yield {# targets are dotfiles that claim we succeeded at this task
                   'targets': [raw_sync_stamp, proc_sync_stamp],
                   # adding two lists of strings makes another list
                   'file_dep': xcms_outputs + ['src/data/download_study.py'],
                   # Sync to s3, raw data and processed data
                   'actions': [('nohup aws s3 sync "{local}" "{s3}"'.format(
                                   local=raw_data_path,
                                   s3=S3_PATH + 'raw/{study}'.format(study=study)
                                   ) +
                                ' &> "{path}/.raw_data_sync_to_aws.log"'.format(
                                    path=raw_data_path)
                                ),
                               ('nohup aws s3 sync "{local}" "{s3}"'.format(
                                   local=processed_data_path,
                                   s3=S3_PATH + '"processed/{study}"'.format(
                                   study=study)
                                   ) +
                                '&> "{path}/.processed_data_sync_to_aws.log"'.format(
                                    path=processed_output_path)
                                ),
                               'touch "{raw}" "{proc}"'.format(
                                   raw = (raw_data_path +
                                       '/' + '.s3_sync_stamp'),
                                   proc = (processed_data_path +
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
