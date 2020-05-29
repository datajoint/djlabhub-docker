ARG PY_VER

from raphaelguzman/djlab:py${PY_VER}-alpine as jup_build
ARG JUPYTERHUB_VER

user root
run apk add git mysql-client jq inotify-tools

USER dja:anaconda
RUN \
    umask u+rwx,g+rwx && \
    export PY_VER=$(python -c "import sys;print(sys.version)" | head -1 | awk '{print $1}') && \
    # conda install -yc conda-forge python=$PY_VER jupyterhub=$JUPYTERHUB_VER && \
    # conda install -yc conda-forge python=$PY_VER nodejs=10.12.0 && \
    pip install --no-cache-dir jupyterhub==$JUPYTERHUB_VER && \
    # jupyter labextension install @jupyterlab/hub-extension && \
    conda clean -ya && \
    chmod -R o+w /home/dja/.cache

# #Squashed Final Image
FROM scratch
COPY --from=jup_build / /
ENV PYTHON_USER dja
RUN chmod 4755 /startup && /startup 3000 anaconda
LABEL maintainerName="Raphael Guzman" \
      maintainerEmail="raphael@vathes.com" \
      maintainerCompany="DataJoint"
USER dja:anaconda
ENV HOME /home/dja
ENV LANG C.UTF-8
ENV APK_REQUIREMENTS /apk_requirements.txt
ENV PIP_REQUIREMENTS /pip_requirements.txt
ENV CONDA_REQUIREMENTS /conda_requirements.txt
ENV PATH "/home/dja/.local/bin:/opt/conda/bin:$PATH"
ENTRYPOINT ["/entrypoint.sh"]
WORKDIR /src
VOLUME /src
VOLUME /tmp/.X11-unix
EXPOSE 8888
CMD ["jupyterhub-singleuser"]