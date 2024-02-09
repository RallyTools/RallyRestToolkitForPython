#!/bin/bash

colorize() { CODE=$1; shift; echo -e '\\033[0;'$CODE'm'$@'\\033[0m'; }
red()    { echo -e $(colorize 31 $@); }
green()  { echo -e $(colorize 32 $@); }
yellow() { echo -e $(colorize 33 $@); }

echo "set the text coloring functions"


#python3 -m pip install --upgrade pip
#pip3 install -q -r requirements.txt
pip3 install -q wheel
pip3 install -q clint
pip3 install -q twine==3.8.0

green "pyral package will be uploaded to local PyPI on repo-depot.f4tech.com/artifactory/python-local"
#ls -lart dist

PYRAL_VERSION="1.5.2"

REPO_DEPOT="http://repo-depot.f4tech.com/artifactory"
LOCAL_PYPI="python-local"
TARGET_PACKAGE="dist/pyral-${PYRAL_VERSION}-py3-none-any.whl"

yellow "    REPO_DEPOT: ${REPO_DEPOT}"
yellow "TARGET_PACKAGE: ${TARGET_PACKAGE}"

# produce a local .pypirc file so we can use the short hand for the target index server
cat << EOF > ./.pypirc
[distutils]
    index-servers =
        repo-depot

[repo-depot]
    repository = ${REPO_DEPOT}/api/pypi/${LOCAL_PYPI}

EOF
#cat ./.pypirc

yellow "all set for twine upload ..."

which twine
twine --version
UPLOADER="twine upload --config-file ./.pypirc -r repo-depot -u "" -p "" ${TARGET_PACKAGE}"
echo "${UPLOADER}"
twine upload --config-file ./.pypirc -r repo-depot -u "" -p "" ${TARGET_PACKAGE}

green "pyral package uploaded to Artifactory python-local"

