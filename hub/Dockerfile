ARG JUPYTERHUB_VERSION
FROM jupyterhub/jupyterhub:${JUPYTERHUB_VERSION}

# https://jupyterhub.readthedocs.io/en/latest/tutorial/getting-started/security-basics.html#using-letsencrypt
ADD https://raw.githubusercontent.com/datajoint/nginx-docker/master/nginx/fullchain.pem /etc/letsencrypt/live/fakeservices.datajoint.io/fullchain.pem
ADD https://raw.githubusercontent.com/datajoint/nginx-docker/master/nginx/privkey.pem /etc/letsencrypt/live/fakeservices.datajoint.io/privkey.pem

COPY ./jupyter-datajoint-extensions /tmp/jupyter-datajoint-extensions
COPY ./config/jupyterhub_config.py /etc/jupyterhub/jupyterhub_config.py
RUN pip install dockerspawner oauthenticator /tmp/jupyter-datajoint-extensions