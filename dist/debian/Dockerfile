ARG PY_VER

FROM raphaelguzman/djlab:py${PY_VER}-debian as jup_build
ARG JUPYTERHUB_VER

USER root
RUN \
    apt install git mysql-client jq inotify-tools vim -y && \
    mkdir /home/tutorial && \
    chown -R dja:anaconda /home/tutorial && \
    chmod g+w /home/tutorial && \
    mkdir /home/common && \
    chown -R dja:anaconda /home/common && \
    chmod g+w /home/common

USER dja:anaconda
RUN \
    umask u+rwx,g+rwx,o-rwx && \
    export PY_VER=$(python -c "import sys;print(sys.version)" | head -1 | awk '{print $1}') && \
    # conda install -yc conda-forge python=$PY_VER jupyterhub=$JUPYTERHUB_VER && \
    # conda install -yc conda-forge python=$PY_VER nodejs=10.12.0 && \
    pip install --no-cache-dir jupyterhub==$JUPYTERHUB_VER && \
    # jupyter labextension install @jupyterlab/hub-extension && \
    conda clean -ya && \
    find /opt/conda/conda-meta -user dja -exec chmod u+rwx,g+rwx,o-rwx "{}" \; && \
    chmod -R o+w /home/dja/.cache && \
    tmp=$(mktemp) && \
    jq '.properties.defaultViewers.default = {"markdown":"Markdown Preview"}' /opt/conda/share/jupyter/lab/schemas/@jupyterlab/docmanager-extension/plugin.json > "$tmp" && \
    mv "$tmp" /opt/conda/share/jupyter/lab/schemas/@jupyterlab/docmanager-extension/plugin.json && \
    chmod u+rwx,g+rwx,o-rwx /opt/conda/share/jupyter/lab/schemas/@jupyterlab/docmanager-extension/plugin.json
COPY ./utilities/README.md /home/
COPY ./utilities/entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh

# #Squashed Final Image
FROM scratch
COPY --from=jup_build / /
RUN chmod 4755 /startup && /startup -user=dja -new_home=/home/.dja
LABEL maintainerName="Raphael Guzman" \
      maintainerEmail="raphael@vathes.com" \
      maintainerCompany="DataJoint"
USER dja:anaconda
ENV LANG C.UTF-8
ENV APT_REQUIREMENTS /apt_requirements.txt
ENV PIP_REQUIREMENTS /pip_requirements.txt
ENV CONDA_REQUIREMENTS /conda_requirements.txt
ENV PATH "/home/.dja/.local/bin:/opt/conda/bin:$PATH"
ENTRYPOINT ["/entrypoint.sh"]
WORKDIR /home/.dja
VOLUME /home/.dja
VOLUME /home/common
VOLUME /opt/conda
VOLUME /tmp/.X11-unix
EXPOSE 8888
CMD ["jupyterhub-singleuser"]