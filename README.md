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
<br> Now you'll have a bash session within the 

**Setup cloud environment**<br>
If you're using cloud storage (datasets are big, you probably should), do: <br>
`python src/get_user_info.py` and give your bucket's path and cloud provider. Exit the container.

Google Cloud has been tested and works. AWS should, but hasn't been tested.

**Add {study}.yaml files to /user_input/study_info/**
<br>These files tell the program how to organize the raw data, and what type of mass spectrometer and column were used in order to parametrize xcms. See /user_input/study_files/ for examples and templates.

For example, /user_input/study_info/MTBLS315.yaml has two assays, uhplc_pos and uhplc_neg, the positive files are "*_P.mzML"

**Run the pipeline**
<br>
`docker-compose run -d project`
<br>This will run the pipeline on every yaml files in /user_input/study_info/ directory

**Troubleshooting**
<br> Check the log files.

* /home/dodo.log to see if xcms failed, or if it was the downloading, organizing, or otherwise.
* /data/processed/{study}/{assay}/*.log to see if xcms or IPO failed.

Some datasets have corrupt files (MTBLS28, for example). Maybe you didn't convert RAW files to mzML/CDF/another xcms-friendly format


More Info
-----
**pydoit** is the automation tool that ties things together. It's like Make, but in python.

Known Issues
---------
* organization and documentation of src/ (A disorganized un-published scientific pipeline - *shocking*)
* Test on AWS
* Tests in general would be nice, too
* The container would more useful (and container-y) if a new contianer was launched for each study/sub-study. Currently we just loop through studies found in /user_input/study_info/
    * This should allow  parallelization if you also let users specify the number of cores to use (currently uses max-cores - bad idea on shared cloud infrastructure)
* pydoit works breadth first for each study it finds - i.e. download MTBLS17 & MTBLS18, then run IPO on each, then xcms, then clean up. I'd prefer depth first to avoid running out of disk space when processing many studies.
* IPO... is it good? feels like I get more features than expected, but this is all conjecture. The alternative is guess-and-checking parameters or using non-xcms things and modifying the code accordingly.
* Need to have a docker container with a windows image that can run msconvert
* Implement CAMERA


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
