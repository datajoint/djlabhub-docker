ARG JUPYTERHUB_VERSION
FROM jupyterhub/jupyterhub:${JUPYTERHUB_VERSION}

COPY ./config/jupyterhub_config.py /etc/jupyterhub/jupyterhub_config.py
RUN pip install dockerspawner