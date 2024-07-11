#!/bin/bash
echo "INFO::Datajoint Startup Hook"

# Changing Markdown Preview to preview as default
echo "INFO::Changing Markdown Preview to preview as default"
yq '.properties.defaultViewers.default = {"markdown":"Markdown Preview"}' \
  /opt/conda/share/jupyter/lab/schemas/@jupyterlab/docmanager-extension/plugin.json -o json -i

# clone and install DJLABHUB_REPO or DJLABHUB_REPO_SUBPATH
# for private repo, include PAT(Personal Access Token) in the https url
if [[ ! -z "${DJLABHUB_REPO}" ]]; then
  REPO_NAME=$(basename $DJLABHUB_REPO | sed 's/.git//')

  echo "INFO::Cloning repo $DJLABHUB_REPO"
  git clone $DJLABHUB_REPO $HOME/$REPO_NAME || echo "WARNING::Failed to clone ${DJLABHUB_REPO}. Continuing..."
  if [[ ! -z "${DJLABHUB_REPO_BRANCH}" ]]; then
    echo "INFO::Switch to branch $DJLABHUB_REPO_BRANCH"
    git -C $HOME/$REPO_NAME switch $DJLABHUB_REPO_BRANCH || echo "WARNING::Failed to checkout branch ${DJLABHUB_REPO_BRANCH}. Continuing..."
    ls -lah
    cd $HOME/$REPO_NAME
    ls -lah
    git branch
  fi

  if [[ $DJLABHUB_REPO_INSTALL == "TRUE" ]]; then
    echo "INFO::Installing repo"
    pip install -e $HOME/$REPO_NAME
  fi
fi