Documentation for the DataJoint's DJLab Image
#############################################

| A docker image optimized for deploying to `JupyterHub <https://jupyterhub.readthedocs.io/en/stable/>`_ a `JupyterLab <https://jupyterlab.readthedocs.io/en/stable/>`_ environment with `DataJoint Python <https://github.com/datajoint/datajoint-python>`_.
| For more details, have a look at `prebuilt images <https://hub.docker.com/r/datajoint/djlabhub>`_, `source <https://github.com/datajoint/djlabhub-docker>`_, and `documentation <https://datajoint.github.io/djlabhub-docker>`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Launch Locally
**************

Debian
======
.. code-block:: shell

   docker-compose -f dist/debian/docker-compose.yaml --env-file config/.env up --build

Alpine
======
.. code-block:: shell

   docker-compose -f dist/alpine/docker-compose.yaml --env-file config/.env up --build

Features
********

- TBD

Usage Notes
***********

- To make files and notebooks available within the image:

   - Add the necessary files to a publicly available github repository.
   - Set the environment variable ``Djlabhub_NotebookRepo_Target`` to the repository url containing your files.
- To use files and notebooks from a subpath of a github repository:

   - Select the correct repository as above.
   - Set the environment variable ``Djlabhub_NotebookRepo_Subpath`` to path to your files from the base of the repository.
   

Testing
*******

To rebuild and run tests locally, execute the following statements:

.. code-block:: shell

   set -a  # automatically export sourced variables
   . config/.env  # source config for build and tests
   docker buildx bake -f dist/${DISTRO}/docker-compose.yaml --set *.platform=${PLATFORM} --set *.context=. --load  # build image
   tests/main.sh  # run tests
   set +a  # disable auto-export behavior for sourced variables

Base Image
**********

Build is a child of `datajoint/djlab <https://datajoint.github.io/djlab-docker/>`_.
