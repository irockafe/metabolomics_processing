import subprocess
import os
import argparse
import pipes
# Use this script to download files from ftp links.
# It contains a dictionary {ID: ftp_path} from Metabolights and
# Metabolomics Workbench, so you only have to specify
# an id.
# Otherwise you can to specify an http or ftp link yourself

# User defined variables
s3_path = "s3://almlab.bucket/isaac/revo_healthcare_data/"


def download_data(ftp_path, study, cwd,  s3_path=None, to_s3=False):
    '''
    GOAL - Given an {ftp_path} and unique {study_name}, download all files
    associated with that ftp path to {cwd}. If you want, send
    those files to s3 ({to_s3}=True)
    '''
    directory = '{cwd}/{study}/'.format(cwd=cwd, study=study)
    if to_s3:
        # check to see if already downloaded
        # prompt if they want to download it.
        ls_s3 = 'nohup aws s3 ls {s3_path}{study}'.format(s3_path=s3_path,
                                                          study=study)
        check_bucket = subprocess.call(ls_s3, shell=True)
        if check_bucket == 0:  # aws returns 1 if error, zero otherwise
            response = raw_input('Bucket for {study} already exists.'
                                 'Do you want to overwrite it? (y/n):'.format(
                                                                 study=study))
            if response == 'y':
                pass
            if response == 'n':
                print 'Ending script'
                return

    os.mkdir(directory)
    # Recursively download all files from ftp path into your directory
    # pipes.quote puts quotes around a path so that bash will
    # play nicely with whitespace and weird characters ik '()'
    wget_command = 'nohup wget -r -nH --cut-dirs=6 {ftp} -P {dir}'.format(
                                ftp=studies[study], dir=pipes.quote(directory))
    subprocess.call(wget_command, shell=True)
    if to_s3:
        send_s3 = 'nohup aws s3 sync {dir} {s3_path}{study}'.format(
                        dir=pipes.quote(directory),
                        s3_path=s3_path, study=study)
        subprocess.call(send_s3, shell=True)


parser = argparse.ArgumentParser()
parser.add_argument('-s', '--study',
                    help='Required. Name of the study, i.e. MTBLS315, '
                    'or ST000392')
parser.add_argument('-p', '--path',
                    help='Optional. Base directory Where you want to download'
                    'files to.'
                    '(default is current directory). Will make a new directory')
parser.add_argument('-s3',
                    help='Optional. Path to an s3 storage bucket '
                    'where you want files deposited')
parser.add_argument('-ftp',
                    help='Optional. Path to an ftp link.'
                    'All files will be downloaded from that link')
args = parser.parse_args()

print args.study
print args.path
print args.s3
print args.ftp

# Make a dictionary of ftp links to download
# These are the directory names and paths to download
# Unzipped files, copy all of them
lights = 'ftp://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/'
bench = 'ftp://www.metabolomicsworkbench.org/Studies/'
studies = {'MTBLS200': lights+'MTBLS200/*',
           'ST000392': bench+'ST000392.zip',
           'MTBLS191': lights+'MTBLS191/*',
           'ST000383': bench+'ST000383.zip',
           'MTBLS105': lights+'MTBLS105/*',
           'ST000397': bench + 'ST000397.7z',
           'ST000368': bench + 'ST000368.zip',
           'ST000369': bench + 'ST000369.zip',
           'ST000385': bench + 'ST000385.zip',
           'ST000386': bench + 'ST000386.zip',
           'ST000062': bench + 'ST000062.zip',
           'ST000063': bench + 'ST000063.zip',
           'ST000396': bench + 'ST000396.7z',
           'ST000381': bench + 'ST000381.zip',
           'ST000382': bench + 'ST000382.zip',
           'ST000329': bench + 'ST000329.zip',
           'ST000388': bench + 'ST000388.zip',
           'ST000389': bench + 'ST000389.zip',
           'MTBLS72': lights + 'MTBLS72/*',
           'MTBLS124': lights + 'MTBLS124/*',
           'ST000421': bench + 'ST000421.zip',
           'ST000422': bench + 'ST000422.zip',
           'ST000578': bench + 'ST000578.zip',
           'ST000041': bench + 'ST000041.zip',
           'MTBLS146': lights + 'MTBLS146/*',
           'MTBLS266': lights + 'MTBLS266/*',
           'MTBLS264': lights + 'MTBLS264/*',
           'ST000355': bench + 'ST000355.zip',
           'ST000356': bench + 'ST000356.zip',
           'MTBLS92': lights + 'MTBLS92/*',
           'MTBLS90': lights + 'MTBLS90/*',
           'MTBLS93': lights + 'MTBLS93/*',
           'ST000284': bench + 'ST000284.zip',
           'MTBLS253': lights + 'MTBLS253/*',
           'MTBLS280': lights + 'MTBLS280/*',
           'MTBLS279': lights + 'MTBLS279/*',
           'MTBLS19': lights + 'MTBLS19/*',
           'MTBLS17': lights + 'MTBLS17/*',
           'MTBLS218': lights + 'MTBLS218/*',
           'MTBLS20': lights + 'MTBLS20/*',
           'MTBLS404': lights + 'MTBLS404/*',
           'MTBLS148': lights + 'MTBLS148/*',
           'ST000450': bench + 'ST000450.zip',
           'MTBLS364': lights + 'MTBLS364/*',
           'MTBLS315': lights + 'MTBLS315/*',
           'ST000608': bench + 'ST000608.zip',
           'MTBLS352': lights + 'MTBLS352/*',
           'MTBLS358': lights + 'MTBLS358/*',
           'ST000284': bench + 'ST000284.zip',
           'ST000405': bench + 'ST000405.zip',
           'MTBLS354': lights + 'MTBLS354/*',
           'MTBLS28': lights + 'MTBLS28/*',
           'MTBLS427': lights + 'MTBLS427/*',
           'ST000291': bench + 'ST000291.zip',
           'ST000292': bench + 'ST000292.zip',
           'ST000046': bench + 'ST000046.7z',
           'ST000091': bench + 'ST000091.zip',
           'ST000045': bench + 'ST000045.7z',
           }

# If they're giving you a study name, but not an ftp address, and you can't
# find the name in your dictionary, raise an error
if (args.study is not None) and \
        (args.study not in studies.keys()) \
        and (not args.ftp):
    raise NameError("Couldn't find the study you were looking for. Add it to "
                    "the dictionary, or specify your own ftp link")

# If they gave an ftp link, use it. If not, find it in the {studies} dict
if args.ftp:
    ftp_path = args.ftp
else:
    ftp_path = studies[args.study]

if args.path:
    cwd = args.path
else:
    cwd = os.getcwd()

print cwd
# If you gave an s3 path, send the data to s3 as well
if args.s3:
    download_data(ftp_path, args.study, cwd, args.s3, to_s3=True)
else:
    download_data(ftp_path, args.study, cwd)
