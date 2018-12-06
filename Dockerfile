# Dockerfile for conda/python/R projects that I might use Jupyter for.

FROM python:3
LABEL maintainer="Isaac Rockafellow <isaac.rockafellow@gmail.com>"
WORKDIR /home/

# Go from least-often changed to most often changed, i.e.
#First get OS packages you want - apt-get install everything you need

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


# Then get packages needed for installation i.e. conda install things
# or npm install things
COPY environment.yml ./
RUN conda env create -f ./environment.yml
SHELL ["/bin/bash", "-c"]
# Running "jupyter-notebook" will startup a session you can access with the right ssh-tunneling
RUN echo "alias jupyter-notebook='jupyter-notebook --no-browser --ip=0.0.0.0 --allow-root'" >> ~/.bashrc 
RUN echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc 
ENV PYTHONPATH=$PYTHONPATH:/home/
# Start the environment. Might be unecessary..?
# and update the environment everytime you login
# RUN echo 'conda env update -f ./environment.yml' >> ~/.bashrc
RUN awk '/name:/ {print $2}' ./environment.yml | xargs echo 'source activate' >> ~/.bashrc
# Update the conda env so we don't have to re-build the container every time 
# we need a new pacakge
#CMD conda env update -f ./environment.yml
CMD source activate $(awk '/name:/ {print $2}' ./environment.yml) && doit &> doit.log
#ENV PATH /opt/conda/envs/seg_map/bin/:$PATH
