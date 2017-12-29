#!/bin/bash
set -ev  # exit on first error, print each command

echo "PMG_MAPI_KEY: 8pkvwRLQSCVbW2Fe" > ${HOME}/.pmgrc.yaml

abinit --version
abinit --build
abicheck.py --with-flow

# Run unit tests with nose.
#nosetests -v --with-coverage --cover-package=abipy --logging-level=INFO --doctest-tests

pytest --cov-config=.coveragerc --cov=abipy -v --doctest-modules abipy \
    --ignore=abipy/gui --ignore=abipy/gw --ignore=abipy/htc

# This is to run the integration tests (append results)
pytest --cov-config=.coveragerc --cov=abipy --cov-append -v abipy/integration_tests 

# Generate documentation
if [[ "${PYTHON_VERSION}" == "3.6" && "${TRAVIS_OS_NAME}" == "linux" ]]; then
    pip install -q -r ./docs/requirements.txt
    cd ./docs && export READTHEDOCS=1 && make && unset READTHEDOCS && cd ..;
fi
