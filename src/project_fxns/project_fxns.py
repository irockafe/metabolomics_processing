# Utility functions used in more than one script
import os
import yaml
import subprocess


class Storage():
    def __init__(self):
        # get cloud provider and bucket path
        path = '/home/user_input/user_settings.yml'
        yml = yaml.load(file(path, 'r'))
        self.cloud_provider = yml['cloud_provider']
        self.storage_path = yml['storage']
        # ensure consistent slashes
        if self.storage_path[-1] == '/':
            self.storage_path = self.storage_path[:-1]
   
    def bucket_exists(self, path):
        # checks if the path to file exists
        # return bool
        # make sure they're giving you relative paths
        if path[0] == '/':
            path = path[1:]
        if self.cloud_provider == 'amazon':
            ls_s3 = ("nohup aws s3 ls  '{s3_path}/{path}'".format(
                s3_path=self.storage_path, path=path)
                )
            check_bucket = subprocess.call(ls_s3, shell=True)
            if check_bucket == 0:
                return True
            else:
                return False

        if self.cloud_provider == 'google':
            ls_gcloud = ("gsutil ls {gcloud}/{path}".format(
                gcloud=(self.storage_path), path=path)
                )
            # returns 0 if directory exists, 1 otherwise
            check_bucket = subprocess.call(ls_gcloud, shell=True)
            if check_bucket == 0:
                return True
            else:
                return False

    def sync_to_storage(self, local_path):
        # syncs local to storage bucket

        # if local_path is absolute, i.e. /home/Data/raw/poop.data
        # drop the /home/
        if '/home/' in local_path:
            relative_path = local_path.replace('/home/', '')
        else:
            relative_path = local_path

        if self.cloud_provider == 'amazon':
            sync = ("nohup aws s3 sync '{local_path}' ".format(
                    local_path=local_path)
                +
               "'{s3_path}/{path}'".format(s3_path=self.storage_path,
                   path=relative_path)
               )
            logging.info("Sync-ing to cloud with:\n%s" % sync)
            subprocess.call(sync, shell=True)

        if self.cloud_provider == 'google':
            sync = ('nohup gsutil rsync -r {path} {storage}/{path}'.format(
                path=local_path, storage=self.storage_path)
                )
            logging.info("Sync-ing to cloud with:\n%s" % sync)
            subprocess.call(sync, shell=True)

    def sync_to_local(self, local_path):
        # syncs sotrage to local
        # syncs local to storage bucket

        # if local_path is absolute, i.e. /home/Data/raw/poop.data
        # drop the /home/
        if '/home/' in local_path:
            relative_path = local_path.replace('/home/', '')
        else:
            relative_path = local_path

        if self.cloud_provider == 'amazon':
            sync = ("nohup aws s3 sync '{s3}/{path}' ".format(
                s3=self.storage_path, 
                path=relative_path)
                +
                "'{local_path}'".format(local_path=local_path)
                )
            logging.info("Sync-ing to local with:\n%s" % sync)
            subprocess.call(sync, shell=True)

        if self.cloud_provider == 'google':
            sync = ('nohup gsutil rsync -r {storage}/{path} {path}'.format(
                storage=self.storage_path, path=local_path)
                )
            logging.info("Sync-ing to local with:\n%s" % sync)
            subprocess.call(sync, shell=True)


#
