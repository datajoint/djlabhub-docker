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
    # Add jupyter*config*.py
    && cp /tmp/config/jupyter*config*.py /etc/jupyter/

RUN \
    # remove default work directory
    [ -d "/home/jovyan/work" ] && rm -r /home/jovyan/work \
    # Install dependencies: pip
    && pip install -r /tmp/config/pip_requirements.txt
