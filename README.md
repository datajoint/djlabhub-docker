# djlabhub-docker

## Table of Contents
  - [Introduction](#introduction)
  - [Quick Start](#quick-start)
  - [Build Jupyterhub Singleuser Image](#build-jupyterhub-singleuser-image)
    - [Configuration](#configuration)
    - [Build](#build)
    - [Test in Local Jupyterhub](#test-in-local-jupyterhub)
      - [Local Jupyterhub Configuration](#local-jupyterhub-configuration)
      - [Start Local Jupyterhub](#start-local-jupyterhub)

## Introduction

This image is made for building customized jupyterhub profile/server option images. It was originally based on [datajoint/djlab](https://github.com/datajoint/djlab-docker) all the way up to [datajoint/djbase](https://github.com/datajoint/djbase-docker). To reduce the maintenance effort, we decided to use quay.io/jupyter/minimal-notebook as the base image. We also kept the previous implementation under `legacy` directory, just in case there are unforeseen issues with the new implementation.

> **Note**: `datajoint/djlab` is deprecated since the `singleuser` part of this image overlaps with the `djlab` image, it'll run jupyter lab server by default.


## Quick Start
Directory explain:
- `~/legacy` contains the old implementation of the image
- `~/singleuser` is used to build the jupyterhub profile images
- `~/hub` is a Docker based jupyterhub host server using DockerSpawner and Docker-in-Docker to launch jupyterhub singleuser server as a Docker container, in order to locally validate the singleuser images for development purpose.(**Don't recommend to use this in production, due to the security concern of Docker-in-Docker**)


## Build Jupyterhub Singleuser Image

### Configuration
We put all the dependencies in the `~/singleuser/config` directory including:
- `apt_install.sh` for system level dependencies
- `pip_requirements.txt` for python packages
- `before_start_hook.sh` to run before the jupyterhub singleuser server starts, [doc](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/common.html#startup-hooks)
- `jupyter**config.py` for jupyter related configurations
  - Jupyter Server Config, [doc](https://jupyter-server.readthedocs.io/en/latest/other/full-config.html#other-full-config)
  - Jupyter Notebook Server Config, [doc](https://jupyter-notebook.readthedocs.io/en/5.7.4/config.html)
  - Jupyter Lab Server Config, [doc](https://jupyterlab-server.readthedocs.io/en/latest/api/app-config.html)
  - Optionally, you can add more configurations for ipython kernel, etc.
> **Note**: We added `jupyter**config.py` to extract configurations from the environment variables for some that are not supported to set by environment variables directly. The goal is to make the jupyterhub profile list clear and easy to maintain.

### Build
```
# make the .env file from the example.env
set -a && source .env && set +a
docker compose build

# To run this image as local jupyterlab server for testing
# The default password is set by the `JUPYTER_SERVER_APP_PASSWORD` in the container
docker compose up djlab
```

### Test in Local Jupyterhub
#### Local Jupyterhub Configuration
Similarly to the singleuser image, we the `jupyterhub_config.py` in the `~/hub/config` directory, you need to modify the `c.DockerSpawner.container_image` and `c.DockerSpawner.environment` to configure your singleuser server container.

#### Start Local Jupyterhub
> **Note**: Local Jupyterhub requires jupyterhub host container to mount `/var/run/docker.sock:/var/run/docker.sock` to enable Docker-in-Docker, [doc](https://devopscube.com/run-docker-in-docker/) 
```
# make the .env file from the example.env
# OAUTH2 related configurations are not necessary
# since the c.JupyterHub.authenticator_class = "jupyterhub.auth.DummyAuthenticator"
set -a && source .env && set +a

# It takes any random username and password
docker compose up
```


