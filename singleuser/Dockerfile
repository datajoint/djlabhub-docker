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
    && cp /tmp/config/*.json /etc/jupyter/labconfig/

USER $NB_UID
RUN \
    # remove default work directory
    [ -d "/home/jovyan/work" ] && rm -r /home/jovyan/work \
    # Install dependencies: pip
    && pip install /tmp/ipython-datajoint-creds-updater -r /tmp/config/pip_requirements.txt
