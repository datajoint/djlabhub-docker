ARG BASE_IMAGE_HASH
ARG PY_VER

FROM datajoint/djlab:py${PY_VER}-alpine-${BASE_IMAGE_HASH} as jup_build
ARG JUPYTERHUB_VER
# Initialize directories
USER root
RUN \
	mkdir /home/notebooks && \
	chown -R anaconda:anaconda /home/notebooks && \
	chmod g+w /home/notebooks && \
	mkdir /home/common && \
	chown -R anaconda:anaconda /home/common && \
	chmod g+w /home/common
USER anaconda:anaconda
# Install jupyterhub client, included utilities, and hide static HOME directory
COPY --chown=anaconda:anaconda ./dist/alpine/apk_requirements.txt \
	./config/pip_requirements.txt /tmp/
COPY ./utilities/dj_config_backup.sh /usr/local/bin/dj_config_backup.sh
RUN \
	umask u+rwx,g+rwx,o-rwx && \
	sed -ie "s|{{JUPYTERHUB_VER}}|${JUPYTERHUB_VER}|g" "$PIP_REQUIREMENTS" && \
	# conda install -yc conda-forge python=$PY_VER jupyterhub=$JUPYTERHUB_VER && \
	# conda install -yc conda-forge python=$PY_VER nodejs=10.12.0 && \
	export NEW_HOME=/home/.anaconda && \
	/entrypoint.sh echo "Requirements updated..." && \
	rm "$APK_REQUIREMENTS" && \
	rm "$PIP_REQUIREMENTS" && \
	cp -R $NEW_HOME /tmp/home_template && \
	conda clean -ya && \
	find /opt/conda/conda-meta -user anaconda -exec chmod u+rwx,g+rwx,o-rwx "{}" \; && \
	chmod -R o+w /home/.anaconda/.cache || echo "no cache..."
ENV HOME /home/.anaconda
COPY --chown=anaconda:anaconda ./config/README.md /home/
COPY ./config/datajoint_config.json /usr/local/bin/.datajoint_config.json
COPY --chown=anaconda:anaconda ./config/djlab_config.yaml $DJLAB_CONFIG
COPY ./utilities/add_entrypoint.sh /tmp/add_entrypoint.sh
# Add post start hook and copy over HOME template files on first boot (if mounted)
USER root:anaconda
RUN \
	(cat /tmp/add_entrypoint.sh && cat /entrypoint.sh | \
		tr '\n' '\r' | \
		sed \
			-e "s~#!/bin/sh~~g" \
			-e "$(echo 's~# Source shell intercept\r\
				~# Copy over template if HOME empty\r\
				[ "$(ls -A $HOME)" ] || cp -R /tmp/home_template/. $HOME\r\
				\# Source shell intercept\r~g' | tr -d '\n' | tr -d '\t')" \
			-e "$(echo 's~\t# Install Conda dependencies\r~\
				\t# Post start hook\r\
				\t[ -z \"$DJLABHUB_REPO_TARGET\" ] || \
					run_post_start_jobs\r\
				\t# Install Conda dependencies\r~g' | \
					tr -d '\n' | tr -d '\t')" | \
		tr '\r' '\n') > /tmp/entrypoint.sh && \
	mv /tmp/entrypoint.sh /entrypoint.sh && \
	chmod +x /entrypoint.sh && \
	rm /tmp/add_entrypoint.sh
USER anaconda:anaconda

# Squashed Final Image
FROM scratch
COPY --from=jup_build / /
LABEL maintainerName="Raphael Guzman" \
	maintainerEmail="raphael@datajoint.com" \
	maintainerCompany="DataJoint"
RUN rm -R /home/anaconda
USER anaconda:anaconda
ENV HOME /home/.anaconda
ENV LANG C.UTF-8
ENV APK_REQUIREMENTS /tmp/apk_requirements.txt
ENV PIP_REQUIREMENTS /tmp/pip_requirements.txt
ENV CONDA_REQUIREMENTS /tmp/conda_requirements.txt
ENV DJLAB_CONFIG /tmp/djlab_config.yaml
ENV PATH /opt/conda/bin:$PATH
ENTRYPOINT ["/entrypoint.sh"]
WORKDIR /home/.anaconda
VOLUME /home/.anaconda
VOLUME /home/common
VOLUME /tmp/.X11-unix
EXPOSE 8888
CMD ["jupyterhub-singleuser"]
