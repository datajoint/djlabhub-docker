ARG JUPYTERHUB_VERSION
FROM quay.io/jupyter/minimal-notebook:hub-${JUPYTERHUB_VERSION}

ARG PYTHON_VERSION
RUN if [ "$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')" != "${PYTHON_VERSION}" ]; then \
    echo "Installing python ${PYTHON_VERSION}.." && conda install --quiet --no-pin --yes python=${PYTHON_VERSION}; \
    else echo "Python version matching"; \
    fi

USER root
COPY ./config /tmp/config
COPY ./ipython-datajoint-creds-updater /tmp/ipython-datajoint-creds-updater
RUN \
    # Install dependencies: apt
    bash /tmp/config/apt_install.sh \
    # Add startup hook
    && cp /tmp/config/before_start_hook.sh /usr/local/bin/before-notebook.d/ \
    && chmod +x /usr/local/bin/before-notebook.d/before_start_hook.sh \
    # Add jupyter*config*.py
    && cp /tmp/config/jupyter*config*.py /etc/jupyter/ \
    && mkdir /etc/jupyter/labconfig/ \
    && cp /tmp/config/*.json /etc/jupyter/labconfig/ \
    # Autoload extension in IPython kernel config
    && mkdir -p /etc/ipython \
    && echo "c.IPKernelApp.extensions = ['ipython_datajoint_creds_updater.extension']" > /etc/ipython/ipython_kernel_config.py

USER $NB_UID
RUN \
    # remove default work directory
    [ -d "/home/jovyan/work" ] && rm -r /home/jovyan/work \
    # Install dependencies: pip
    && pip install /tmp/ipython-datajoint-creds-updater -r /tmp/config/pip_requirements.txt


# CODE-SERVER INSTALLATION
ARG code_server_proxy_wheel="jupyter_codeserver_proxy-1.0b3-py3-none-any.whl"
ARG JUPYTER_CODESERVER_PROXY_DIR="jupyter_codeserver_proxy_dir"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

# prerequisites ----
RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# creation of the jupyter_codeserver_proxy package ----
WORKDIR $HOME/$JUPYTER_CODESERVER_PROXY_DIR
COPY setup.py /${HOME}/${JUPYTER_CODESERVER_PROXY_DIR}
COPY jupyter_codeserver_proxy /${HOME}/${JUPYTER_CODESERVER_PROXY_DIR}/jupyter_codeserver_proxy
RUN python setup.py bdist_wheel
WORKDIR ../..

# code-server install ----
#TODO: replace by wget already installed in the imag
RUN curl -fsSL https://code-server.dev/install.sh | sh && \
    rm -rf "${HOME}/.cache"

USER $NB_UID

# jupyter-server-proxy + code-server proxy install ----
USER root
RUN conda install --quiet --yes \
    'jupyter-server-proxy' && \
    jupyter labextension install @jupyterlab/server-proxy --version latest && \
    pip install --quiet --no-cache-dir "${HOME}/${JUPYTER_CODESERVER_PROXY_DIR}/dist/${code_server_proxy_wheel}" && \
    rm -rf "${HOME}/${JUPYTER_CODESERVER_PROXY_DIR}" && \
    jupyter lab clean -y && \
    npm cache clean --force && \
    conda clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

WORKDIR $HOME
RUN touch .gitconfig
