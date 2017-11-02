import subprocess
import os
import argparse
import pipes
import pandas as pd


# Use this script to download files from ftp links.
# It contains a dictionary {ID: ftp_path} from Metabolights and
# Metabolomics Workbench, so you only have to specify
# an id.
# Otherwise you can to specify an http or ftp link yourself


parser = argparse.ArgumentParser()
parser.add_argument('-s', '--study',
                    help='Required. Name of the study, i.e. MTBLS315, '
                    'or ST000392')
parser.add_argument('-o', '--output',
                    help='Optional. Base directory Where you want to download'
                    'files to.'
                    '(default is current directory). Will make a new directory')
parser.add_argument('-ftp',
                    help='Optional. Path to an ftp link.'
                    'All files will be downloaded from that link')
args = parser.parse_args()

metabolights_ftp = ('ftp://ftp.ebi.ac.uk/pub/databases/' +
                    'metabolights/studies/public/')
metabolomics_workbench_ftp = ('ftp://www.metabolomicsworkbench.org/Studies/')


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


def s3_bucket_exists(s3_path, study):
    # Test if bucket exists on S3 based on s3_path string and
    # study string and sync if it does
     
    # check if bucket exists
    ls_s3 = 'aws s3 ls {s3_path}raw/{study}'.format(
    					s3_path=s3_path,
       					study=study)
    print 'ls_s3 ', ls_s3
    check_bucket = subprocess.call(ls_s3, shell=True)
    if check_bucket == 0:
        return True
    else:
        return False


def download_data(study, ftp_path=None):
    '''
    Download data. If in S3, get it from there.
    If you've already downloaded the data, make a dotfile so that
    makefile can tell you have downloaded and deleted files..
    '''
    # get local_path and s3_path (if exists)
    user_settings = get_user_settings()
    s3_path = user_settings.loc['s3_path'].to_string(index=False, header=False)
    local_path = user_settings.loc['local_path'].to_string(index=False,
                                                           header=False)
    directory = '{local}/data/raw/{study}'.format(local=local_path,
                                                  study=study)
    try:
        os.mkdir(directory)
    except OSError:
        print('\n'+'-'*20 + '\n' +  'directory already exists ' +
              'I think that means you downloaded ' +
              'these files previously. Going to try to download from S3\n' +
              '-'*20)
    # Check if study already in s3, if so, download it from there
    # instead of the internets
    if s3_path:
        bucket_exists = s3_bucket_exists(s3_path, study)
        # check if bucket exists
        if bucket_exists:
            # sync bucket
            sync = ('nohup aws s3 sync {s3}raw/{study} '.format(
        		s3=s3_path, study=study) +
        	    '{dir}'.format(dir=directory)
        	    )
            print 'sync  command', sync
            subprocess.call(sync, shell=True)
        else:
            print 'Couldnt find bucket. Gotta download from database'
    
    else:
        # TODO:
	#Download via links (define a couple functions for each) 
    	# TODO - This seems like a bulky, ugly function right now
	#    I should probably check_bucket_exists as its own function
 	#    
    # Download files
    # if ftp_path, just do the ftp thing
    # if mtbls is prefix, download_mtlbs()
    # if ST is prefix of study, download_workbench()
    pass

download_data('poop')
#
