import subprocess
import os
import argparse
import pipes
import urllib2
import pandas as pd
# My code
import project_fxns.project_fxns as project_fxns

# Use this script to download files from Metabolights IDs or
# Metabolomics workbench Study IDs.
# Usage - python scriptname.py --study MTBLSxxxx
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--study',
                    help='Required. Name of the study, i.e. MTBLS315, '
                    'or ST000392')
parser.add_argument('-o', '--output',
                    help='Optional. Base directory Where you want to download'
                    'files to.'
                    '(default is current directory). Will make a new directory')
args = parser.parse_args()

metabolights_ftp = ('ftp://ftp.ebi.ac.uk/pub/databases/' +
                    'metabolights/studies/public/')
metabolomics_workbench_ftp = ('ftp://www.metabolomicsworkbench.org/Studies/')

"""
def walk_up(target):
    # Walk up directory until find target file/directory
    pwd = os.getcwd()
    lst = os.listdir(pwd)
    if target in lst:
        out = pwd + '/' + target
        return out
    else:
        os.chdir('..')
        out = walk_up(target)
    return out
"""
"""
def get_user_settings():
    '''
    GOAL - walk up directories until you find user_settings.tab,
        file containing user defined stuff
    '''
    user_settings_path = walk_up('user_settings.tab')
    pd.set_option("display.max_colwidth", 10000)
    user_settings = pd.read_csv(user_settings_path, sep='\t',
                                header=None, index_col=0,
                                dtype=str)
    return user_settings
"""


def s3_bucket_exists(s3_path, study):
    # Test if bucket exists on S3 based on s3_path string and
    # study string and sync if it does

    # check if bucket exists
    ls_s3 = 'aws s3 ls {s3_path}raw/{study}'.format(s3_path=s3_path,
                                                    study=study)
    print 'ls_s3 ', ls_s3
    check_bucket = subprocess.call(ls_s3, shell=True)
    if check_bucket == 0:
        return True
    else:
        return False

"""
def get_s3_path(study):
    user_settings = get_user_settings()
    s3_path = user_settings.loc['s3_path'].to_string(index=False, header=False)
    return s3_path
"""


def s3_sync_to_aws(s3_path, study, output_dir):
    sync = ("nohup aws s3 sync '{dir}' '{s3}raw/{study}' ".format(
            s3=s3_path, study=study, dir=output_dir)
            )
    print ('\n\nUploading data to S3 here \n{s3}'.format(s3=sync))
    subprocess.call(sync, shell=True)


def s3_sync_to_local(s3_path, study, output_dir):
    sync = ("nohup aws s3 sync '{s3}raw/{study}' ".format(
            s3=s3_path, study=study) +
            "'{dir}'".format(dir=output_dir)
            )
    print ('\n\nDownloading from S3 - if you want to re-download dataset' +
           ' please delete the S3 bucket (future humans, please ' +
           'make this better)\n\n')
    subprocess.call(sync, shell=True)


def get_mtbls_ftp(study, mtbls_base):
    # Goal is ftp://path/to/stuff/*
    ftp = mtbls_base + study + '/*'
    return ftp


def get_workbench_ftp(study, mwb_base):
    '''
    Given Metabolomics Workbench study (ST...), check if .zip extension
    or .7z extension is correct, then return the ftp link
    '''
    # touch to see if file is .zip or .7z format
    ftp = mwb_base + study
    # try .zip extension
    req = url_exists(ftp + '.zip')
    if req:
        return ftp + '.zip'
    # try .7z extension
    req = url_exists(ftp + '.7z')
    if req:
        return ftp + '.7z'
    # If couldn't find ftp with those extensions, raise an error
    else:
        raise NameError('We tried out .zip and .7z extensions, but couldnt' +
                        ' find {ftp} with those extensions'.format(ftp=ftp)
                        )


def url_exists(url):
    '''
    Test if an http or ftp url exists
    Return True if exists, False otherwise
    '''
    request = urllib2.Request(url)
    request.get_method = lambda: 'HEAD'
    try:
        urllib2.urlopen(request)
        return True
    except:
        return False


def get_ftp(study, ftp_mtbls, ftp_mwb):
    '''
    given a study name from mtbls or mwb, get the ftp link
    '''
    if 'MTBLS' == study[0:5]:
        ftp_path = get_mtbls_ftp(study, ftp_mtbls)
        return ftp_path
    elif 'ST' == study[0:2]:
        ftp_path = get_workbench_ftp(study, ftp_mwb)
        return ftp_path
    else:
        raise NameError('Code only accepts Metabolights IDs (MTBLS...) and' +
                        'Metabolomics Workbench Study IDs (ST...) project names'
                        )


def make_dir(study):
    ''' Make a directory in the data/raw/ folder.
    also, create a file, .dirstamp, so that your makefile has
    something to look for.
    '''
    user_settings = project_fxns.get_user_settings()
    local_path = user_settings.loc['local_path'].to_string(index=False,
                                                           header=False)
    directory = '{local}/data/raw/{study}'.format(local=local_path,
                                                  study=study)
    try:
        os.mkdir(directory)
    except OSError:
        print('\n' + '-' * 20 + '\n' + 'raw_data directory already exists ' +
              'I think that means you downloaded ' +
              'these files previously. Going to try to download from S3\n' +
              '-'*20)
    return directory


def download_ftp(ftp_path, output_dir):
    # Recursively download all files from ftp path into your directory
    # pipes.quote puts quotes around a path so that bash will
    # play nicely with whitespace and weird characters ik '()'
    # cut-dirs removes parts of the ftp url that would otherwise
    # be assigned to directories (very annoying)

    # Always three entries when split [ftp:, '', 'hostname']
    # that we handle with -nH, ftp://hostname.org/path/to/things/*
    # Note that we also have a /*, so we exclude the last / when counting
    # directorystructures to ignore
    url_dirs_to_cut = len(ftp_path.split('/')[3:-1])
    print url_dirs_to_cut
    wget_command = (
        'nohup wget -r -nH --cut-dirs={cut} ' +
        '{ftp} -P {dir} --no-verbose &'.format(ftp=ftp_path,
                                               dir=pipes.quote(output_dir),
                                               cut=url_dirs_to_cut)
                    )
    subprocess.call(wget_command, shell=True)


output_dir = make_dir(args.study)
# Check if there is an s3 bucket and sync from there if exists
s3_path = project_fxns.get_s3_path(args.study)
s3_exists = s3_bucket_exists(s3_path, args.study)
if s3_exists:  # sync from s3 and exit script
    s3_sync_to_local(s3_path, args.study, output_dir)
    # exit()

# If didn't find s3 bucket, get ftp link and download from database
else:
    ftp_path = get_ftp(args.study, metabolights_ftp, metabolomics_workbench_ftp)
    download_ftp(ftp_path, output_dir)

# If script is successful, make a file-stamp telling me
# that download was successful
make_dirstamp = "touch '{dir}/.download_stamp'".format(
            dir=output_dir)
subprocess.call(make_dirstamp, shell=True)

# sync to aws
if s3_path:  # Assumes that will return None if no S3 specified
    s3_sync_to_aws(s3_path, args.study, output_dir)
#
