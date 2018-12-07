# Utility functions used in more than one script
import os
import yaml


class Storage():
    def __init__(self, study):
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
            # TODO probably more direct/better way to do this
            if check_bucket == 0:
                return True
            else:
                return False

        if self.cloud_provider == 'google':
            #TODO
            pass

    def sync_to_storage(self, local_path, bucket_path):
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
        if self.cloud_provider == 'google':
            #TODO`
            pass

    def sync_to_local(self, local_path, bucket_path):
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
            subprocess.call(sync, shell=True)

        if self.cloud_provider == 'google':
            pass


#
