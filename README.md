Metabolomics Processing
==============================

Description
---------------
Docker Container to reproducibly process metabolomics studies from Metabolights and Metabolomics Workbench using xcms and IPO.

User must input a yaml file detailing information about which files to process, then xcms/IPO should take care of the processing. See /user_input/study_info/yaml.template for more details.

Usage
----------

**Install Docker and docker-compose**<br>
Follow instructions [here](https://docs.docker.com/install/)

**Build the container**<br>
`docker-compose build` 
<br>(this will take a while to download all the dependencies. Go grab tea.)

**Enter the container**<br>
`docker-compose run --rm project bash`
<br> Now you'll have a bash session within the container

**Setup cloud environment**<br>
If you don't care to store all the raw data files in a cloud bucket, answer 'n' when it asks if you are using a cloud provider

If you're using cloud storage for datasets (datasets are big, you probably should), do: 
<br>
`python src/get_user_info.py` and give your bucket's path and cloud provider. Exit the container.

Google Cloud has been tested and works. AWS should too, but hasn't been tested. 


**Add {study}.yaml files to /user_input/study_info/**
<br>These files tell the program how to organize the raw data, and what type of mass spectrometer and column were used in order to parametrize xcms. See /user_input/study_files/ for examples and templates.

For example, /user_input/study_info/MTBLS315.yaml has two assays, uhplc_pos and uhplc_neg, the positive files are "*_P.mzML"

**Run the pipeline**
<br>
This will run the pipeline on every study that has a yaml file in /user_input/study_info/  

`python run_all.py --paralellism {number of pydoit process to start} --cores {Number of cores per pydoit process}` 

So, if you want to run two studies at once, with 5 cores each, do:
<br>
`nohup python run_all.py -p 2 -c 5 &`

I recommend at least 12Gb of RAM per process (not an exact number).
The number of cores you select depends on a couple things:
* If you already have xcms parameters in user_input/xcms_parameters/,  set `--cores` to whatever you want, speed/costwise
* If you don't have xcms parameters in user_input/xcms_parameters/, use `--cores 5`. IPO takes much longer than xcms, and only uses 5 cores the whole time (I use 5 randomly chosen samples for IPO, so it uses 5 cores to process them)

<br>

**Troubleshooting**
<br> Check the log files.

* /logs/doit_{study}.log to see if xcms failed, or if it was the downloading, organizing, or otherwise.
* /data/processed/{study}/{assay}/*.log to see if xcms or IPO failed.

Some datasets have corrupt files (MTBLS28, for example). Maybe you didn't convert RAW files to mzML/CDF/another xcms-friendly format


More Info
-----
**pydoit** is the automation tool that ties things together. It's sort of like Make, but python.

Known Issues
---------
* organization and documentation of src/ (A disorganized un-published scientific pipeline - *shocking*)
* Test on AWS
* Tests in general would be nice, too
* pydoit works breadth first for each study it finds - i.e. download MTBLS17 & MTBLS18, then run IPO on each, then xcms, then clean up. I'd prefer depth first to avoid running out of disk space when processing many studies.
* IPO... is it good? feels like I get more features than expected, but this is all conjecture. The alternative is guess-and-checking parameters or using non-xcms things and modifying the code accordingly.
* Need to have a docker container with a windows image that can run msconvert
* Implement CAMERA
* This should be able to run on a cluster with kubernetes or docker-swarm to make things faster, but I dunno how to do that right now.


Project Organization
------------

    ├── LICENSE
    ├── dodo.py            <- pydoit automation file - runs data-processing functions
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── notebooks          <- Jupyter notebooks.
    │
    ├── references         <- Notes to self while writing the project
    │
    ├── environment.yml    <- conda environment to reproduce results
    │
    ├── Dockerfile         <- Make the docker environment
    │
    ├── docker-compose.yml <- Link volumes between host and docker, open appropriate ports
    │
    │
    ├── src                <- Source code for use in this project. Honestly, a hot-mess that needs organization - the dodo.py shows how files are processed, but the analysis code is quite disorganized.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download studies and do preliminary data exploration (i.e. detect outliers, etc). TODO: needs better organization
    │   │
    │   ├── project_fxns   <- Assorted code associated with project. Needs organization
    │   ├── xcms_wrapper   <- processes raw data. Runs IPO if no user-provided parameters found, then runs xcms to identify peaks
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
