#!/bin/bash
set -ev  # exit on first error, print each command

echo "PMG_MAPI_KEY: 8pkvwRLQSCVbW2Fe" > ${HOME}/.pmgrc.yaml

abinit --version
abinit --build
abicheck.py --with-flow

# Run unit tests with nose.
#nosetests -v --with-coverage --cover-package=abipy --logging-level=INFO --doctest-tests
#nosetests -v --with-coverage --cover-package=abipy --doctest-tests

#./dev_scripts/pyclean.py .

pytest --cov-config=.coveragerc --cov=abipy -v --doctest-modules abipy \
    --ignore=abipy/gui --ignore=abipy/data/refs --ignore=abipy/examples/plot --ignore=abipy/examples/flows
#cd ..

# This is to run the integration tests (append results)
# integration_tests are excluded in setup.cfg
if [[ "${TRAVIS_PYTHON_VERSION}" == "3.6" && "${TRAVIS_OS_NAME}" == "linux" ]]; then 
    pytest -n 2 --cov-config=.coveragerc --cov=abipy --cov-append -v abipy/integration_tests 
fi

# Generate documentation
if [[ "${TRAVIS_PYTHON_VERSION}" == "2.7" && "${TRAVIS_OS_NAME}" == "linux" ]]; then
    pip install -r ./docs/requirements.txt
    cd ./docs && export READTHEDOCS=1 && make && unset READTHEDOCS && cd ..;
fi
