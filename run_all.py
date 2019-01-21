import glob
import os
import time
import docker
import argparse

# To call: python run_all.py -p {number of parallel proc to run}


# This script must be in the top level of the
# project directory
# It will find all the yaml files in user_input/study_info/
# and run the pipeline from dodo.py on all of them
# in a new container for each. They don't need a new container,
# technically, but in order to run one at a time,
# I want this script to wait for container to finish work and exit

# 1 - Find out the resources available,
# estimate you need 5 CPUs and ~ 12gigs of RAM
# per study.
# 2 - collect running containers in a list and only continue for loop
# if an opening arises. Need to write a function that reloads
# containers and pops off any that have stopped.
def pop_stopped_containers(container_list):
    '''

    reload() each container and check if still running.
    remove containers that aren't there and
    return container_list with only containers still running
    '''
    updated_container_lst = []
    for container in container_list:
        # If you can't find the container, don't append it
        # means it has been removed/exited
        try:
            container.reload()
        except docker.errors.NotFound:
            continue    

        if container.status == 'exited':
            try:
                container.remove()
            except docker.errors.NotFound:
                continue

        if container.status == 'paused':
            try:
                container.restart()
            except docker.errors.APIError:
                container.remove()
                continue

        if container.status != 'exited':
            updated_container_lst.append(container)
            
    return updated_container_lst
            

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--paralellism', 
    help=('The number of parallel processes you want to start. Each will'
        ' start a new pydoit run for a different study')
    )
args = parser.parse_args()
parallelism = int(args.paralellism)

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
# Keep track of containers that are running
container_list = []
for sf in summary_files:
    study = os.path.split(sf)[-1].replace('.yaml', '')
    # Runs pydoit in conda environment
    log_dir = os.path.join(script_path, 'logs')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    # Command that will be run in container - starts the conda env
    # and runs doit
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
    container_list.append(container)
    while len(container_list) == parallelism:
        # wait until one of the containers ends
        time.sleep(60)
        container_list = pop_stopped_containers(container_list)
        
