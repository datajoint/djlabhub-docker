#!/bin/bash

assert ()
{
	E_PARAM_ERR=98
	E_ASSERT_FAILED=99

	if [ -z "$3" ]; then
		return $E_PARAM_ERR
	fi

	lineno=$3
	# echo "$2"
	if ! eval "$2"; then
		echo "Assertion ($1) failed:  \"$2\""
		echo "File \"$0\", line $lineno"
		exit $E_ASSERT_FAILED
	else
		echo "---------------- TEST[$SHELL_CMD_FLAGS]: $1 ✔️ ----------------" | \
			tr -d '\t'
	fi
}
validate () {
	assert "system packages installed" "[ $($SHELL_CMD 'eval "$(cat)"' <<-END
		git --version > /dev/null && \
		otumat --version > /dev/null && \
		vim --version > /dev/null && \
		mysql --version > /dev/null && \
		echo done
	END
	) == 'done' ]" $LINENO
}
# set image context
REF=$(eval \
	"echo $(cat dist/${DISTRO}/docker-compose.yaml | grep 'image:' | awk '{print $2}')")
TAG=$(echo $REF | awk -F':' '{print $2}')
IMAGE=$(echo $REF | awk -F':' '{print $1}')
SHELL_CMD_TEMPLATE="docker run --rm -i \$SHELL_CMD_FLAGS $REF \
	$([ ${DISTRO} == 'debian' ] && echo bash || echo sh) -c"
# determine reference size
if [ $DISTRO == alpine ] && [ $PY_VER == '3.10' ]; then
	SIZE_LIMIT=991
elif [ $DISTRO == alpine ] && [ $PY_VER == '3.9' ]; then
	SIZE_LIMIT=723
elif [ $DISTRO == alpine ] && [ $PY_VER == '3.8' ]; then
	SIZE_LIMIT=682
elif [ $DISTRO == alpine ] && [ $PY_VER == '3.7' ]; then
	SIZE_LIMIT=693
elif [ $DISTRO == debian ] && [ $PY_VER == '3.10' ]; then
	SIZE_LIMIT=1210
elif [ $DISTRO == debian ] && [ $PY_VER == '3.9' ]; then
	SIZE_LIMIT=962
elif [ $DISTRO == debian ] && [ $PY_VER == '3.8' ]; then
	SIZE_LIMIT=915
elif [ $DISTRO == debian ] && [ $PY_VER == '3.7' ]; then
	SIZE_LIMIT=912
fi
SIZE_LIMIT=$(echo "scale=4; $SIZE_LIMIT * 1.02" | bc)
# verify size minimal
SIZE=$(docker images --filter "reference=$REF" --format "{{.Size}}" | awk -F'MB' '{print $1}')
assert "minimal footprint" "(( $(echo "$SIZE <= $SIZE_LIMIT" | bc -l) ))" $LINENO
# run tests
SHELL_CMD=$(eval "echo \"$SHELL_CMD_TEMPLATE\"")
validate
