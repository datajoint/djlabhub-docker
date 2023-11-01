ARG JUPYTERHUB_VERSION
FROM quay.io/jupyter/minimal-notebook:hub-${JUPYTERHUB_VERSION}

COPY ./config /tmp/config

USER root
RUN \
    # Install dependencies: apt
    bash /tmp/config/apt_install.sh \
    # Add startup hook
    && cp /tmp/config/before_start_hook.sh /usr/local/bin/before-notebook.d/ \
    && chmod +x /usr/local/bin/before-notebook.d/before_start_hook.sh \
    # Add jupyterhub_config
    && cp /tmp/config/jupyter*config*.py /etc/jupyter/

USER ${NB_UID}
ARG PYTHON_VERSION
RUN \
    # remove default work directory
    [ -d "/home/jovyan/work" ] && rm -r /home/jovyan/work \
    # Install dependencies: pip and conda
    && conda install -y -n base python=${PYTHON_VERSION} \
    && pip install -r /tmp/config/pip_requirements.txt \
    && conda install --yes --file /tmp/config/conda_requirements.txt \
    && conda clean --all -f -y 
