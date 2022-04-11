#!/bin/sh
echo "DataJoint global config change detected. Backing up..." 1>&2
cp ~/.datajoint_config.json "$1"
echo "$1"