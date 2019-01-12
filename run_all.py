import glob
import os
import time
import docker
# This script must be in the top level of the
# project directory
script_path = os.path.dirname(os.path.realpath(__file__))
# get all the summaryfiles with glob

summary_files = glob.glob(os.path.join(script_path, 'user_input',
                                       'study_info', '*.yaml'))
# First, start the docker client and build the image
# for launching containers
client = docker.from_env()
# Assume dockerfile is in same directory
img, json = client.images.build(path='.')
img_id = img.attrs['Id']
# TODO figure out how to do this with kubernetes engine or
# some other scheduler-type thing.
# currently just linearly processing studies
for sf in summary_files:
    study = os.path.split(sf)[-1].replace('.yaml', '')
    # Runs pydoit in conda environment
    log_dir = os.path.join(script_path, 'logs')
    if not os.path.exists(log_dir):
    	os.mkdir(log_dir)
    # Command that will be run in container
    cmd = ('''/bin/bash'''
           ''' -c "source activate'''
           ''' $(awk '/name:/ {print $2}' ./environment.yml)'''
           ''' && doit study=%s''' 
           ''' &>> logs/doit_%s.log"''' #% study
           ) % (study, study)
    # Start a container with the right image and command
    # and volume
    container = client.containers.run(img_id, command=cmd,
                                      detach=True,
                                      volumes={script_path:
                                               {'bind': '/home/',
                                                'mode': 'rw'}
                                               },
                                      stdout=True,
                                      stderr=True
                                      )
    container.reload()
    while container.status != 'exited':
        # tell it to wait a minute bit before re-checking
        time.sleep(1)
        # Try to reload, unless not found. If not found,
        # assume container exited and continue
        try:
            container.reload()
        except docker.errors.NotFound:
            break
    try:
        container.remove()
    except docker.errors.NotFound:
        pass
    raise hell
