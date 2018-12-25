# Utility functions used in more than one script
import os
import yaml
import subprocess
import logging


class Storage():
    def __init__(self):
        # get cloud provider and bucket path
        path = '/home/user_input/user_settings.yml'
        yml = yaml.load(file(path, 'r'))
        self.cloud_provider = yml['cloud_provider']
        self.cloud_url_base = yml['storage']
   
    def bucket_exists(self, path):
        # checks if the path to file exists
        # return bool
        # make sure they're giving you relative paths
        #if path[0] == '/':
        #    path = path[1:]
        # TODO this assumes linux url joining
        cloud_url = os.path.join(self.cloud_url_base, path)
        if self.cloud_provider == 'amazon':
            ls_s3 = ("nohup aws s3 ls  '{aws_path}'".format(
                aws_path = cloud_url)
                )
            check_bucket = subprocess.call(ls_s3, shell=True)
            if check_bucket == 0:
                return True
            else:
                return False

        elif self.cloud_provider == 'google':
            ls_gcloud = ("gsutil ls {gcloud_path}".format(
                gcloud_path = cloud_url)
                )
            # returns 0 if directory exists, 1 otherwise
            check_bucket = subprocess.call(ls_gcloud, shell=True)
            if check_bucket == 0:
                return True
            else:
                return False

    def sync_to_storage(self, local_path, storage_path):
        # Local path is the path where data is
        # storage_path is where you want it in the cloud
        # syncs local to storage bucket
        cloud_url = os.path.join(self.cloud_url_base, storage_path)
        if self.cloud_provider == 'amazon':
            sync = "nohup aws s3 sync '{local_path}' '{s3_path}'".format(
                    local_path=local_path, s3_path=cloud_url)
                          
               
            logging.info("Sync-ing to cloud with:\n%s" % sync)
            subprocess.call(sync, shell=True)

        if self.cloud_provider == 'google':
            sync = "nohup gsutil rsync -r '{local}' '{gcloud_path}'".format(
                      local=local_path, 
                      gcloud_path=cloud_url) 
                      
            logging.info("Sync-ing to cloud with:\n%s" % sync)
            subprocess.call(sync, shell=True)

    def sync_to_local(self, local_path, storage_path):
        # syncs sotrage to local
        # syncs local_path to storage_path
        cloud_url = os.path.join(self.cloud_url_base, storage_path)
        if self.cloud_provider == 'amazon':
            sync = ("nohup aws s3 sync '{s3_path}' '{local_path}'".format(
                s3_path=self.cloud_url_base, 
                local_path=local_path)
                )
            logging.info("Sync-ing to local with:\n%s" % sync)
            subprocess.call(sync, shell=True)

        if self.cloud_provider == 'google':
            sync = ("nohup gsutil rsync -r '{gcloud_path}' '{local_path}'".format(
                gcloud_path=cloud_url,
                local_path=local_path)
                )
            logging.info("Sync-ing to local with:\n%s" % sync)
            subprocess.call(sync, shell=True)


def class_names(study, assay, 
        a_path, s_path, yaml_path):
    # Goal: output mapping b/t sample name, 
    #     MS Assay name, class labels
    #     Then output this info to its own file,
    #     since I'm guessint the user-input
    #     will make automating this a huge pain
    # paths to a_*.txt and s_*.txt 
    # Given yaml file with the correct class name
    # column listed, output a mapping b/t 
    # assay names and sample names and classes
    yml = yaml.load(file(yaml_path, 'r'))
    col_name = yml[study][assay]['class_label_column']
    a = (pd.read_csv(a_path, sep='\t')
            .set_index('Sample Name'))
    s = (pd.read_csv(a_path, sep='\t')
            .set_index('Sample Name'))
    mapping = pd.concat([a['MS Assay Name', 
        'Raw Spectral Data File'], s[col_name]]) 
    return mapping
