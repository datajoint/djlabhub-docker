#!/bin/sh
run_post_start_jobs() {
	# Copy global config
	if [ ! -z "${DJ_PASS}" ]; then
		# Handle password since available
		cp /usr/local/bin/.datajoint_config.json ~/
		sed -i "s|\"database.host\": null|\"database.host\": \"${DJ_HOST}\"|g"\
			~/.datajoint_config.json
		sed -i "s|\"database.user\": null|\"database.user\": \"${DJ_USER}\"|g"\
			~/.datajoint_config.json
		sed -i "s|\"database.password\": null|\"database.p.+word\": \"${DJ_PASS}\"|g"\
			~/.datajoint_config.json
	elif [ -z "${DJ_PASS}" ] && [ ! -f "~/.datajoint_config.json" ]; then
		# Password may be unset but config has not been initialized
		rm ~/../common/.${DJLABHUB_SERVERNAME}_datajoint_config.json || \
			echo "No ${DJLABHUB_SERVERNAME} datajoint config backup detected"
		cp /usr/local/bin/.datajoint_config.json ~/
		sed -i "s|\"database.host\": null|\"database.host\": \"${DJ_HOST}\"|g" \
			~/.datajoint_config.json
		sed -i "s|\"database.user\": null|\"database.user\": \"${DJ_USER}\"|g" \
			~/.datajoint_config.json
		for i in ~/../common/.*datajoint_config.json; do
			if [ ! "$i" = "${HOME}/../common/.*datajoint_config.json" ] && \
					[ "$(jq -r '.["database.host"]' $i)" = \
						"$DJ_HOST" ] && \
					[ "$(jq -r '.["database.user"]' $i)" = \
						"$DJ_USER" ]; then
				sed -i "$(echo "s|\"database.password\": null|\
					\"database.password\": \""$(jq -r \
						'.["database.password"]' $i)"\"|g" | \
					tr -d '\n' | tr -d '\t')" ~/.datajoint_config.json
				break
			fi
		done
	fi
	cp ~/.datajoint_config.json ~/../common/.${DJLABHUB_SERVERNAME}_datajoint_config.json
	# Start monitoring global config
	BACKUP_TARGET=~/../common/.${DJLABHUB_SERVERNAME}_datajoint_config.json
	sh - <<-EOF &
	otumat watch -f ~/.datajoint_config.json -s dj_config_backup.sh "${BACKUP_TARGET}"
	EOF
	if [ ! -z "${DJLABHUB_REPO_TARGET}" ]; then
		# Remove files and hidden files
		rm -R /home/notebooks/* || echo "no files to remove"
		rm -rf /home/notebooks/.* 2> /dev/null || echo "no hidden files to remove"
		# Clone reference notebooks
		git clone $DJLABHUB_REPO_TARGET /home/notebooks
		
		# Pip install requirements from reference notebooks repo
		if [ -f "/home/notebooks/requirements.txt" ]; then
			# pip install --user -r /home/notebooks/requirements.txt
			pip install -r /home/notebooks/requirements.txt --upgrade
		fi
		if [ -f "/home/notebooks/setup.py" ]; then
			pip install /home/notebooks --upgrade 
		fi
		# Copy over only subpath
		mkdir /tmp/notebooks
		cp -R /home/notebooks/${DJLABHUB_REPO_TARGET_SUBPATH}/* /tmp/notebooks
		cp -r /home/notebooks/${DJLABHUB_REPO_TARGET_SUBPATH}/.[^.]* /tmp/notebooks
		# Remove files and hidden files
		rm -R /home/notebooks/*
		rm -rf /home/notebooks/.* 2> /dev/null
		# Move contents
		mv /tmp/notebooks/* /home/notebooks
		mv /tmp/notebooks/.[^.]* /home/notebooks
		# Remove temp notebooks directory
		rm -R /tmp/notebooks
	fi
}