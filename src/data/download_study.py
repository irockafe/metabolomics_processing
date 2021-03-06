import subprocess
import os
import argparse
import pipes
import urllib2
import logging
# My code
import sys
src_path = '/home/'
sys.path.append(src_path)
import src.project_fxns.project_fxns as project_fxns

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


def make_dir(abs_path):
    ''' Make a directory in the data/raw/ folder.
    also, create a file, .dirstamp, so that your makefile has
    something to look for.
    '''
    try:
        os.mkdir(abs_path)
    except OSError:
        logger.info('\n' + '-' * 20 + '\n' + 'raw_data directory already exists ' +
              'I think that means you downloaded ' +
              'these files previously. Going to try to download from S3\n' +
              '-'*20)


def download_ftp(ftp_path, output_dir):
    # Recursively download all files from ftp path into your directory
    # pipes.quote puts quotes around a path so that bash will
    # play nicely with whitespace and weird characters ik '()'
    # cut-dirs removes parts of the ftp url that would otherwise
    # be assigned to directories (very annoying)

    # Always three entries when split [ftp:, '', 'hostname']
    # that we handle with -nH, ftp://hostname.org/path/to/things/*
    # Note that we also have a /*, so we exclude the last / when counting
    # directory structures to ignore
    url_dirs_to_cut = len(ftp_path.split('/')[3:-1])
    logger.debug(url_dirs_to_cut)
    wget_command = (
        'nohup wget -r -nH --cut-dirs={cut} '.format(cut=url_dirs_to_cut) +
        '{ftp} -P {dir} --no-verbose &'.format(ftp=ftp_path,
                                               dir=pipes.quote(output_dir),
                                               )
                    )
    subprocess.call(wget_command, shell=True)

# TODO: add an ftp flag so that users can specify non-MTBLS/MWB projects
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



if __name__ == '__main__':
    # Logging
    try:
        os.mkdir('/home/logs/')
    except OSError:
        # if directory already exists
        pass
    logger = logging.getLogger('download_study')
    logger.setLevel(logging.DEBUG)
    fhandler = logging.FileHandler('/home/logs/%s.log' % args.study)
    logger.addHandler(fhandler)
    output_dir = '/home/data/raw/{study}'.format(
            study=args.study)
    make_dir(output_dir)
    # Check if there is an s3 bucket and sync from there if exists
    storage_obj = project_fxns.Storage()
    bucket_exists = storage_obj.bucket_exists(output_dir)
    if bucket_exists:  # sync from s3 and exit script
        storage_obj.sync_to_local(s3_path, args.study, output_dir)
        # exit()
    
    # If didn't find s3 bucket, get ftp link and download from database
    else:
        ftp_path = get_ftp(args.study, metabolights_ftp, metabolomics_workbench_ftp)
        download_ftp(ftp_path, output_dir)
    
