# Utility functions used in more than one script
import os
import pandas as pd

def walk_up(target):
    # Walk up directory until find target file/directory
    # in my case, mostly just looking for a user_settings.tab file
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
        file containing user defined stuff (local path, s3 path)
    '''
    user_settings_path = walk_up('user_settings.tab')
    pd.set_option("display.max_colwidth", 10000)
    user_settings = pd.read_csv(user_settings_path, sep='\t',
                                header=None, index_col=0,
                                dtype=str)
    return user_settings


def get_s3_path(study):
    user_settings = get_user_settings()
    s3_path = user_settings.loc['s3_path'].to_string(index=False, header=False)
    return s3_path

def get_local_path():
    user_settings = get_user_settings()
    local_path = user_settings.loc['local_path'].to_string(index=False,
                                                           header=False)
    return local_path

#
