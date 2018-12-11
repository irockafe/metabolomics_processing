# Dockerfile for conda/python/R projects that I might use Jupyter for.

FROM python:3
LABEL maintainer="Isaac Rockafellow <isaac.rockafellow@gmail.com>"
WORKDIR /home/

# Go from least-often changed to most often changed, i.e.
#First get OS packages you want - apt-get install everything you need
# Then get conda packages

# Install conda
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 
ENV PATH /opt/conda/bin:$PATH
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-4.5.4-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    cp ~/.bashrc /home/ && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> .bashrc && \
    echo "conda activate base" >> .bashrc 

# Get vim and gcloud v.227.0.0
RUN apt-get update \
	&& apt-get install -y vim \
	&& wget https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-227.0.0-linux-x86_64.tar.gz -P /usr/local/ \
	&& tar -C /usr/local/ -xvf /usr/local/google-cloud-sdk-227.0.0-linux-x86_64.tar.gz \
	&& /usr/local/google-cloud-sdk/install.sh --quiet 
	# && /usr/local/google-cloud-sdk/bin/gcloud init
# Add gcloud commands to path
# Add /home/ to python-path so can import my code at 
# /home/src/
ENV PATH $PATH:/usr/local/google-cloud-sdk/bin 
ENV PYTHONPATH=$PYTHONPATH:/home/
# copy your bashrc to docker - makes
# developing in the container actually nice
COPY .bashrc /root/
COPY environment.yml ./
# Enter your conda env everytime you start a bash shell in
# the container
# RUN echo 'conda env update -f ./environment.yml' >> ~/.bashrc
RUN awk '/name:/ {print $2}' ./environment.yml | xargs echo 'source activate' >> ~/.bashrc
# Running "jupyter-notebook" will startup a session you can access with the right ssh-tunneling
RUN echo "alias jupyter-notebook='jupyter-notebook --no-browser --ip=0.0.0.0 --allow-root'" >> ~/.bashrc \
	&& echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc \
	# package for aws-cli
	&& apt-get install -y groff

# Then get packages needed for installation i.e. conda install things
# or npm install things
# copy your bashrc into docker
RUN conda env create -f ./environment.yml
SHELL ["/bin/bash", "-c"]
# Copy vimrc
COPY .vimrc /root/
# run doit if you just do ">> docker-compose run -d project" 
CMD source activate $(awk '/name:/ {print $2}' ./environment.yml) && doit &> doit.log
#ENV PATH /opt/conda/envs/seg_map/bin/:$PATH
